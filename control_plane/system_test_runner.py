"""Automated sandbox tests for SHIELD workflows."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from control_plane.compiler.build_indexes import build_all
from control_plane.compiler.dashboard_snapshot import build_dashboard_snapshot
from control_plane.compiler.local_indexes import build_local_indexes
from control_plane.orchestrator import Orchestrator, OrchestratorConfig


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


@dataclass
class PromptScenario:
    task_id: str
    session_id: str
    path: Path
    expected: dict[str, Any]
    task: dict[str, Any]


def _make_config(repo_root: Path) -> OrchestratorConfig:
    return OrchestratorConfig(
        repo_root=repo_root,
        runtime_dir=repo_root / "runtime",
        knowledge_dir=repo_root / "knowledge",
        hub_dir=repo_root / ".hub",
    )


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


def run_prompt_sandbox(repo_root: Path) -> dict[str, Any]:
    """Run a prompt-driven multi-session project flow inside the current repo."""
    started_at = datetime.now(timezone.utc).isoformat()
    report_dir = repo_root / "runtime" / "reports" / "system_tests"
    report_dir.mkdir(parents=True, exist_ok=True)

    build_all(repo_root, include_pool=False)
    prompt_asset = _validate_prompt_assets(repo_root)
    _reset_prompt_sandbox_outputs(repo_root)

    scenario_dir = repo_root / "runtime" / "state" / "prompt_sandbox_tasks"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    orchestrator = Orchestrator(_make_config(repo_root))

    product = PromptScenario(
        task_id="PROMPT-PRODUCT-001",
        session_id="SESSION-PRODUCT-001",
        path=scenario_dir / "product_brief.yaml",
        expected={
            "task_type": "planning",
            "role": "product",
            "mode": "solo",
            "status": "completed",
            "verifier_status": "passed",
            "retry_count": 0,
            "report_refs": [],
        },
        task=_prompt_product_task(),
    )
    product_result = _run_prompt_scenario(repo_root, orchestrator, product)
    product_report = _result_report_ref(repo_root, product_result["runtime_result"])

    cto = PromptScenario(
        task_id="PROMPT-CTO-001",
        session_id="SESSION-CTO-001",
        path=scenario_dir / "cto_plan.yaml",
        expected={
            "task_type": "planning",
            "role": "cto",
            "mode": "solo",
            "status": "completed",
            "verifier_status": "passed",
            "retry_count": 0,
            "report_refs": [product_report],
        },
        task=_prompt_cto_task([product_report]),
    )
    cto_result = _run_prompt_scenario(repo_root, orchestrator, cto)
    cto_report = _result_report_ref(repo_root, cto_result["runtime_result"])

    frontend = PromptScenario(
        task_id="PROMPT-FRONTEND-001",
        session_id="SESSION-FRONTEND-001",
        path=scenario_dir / "frontend_build.yaml",
        expected={
            "task_type": "feature",
            "role": "frontend",
            "mode": "solo",
            "status": "completed",
            "verifier_status": "passed",
            "retry_count": 0,
            "report_refs": [product_report, cto_report],
        },
        task=_prompt_frontend_task([product_report, cto_report]),
    )
    frontend_result = _run_prompt_scenario(repo_root, orchestrator, frontend)
    frontend_report = _result_report_ref(repo_root, frontend_result["runtime_result"])

    qa = PromptScenario(
        task_id="PROMPT-QA-001",
        session_id="SESSION-QA-001",
        path=scenario_dir / "qa_verify.yaml",
        expected={
            "task_type": "test",
            "role": "qa",
            "mode": "solo",
            "status": "completed",
            "verifier_status": "passed",
            "retry_count": 0,
            "report_refs": [cto_report, frontend_report],
        },
        task=_prompt_qa_task([cto_report, frontend_report]),
    )
    qa_result = _run_prompt_scenario(repo_root, orchestrator, qa)

    dashboard_path = build_dashboard_snapshot(repo_root)
    index_paths = build_local_indexes(repo_root)
    continuity, continuity_failures = _validate_prompt_continuity(
        repo_root,
        task_ids=[product.task_id, cto.task_id, frontend.task_id, qa.task_id],
    )

    session_runs = [
        product_result["inspection"],
        cto_result["inspection"],
        frontend_result["inspection"],
        qa_result["inspection"],
    ]
    failures = [*prompt_asset["failures"], *continuity_failures]
    for run in session_runs:
        failures.extend(run.get("failures", []))

    result = {
        "status": "passed" if not failures else "failed",
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "prompt_asset_check": prompt_asset,
        "sessions": session_runs,
        "continuity": continuity,
        "dashboard_path": str(dashboard_path),
        "index_paths": index_paths,
        "failures": failures,
    }
    report_path = report_dir / f"prompt_sandbox_{_timestamp()}.json"
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

    command_results.append(_run_command(sandbox, ["prompt-sandbox"]))
    prompt_sandbox = _inspect_prompt_sandbox_result(sandbox)
    failures.extend(prompt_sandbox.get("failures", []))

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
        "prompt_sandbox": prompt_sandbox,
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
            "related_reports": [],
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


def _run_prompt_scenario(
    repo_root: Path,
    orchestrator: Orchestrator,
    scenario: PromptScenario,
) -> dict[str, Any]:
    scenario.path.write_text(
        yaml.safe_dump(scenario.task, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    runtime_result = orchestrator.execute_task(task=scenario.task, session_id=scenario.session_id)
    inspection = _inspect_task_result(repo_root, {
        "id": scenario.task_id,
        "expected": scenario.expected,
    })
    inspection["session_id"] = scenario.session_id
    inspection["task_path"] = str(scenario.path.relative_to(repo_root))
    inspection["session_report_path"] = runtime_result["post_task"].get("session_report_path")
    inspection["quick_report_path"] = runtime_result["post_task"].get("quick_report_path")
    return {
        "runtime_result": runtime_result,
        "inspection": inspection,
    }


def _validate_prompt_assets(repo_root: Path) -> dict[str, Any]:
    prompt_pack = repo_root / "PROMPT_PACK.md"
    shield_template = repo_root / "tools" / "prompt-builder" / "templates" / "shield.js"
    failures: list[str] = []
    checks = {
        "prompt_pack": [
            "## Universal Session Boot Prompt",
            "### Product Session",
            "### CTO Session",
            "### Frontend",
            "### QA",
            "## Short Prompt Adapter",
        ],
        "shield_template": [
            "shield_session_boot",
            "shield_zero_build",
            "shield_improve_repo",
            "shield_solve_issue",
            "shield_short_prompt_adapter",
        ],
    }
    sources = {
        "prompt_pack": prompt_pack,
        "shield_template": shield_template,
    }
    for label, path in sources.items():
        if not path.exists():
            failures.append(f"prompt asset missing: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in checks[label]:
            if needle not in text:
                failures.append(f"{label}: missing '{needle}'")
    return {
        "status": "passed" if not failures else "failed",
        "checked_files": {key: str(value) for key, value in sources.items()},
        "failures": failures,
    }


def _reset_prompt_sandbox_outputs(repo_root: Path) -> None:
    for rel_path in (
        "runtime/sessions/prompt_sandbox",
        "runtime/state/prompt_sandbox_tasks",
    ):
        path = repo_root / rel_path
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def _prompt_product_task() -> dict[str, Any]:
    brief_path = "runtime/sessions/prompt_sandbox/leadership_brief.json"
    criteria = [
        f"brief file {brief_path} exists",
        "brief file mentions Tide Board",
        "brief file mentions frontend and qa tasks",
    ]
    return {
        "schema_version": "2.1",
        "id": "PROMPT-PRODUCT-001",
        "task_type": "planning",
        "title": "Plan product brief for Tide Board microsite",
        "description": "Turn a short zero-build intent into a tiny product brief for a prompt-driven multi-session project.",
        "assigned_role": "product",
        "priority": "medium",
        "status": "queued",
        "domain": "general",
        "inputs": {
            "related_paths": [],
            "related_tests": [],
            "related_handoffs": [],
            "related_reports": [],
            "related_logs": [],
            "related_modules": [],
        },
        "constraints": ["planning_only", "small_scope", "no_worker_execution"],
        "acceptance_criteria": criteria,
        "metadata": {
            "collaboration": {
                "scenario": "zero_build",
                "owner_role": "product",
                "owner_session": "SESSION-PRODUCT-001",
                "expected_report": "session_report",
            },
            "execution": {
                "primary_commands": [_write_text_file_command(
                    brief_path,
                    json.dumps({
                        "project": "Tide Board",
                        "problem": "A simple shared launch page is needed for a coastal research tool.",
                        "scope_now": ["simple landing page", "clear CTA", "one QA pass"],
                        "proposed_tasks": [
                            {"assigned_role": "frontend", "title": "Build microsite"},
                            {"assigned_role": "qa", "title": "Verify microsite"},
                        ],
                    }, indent=2),
                )],
                "output_files": [brief_path],
                "changed_files": [brief_path],
                "satisfied_criteria": criteria,
            },
        },
    }


def _prompt_cto_task(report_refs: list[str]) -> dict[str, Any]:
    decision_path = "runtime/sessions/prompt_sandbox/decision_log.json"
    brief_path = "runtime/sessions/prompt_sandbox/leadership_brief.json"
    criteria = [
        f"decision log {decision_path} exists",
        "decision log mentions frontend owner",
        "decision log mentions qa verification",
    ]
    return {
        "schema_version": "2.1",
        "id": "PROMPT-CTO-001",
        "task_type": "planning",
        "title": "Plan technical slice for Tide Board microsite",
        "description": "Use the product brief to set the smallest technical direction and worker ownership for the microsite.",
        "assigned_role": "cto",
        "priority": "medium",
        "status": "queued",
        "domain": "general",
        "inputs": {
            "related_paths": [brief_path],
            "related_tests": [],
            "related_handoffs": [],
            "related_reports": report_refs,
            "related_logs": [],
            "related_modules": [],
        },
        "constraints": ["planning_only", "no_runtime_expansion", "single_frontend_slice"],
        "acceptance_criteria": criteria,
        "metadata": {
            "collaboration": {
                "scenario": "zero_build",
                "owner_role": "cto",
                "owner_session": "SESSION-CTO-001",
                "expected_report": "session_report",
            },
            "execution": {
                "primary_commands": [_write_text_file_command(
                    decision_path,
                    json.dumps({
                        "project": "Tide Board",
                        "technical_direction": "Static HTML and CSS only.",
                        "owners": {
                            "frontend": "Build the landing page",
                            "qa": "Verify CTA and core content",
                        },
                        "verification": "QA verifies brand, CTA, and report flow.",
                    }, indent=2),
                )],
                "output_files": [decision_path],
                "changed_files": [decision_path],
                "satisfied_criteria": criteria,
            },
        },
    }


def _prompt_frontend_task(report_refs: list[str]) -> dict[str, Any]:
    index_path = "runtime/sessions/prompt_sandbox/site/index.html"
    css_path = "runtime/sessions/prompt_sandbox/site/styles.css"
    criteria = [
        f"landing page file {index_path} exists",
        f"stylesheet file {css_path} exists",
        "page includes Tide Board brand",
        "page includes a primary CTA",
    ]
    return {
        "schema_version": "2.1",
        "id": "PROMPT-FRONTEND-001",
        "title": "Build Tide Board landing page",
        "description": "Implement the tiny prompt-driven launch page from the approved brief and CTO direction.",
        "assigned_role": "frontend",
        "priority": "medium",
        "status": "queued",
        "domain": "frontend",
        "inputs": {
            "related_paths": [index_path, css_path],
            "related_tests": [],
            "related_handoffs": [],
            "related_reports": report_refs,
            "related_logs": [],
            "related_modules": [],
        },
        "constraints": ["no_framework", "small_static_website_only", "match_leadership_scope"],
        "acceptance_criteria": criteria,
        "metadata": {
            "collaboration": {
                "scenario": "zero_build",
                "owner_role": "frontend",
                "owner_session": "SESSION-FRONTEND-001",
                "expected_report": "session_report",
            },
            "execution": {
                "primary_commands": [_write_prompt_site_command("runtime/sessions/prompt_sandbox/site")],
                "output_files": [index_path, css_path],
                "changed_files": [index_path, css_path],
                "satisfied_criteria": criteria,
            },
        },
    }


def _prompt_qa_task(report_refs: list[str]) -> dict[str, Any]:
    verdict_path = "runtime/sessions/prompt_sandbox/qa_verdict.json"
    index_path = "runtime/sessions/prompt_sandbox/site/index.html"
    css_path = "runtime/sessions/prompt_sandbox/site/styles.css"
    criteria = [
        f"qa verdict file {verdict_path} exists",
        "qa verdict says passed",
        "qa verified Tide Board CTA and brand",
    ]
    return {
        "schema_version": "2.1",
        "id": "PROMPT-QA-001",
        "task_type": "test",
        "title": "Verify Tide Board microsite",
        "description": "Run a QA verification pass on the small Tide Board site and write a concise verdict artifact.",
        "assigned_role": "qa",
        "priority": "medium",
        "status": "queued",
        "domain": "frontend",
        "inputs": {
            "related_paths": [index_path, css_path],
            "related_tests": [],
            "related_handoffs": [],
            "related_reports": report_refs,
            "related_logs": [],
            "related_modules": [],
        },
        "constraints": ["verification_only", "no_scope_change", "report_results"],
        "acceptance_criteria": criteria,
        "metadata": {
            "collaboration": {
                "scenario": "zero_build",
                "owner_role": "qa",
                "owner_session": "SESSION-QA-001",
                "expected_report": "session_report",
            },
            "execution": {
                "primary_commands": [_write_qa_verdict_command(verdict_path, index_path, css_path)],
                "output_files": [verdict_path],
                "changed_files": [verdict_path],
                "satisfied_criteria": criteria,
            },
        },
    }


def _validate_prompt_continuity(repo_root: Path, task_ids: list[str]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    expected_outputs = [
        "runtime/sessions/prompt_sandbox/leadership_brief.json",
        "runtime/sessions/prompt_sandbox/decision_log.json",
        "runtime/sessions/prompt_sandbox/qa_verdict.json",
        "runtime/sessions/prompt_sandbox/site/index.html",
        "runtime/sessions/prompt_sandbox/site/styles.css",
    ]
    for rel_path in expected_outputs:
        if not (repo_root / rel_path).exists():
            failures.append(f"prompt_sandbox: missing expected output {rel_path}")

    session_index = _read_json(repo_root / "runtime" / "cache" / "indexes" / "session_report_index.json")
    task_index = _read_json(repo_root / "runtime" / "cache" / "indexes" / "task_status_index.json")
    dashboard = _read_json(repo_root / "runtime" / "cache" / "summaries" / "dashboard_snapshot.json")

    session_reports = session_index.get("reports", [])
    task_statuses = task_index.get("tasks", [])
    session_report_ids = {item.get("task_id") for item in session_reports}
    task_status_ids = {item.get("task_id") for item in task_statuses}

    for task_id in task_ids:
        if task_id not in session_report_ids:
            failures.append(f"prompt_sandbox: session report index missing {task_id}")
        if task_id not in task_status_ids:
            failures.append(f"prompt_sandbox: task status index missing {task_id}")

    dashboard_report_ids = {
        item.get("task_id")
        for item in dashboard.get("recent_session_reports", [])
        if isinstance(item, dict)
    }
    if not dashboard_report_ids.intersection(task_ids):
        failures.append("prompt_sandbox: dashboard snapshot did not pick up prompt session reports")

    done_paths = [repo_root / ".hub" / "done" / f"{task_id}.json" for task_id in task_ids]
    done_payloads = [_read_json(path) for path in done_paths]
    unexpected_handoffs = [
        payload.get("artifacts", {}).get("handoff_path")
        for payload in done_payloads
        if payload.get("artifacts", {}).get("handoff_path")
    ]
    if unexpected_handoffs:
        failures.append("prompt_sandbox: success flow unexpectedly produced handoffs")

    return {
        "expected_outputs": expected_outputs,
        "session_report_index_count": session_index.get("count", 0),
        "task_status_index_count": task_index.get("count", 0),
        "dashboard_recent_session_reports": list(dashboard_report_ids),
        "unexpected_handoffs": unexpected_handoffs,
    }, failures


def _inspect_prompt_sandbox_result(sandbox: Path) -> dict[str, Any]:
    report_dir = sandbox / "runtime" / "reports" / "system_tests"
    reports = sorted(report_dir.glob("prompt_sandbox_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not reports:
        return {
            "status": "failed",
            "failures": ["prompt_sandbox: missing prompt sandbox report"],
        }
    payload = _read_json(reports[0])
    failures = list(payload.get("failures", []))
    if payload.get("status") != "passed":
        failures.append("prompt_sandbox command returned failed status")
    payload["failures"] = failures
    return payload


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


def _write_prompt_site_command(site_dir: str) -> str:
    index = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tide Board</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main class="hero">
    <p class="eyebrow">Tide Board</p>
    <h1>Log coastal observations before the next shift.</h1>
    <p class="lede">A tiny landing page for field teams who need fast capture and clean handoffs.</p>
    <a class="cta" href="#pilot">Start free pilot</a>
  </main>
  <section class="proof" id="pilot">
    <p>Built through Product -> CTO -> Frontend -> QA session flow.</p>
  </section>
</body>
</html>"""
    css = """body {
  margin: 0;
  min-height: 100vh;
  font-family: Georgia, 'Times New Roman', serif;
  color: #173038;
  background: linear-gradient(160deg, #f6f1dd 0%, #d8ebe8 45%, #a9c7c1 100%);
}
.hero {
  min-height: 88vh;
  display: grid;
  align-content: center;
  gap: 1.2rem;
  padding: clamp(2rem, 7vw, 7rem);
  max-width: 960px;
}
.eyebrow {
  margin: 0;
  font-family: Verdana, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.26em;
  font-size: 0.78rem;
}
h1 {
  margin: 0;
  max-width: 10ch;
  font-size: clamp(3.4rem, 9vw, 7.8rem);
  line-height: 0.84;
}
.lede {
  max-width: 42rem;
  font-size: clamp(1.05rem, 2vw, 1.4rem);
  line-height: 1.55;
}
.cta {
  width: fit-content;
  border-radius: 999px;
  padding: 0.95rem 1.3rem;
  background: #0e6570;
  color: #ffffff;
  text-decoration: none;
  font-family: Verdana, sans-serif;
  box-shadow: 0 16px 36px rgba(14, 101, 112, 0.25);
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


def _write_text_file_command(path: str, content: str) -> str:
    parent = Path(path).parent.as_posix()
    return f"""New-Item -ItemType Directory -Path '{parent}' -Force | Out-Null
