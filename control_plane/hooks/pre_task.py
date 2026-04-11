"""Pre-task hook that keeps compiled state and dashboard cache fresh."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from control_plane.compiler.dashboard_snapshot import build_dashboard_snapshot


class PreTaskHook:
    """Pre-task lifecycle hook."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.compiled_dir = repo_root / "knowledge" / "compiled"
        self.cache_dir = repo_root / "runtime" / "cache" / "summaries"

    def run(self) -> dict[str, Any]:
        """Check caches and recompile if stale."""
        actions: list[str] = []

        if not (self.compiled_dir / "role_index.json").exists():
            actions.append("role_index_missing")
        if not (self.compiled_dir / "skill_index.json").exists():
            actions.append("skill_index_missing")
        if not (self.compiled_dir / "project_index.json").exists():
            actions.append("project_index_missing")
        if not (self.compiled_dir / "module_index.json").exists():
            actions.append("module_index_missing")

        self._hydrate_dashboard()
        actions.append("dashboard_snapshot_hydrated")

        return {
            "hook": "pre_task",
            "actions": actions,
            "needs_recompile": any("missing" in action for action in actions),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _hydrate_dashboard(self) -> None:
        """Ensure runtime cache contains the canonical dashboard snapshot."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = build_dashboard_snapshot(self.repo_root)
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        current_path = self.cache_dir / "current_dashboard.json"
        current_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
