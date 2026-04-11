"""Handoff Retriever — Fetches handoff documents from .hub/handoffs/."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class HandoffRetriever:
    """Retrieve the most recent handoff for a given task or domain."""

    def __init__(self, hub_dir: Path) -> None:
        self.handoffs_dir = hub_dir / "handoffs"

    def get_latest(self, task_id: str | None = None, limit: int = 1) -> list[dict[str, Any]]:
        """Return most recent handoff(s), optionally filtered by task_id."""
        if not self.handoffs_dir.exists():
            return []

        files = sorted(
            [*self.handoffs_dir.glob("*.json"), *self.handoffs_dir.glob("*.md")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        results: list[dict[str, Any]] = []
        for f in files:
            if task_id and task_id.lower() not in f.name.lower():
                continue
            results.append({
                "path": str(f),
                "name": f.name,
                "content_preview": f.read_text(encoding="utf-8", errors="replace")[:500],
            })
            if len(results) >= limit:
                break
        return results
