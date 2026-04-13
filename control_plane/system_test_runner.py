"""Automated sandbox tests for SHIELD workflows."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


_IGNORE_DIRS = {
    ".git",
    ".hub",
    ".skills_pool",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "runtime",
    "refs_github",
}


def run_system_tests(repo_root: Path, iterations: int = 1, keep: bool = True) -> dict[str, Any]:
    """Create fresh sandbox copies and run end-to-end workflow scenarios."""
    started_at = datetime.now(timezone.utc).isoformat()
    report_dir = repo_root / "runtime" / "reports" / "system_tests"
    report_dir.mkdir(parents=True, exist_ok=True)

    runs: list[dict[str, Any]] = []
    failures: list[str] = []
    for index in range(1, iterations + 1):
        sandbox = _create_sandbox(repo_root, index)
        run_result = _run_sandbox_suite(sandbox, index)
        runs.append(run_result)
        failures.extend(
            f"iteration {index}: {failure}" for failure in run_result.get("failures", [])
        )
        if not keep and run_result.get("status") == "passed":
            shutil.rmtree(sandbox, ignore_errors=True)
            run_result["sandbox_removed"] = True

    result = {
        "status": "passed" if not failures else "failed",
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "iterations": iterations,
        "failures": failures,
        "runs": runs,
    }
    report_path = report_dir / f"system_test_{_timestamp()}.json"
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    result["report_path"] = str(report_path)
    return result


def _create_sandbox(repo_root: Path, iteration: int) -> Path:
    sandbox = repo_root.parent / f"{repo_root.name}_SYSTEM_TEST_{_timestamp()}_{iteration}"
    if sandbox.exists():
        shutil.rmtree(sandbox)

    def ignore(_: str, names: list[str]) -> set[str]:
        ignored = {name for name in names if name in _IGNORE_DIRS}
        ignored.update({name for name in names if name.endswith(".pyc")})
        return ignored

    shutil.copytree(repo_root, sandbox, ignore=ignore)
    (sandbox / "SYSTEM_TEST_SOURCE.txt").write_text(str(repo_root), encoding="utf-8")
    return sandbox


def _run_sandbox_suite(sandbox: Path, iteration: int) -> dict[str, Any]:
    system_dir = sandbox / "tests" / "system"
    system_dir.mkdir(parents=True, exist_ok=True)
    tasks = _write_system_tasks(system_dir)

    command_results = [_run_command(sandbox, ["compile"])]
    scenario_results: list[dict[str, Any]] = []
    failures: list[str] = []

    for scenario in tasks:
        command_results.append(_run_command(sandbox, ["plan", str(scenario["path"])]))
        command_results.append(_run_command(sandbox, ["run", str(scenario["path"])]))
        result = _inspect_task_result(sandbox, scenario)
        scenario_results.append(result)
        failures.extend(result.get("failures", []))

    command_results.append(_run_command(sandbox, ["audit"]))
    for command in command_results:
        if command["returncode"] != 0:
            failures.append(f"command failed: {' '.join(command['args'])}")

    return {
        "status": "passed" if not failures else "failed",
        "iteration": iteration,
        "sandbox_path": str(sandbox),
        "failures": failures,
        "commands": command_results,
        "scenarios": scenario_results,
    }


def _write_system_tasks(system_dir: Path) -> list[dict[str, Any]]:
    scenarios = [
        {
            "id": "SYSTEM-ZERO-WEB-001",
            "path": system_dir / "zero_build_noisy_website.yaml",
            "expected": {
                "task_type": "feature",
                "role": "frontend",
                "mode": "solo",
                "status": "completed",
                "verifier_status": "passed",
                "retry_count": 0,
            },
            "task": _website_task(
                task_id="SYSTEM-ZERO-WEB-001",
                title="Build a simple launch website",
                description=(
                    "Create a minimal static landing page for the Harbor Notes product. "
                    "This zero-build scenario should test whether SHIELD execution and "
                    "reporting stay small without triggering QA ownership."
                ),
                site_dir="system_site_zero",
            ),
        },
        {
            "id": "SYSTEM-IMPROVE-WEB-001",
            "path": system_dir / "improve_website.yaml",
            "expected": {
                "task_type": "feature",
                "role": "frontend",
                "mode": "solo",
                "status": "completed",
                "verifier_status": "passed",
                "retry_count": 0,
            },
            "task": _website_task(
                task_id="SYSTEM-IMPROVE-WEB-001",
                title="Add a simple proof section",
                description="Improve the Harbor Notes landing page with one small proof section.",
                site_dir="system_site_improve",
            ),
        },
        {
            "id": "SYSTEM-FIX-WEB-001",
            "path": system_dir / "solve_issue_retry_website.yaml",
            "expected": {
                "task_type": "bugfix",
                "role": "frontend",
                "mode": "solo",
                "status": "completed",
                "verifier_status": "passed",
                "retry_count": 1,
            },
            "task": _retry_website_task(),
        },
    ]

    for scenario in scenarios:
        scenario["path"].write_text(
            yaml.safe_dump(scenario["task"], sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return scenarios


def _website_task(task_id: str, title: str, description: str, site_dir: str) -> dict[str, Any]:
    index_path = f"{site_dir}/index.html"
    css_path = f"{site_dir}/styles.css"
    return {
        "schema_version": "2.1",
        "id": task_id,
        "title": title,
        "description": description,
        "assigned_role": "frontend",
        "priority": "low",
        "status": "queued",
        "domain": "frontend",
        "inputs": {
            "related_paths": [index_path, css_path],
            "related_tests": [],
            "related_handoffs": [],
            "related_logs": [],
            "related_modules": [],
        },
        "constraints": ["no_framework", "no_extra_architecture", "small_static_website_only"],
        "acceptance_criteria": [
            f"landing page file {index_path} exists",
            f"stylesheet file {css_path} exists",
            "page includes Harbor Notes brand",
            "page includes a primary CTA",
        ],
        "metadata": {
            "collaboration": {
                "leadership_brief_id": f"BRIEF-{task_id}",
                "scenario": "zero_build",
                "owner_role": "frontend",
                "owner_session": f"SESSION-{task_id}",
                "expected_report": "session_report",
            },
            "execution": {
                "primary_commands": [_write_site_command(site_dir, include_cta=True)],
                "output_files": [index_path, css_path],
                "changed_files": [index_path, css_path],
                "satisfied_criteria": [
                    f"landing page file {index_path} exists",
                    f"stylesheet file {css_path} exists",
                    "page includes Harbor Notes brand",
                    "page includes a primary CTA",
                ],
            },
        },
    }


def _retry_website_task() -> dict[str, Any]:
    task = _website_task(
        task_id="SYSTEM-FIX-WEB-001",
        title="Fix missing primary CTA",
        description="Fix the landing page so the primary CTA is present after verification catches it.",
        site_dir="system_site_fix",
    )
    task["metadata"]["execution"]["primary_commands"] = [_write_site_command("system_site_fix", include_cta=False)]
    task["metadata"]["execution"]["retry_commands"] = [_write_site_command("system_site_fix", include_cta=True)]
    task["metadata"]["execution"]["satisfied_criteria"] = [
        "landing page file system_site_fix/index.html exists",
        "stylesheet file system_site_fix/styles.css exists",
        "page includes Harbor Notes brand",
    ]
    task["metadata"]["execution"]["retry_satisfied_criteria"] = list(task["acceptance_criteria"])
    return task


def _write_site_command(site_dir: str, include_cta: bool) -> str:
    cta = '<a class="cta" href="#start">Start a field log</a>' if include_cta else ""
    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Harbor Notes</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main class="hero">
    <p class="eyebrow">Harbor Notes</p>
    <h1>Capture field notes before the tide turns.</h1>
    <p class="lede">A calm offline notebook for small research teams.</p>
    {cta}
  </main>
  <section class="proof" id="start">
    <p>Quick capture, clean review, and one-page handoff summaries.</p>
  </section>
</body>
</html>"""
    css = """body {
  margin: 0;
  min-height: 100vh;
  font-family: Georgia, 'Times New Roman', serif;
  color: #11251f;
  background: radial-gradient(circle at 20% 10%, #fff8e8 0, #f3ead7 42%, #d8c8a9 100%);
}
.hero {
  min-height: 88vh;
  display: grid;
  align-content: center;
  gap: 1.25rem;
  padding: clamp(2rem, 7vw, 7rem);
  max-width: 980px;
}
.eyebrow {
  margin: 0;
  font-family: Verdana, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  font-size: 0.78rem;
}
h1 {
  margin: 0;
  max-width: 11ch;
  font-size: clamp(3.6rem, 10vw, 8.5rem);
  line-height: 0.82;
}
.lede {
  max-width: 42rem;
  font-size: clamp(1.1rem, 2vw, 1.45rem);
  line-height: 1.55;
}
.cta {
  width: fit-content;
  border-radius: 999px;
  padding: 0.95rem 1.25rem;
  background: #dd6e42;
  color: white;
  font-family: Verdana, sans-serif;
  text-decoration: none;
  box-shadow: 0 14px 36px rgba(17, 37, 31, 0.18);
}
.proof {
  padding: 2rem clamp(2rem, 7vw, 7rem) 5rem;
  font-family: Verdana, sans-serif;
  font-size: 0.95rem;
}"""
    return f"""New-Item -ItemType Directory -Path '{site_dir}' -Force | Out-Null
@'
{index}
'@ | Set-Content -Path '{site_dir}/index.html' -Encoding utf8
@'
{css}
'@ | Set-Content -Path '{site_dir}/styles.css' -Encoding utf8"""


