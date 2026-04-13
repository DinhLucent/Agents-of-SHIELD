"""Build a minimal task packet for the downstream executor."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from control_plane.contracts import DEFAULT_CONTRACT_VALIDATOR


class PacketBuilder:
    """Build a focused task packet from classified and retrieved data."""

    def __init__(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.packet_dir = runtime_dir / "state" / "task_packets"
        self.packet_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        task: dict[str, Any],
        session_id: str,
        classification: dict[str, Any],
        routing: dict[str, Any],
        execution_mode: dict[str, Any],
        runtime_plan: dict[str, Any],
        context_bundle: dict[str, Any],
    ) -> tuple[dict[str, Any], Path]:
        """Build and persist a task packet, return the packet and file path."""
        task_id = task["id"]

        packet = {
            "schema_version": "2.1",
            "task_id": task_id,
            "session_id": session_id,
            "role": execution_mode["primary_role"],
            "secondary_roles": execution_mode.get("secondary_roles", []),
            "mode": execution_mode.get("mode", "solo"),
            "execution_mode": execution_mode,
            "runtime_plan": {
                "mode": runtime_plan["mode"],
                "steps": runtime_plan["steps"],
                "assigned_roles": runtime_plan["assigned_roles"],
                "review_required": runtime_plan["review_required"],
                "verification_profile": runtime_plan["verification_profile"],
            },
            "routing": routing,
            "task_type": classification["task_type"],
            "domain": classification["domain"],
            "risk_level": classification["risk_level"],
            "goal": task.get("title", ""),
            "summary": task.get("description", ""),
            "rules": self._build_rules(task),
            "role_gate": self._role_gate(task, execution_mode),
            "context_check": self._context_check(task, context_bundle),
            "reporting_requirements": self._reporting_requirements(),
            "context_budget": {
                "max_input_tokens": 12000,
                "max_code_tokens": 8000,
                "max_memory_tokens": 1500,
            },
            "modules": context_bundle.get("modules", []),
            "context_fragments": context_bundle.get("fragments", []),
            "files": context_bundle.get("files", []),
            "tests": context_bundle.get("tests", []),
            "handoff_refs": context_bundle.get("handoffs", []),
            "report_refs": context_bundle.get("reports", []),
            "memory_refs": [],
            "verification_plan": self._build_verification_plan(
                execution_mode["primary_role"], classification["risk_level"]
            ),
            "expected_outputs": self._expected_outputs(classification["task_type"]),
            "acceptance_criteria": task.get("acceptance_criteria", []),
        }

        DEFAULT_CONTRACT_VALIDATOR.validate("task_packet", packet)

        out_path = self.packet_dir / f"{task_id}.json"
        out_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
        return packet, out_path

    def _build_rules(self, task: dict[str, Any]) -> list[str]:
        rules = [
            "Run role gate before work",
            "If this packet role does not match task ownership, stop and hand off",
            "Prefer minimal patch",
            "Do not change unrelated modules",
            "Read latest handoff/report before editing",
            "End with session_report or handoff",
        ]
        rules.extend(task.get("constraints", []))
        return rules

    def _role_gate(self, task: dict[str, Any], execution_mode: dict[str, Any]) -> dict[str, Any]:
        assigned_role = task.get("assigned_role", "")
        packet_role = execution_mode.get("primary_role", "")
        allowed = bool(packet_role) and (not assigned_role or packet_role == assigned_role)
        return {
            "task_assigned_role": assigned_role,
            "packet_role": packet_role,
            "allowed_to_execute": allowed,
            "decision": "claim" if allowed else "handoff_required",
            "on_mismatch": "Do not execute; create handoff or ask Product/CTO to reassign.",
        }

    def _context_check(
        self,
        task: dict[str, Any],
        context_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "must_read_before_work": [
                "DASHBOARD.md",
                "OPERATING_RULES.md",
                "ROLE_SKILL_MATRIX.md",
                "task contract",
                "latest relevant handoff or session report",
            ],
            "task_handoff_refs": task.get("inputs", {}).get("related_handoffs", []),
            "packet_handoff_refs": context_bundle.get("handoffs", []),
            "task_report_refs": task.get("inputs", {}).get("related_reports", []),
            "packet_report_refs": context_bundle.get("reports", []),
            "rule": "If a done report already exists for this task, do not redo work without a new task or retry request.",
        }

    def _reporting_requirements(self) -> dict[str, Any]:
        return {
            "required_exit_artifact": "session_report_or_handoff",
            "session_report_required_fields": [
                "task_id",
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
            ],
            "handoff_required_when": [
                "role_mismatch",
                "scope_or_architecture_change",
                "blocked_by_another_role",
                "verification_failed_after_retry_budget",
                "security_or_release_risk",
            ],
        }

    def _build_verification_plan(self, role: str, risk: str) -> list[str]:
        plan = ["lint changed files"]
        if role in ("backend", "fullstack", "frontend"):
            plan.append("typecheck related module")
        plan.append("run related tests")
        if risk == "high":
            plan.append("security check")
        return plan

    def _expected_outputs(self, task_type: str) -> list[str]:
        base = ["patch", "change_summary", "handoff_update"]
        if task_type == "documentation":
            base = ["doc_update", "change_summary"]
        elif task_type == "test":
            base = ["test_files", "coverage_report"]
        return base
