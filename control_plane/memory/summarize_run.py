"""Generate compact run summaries after each task orchestration step."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RunSummarizer:
    """Produce a compact summary after each agent run."""

    def __init__(self, runtime_dir: Path) -> None:
        self.summary_dir = runtime_dir / "reports"
        self.summary_dir.mkdir(parents=True, exist_ok=True)

    def summarize(
        self,
        task: dict[str, Any],
        session_id: str,
        agent_output: dict[str, Any],
        runtime_plan: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        verification_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        summary = {
            "session_id": session_id,
            "task_id": task["id"],
            "title": task.get("title", ""),
            "assigned_role": task.get("assigned_role"),
            "agent_status": agent_output.get("status"),
            "execution_mode": agent_output.get("mode"),
            "runtime_steps": [step["name"] for step in (runtime_plan or {}).get("steps", [])],
            "verification": verification_results or [],
            "metrics_path": metrics.get("metrics_path") if metrics else None,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "next_step": self._decide_next(agent_output, runtime_plan, verification_results),
        }

        out_path = self.summary_dir / f"{task['id']}.summary.json"
        out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return summary

    def _decide_next(
        self,
        output: dict[str, Any],
        runtime_plan: dict[str, Any] | None,
        verifications: list[dict[str, Any]] | None,
    ) -> str:
        if output.get("status") == "completed":
            return "complete_and_handoff"
        if output.get("status") == "failed":
            return "stop_and_escalate"
        if output.get("status") == "pending_primary_execution":
            return "execute_primary"
        if output.get("status") == "pending_paired_execution":
            return "execute_primary_then_review"
        if output.get("status") == "pending_swarm_execution":
            return "dispatch_parallel_agents"
        if verifications:
            failed = [verification for verification in verifications if verification.get("result") == "failed"]
            if failed:
                return "retry_with_failure_context"
        if runtime_plan and runtime_plan.get("review_required"):
            return "complete_review_and_handoff"
        return "complete_and_handoff"
