"""Produce retry packets with only failure-specific context."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


MAX_RETRIES = 3


def on_verification_fail(
    repo_root: Path,
    task_packet_path: Path,
    verification_report_path: Path,
    attempt: int = 1,
) -> dict[str, Any]:
    """Read a failed verification report and produce a minimal retry packet."""
    packet = json.loads(task_packet_path.read_text(encoding="utf-8"))
    report = json.loads(verification_report_path.read_text(encoding="utf-8"))

    failed_checks = [check for check in report.get("checks", []) if check.get("result") == "failed"]
    next_context_needs = report.get("next_context_needs", [])
    failure_fragments = _materialize_failure_fragments(
        repo_root=repo_root,
        packet=packet,
        report=report,
        next_context_needs=next_context_needs,
    )

    retry_packet = dict(packet)
    retry_packet["retry_of"] = packet["task_id"]
    retry_packet["retry_attempt"] = attempt
    retry_packet["failure_context"] = {
        "checks": report.get("checks", []),
        "next_context_needs": next_context_needs,
        "failed_check_names": [check["name"] for check in failed_checks],
    }
    retry_packet["context_fragments"] = _augment_fragments(
        packet.get("context_fragments", []),
        failure_fragments,
    )

    retry_dir = repo_root / "runtime" / "state" / "task_packets"
    retry_dir.mkdir(parents=True, exist_ok=True)
    out_path = retry_dir / f"{packet['task_id']}.retry-{attempt}.json"
    out_path.write_text(json.dumps(retry_packet, indent=2, ensure_ascii=False), encoding="utf-8")

    should_retry = attempt < MAX_RETRIES
    return {
        "hook": "on_verification_fail",
        "retry_packet_path": str(out_path),
        "failed_checks": [check["name"] for check in failed_checks],
        "additional_context_needed": next_context_needs,
        "attempt": attempt,
        "should_retry": should_retry,
        "should_escalate": not should_retry,
        "escalation_target": "reviewer" if not should_retry else None,
    }


def _augment_fragments(
    fragments: list[dict[str, Any]],
    extra_fragments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updated = list(fragments)
    for fragment in extra_fragments:
        if not any(existing.get("id") == fragment["id"] for existing in updated):
            updated.append(fragment)
    return updated


def _materialize_failure_fragments(
    repo_root: Path,
    packet: dict[str, Any],
    report: dict[str, Any],
    next_context_needs: list[str],
) -> list[dict[str, Any]]:
    cache_dir = repo_root / "runtime" / "cache" / "summaries"
    cache_dir.mkdir(parents=True, exist_ok=True)

    fragments: list[dict[str, Any]] = []
    for need in next_context_needs:
        payload = _payload_for_need(repo_root, packet, report, need)
        if payload is None:
            continue

        file_name = f"{need}.json"
        out_path = cache_dir / file_name
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        fragments.append({
            "id": need,
            "type": payload.get("type", "failure_context"),
            "path": str(out_path.relative_to(repo_root)),
        })

    return fragments


def _payload_for_need(
    repo_root: Path,
    packet: dict[str, Any],
    report: dict[str, Any],
    need: str,
) -> dict[str, Any] | None:
    failed_checks = [check for check in report.get("checks", []) if check.get("result") == "failed"]
    packet_files = packet.get("files", [])
    packet_tests = packet.get("tests", [])

    if need == "stack_trace":
        details = next((check.get("details") for check in failed_checks if check.get("details")), "")
        return {
            "type": "failure_trace",
            "failed_checks": [check.get("name") for check in failed_checks],
            "stack_trace": details,
        }

    if need == "failing_test_source":
        test_path = _failing_test_path(failed_checks, packet_tests)
        return {
            "type": "test_source",
            "test_path": test_path,
            "source_excerpt": _read_excerpt(repo_root, test_path, max_lines=120),
        }

    if need in {"recent_auth_diff", "retry_helper_context", "token_rotation_helper"}:
        relevant_paths = _relevant_paths_for_need(packet_files, need)
        return {
            "type": "code_hint" if need != "recent_auth_diff" else "recent_diff",
            "paths": relevant_paths,
            "diff_excerpt": _git_diff_excerpt(repo_root, relevant_paths),
            "source_excerpt": {
                path: _read_excerpt(repo_root, path, max_lines=80) for path in relevant_paths
            },
        }

    if need == "lint_error_details":
        return _check_payload(failed_checks, "lint", "lint_report")
    if need == "type_error_details":
        return _check_payload(failed_checks, "typecheck", "typecheck_report")
    if need == "security_finding_details":
        return _check_payload(failed_checks, "security", "security_report")

    return None


def _check_payload(
    failed_checks: list[dict[str, Any]],
    check_name: str,
    payload_type: str,
) -> dict[str, Any]:
    check = next((item for item in failed_checks if item.get("name") == check_name), {})
    return {
        "type": payload_type,
        "details": check.get("details", ""),
        "check": check,
    }


def _failing_test_path(failed_checks: list[dict[str, Any]], packet_tests: list[str]) -> str:
    for check in failed_checks:
        for key in ("failed_test", "test_path"):
            if check.get(key):
                return check[key]
    return packet_tests[0] if packet_tests else ""


def _relevant_paths_for_need(packet_files: list[str], need: str) -> list[str]:
    keywords = {
        "recent_auth_diff": ("auth", "token", "session"),
        "token_rotation_helper": ("token", "service", "helper"),
        "retry_helper_context": ("retry", "hook", "helper"),
    }
    matched = [
        path for path in packet_files
        if any(keyword in path.lower() for keyword in keywords.get(need, ()))
    ]
    if matched:
        return matched[:2]
    return packet_files[:2]


def _git_diff_excerpt(repo_root: Path, paths: list[str]) -> str:
    if not paths:
        return ""

    try:
        proc = subprocess.run(
            ["git", "diff", "--", *paths],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""

    diff_text = proc.stdout or proc.stderr
    return diff_text[:1200]


def _read_excerpt(repo_root: Path, relative_path: str, max_lines: int) -> str:
    if not relative_path:
        return ""
    full_path = repo_root / relative_path
    if not full_path.exists() or not full_path.is_file():
        return ""
    try:
        lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[:max_lines])
