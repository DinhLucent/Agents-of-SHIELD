"""Persist task state transitions for the local control-plane loop."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TaskStateMachine:
    """Track task state transitions and mirror active/done artifacts."""

    TERMINAL_STATES = {"completed", "failed"}

    def __init__(self, runtime_dir: Path, hub_dir: Path) -> None:
        self.active_state_dir = runtime_dir / "state" / "active_tasks"
        self.active_state_dir.mkdir(parents=True, exist_ok=True)
        self.hub_active_dir = hub_dir / "active"
        self.hub_done_dir = hub_dir / "done"
        self.hub_active_dir.mkdir(parents=True, exist_ok=True)
        self.hub_done_dir.mkdir(parents=True, exist_ok=True)

    def start(
        self,
        task: dict[str, Any],
        session_id: str,
        execution_mode: dict[str, Any],
        runtime_plan_path: Path,
        task_packet_path: Path,
    ) -> dict[str, Any]:
        state = {
            "task_id": task["id"],
            "session_id": session_id,
            "title": task.get("title", ""),
            "status": "prepared",
            "attempt": 0,
            "execution_mode": execution_mode.get("mode", "solo"),
            "current_step": None,
            "artifacts": {
                "task_packet_path": str(task_packet_path),
                "runtime_plan_path": str(runtime_plan_path),
            },
            "history": [],
            "updated_at": self._timestamp(),
        }
        return self.transition(
            task_id=task["id"],
            status="prepared",
            attempt=0,
            current_step=None,
            artifacts=state["artifacts"],
            title=state["title"],
            session_id=session_id,
            execution_mode=execution_mode.get("mode", "solo"),
            history=state["history"],
        )

    def transition(
        self,
        task_id: str,
        status: str,
        attempt: int,
        current_step: str | None,
        artifacts: dict[str, str] | None = None,
        title: str | None = None,
        session_id: str | None = None,
        execution_mode: str | None = None,
        history: list[dict[str, Any]] | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        state = self._load(task_id)
        if history is not None:
            state["history"] = history
        state.setdefault("artifacts", {})
        state.setdefault("history", [])
        if artifacts:
            state["artifacts"].update(artifacts)
        if title is not None:
            state["title"] = title
        if session_id is not None:
            state["session_id"] = session_id
        if execution_mode is not None:
            state["execution_mode"] = execution_mode

        state["status"] = status
        state["attempt"] = attempt
        state["current_step"] = current_step
        state["updated_at"] = self._timestamp()
        state["history"].append({
            "status": status,
            "attempt": attempt,
            "step": current_step,
            "note": note,
            "timestamp": state["updated_at"],
        })

        self._write_active_state(task_id, state)
        return state

    def finalize(
        self,
        task_id: str,
        final_status: str,
        summary: dict[str, Any],
        verification_report: dict[str, Any],
        execution_results: list[dict[str, Any]],
        retries: list[dict[str, Any]],
        handoff_path: Path | None = None,
    ) -> dict[str, Any]:
        state = self._load(task_id)
        state["status"] = final_status
        state["current_step"] = None
        state["updated_at"] = self._timestamp()
        state.setdefault("history", []).append({
            "status": final_status,
            "attempt": state.get("attempt", 0),
            "step": None,
            "note": "Task reached terminal state",
            "timestamp": state["updated_at"],
        })
        if handoff_path is not None:
            state.setdefault("artifacts", {})["handoff_path"] = str(handoff_path)
        done_payload = {
            "task_id": task_id,
            "title": state.get("title", ""),
            "session_id": state.get("session_id"),
            "execution_mode": state.get("execution_mode"),
            "status": final_status,
            "attempt": state.get("attempt", 0),
            "artifacts": state.get("artifacts", {}),
            "verification_report": verification_report,
            "execution_results": execution_results,
            "retries": retries,
            "summary": summary,
            "history": state.get("history", []),
            "completed_at": state["updated_at"],
        }
        done_path = self.hub_done_dir / f"{task_id}.json"
        done_path.write_text(json.dumps(done_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        active_path = self._active_state_path(task_id)
        hub_active_path = self.hub_active_dir / f"{task_id}.json"
        if active_path.exists():
            active_path.unlink()
        if hub_active_path.exists():
            hub_active_path.unlink()
        return {
            "done_report_path": str(done_path),
            "final_status": final_status,
        }

    def set_runtime_plan_step(
        self,
        runtime_plan_path: Path,
        step_name: str,
        status: str,
    ) -> dict[str, Any]:
        runtime_plan = json.loads(runtime_plan_path.read_text(encoding="utf-8"))
        for step in runtime_plan.get("steps", []):
            if step.get("name") == step_name:
                step["status"] = status
        runtime_plan_path.write_text(
            json.dumps(runtime_plan, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return runtime_plan

    def reset_runtime_plan(self, runtime_plan_path: Path) -> dict[str, Any]:
        runtime_plan = json.loads(runtime_plan_path.read_text(encoding="utf-8"))
        for step in runtime_plan.get("steps", []):
            step["status"] = "pending"
        runtime_plan_path.write_text(
            json.dumps(runtime_plan, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return runtime_plan

    def _load(self, task_id: str) -> dict[str, Any]:
        state_path = self._active_state_path(task_id)
        if not state_path.exists():
            return {"task_id": task_id, "artifacts": {}, "history": []}
        return json.loads(state_path.read_text(encoding="utf-8"))

    def _write_active_state(self, task_id: str, state: dict[str, Any]) -> None:
        serialized = json.dumps(state, indent=2, ensure_ascii=False)
        self._active_state_path(task_id).write_text(serialized, encoding="utf-8")
        hub_payload = {
            "task_id": task_id,
            "title": state.get("title", ""),
            "status": state.get("status", ""),
            "attempt": state.get("attempt", 0),
            "current_step": state.get("current_step"),
            "execution_mode": state.get("execution_mode"),
            "updated_at": state.get("updated_at"),
        }
        (self.hub_active_dir / f"{task_id}.json").write_text(
            json.dumps(hub_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _active_state_path(self, task_id: str) -> Path:
        return self.active_state_dir / f"{task_id}.state.json"

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
