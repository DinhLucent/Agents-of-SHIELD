"""Parse DASHBOARD.md into a machine-readable snapshot."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_dashboard_snapshot(repo_root: Path) -> Path:
    """Parse DASHBOARD.md into a structured JSON snapshot."""
    dashboard_path = repo_root / "DASHBOARD.md"
    out_dir = repo_root / "runtime" / "cache" / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot: dict[str, Any] = {
        "active_tasks": [],
        "blocked_tasks": [],
        "recent_handoffs": [],
        "focus_modules": [],
        "system_state": {
            "mode": "normal",
            "parallel_agents_active": 0,
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if dashboard_path.exists():
        text = dashboard_path.read_text(encoding="utf-8", errors="replace")
        snapshot["active_tasks"] = _extract_tasks(text, "TODO")
        snapshot["blocked_tasks"] = _extract_blocked(text)
        snapshot["focus_modules"] = _extract_focus_modules(text)
        snapshot["raw_preview"] = text.splitlines()[:40]

    handoffs_dir = repo_root / ".hub" / "handoffs"
    if handoffs_dir.exists():
        recent = sorted(handoffs_dir.glob("*"), key=lambda path: path.stat().st_mtime, reverse=True)
        snapshot["recent_handoffs"] = [str(path.relative_to(repo_root)) for path in recent[:5]]

    active_dir = repo_root / ".hub" / "active"
    if active_dir.exists():
        snapshot["active_tasks"] = _load_json_summaries(active_dir, repo_root, limit=20)

    done_dir = repo_root / ".hub" / "done"
    if done_dir.exists():
        snapshot["recent_done"] = _load_json_summaries(done_dir, repo_root, limit=10)

    reports_dir = repo_root / "runtime" / "reports" / "session_reports"
    if reports_dir.exists():
        snapshot["recent_session_reports"] = _load_json_summaries(reports_dir, repo_root, limit=10)

    system_tests_dir = repo_root / "runtime" / "reports" / "system_tests"
    if system_tests_dir.exists():
        snapshot["recent_system_tests"] = _load_system_test_summaries(system_tests_dir, repo_root, limit=5)

    out_path = out_dir / "dashboard_snapshot.json"
    tmp_path = out_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(out_path)
    return out_path


def _extract_tasks(text: str, section: str) -> list[dict[str, str]]:
    """Extract task rows from markdown tables under a section header."""
    tasks: list[dict[str, str]] = []
    in_section = False
    for line in text.splitlines():
        if section.lower() in line.lower() and line.strip().startswith("#"):
            in_section = True
            continue
        if in_section and line.strip().startswith("#"):
            break
        if in_section and "|" in line and "---" not in line:
            cells = [cell.strip() for cell in line.split("|") if cell.strip()]
            if len(cells) >= 3 and cells[0].startswith("TASK-"):
                tasks.append({
                    "task_id": cells[0],
                    "title": cells[1] if len(cells) > 1 else "",
                    "role": cells[2] if len(cells) > 2 else "",
                })
    return tasks


def _extract_blocked(text: str) -> list[str]:
    """Find tasks marked as blocked."""
    blocked: list[str] = []
    for match in re.finditer(r"(TASK-\d+\S*)\s*.*?(?:blocked|🟠|🔴)", text, re.IGNORECASE):
        blocked.append(match.group(1))
    return blocked


def _extract_focus_modules(text: str) -> list[str]:
    """Infer focus modules from active task domains."""
    modules: list[str] = []
    for match in re.finditer(r"domain[:\s]+(\w+)", text, re.IGNORECASE):
        modules.append(match.group(1))
    return sorted(set(modules))


def _load_json_summaries(directory: Path, repo_root: Path, limit: int) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    recent = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in recent[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        summaries.append({
            "path": str(path.relative_to(repo_root)),
            "task_id": payload.get("task_id"),
            "title": payload.get("title") or payload.get("task_title") or "",
            "status": payload.get("status", ""),
            "owner_role": payload.get("owner_role") or payload.get("role", ""),
            "owner_session": payload.get("owner_session") or payload.get("session_id", ""),
            "updated_at": payload.get("updated_at") or payload.get("completed_at") or payload.get("created_at", ""),
        })
    return summaries


def _load_system_test_summaries(directory: Path, repo_root: Path, limit: int) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    recent = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in recent[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        summaries.append({
            "path": str(path.relative_to(repo_root)),
            "status": payload.get("status", ""),
            "iterations": payload.get("iterations", 0),
            "failure_count": len(payload.get("failures", [])),
            "completed_at": payload.get("completed_at", ""),
        })
    return summaries


if __name__ == "__main__":
    result = build_dashboard_snapshot(Path(".").resolve())
    print(f"Dashboard snapshot -> {result}")
