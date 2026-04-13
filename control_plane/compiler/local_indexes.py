"""Build lightweight local-driven indexes for multi-session consumption.

Generates deterministic small JSON indexes under runtime/cache/indexes/:
- task_status_index.json     — all tasks from .hub/active + .hub/done with status
- handoff_index.json         — all handoffs from .hub/handoffs
- session_report_index.json  — all session reports from runtime/reports/session_reports
- project_snapshot_index.json — merged summary of above 3 + dashboard state
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _safe_load_json(path: Path) -> dict[str, Any] | None:
    """Load a JSON file, returning None on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_index(out_dir: Path, name: str, data: Any) -> Path:
    """Atomically write an index file."""
    out_path = out_dir / name
    tmp_path = out_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(out_path)
    return out_path


def build_task_status_index(repo_root: Path, out_dir: Path) -> Path:
    """Index all tasks from .hub/active and .hub/done."""
    tasks: list[dict[str, Any]] = []

    for subdir, status_default in [(".hub/active", "active"), (".hub/done", "done")]:
        d = repo_root / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            payload = _safe_load_json(f)
            if payload is None:
                continue
            tasks.append({
                "task_id": payload.get("task_id", f.stem),
                "title": payload.get("title") or payload.get("task_title", ""),
                "status": payload.get("status", status_default),
                "owner_role": payload.get("owner_role") or payload.get("role", ""),
                "next_owner_role": payload.get("next_owner_role", ""),
                "source": subdir,
                "path": str(f.relative_to(repo_root)),
            })

    index = {
        "type": "task_status_index",
        "count": len(tasks),
        "tasks": tasks,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    return _write_index(out_dir, "task_status_index.json", index)


def build_handoff_index(repo_root: Path, out_dir: Path) -> Path:
    """Index all handoffs from .hub/handoffs."""
    handoffs: list[dict[str, Any]] = []

    d = repo_root / ".hub" / "handoffs"
    if d.exists():
        for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            payload = _safe_load_json(f)
            if payload is None:
                continue
            handoffs.append({
                "task_id": payload.get("task_id", ""),
                "from_role": payload.get("from_role", ""),
                "to_role": payload.get("to_role", ""),
                "reason": payload.get("reason", ""),
                "path": str(f.relative_to(repo_root)),
                "created_at": payload.get("created_at", ""),
            })

    index = {
        "type": "handoff_index",
        "count": len(handoffs),
        "handoffs": handoffs,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    return _write_index(out_dir, "handoff_index.json", index)


def build_session_report_index(repo_root: Path, out_dir: Path) -> Path:
    """Index all session reports from runtime/reports/session_reports."""
    reports: list[dict[str, Any]] = []

    d = repo_root / "runtime" / "reports" / "session_reports"
    if d.exists():
        for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            payload = _safe_load_json(f)
            if payload is None:
                continue
            reports.append({
                "task_id": payload.get("task_id", ""),
                "session_id": payload.get("session_id", ""),
                "role": payload.get("role", ""),
                "status": payload.get("status", ""),
                "summary": payload.get("summary", "")[:200],
                "handoff_needed": payload.get("handoff_needed", False),
                "next_owner_role": payload.get("next_owner_role", ""),
                "path": str(f.relative_to(repo_root)),
                "updated_at": payload.get("updated_at", ""),
            })

    index = {
        "type": "session_report_index",
        "count": len(reports),
        "reports": reports,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    return _write_index(out_dir, "session_report_index.json", index)


def build_project_snapshot_index(
    repo_root: Path,
    out_dir: Path,
    task_count: int = 0,
    handoff_count: int = 0,
    report_count: int = 0,
) -> Path:
    """Merged summary snapshot for quick session boot."""
    dashboard_path = repo_root / "runtime" / "cache" / "summaries" / "dashboard_snapshot.json"
    dashboard = _safe_load_json(dashboard_path) or {}

    snapshot = {
        "type": "project_snapshot_index",
        "counts": {
            "tasks": task_count,
            "handoffs": handoff_count,
            "session_reports": report_count,
        },
        "active_tasks": dashboard.get("active_tasks", []),
        "blocked_tasks": dashboard.get("blocked_tasks", []),
        "recent_handoffs": dashboard.get("recent_handoffs", []),
        "focus_modules": dashboard.get("focus_modules", []),
        "system_state": dashboard.get("system_state", {}),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    return _write_index(out_dir, "project_snapshot_index.json", snapshot)


def build_local_indexes(repo_root: Path) -> dict[str, str]:
    """Build all 4 local indexes. Returns dict of name -> path."""
    out_dir = repo_root / "runtime" / "cache" / "indexes"
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, str] = {}

    task_path = build_task_status_index(repo_root, out_dir)
    results["task_status_index"] = str(task_path)
    task_index = _safe_load_json(task_path) or {}

    handoff_path = build_handoff_index(repo_root, out_dir)
    results["handoff_index"] = str(handoff_path)
    handoff_index = _safe_load_json(handoff_path) or {}

    report_path = build_session_report_index(repo_root, out_dir)
    results["session_report_index"] = str(report_path)
    report_index = _safe_load_json(report_path) or {}

    snapshot_path = build_project_snapshot_index(
        repo_root, out_dir,
        task_count=task_index.get("count", 0),
        handoff_count=handoff_index.get("count", 0),
        report_count=report_index.get("count", 0),
    )
    results["project_snapshot_index"] = str(snapshot_path)

    return results