@'
{content}
'@ | Set-Content -Path '{path}' -Encoding utf8"""


def _write_qa_verdict_command(verdict_path: str, index_path: str, css_path: str) -> str:
    verdict = json.dumps({
        "status": "passed",
        "checked": ["brand", "cta", "styles"],
        "project": "Tide Board",
    }, indent=2)
    return f"""$indexPath = '{index_path}'
$cssPath = '{css_path}'
if (!(Test-Path $indexPath)) {{ Write-Error 'Missing landing page'; exit 1 }}
if (!(Test-Path $cssPath)) {{ Write-Error 'Missing stylesheet'; exit 1 }}
$indexContent = Get-Content $indexPath -Raw
if ($indexContent -notmatch 'Tide Board') {{ Write-Error 'Missing brand'; exit 1 }}
if ($indexContent -notmatch 'Start free pilot') {{ Write-Error 'Missing CTA'; exit 1 }}
New-Item -ItemType Directory -Path 'runtime/sessions/prompt_sandbox' -Force | Out-Null
@'
{verdict}
'@ | Set-Content -Path '{verdict_path}' -Encoding utf8"""


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
        "report_refs": packet.get("report_refs", []),
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


def _result_report_ref(repo_root: Path, runtime_result: dict[str, Any]) -> str:
    path = runtime_result.get("post_task", {}).get("session_report_path", "")
    return str(Path(path).resolve().relative_to(repo_root.resolve())).replace("\\", "/")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
