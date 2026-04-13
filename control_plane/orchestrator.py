"""Main orchestrator for the v2 control plane."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from control_plane.classifier.task_classifier import TaskClassifier
from control_plane.context_builder.packet_builder import PacketBuilder
from control_plane.legacy_experimental.prompt_budget import PromptBudget
from control_plane.contracts import DEFAULT_CONTRACT_VALIDATOR
from control_plane.execution import AgentExecutor, ExecutionPlanner, TaskStateMachine
from control_plane.hooks.on_handoff import OnHandoffHook
from control_plane.hooks.on_verification_fail import on_verification_fail
from control_plane.hooks.post_task import PostTaskHook
from control_plane.hooks.pre_task import PreTaskHook
from control_plane.legacy_experimental.memory.store_decisions import DecisionStore
from control_plane.legacy_experimental.memory.summarize_run import RunSummarizer
from control_plane.legacy_experimental.retriever.knowledge_retriever import KnowledgeRetriever
from control_plane.router.parallel_policy import ParallelPolicy
from control_plane.router.role_router import RoleRouter
from control_plane.runtime_metrics import RuntimeMetricsLogger
from control_plane.verifier.acceptance_checker import AcceptanceChecker
from control_plane.verifier.lint_runner import LintRunner
from control_plane.verifier.security_checker import SecurityChecker
from control_plane.verifier.test_runner import TestRunner
from control_plane.verifier.typecheck_runner import TypecheckRunner


@dataclass
class OrchestratorConfig:
    """Configuration paths for the orchestrator."""

    repo_root: Path
    runtime_dir: Path
    knowledge_dir: Path
    hub_dir: Path
    max_verification_retries: int = 3


class Orchestrator:
    """Coordinate classification, routing, retrieval, execution, and verification."""

    def __init__(self, config: OrchestratorConfig) -> None:
        self.config = config
        self.classifier = TaskClassifier(config.knowledge_dir)
        self.router = RoleRouter(config.knowledge_dir)
        self.parallel_policy = ParallelPolicy()
        self.retriever = KnowledgeRetriever(
            config.repo_root,
            config.knowledge_dir,
            config.hub_dir,
        )
        self.packet_builder = PacketBuilder(config.runtime_dir)
        self.execution_planner = ExecutionPlanner(config.runtime_dir)
        self.agent_executor = AgentExecutor(config.repo_root, config.runtime_dir)
        self.task_state_machine = TaskStateMachine(config.runtime_dir, config.hub_dir)
        self.prompt_budget = PromptBudget()
        self.acceptance_checker = AcceptanceChecker()
        self.lint_runner = LintRunner(config.repo_root)
        self.typecheck_runner = TypecheckRunner(config.repo_root)
        self.test_runner = TestRunner(config.repo_root)
        self.security_checker = SecurityChecker(config.repo_root)
        self.run_summarizer = RunSummarizer(config.runtime_dir)
        self.decision_store = DecisionStore(config.knowledge_dir / "memory")
        self.metrics_logger = RuntimeMetricsLogger(config.runtime_dir)
        self.pre_task_hook = PreTaskHook(config.repo_root)
        self.post_task_hook = PostTaskHook(config.runtime_dir)
        self.on_handoff_hook = OnHandoffHook(config.hub_dir)

    def run_task(self, task: dict[str, Any], session_id: str) -> dict[str, Any]:
        """Prepare a task packet and runtime plan without executing the task."""
        prepared = self._prepare_task(task, session_id)
        agent_output = self._build_planned_agent_output(
            execution_mode=prepared["execution_mode"],
            runtime_plan=prepared["runtime_plan"],
            runtime_plan_path=prepared["runtime_plan_path"],
            task_packet_path=prepared["task_packet_path"],
        )

        summary = self.run_summarizer.summarize(
            task=prepared["task"],
            session_id=session_id,
            agent_output=agent_output,
            runtime_plan=prepared["runtime_plan"],
            metrics=prepared["metrics"],
        )
        post_result = self.post_task_hook.run(
            task=prepared["task"],
            session_id=session_id,
            agent_output=agent_output,
            runtime_plan=prepared["runtime_plan"],
        )

        return {
            "pre_task": prepared["pre_task"],
            "classification": prepared["classification"],
            "routing": prepared["routing"],
            "execution_mode": prepared["execution_mode"],
            "runtime_plan": prepared["runtime_plan"],
            "runtime_plan_path": str(prepared["runtime_plan_path"]),
            "task_packet_path": str(prepared["task_packet_path"]),
            "metrics_path": str(self.metrics_logger.path_for(prepared["task"]["id"])),
            "summary": summary,
            "post_task": post_result,
        }

    def execute_task(
        self,
        task: dict[str, Any],
        session_id: str,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        """Run the full task lifecycle through execution, verification, and retry."""
        prepared = self._prepare_task(task, session_id)
        normalized_task = prepared["task"]
        task_id = normalized_task["id"]
        runtime_plan_path = prepared["runtime_plan_path"]
        packet_path = prepared["task_packet_path"]
        max_attempts = max_attempts or self.config.max_verification_retries

        state = self.task_state_machine.start(
            task=normalized_task,
            session_id=session_id,
            execution_mode=prepared["execution_mode"],
            runtime_plan_path=runtime_plan_path,
            task_packet_path=packet_path,
        )
        self.metrics_logger.record_state_transition(task_id, "prepared", 0, None)

        execution_results: list[dict[str, Any]] = []
        retry_results: list[dict[str, Any]] = []
        verification_report: dict[str, Any] = {
            "schema_version": "2.1",
            "task_id": task_id,
            "status": "failed",
            "checks": [],
            "next_context_needs": [],
            "recommended_next_role": prepared["execution_mode"]["primary_role"],
        }
        final_status = "failed"
        current_packet_path = packet_path

        for attempt in range(1, max_attempts + 1):
            self.task_state_machine.transition(
                task_id=task_id,
                status="executing",
                attempt=attempt,
                current_step="primary_execute",
                note="Starting execution attempt",
            )
            self.metrics_logger.record_state_transition(task_id, "executing", attempt, "primary_execute")
            self.task_state_machine.reset_runtime_plan(runtime_plan_path)

            packet = json.loads(current_packet_path.read_text(encoding="utf-8"))
            packet["task_packet_path"] = str(current_packet_path)
            execution_result = self.agent_executor.execute(
                task=normalized_task,
                packet=packet,
                runtime_plan=prepared["runtime_plan"],
                attempt=attempt,
            )
            execution_results.append(execution_result)
            self.metrics_logger.record_execution(task_id, execution_result)

            # Role gate block is deterministic - retrying won't help.
            # Break immediately and let the failure handoff happen.
            _is_role_gate_blocked = any(
                step.get('status') == 'blocked'
                for step in execution_result.get('step_results', [])
            )
            if _is_role_gate_blocked:
                final_status = 'failed'
                break

            self.task_state_machine.transition(
                task_id=task_id,
                status="executed",
                attempt=attempt,
                current_step="primary_execute",
                artifacts={"execution_report_path": execution_result["execution_report_path"]},
                note=execution_result.get("details", ""),
            )
            self.metrics_logger.record_state_transition(task_id, "executed", attempt, "primary_execute")

            for step_result in execution_result.get("step_results", []):
                self.task_state_machine.set_runtime_plan_step(
                    runtime_plan_path=runtime_plan_path,
                    step_name=step_result["name"],
                    status=step_result["status"],
                )
                if step_result["name"] != "primary_execute":
                    self.task_state_machine.transition(
                        task_id=task_id,
                        status="reviewing",
                        attempt=attempt,
                        current_step=step_result["name"],
                        note=step_result.get("details", ""),
                    )
                    self.metrics_logger.record_state_transition(
                        task_id,
                        "reviewing",
                        attempt,
                        step_result["name"],
                    )

            self.task_state_machine.transition(
                task_id=task_id,
                status="verifying",
                attempt=attempt,
                current_step="verification",
                note="Running verification",
            )
            self.metrics_logger.record_state_transition(task_id, "verifying", attempt, "verification")
            verification_report = self.run_verification(normalized_task, execution_result)

            if verification_report["status"] == "passed":
                final_status = "completed"
                break

            if attempt >= max_attempts:
                final_status = "failed"
                break

            retry_result = self.handle_verification_failure(
                task_packet_path=current_packet_path,
                verification_report_path=self._verification_report_path(task_id),
                attempt=attempt,
            )
            retry_results.append(retry_result)
            current_packet_path = Path(retry_result["retry_packet_path"])
            self.task_state_machine.transition(
                task_id=task_id,
                status="retrying",
                attempt=attempt,
                current_step="retry",
                artifacts={"retry_packet_path": retry_result["retry_packet_path"]},
                note="Verification failed; retry packet generated",
            )
            self.metrics_logger.record_state_transition(task_id, "retrying", attempt, "retry")

        handoff_path = self._maybe_create_failure_handoff(
            task=normalized_task,
            session_id=session_id,
            execution_mode=prepared["execution_mode"],
            verification_report=verification_report,
            final_status=final_status,
            execution_results=execution_results,
        )
        final_agent_output = self._build_terminal_agent_output(
            execution_mode=prepared["execution_mode"],
            runtime_plan_path=runtime_plan_path,
            task_packet_path=current_packet_path,
            execution_result=execution_results[-1] if execution_results else {},
            final_status=final_status,
            attempts=len(execution_results),
        )
        metrics = json.loads(self.metrics_logger.path_for(task_id).read_text(encoding="utf-8"))
        summary = self.run_summarizer.summarize(
            task=normalized_task,
            session_id=session_id,
            agent_output=final_agent_output,
            runtime_plan=json.loads(runtime_plan_path.read_text(encoding="utf-8")),
            metrics=metrics,
            verification_results=verification_report.get("checks", []),
        )
        post_result = self.post_task_hook.run(
            task=normalized_task,
            session_id=session_id,
            agent_output=final_agent_output,
            runtime_plan=json.loads(runtime_plan_path.read_text(encoding="utf-8")),
            verification_results=verification_report.get("checks", []),
        )
        task_state = self.task_state_machine.finalize(
            task_id=task_id,
            final_status=final_status,
            summary=summary,
            verification_report=verification_report,
            execution_results=execution_results,
            retries=retry_results,
            handoff_path=handoff_path,
            session_report_path=Path(post_result["session_report_path"]) if post_result.get("session_report_path") else None,
            quick_report_path=Path(post_result["quick_report_path"]) if post_result.get("quick_report_path") else None,
        )
        self.decision_store.store_task_decision(task_id, {
            "action": "task_completed" if final_status == "completed" else "task_failed",
            "final_status": final_status,
            "attempts": len(execution_results),
            "verification_status": verification_report.get("status"),
            "metrics_path": str(self.metrics_logger.path_for(task_id)),
            "done_report_path": task_state["done_report_path"],
        })

        return {
            "pre_task": prepared["pre_task"],
            "classification": prepared["classification"],
            "routing": prepared["routing"],
            "execution_mode": prepared["execution_mode"],
            "runtime_plan_path": str(runtime_plan_path),
            "task_packet_path": str(current_packet_path),
            "metrics_path": str(self.metrics_logger.path_for(task_id)),
            "execution_results": execution_results,
            "verification_report": verification_report,
            "retry_results": retry_results,
            "task_state": task_state,
            "summary": summary,
            "post_task": post_result,
        }

    def handle_verification_failure(
        self,
        task_packet_path: Path,
        verification_report_path: Path,
        attempt: int = 1,
    ) -> dict[str, Any]:
        """Handle verification failure with minimal context retry."""
        packet = json.loads(task_packet_path.read_text(encoding="utf-8"))
        result = on_verification_fail(
            repo_root=self.config.repo_root,
            task_packet_path=task_packet_path,
            verification_report_path=verification_report_path,
            attempt=attempt,
        )
        self.metrics_logger.record_retry(
            task_id=packet["task_id"],
            retry_packet_path=Path(result["retry_packet_path"]),
            additional_context_needed=result.get("additional_context_needed", []),
        )
        return result

    def run_verification(
        self,
        task: dict[str, Any],
        execution_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Run verification checks on agent output."""
        normalized_task = self._normalize_task(task)
        DEFAULT_CONTRACT_VALIDATOR.validate("task", normalized_task)

        checks: list[dict[str, Any]] = []
        checks.append(self.acceptance_checker.check(normalized_task, execution_result))

        changed_files = execution_result.get("changed_files", [])
        code_files = [
            path for path in changed_files
            if Path(path).suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
        ]
        if code_files:
            checks.append(self.lint_runner.run(code_files))
            checks.append(self.typecheck_runner.run(code_files))
            checks.append(self.security_checker.check(code_files))

        requested_tests = execution_result.get("test_paths")
        task_tests = normalized_task.get("inputs", {}).get("related_tests", [])
        if requested_tests or task_tests or execution_result.get("run_tests"):
            checks.append(self.test_runner.run(requested_tests or task_tests or None))

        all_passed = all(check.get("result") in {"passed", "skipped"} for check in checks)
        status = "passed" if all_passed else "failed"
        report = {
            "schema_version": "2.1",
            "task_id": normalized_task["id"],
            "status": status,
            "checks": checks,
            "next_context_needs": self._derive_next_context_needs(
                task=normalized_task,
                checks=checks,
                execution_result=execution_result,
            ),
            "recommended_next_role": self._recommend_next_role(normalized_task, checks),
        }

        DEFAULT_CONTRACT_VALIDATOR.validate("verification_report", report)

        report_path = self._verification_report_path(normalized_task["id"])
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        self.metrics_logger.record_verification(normalized_task["id"], report)
        return report

    def _prepare_task(self, task: dict[str, Any], session_id: str) -> dict[str, Any]:
        normalized_task = self._normalize_task(task)
        DEFAULT_CONTRACT_VALIDATOR.validate("task", normalized_task)

        pre_result = self.pre_task_hook.run()
        classification = self.classifier.classify(normalized_task)
        routing = self.router.route(normalized_task, classification)
        execution_mode = self.parallel_policy.decide(normalized_task, classification, routing)
        runtime_plan, runtime_plan_path = self.execution_planner.build(
            normalized_task,
            routing,
            execution_mode,
        )
        context_bundle = self.retriever.retrieve(normalized_task, classification, routing)
        packet, task_packet_path = self.packet_builder.build(
            task=normalized_task,
            session_id=session_id,
            classification=classification,
            routing=routing,
            execution_mode=execution_mode,
            runtime_plan=runtime_plan,
            context_bundle=context_bundle,
        )
        metrics = self.metrics_logger.record_task_run(
            task_id=normalized_task["id"],
            session_id=session_id,
            execution_mode=execution_mode,
            packet_path=task_packet_path,
            packet=packet,
            runtime_plan=runtime_plan,
            runtime_plan_path=runtime_plan_path,
        )
        self.decision_store.store_task_decision(normalized_task["id"], {
            "action": "task_packet_generated",
            "classification": classification,
            "routing": routing,
            "execution_mode": execution_mode,
            "runtime_plan_path": str(runtime_plan_path),
            "metrics_path": str(self.metrics_logger.path_for(normalized_task["id"])),
        })
        return {
            "task": normalized_task,
            "pre_task": pre_result,
            "classification": classification,
            "routing": routing,
            "execution_mode": execution_mode,
            "runtime_plan": runtime_plan,
            "runtime_plan_path": runtime_plan_path,
            "task_packet_path": task_packet_path,
            "packet": packet,
            "metrics": metrics,
        }

    def _normalize_task(self, task: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(task)
        normalized.setdefault("schema_version", "2.1")
        inputs = dict(normalized.get("inputs", {}))
        inputs.setdefault("related_paths", [])
        inputs.setdefault("related_tests", [])
        inputs.setdefault("related_handoffs", [])
        inputs.setdefault("related_logs", [])
        inputs.setdefault("related_modules", [])
        normalized["inputs"] = inputs
        normalized.setdefault("constraints", [])
        normalized.setdefault("acceptance_criteria", [])
        normalized.setdefault("domain", "general")
        normalized.setdefault("assigned_role", "backend")
        normalized.setdefault("metadata", {})
        return normalized

    def _build_planned_agent_output(
        self,
        execution_mode: dict[str, Any],
        runtime_plan: dict[str, Any],
        runtime_plan_path: Path,
        task_packet_path: Path,
    ) -> dict[str, Any]:
        mode = execution_mode["mode"]
        status_by_mode = {
            "solo": "pending_primary_execution",
            "paired": "pending_paired_execution",
            "directed_swarm": "pending_swarm_execution",
        }
        return {
            "status": status_by_mode.get(mode, "pending_primary_execution"),
            "task_packet_path": str(task_packet_path),
            "runtime_plan_path": str(runtime_plan_path),
            "assigned_role": execution_mode["primary_role"],
            "mode": mode,
            "next_action": runtime_plan["next_action"],
            "execution_queue": runtime_plan["steps"],
        }

    def _build_terminal_agent_output(
        self,
        execution_mode: dict[str, Any],
        runtime_plan_path: Path,
        task_packet_path: Path,
        execution_result: dict[str, Any],
        final_status: str,
        attempts: int,
    ) -> dict[str, Any]:
        runtime_plan = json.loads(runtime_plan_path.read_text(encoding="utf-8"))
        return {
            "status": final_status,
            "task_packet_path": str(task_packet_path),
            "runtime_plan_path": str(runtime_plan_path),
            "assigned_role": execution_mode["primary_role"],
            "mode": execution_mode["mode"],
            "next_action": "complete_and_report" if final_status == "completed" else "stop_and_escalate",
            "execution_queue": runtime_plan.get("steps", []),
            "execution_report_path": execution_result.get("execution_report_path"),
            "attempts": attempts,
            "changed_files": execution_result.get("changed_files", []),
        }

    def _maybe_create_failure_handoff(
        self,
        task: dict[str, Any],
        session_id: str,
        execution_mode: dict[str, Any],
        verification_report: dict[str, Any],
        final_status: str,
        execution_results: list[dict[str, Any]],
    ) -> Path | None:
        if final_status != "failed":
            return None

        handoff_policy = self._failure_handoff_policy(
            task=task,
            execution_mode=execution_mode,
            verification_report=verification_report,
            execution_results=execution_results,
        )

        return self.on_handoff_hook.run(
            task_id=task["id"],
            from_role=execution_mode.get("primary_role", "backend"),
            to_role=handoff_policy["target_role"],
            from_session=session_id,
            completed=[
                f"Executed {len(execution_results)} attempt(s).",
                f"Final verification status: {verification_report.get('status')}.",
            ],
            needs_continuation=self._handoff_needs(verification_report),
            context=handoff_policy["context"],
            related_files=self._handoff_related_files(execution_results),
            open_questions=[],
            reason=handoff_policy["reason"],
            recommended_next_step=handoff_policy["recommended_next_step"],
        )

    def _failure_handoff_policy(
        self,
        task: dict[str, Any],
        execution_mode: dict[str, Any],
        verification_report: dict[str, Any],
        execution_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self._role_gate_blocked(execution_results):
            assigned_role = task.get("assigned_role") or "reviewer"
            return {
                "target_role": assigned_role,
                "reason": "Role gate blocked execution; the assigned role should continue.",
                "context": [
                    "Execution stopped before commands ran because session role did not match task.assigned_role.",
                    f"Assigned role: {assigned_role}",
                ],
                "recommended_next_step": "Assigned role should claim the task, review the packet, and continue execution.",
            }

        target_role = verification_report.get("recommended_next_role") or "reviewer"
        if target_role == execution_mode.get("primary_role"):
            target_role = "reviewer"
        return {
            "target_role": target_role,
            "reason": "Verification failed after retry budget; another role should continue.",
            "context": [
                f"Verification failed: {verification_report.get('status')}",
                f"Recommended next role: {target_role}",
            ],
            "recommended_next_step": "Review the verification report, latest execution report, and retry packets before patching.",
        }

    def _handoff_needs(self, verification_report: dict[str, Any]) -> list[str]:
        needs = list(verification_report.get("next_context_needs", []))
        for check in verification_report.get("checks", []):
            if check.get("result") != "failed":
                continue
            if check.get("missing_criteria"):
                needs.extend([f"Fix missing criterion: {item}" for item in check["missing_criteria"]])
            else:
                needs.append(f"Resolve failed check: {check.get('name', 'verification')}")
        return needs or ["Review failure evidence and decide next patch."]

    def _handoff_related_files(self, execution_results: list[dict[str, Any]]) -> list[str]:
        files: list[str] = []
        for result in execution_results:
            for file_path in result.get("changed_files", []):
                if file_path not in files:
                    files.append(file_path)
        return files

    def _role_gate_blocked(self, execution_results: list[dict[str, Any]]) -> bool:
        for result in execution_results:
            for step in result.get("step_results", []):
                if step.get("status") != "blocked":
                    continue
                details = str(step.get("details", ""))
                if "Role gate blocked execution" in details:
                    return True
        return False

    def _verification_report_path(self, task_id: str) -> Path:
        return self.config.runtime_dir / "state" / "verification_reports" / f"{task_id}.verification.json"

    def _derive_next_context_needs(
        self,
        task: dict[str, Any],
        checks: list[dict[str, Any]],
        execution_result: dict[str, Any],
    ) -> list[str]:
        needs: list[str] = []
        related_paths = task.get("inputs", {}).get("related_paths", [])
        related_tests = task.get("inputs", {}).get("related_tests", [])
        auth_sensitive = (
            task.get("domain") == "auth"
            or any("auth" in path.lower() or "token" in path.lower() for path in related_paths)
        )

        for check in checks:
            if check.get("result") in {"passed", "skipped"}:
                continue

            name = check.get("name", "")
            details = (check.get("details") or "").lower()

            if name in {"python", "pytest", "tests"}:
                needs.extend(["stack_trace", "failing_test_source"])
            if name == "acceptance":
                if related_tests:
                    needs.append("failing_test_source")
                if execution_result.get("stack_trace") or "traceback" in details:
                    needs.append("stack_trace")
            if name == "lint":
                needs.append("lint_error_details")
            if name == "typecheck":
                needs.append("type_error_details")
            if name == "security":
                needs.append("security_finding_details")

        if auth_sensitive and any(check.get("result") == "failed" for check in checks):
            needs.extend(["recent_auth_diff", "token_rotation_helper"])

        helper_context = self._helper_context_need(related_paths)
        if helper_context and any(check.get("result") == "failed" for check in checks):
            needs.append(helper_context)

        if execution_result.get("stack_trace"):
            needs.append("stack_trace")

        unique_needs: list[str] = []
        for need in needs:
            if need not in unique_needs:
                unique_needs.append(need)
        return unique_needs

    def _helper_context_need(self, related_paths: list[str]) -> str | None:
        lowered = " ".join(path.lower() for path in related_paths)
        if any(keyword in lowered for keyword in ("retry", "hook", "helper")):
            return "retry_helper_context"
        return None

    def _recommend_next_role(self, task: dict[str, Any], checks: list[dict[str, Any]]) -> str:
        if any(check.get("name") == "security" and check.get("result") == "failed" for check in checks):
            return "security"
        if any(check.get("name") in {"lint", "typecheck"} and check.get("result") == "failed" for check in checks):
            return task.get("assigned_role", "backend")
        if any(check.get("result") == "failed" for check in checks):
            return task.get("assigned_role", "backend")
        return task.get("assigned_role", "backend")
