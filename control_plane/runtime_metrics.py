"""Persist per-run runtime metrics for Phase 2.1 telemetry."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RuntimeMetricsLogger:
    """Store task-level metrics snapshots and append event logs."""

    def __init__(self, runtime_dir: Path) -> None:
        self.metrics_dir = runtime_dir / "reports" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.event_log_path = self.metrics_dir / "events.jsonl"

    def record_task_run(
        self,
        task_id: str,
        session_id: str,
        execution_mode: dict[str, Any],
        packet_path: Path,
        packet: dict[str, Any],
        runtime_plan: dict[str, Any],
        runtime_plan_path: Path,
    ) -> dict[str, Any]:
        metrics = {}
        metrics_path = self._metrics_path(task_id)
        metrics.update({
            "task_id": task_id,
            "session_id": session_id,
            "packet_size": packet_path.stat().st_size if packet_path.exists() else 0,
            "loaded_file_count": len(packet.get("files", [])),
            "loaded_test_count": len(packet.get("tests", [])),
            "loaded_fragment_count": len(packet.get("context_fragments", [])),
            "retry_count": 0,
            "verifier_status": "pending",
            "execution_mode": execution_mode.get("mode"),
            "metrics_path": str(metrics_path),
            "runtime_plan_path": str(runtime_plan_path),
            "runtime_steps": [step["name"] for step in runtime_plan.get("steps", [])],
            "updated_at": self._timestamp(),
        })
        self._store(task_id, metrics)
        self._append_event({"event": "task_run", **metrics})
        return metrics

    def record_verification(self, task_id: str, report: dict[str, Any]) -> dict[str, Any]:
        metrics = self._load(task_id)
        metrics.update({
            "task_id": task_id,
            "verifier_status": report.get("status", "unknown"),
            "failed_check_count": len([
                check for check in report.get("checks", [])
                if check.get("result") == "failed"
            ]),
            "updated_at": self._timestamp(),
        })
        self._store(task_id, metrics)
        self._append_event({
            "event": "verification",
            "task_id": task_id,
            "verifier_status": report.get("status", "unknown"),
            "updated_at": metrics["updated_at"],
        })
        return metrics

    def record_execution(self, task_id: str, execution_result: dict[str, Any]) -> dict[str, Any]:
        metrics = self._load(task_id)
        metrics.update({
            "task_id": task_id,
            "last_execution_status": execution_result.get("status", "unknown"),
            "execution_attempts": max(
                int(metrics.get("execution_attempts", 0)),
                int(execution_result.get("attempt", 0)),
            ),
            "last_changed_file_count": len(execution_result.get("changed_files", [])),
            "last_command_count": sum(
                len(step.get("commands", []))
                for step in execution_result.get("step_results", [])
            ),
            "last_execution_report_path": execution_result.get("execution_report_path"),
            "updated_at": self._timestamp(),
        })
        self._store(task_id, metrics)
        self._append_event({
            "event": "execution",
            "task_id": task_id,
            "attempt": execution_result.get("attempt", 0),
            "execution_status": execution_result.get("status", "unknown"),
            "changed_file_count": len(execution_result.get("changed_files", [])),
            "updated_at": metrics["updated_at"],
        })
        return metrics

    def record_state_transition(
        self,
        task_id: str,
        status: str,
        attempt: int,
        current_step: str | None,
    ) -> None:
        self._append_event({
            "event": "state_transition",
            "task_id": task_id,
            "status": status,
            "attempt": attempt,
            "current_step": current_step,
            "updated_at": self._timestamp(),
        })

    def record_retry(
        self,
        task_id: str,
        retry_packet_path: Path,
        additional_context_needed: list[str],
    ) -> dict[str, Any]:
        metrics = self._load(task_id)
        metrics.update({
            "task_id": task_id,
            "retry_count": int(metrics.get("retry_count", 0)) + 1,
            "last_retry_packet_size": retry_packet_path.stat().st_size if retry_packet_path.exists() else 0,
            "last_retry_context_count": len(additional_context_needed),
            "updated_at": self._timestamp(),
        })
        self._store(task_id, metrics)
        self._append_event({
            "event": "retry",
            "task_id": task_id,
            "retry_count": metrics["retry_count"],
            "additional_context_needed": additional_context_needed,
            "updated_at": metrics["updated_at"],
        })
        return metrics

    def _metrics_path(self, task_id: str) -> Path:
        return self.metrics_dir / f"{task_id}.metrics.json"

    def path_for(self, task_id: str) -> Path:
        return self._metrics_path(task_id)

    def _load(self, task_id: str) -> dict[str, Any]:
        path = self._metrics_path(task_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _store(self, task_id: str, metrics: dict[str, Any]) -> None:
        self._metrics_path(task_id).write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _append_event(self, payload: dict[str, Any]) -> None:
        with self.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