def _run_command(sandbox: Path, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "run_orchestrator.py", *args],
        cwd=sandbox,
        capture_output=True,
        text=True,
        timeout=240,
    )
    return {
        "args": ["run_orchestrator.py", *args],
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
    }


def _inspect_task_result(sandbox: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    task_id = scenario["id"]
    expected = scenario["expected"]
    packet = _read_json(sandbox / "runtime" / "state" / "task_packets" / f"{task_id}.json")
    metrics = _read_json(sandbox / "runtime" / "reports" / "metrics" / f"{task_id}.metrics.json")
    done = _read_json(sandbox / ".hub" / "done" / f"{task_id}.json")

    actual = {
        "task_type": packet.get("task_type"),
        "role": packet.get("role"),
        "mode": packet.get("mode"),
        "status": done.get("status"),
        "verifier_status": metrics.get("verifier_status"),
        "retry_count": metrics.get("retry_count"),
        "packet_size": metrics.get("packet_size"),
        "loaded_file_count": metrics.get("loaded_file_count"),
        "loaded_fragment_count": metrics.get("loaded_fragment_count"),
        "runtime_steps": metrics.get("runtime_steps", []),
        "done_report_path": str(sandbox / ".hub" / "done" / f"{task_id}.json"),
        "session_report_path": done.get("artifacts", {}).get("session_report_path"),
        "quick_report_path": done.get("artifacts", {}).get("quick_report_path"),
    }

    failures = []
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            failures.append(
                f"{task_id}: expected {key}={expected_value!r}, got {actual.get(key)!r}"
            )
    if actual["loaded_file_count"] > 3:
        failures.append(f"{task_id}: loaded too many files ({actual['loaded_file_count']})")
    if actual["loaded_fragment_count"] > 3:
        failures.append(f"{task_id}: loaded too many fragments ({actual['loaded_fragment_count']})")

    return {
        "task_id": task_id,
        "expected": expected,
        "actual": actual,
        "failures": failures,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
