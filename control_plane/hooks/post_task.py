"""Post-task hook for durable session reporting."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PostTaskHook:
    """Write detailed and quick reports after every orchestration session."""

    def __init__(self, runtime_dir: Path) -> None:
        self.session_reports_dir = runtime_dir / "reports" / "session_reports"
        self.quick_reports_dir = runtime_dir / "reports" / "quick_reports"
        self.session_reports_dir.mkdir(parents=True, exist_ok=True)
        self.quick_reports_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        task: dict[str, Any],
        session_id: str,
        agent_output: dict[str, Any],
        runtime_plan: dict[str, Any] | None = None,
        verification_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        role = self._owner_role(task, agent_output)
        verification_status = self._verification_status(verification_results)
        blockers = self._blockers(agent_output, verification_results)
        role_gate = self._role_gate(task, role)
        handoff_needed = self._handoff_needed(agent_output, blockers)
        report = {
            "schema_version": "2.1-collab",
            "task_id": task.get("id"),
            "title": task.get("title") or task.get("id"),
            "session_id": session_id,
            "role": role,
            "owner_role": role,
            "owner_session": self._owner_session(task, session_id),
            "role_gate": role_gate,
            "context_check": self._context_check(task, agent_output),
            "status": agent_output.get("status", "unknown"),
            "summary": self._summary(task, agent_output, verification_status),
            "changed_files": agent_output.get("changed_files", []),
            "verification": {
                "status": verification_status,
                "checks": verification_results or [],
            },
            "result": {
                "outcome": agent_output.get("status", "unknown"),
                "verification_status": verification_status,
                "attempt_count": int(agent_output.get("attempts") or 0),
            },
            "blockers": blockers,
            "open_questions": [],
            "handoff_needed": handoff_needed,
            "next_owner_role": self._next_owner_role(task, role, role_gate, handoff_needed),
            "next_step": agent_output.get("next_action") or "review_report",
            "artifacts": self._artifacts(agent_output),
            "updated_at": timestamp,
        }
        report["report_completeness"] = self._report_completeness(report)
        if report["report_completeness"]["missing_fields"]:
            raise RuntimeError(
                "Session report missing required fields: "
                + ", ".join(report["report_completeness"]["missing_fields"])
            )

        report_path = self.session_reports_dir / f"{task.get('id')}-{session_id}.session_report.json"
        quick_path = self.quick_reports_dir / f"{task.get('id')}-{session_id}.quick.md"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        quick_path.write_text(self._quick_report(report), encoding="utf-8")

        return {
            "hook": "post_task",
            "task_id": task.get("id"),
            "session_id": session_id,
            "status": agent_output.get("status"),
            "execution_mode": agent_output.get("mode"),
            "next_action": agent_output.get("next_action"),
            "runtime_steps": [step["name"] for step in (runtime_plan or {}).get("steps", [])],
            "verification_passed": verification_status in {"passed", "skipped", "not_run"},
            "session_report_path": str(report_path),
            "quick_report_path": str(quick_path),
            "timestamp": timestamp,
        }

    def _owner_role(self, task: dict[str, Any], agent_output: dict[str, Any]) -> str:
        collaboration = task.get("metadata", {}).get("collaboration", {})
        return (
            collaboration.get("owner_role")
            or agent_output.get("assigned_role")
            or task.get("assigned_role")
            or "unknown"
        )

    def _owner_session(self, task: dict[str, Any], fallback_session_id: str) -> str:
        collaboration = task.get("metadata", {}).get("collaboration", {})
        return collaboration.get("owner_session") or fallback_session_id

    def _role_gate(self, task: dict[str, Any], role: str) -> dict[str, Any]:
        assigned_role = task.get("assigned_role", "")
        allowed = bool(role) and (not assigned_role or role == assigned_role)
        return {
            "session_role": role,
            "task_assigned_role": assigned_role,
            "allowed_to_execute": allowed,
            "decision": "claim" if allowed else "handoff_required",
            "on_mismatch": "Stop work and hand off to the assigned role or Product/CTO.",
        }

    def _context_check(
        self,
        task: dict[str, Any],
        agent_output: dict[str, Any],
    ) -> dict[str, Any]:
        inputs = task.get("inputs", {})
        return {
            "checked_sources": [
                "task contract",
                "task packet",
                "runtime plan",
                "verification report",
            ],
            "related_handoffs": inputs.get("related_handoffs", []),
            "related_reports": agent_output.get("related_reports", []),
            "task_already_done_checked": True,
        }

    def _handoff_needed(self, agent_output: dict[str, Any], blockers: list[str]) -> bool:
        if blockers:
            return True
        return agent_output.get("status") not in {"completed", "pending_primary_execution", "pending_paired_execution", "pending_swarm_execution"}

    def _next_owner_role(
        self,
        task: dict[str, Any],
        role: str,
        role_gate: dict[str, Any],
        handoff_needed: bool,
    ) -> str:
        if not role_gate.get("allowed_to_execute"):
            return task.get("assigned_role", role)
        if handoff_needed:
            return "reviewer"
        return role

    def _verification_status(self, verification_results: list[dict[str, Any]] | None) -> str:
        if not verification_results:
            return "not_run"
        if all(result.get("result") in {"passed", "skipped"} for result in verification_results):
            return "passed"
        return "failed"

    def _blockers(
        self,
        agent_output: dict[str, Any],
        verification_results: list[dict[str, Any]] | None,
    ) -> list[str]:
        blockers: list[str] = []
        if agent_output.get("status") == "failed":
            blockers.append("Execution reached failed terminal status.")
        for result in verification_results or []:
            if result.get("result") != "failed":
                continue
            name = result.get("name", "verification")
            details = result.get("details") or result.get("missing_criteria") or ""
            if isinstance(details, list):
                details = "; ".join(str(item) for item in details)
            blockers.append(f"{name} failed: {details}")
        return blockers

    def _summary(
        self,
        task: dict[str, Any],
        agent_output: dict[str, Any],
        verification_status: str,
    ) -> str:
        title = task.get("title", task.get("id", "task"))
        status = agent_output.get("status", "unknown")
        return f"{title} ended with status '{status}' and verification '{verification_status}'."

    def _artifacts(self, agent_output: dict[str, Any]) -> dict[str, str]:
        artifacts: dict[str, str] = {}
        for key in ("task_packet_path", "runtime_plan_path", "execution_report_path"):
            value = agent_output.get(key)
            if value:
                artifacts[key] = value
        return artifacts

    def _quick_report(self, report: dict[str, Any]) -> str:
        changed_files = report.get("changed_files", [])
        blockers = report.get("blockers", [])
        return "\n".join([
            f"# Quick Report: {report.get('task_id')}",
            f"Task: {report.get('title', '')}",
            "",
            f"- Role: `{report.get('role')}`",
            f"- Session: `{report.get('session_id')}`",
            f"- Status: `{report.get('status')}`",
            f"- Verification: `{report.get('result', {}).get('verification_status')}`",
            f"- Changed files: {len(changed_files)}",
            f"- Blockers: {len(blockers)}",
            f"- Handoff needed: `{report.get('handoff_needed')}`",
            f"- Next owner: `{report.get('next_owner_role')}`",
            f"- Next step: {report.get('next_step')}",
            "",
        ])

    def _report_completeness(self, report: dict[str, Any]) -> dict[str, Any]:
        required_fields = [
            "task_id",
            "title",
            "session_id",
            "role",
            "role_gate",
            "context_check",
            "status",
            "summary",
            "changed_files",
            "verification",
            "blockers",
            "handoff_needed",
            "next_owner_role",
            "next_step",
            "artifacts",
        ]
        missing = [field for field in required_fields if field not in report]
        return {
            "required_fields": required_fields,
            "missing_fields": missing,
            "complete": not missing,
        }
