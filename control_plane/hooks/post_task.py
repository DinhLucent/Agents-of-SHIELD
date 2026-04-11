"""Post-task hook for compact runtime status reporting."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class PostTaskHook:
    """Post-task lifecycle hook."""

    def run(
        self,
        task: dict[str, Any],
        session_id: str,
        agent_output: dict[str, Any],
        runtime_plan: dict[str, Any] | None = None,
        verification_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "hook": "post_task",
            "task_id": task.get("id"),
            "session_id": session_id,
            "status": agent_output.get("status"),
            "execution_mode": agent_output.get("mode"),
            "next_action": agent_output.get("next_action"),
            "runtime_steps": [step["name"] for step in (runtime_plan or {}).get("steps", [])],
            "verification_passed": all(
                result.get("result") in {"passed", "skipped"} for result in (verification_results or [])
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
