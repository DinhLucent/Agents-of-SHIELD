"""On-handoff hook for structured agent-to-agent transfer artifacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class OnHandoffHook:
    """Normalize and store handoff documents."""

    def __init__(self, hub_dir: Path) -> None:
        self.handoffs_dir = hub_dir / "handoffs"
        self.handoffs_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        task_id: str,
        from_role: str,
        to_role: str,
        completed: list[str],
        needs_continuation: list[str],
        context: str | list[str] = "",
        from_session: str | None = None,
        related_files: list[str] | None = None,
        open_questions: list[str] | None = None,
        reason: str = "Work requires continuation by another role.",
        recommended_next_step: str | None = None,
    ) -> Path:
        required_context = context if isinstance(context, list) else ([context] if context else [])
        handoff = {
            "schema_version": "2.1-collab",
            "task_id": task_id,
            "from_session": from_session or "",
            "from_role": from_role,
            "to_role": to_role,
            "handoff_gate": {
                "from_role": from_role,
                "to_role": to_role,
                "allowed_reason": bool(reason and to_role and from_role != to_role),
                "rule": "Use handoff when work needs another role, role mismatch, blocker, failed verification, scope change, or security/release review.",
            },
            "reason": reason,
            "completed": completed,
            "needs_continuation": needs_continuation,
            "required_context": required_context,
            "related_files": related_files or [],
            "evidence": required_context,
            "open_questions": open_questions or [],
            "recommended_next_step": recommended_next_step
            or "Continue from the latest session report and verification evidence.",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        filename = f"{task_id}-{from_role}-to-{to_role}.json"
        out_path = self.handoffs_dir / filename
        out_path.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path
