"""Main orchestrator for the v2 control plane."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from control_plane.classifier.task_classifier import TaskClassifier
from control_plane.context_builder.packet_builder import PacketBuilder
from control_plane.context_builder.prompt_budget import PromptBudget
from control_plane.contracts import DEFAULT_CONTRACT_VALIDATOR
from control_plane.execution.runtime_planner import ExecutionPlanner
from control_plane.hooks.on_verification_fail import on_verification_fail
from control_plane.hooks.post_task import PostTaskHook
from control_plane.hooks.pre_task import PreTaskHook
from control_plane.memory.store_decisions import DecisionStore
from control_plane.memory.summarize_run import RunSummarizer
from control_plane.retriever.knowledge_retriever import KnowledgeRetriever
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
    """Coordinate classification, routing, retrieval, packet building, and verification."""

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
        self.post_task_hook = PostTaskHook()

    def run_task(self, task: dict[str, Any], session_id: str) -> dict[str, Any]:
        """Full task lifecycle: classify, route, retrieve, build packet, verify, summarize."""
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

        agent_output = self._build_agent_output(
            execution_mode=execution_mode,
            runtime_plan=runtime_plan,
            runtime_plan_path=runtime_plan_path,
            task_packet_path=task_packet_path,
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

        summary = self.run_summarizer.summarize(
            task=normalized_task,
            session_id=session_id,
            agent_output=agent_output,
            runtime_plan=runtime_plan,
            metrics=metrics,
        )

        post_result = self.post_task_hook.run(
            task=normalized_task,
            session_id=session_id,
            agent_output=agent_output,
            runtime_plan=runtime_plan,
        )

        return {
            "pre_task": pre_result,
            "classification": classification,
            "routing": routing,
            "execution_mode": execution_mode,
            "runtime_plan": runtime_plan,
            "runtime_plan_path": str(runtime_plan_path),
            "task_packet_path": str(task_packet_path),
            "metrics_path": str(self.metrics_logger.path_for(normalized_task["id"])),
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
        if changed_files:
            checks.append(self.lint_runner.run(changed_files))
            checks.append(self.typecheck_runner.run(changed_files))
            checks.append(self.security_checker.check(changed_files))

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

        report_dir = self.config.runtime_dir / "state" / "verification_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{normalized_task['id']}.verification.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        self.metrics_logger.record_verification(normalized_task["id"], report)
        return report

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
        return normalized

    def _build_agent_output(
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
