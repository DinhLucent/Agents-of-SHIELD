"""CLI entrypoint for the Agents-of-SHIELD v2 control plane.

Usage:
    python run_orchestrator.py compile           # Compile all knowledge indexes
    python run_orchestrator.py plan <task.yaml>  # Build packet + runtime plan only
    python run_orchestrator.py run <task.yaml>   # Execute a task end-to-end
    python run_orchestrator.py dashboard         # Print CEO progress view
    python run_orchestrator.py audit             # Run serial system audit fixtures
    python run_orchestrator.py prompt-sandbox    # Run prompt-driven multi-session project flow
    python run_orchestrator.py system-test       # Run automated sandbox scenarios
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from control_plane.compiler.build_indexes import build_all
from control_plane.compiler.dashboard_snapshot import build_dashboard_snapshot
from control_plane.orchestrator import Orchestrator, OrchestratorConfig
from control_plane.system_test_runner import run_prompt_sandbox, run_system_tests


def _make_config(repo_root: Path) -> OrchestratorConfig:
    return OrchestratorConfig(
        repo_root=repo_root,
        runtime_dir=repo_root / "runtime",
        knowledge_dir=repo_root / "knowledge",
        hub_dir=repo_root / ".hub",
    )


def cmd_compile(repo_root: Path, include_pool: bool = False) -> None:
    """Compile all knowledge source into indexes."""
    build_all(repo_root, include_pool=include_pool)


def cmd_run(repo_root: Path, task_path: Path | None = None) -> None:
    """Run a task end-to-end through execution, verification, and retry."""
    config = _make_config(repo_root)
    orchestrator = Orchestrator(config)

    if task_path is None:
        task_path = repo_root / "templates" / "task.yaml"

    if not task_path.exists():
        print(f"Error: Task file not found: {task_path}")
        sys.exit(1)

    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    result = orchestrator.execute_task(task=task, session_id="SESSION-LOCAL-001")
    _print_json("Orchestrator Result", result)


def cmd_plan(repo_root: Path, task_path: Path | None = None) -> None:
    """Build packet + runtime plan without executing the task."""
    config = _make_config(repo_root)
    orchestrator = Orchestrator(config)

    if task_path is None:
        task_path = repo_root / "templates" / "task.yaml"

    if not task_path.exists():
        print(f"Error: Task file not found: {task_path}")
        sys.exit(1)

    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    result = orchestrator.run_task(task=task, session_id="SESSION-LOCAL-001")
    _print_json("Orchestrator Result", result)


def cmd_audit(repo_root: Path) -> None:
    """Run the serial execution + collaboration audit baseline."""
    build_all(repo_root, include_pool=False)
    _validate_collaboration_templates(repo_root)
    _validate_common_session_protocol(repo_root)
    _validate_role_curriculum(repo_root)

    config = _make_config(repo_root)
    orchestrator = Orchestrator(config)
    audit_tasks = [
        ("plan", repo_root / "templates" / "task.yaml", "pending_primary_execution"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "happy_path.yaml", "completed"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "retry_scenario.yaml", "completed"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "hard_fail.yaml", "failed"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "role_gate_mismatch.yaml", "failed"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "security_blocked.yaml", "failed"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "workspace_blocked.yaml", "failed"),
        ("run", repo_root / "tests" / "fixtures" / "audit" / "destructive_traversal.yaml", "failed"),
    ]
    results = []
    failures = []
    for mode, task_path, expected_status in audit_tasks:
        task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
        _remove_expected_absent_outputs(repo_root, task)
        if mode == "plan":
            result = orchestrator.run_task(task=task, session_id="SESSION-AUDIT-001")
        else:
            result = orchestrator.execute_task(task=task, session_id="SESSION-AUDIT-001")
        status = result["summary"]["agent_status"]
        session_report_path = result["post_task"].get("session_report_path")
        quick_report_path = result["post_task"].get("quick_report_path")
        done_report_path = result.get("task_state", {}).get("done_report_path")
        handoff_path = _handoff_path_from_done(done_report_path)
        if status != expected_status:
            failures.append(f"{task_path.name}: expected {expected_status}, got {status}")
        for report_path in (session_report_path, quick_report_path):
            if report_path and not Path(report_path).exists():
                failures.append(f"{task_path.name}: missing report artifact {report_path}")
        if session_report_path and Path(session_report_path).exists():
            failures.extend(_validate_session_report_artifact(Path(session_report_path), task_path.name))
        if task_path.name == "hard_fail.yaml" and not handoff_path:
            failures.append("hard_fail.yaml: expected a handoff artifact")
        if task_path.name == "role_gate_mismatch.yaml":
            failures.extend(_validate_role_gate_mismatch(repo_root, task, result, handoff_path))
        if task_path.name in {"security_blocked.yaml", "workspace_blocked.yaml", "destructive_traversal.yaml"}:
            failures.extend(_validate_security_blocked(repo_root, task, result, handoff_path))
        if handoff_path:
            failures.extend(_validate_handoff_artifact(Path(handoff_path), task_path.name))
        results.append({
            "mode": mode,
            "task_path": str(task_path.relative_to(repo_root)),
            "task_id": result["summary"]["task_id"],
            "status": status,
            "expected_status": expected_status,
            "execution_mode": result["summary"].get("execution_mode"),
            "verification": result["summary"].get("verification", []),
            "session_report_path": session_report_path,
            "quick_report_path": quick_report_path,
            "done_report_path": done_report_path,
            "handoff_path": handoff_path,
        })
    if failures:
        _print_json("SHIELD Audit Result", {"status": "failed", "failures": failures, "results": results})
        sys.exit(1)

    _print_json("SHIELD Audit Result", {
        "status": "completed",
        "checks": [
            "compile",
            "collaboration_templates",
            "common_session_protocol",
            "role_curriculum",
            "plan_task",
            "happy_path",
            "retry_path",
            "hard_fail_path",
            "role_gate_mismatch",
            "security_blocked",
            "workspace_blocked",
            "destructive_traversal",
        ],
        "results": results,
    })


def cmd_dashboard(repo_root: Path) -> None:
    """Print a CEO-friendly progress view from .hub and runtime reports."""
    snapshot_path = build_dashboard_snapshot(repo_root)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    _print_json("SHIELD Dashboard", {
        "snapshot_path": str(snapshot_path),
        "active_tasks": snapshot.get("active_tasks", [])[:10],
        "recent_done": snapshot.get("recent_done", [])[:10],
        "recent_handoffs": snapshot.get("recent_handoffs", [])[:10],
        "recent_session_reports": snapshot.get("recent_session_reports", [])[:10],
        "recent_system_tests": snapshot.get("recent_system_tests", [])[:5],
        "blocked_tasks": snapshot.get("blocked_tasks", []),
        "updated_at": snapshot.get("updated_at"),
    })


def cmd_system_test(repo_root: Path, args: list[str]) -> None:
    """Run automated sandbox system tests."""
    iterations = _int_arg(args, "--iterations", default=1)
    keep = "--clean" not in args
    result = run_system_tests(repo_root=repo_root, iterations=iterations, keep=keep)
    _print_json("SHIELD System Test Result", result)
    if result["status"] != "passed":
        sys.exit(1)


def cmd_prompt_sandbox(repo_root: Path) -> None:
    """Run a prompt-driven multi-session sandbox project."""
    result = run_prompt_sandbox(repo_root)
    _print_json("SHIELD Prompt Sandbox Result", result)
    if result["status"] != "passed":
        sys.exit(1)


def _handoff_path_from_done(done_report_path: str | None) -> str | None:
    if not done_report_path:
        return None
    path = Path(done_report_path)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    handoff_path = payload.get("artifacts", {}).get("handoff_path")
    if handoff_path and Path(handoff_path).exists():
        return handoff_path
    return None


def _remove_expected_absent_outputs(repo_root: Path, task: dict[str, object]) -> None:
    metadata = task.get("metadata", {})
    if not isinstance(metadata, dict):
        return
    for rel_path in metadata.get("expected_no_output_files", []):
        path = repo_root / str(rel_path)
        if path.exists() and path.is_file():
            path.unlink()


def _validate_role_gate_mismatch(
    repo_root: Path,
    task: dict[str, object],
    result: dict[str, object],
    handoff_path: str | None,
) -> list[str]:
    failures: list[str] = []
    if not handoff_path:
        failures.append("role_gate_mismatch.yaml: expected a handoff artifact")

    metadata = task.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    for rel_path in metadata.get("expected_no_output_files", []):
        path = repo_root / str(rel_path)
        if path.exists():
            failures.append(f"role_gate_mismatch.yaml: forbidden output was created: {rel_path}")

    execution_results = result.get("execution_results", [])
    if not isinstance(execution_results, list) or not execution_results:
        failures.append("role_gate_mismatch.yaml: missing execution result")
        return failures
    first_result = execution_results[0]
    if not isinstance(first_result, dict):
        failures.append("role_gate_mismatch.yaml: malformed execution result")
        return failures
    step_results = first_result.get("step_results", [])
    if not isinstance(step_results, list) or not step_results:
        failures.append("role_gate_mismatch.yaml: missing step result")
        return failures
    first_step = step_results[0]
    if not isinstance(first_step, dict):
        failures.append("role_gate_mismatch.yaml: malformed step result")
        return failures
    if first_step.get("status") != "blocked":
        failures.append("role_gate_mismatch.yaml: expected blocked step status")
    if first_step.get("commands"):
        failures.append("role_gate_mismatch.yaml: command list should be empty when role gate blocks execution")
    retry_results = result.get("retry_results", [])
    if isinstance(retry_results, list) and retry_results:
        failures.append("role_gate_mismatch.yaml: role gate mismatch should not create retry packets")
    expected_handoff_to = metadata.get("expected_handoff_to")
    if expected_handoff_to and handoff_path and Path(handoff_path).exists():
        handoff_payload = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
        if handoff_payload.get("to_role") != expected_handoff_to:
            failures.append(
                "role_gate_mismatch.yaml: expected handoff to "
                f"{expected_handoff_to}, got {handoff_payload.get('to_role')}"
            )
    return failures


def _validate_security_blocked(
    repo_root: Path,
    task: dict[str, object],
    result: dict[str, object],
    handoff_path: str | None,
) -> list[str]:
    failures: list[str] = []
    metadata = task.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    for rel_path in metadata.get("expected_no_output_files", []):
        path = repo_root / str(rel_path)
        if path.exists():
            failures.append(f"{task.get('id')}: forbidden output was created: {rel_path}")

    execution_results = result.get("execution_results", [])
    if not isinstance(execution_results, list) or not execution_results:
        failures.append(f"{task.get('id')}: missing execution result")
        return failures
    first_result = execution_results[0]
    if not isinstance(first_result, dict):
        failures.append(f"{task.get('id')}: malformed execution result")
        return failures
    step_results = first_result.get("step_results", [])
    if not isinstance(step_results, list) or not step_results:
        failures.append(f"{task.get('id')}: missing step result")
        return failures
    first_step = step_results[0]
    if not isinstance(first_step, dict):
        failures.append(f"{task.get('id')}: malformed step result")
        return failures
    if first_step.get("status") != "blocked":
        failures.append(f"{task.get('id')}: expected blocked step status")
    details = str(first_step.get("details", ""))
    if "Security policy blocked command" not in details:
        failures.append(f"{task.get('id')}: expected security block reason in details")

    retry_results = result.get("retry_results", [])
    if isinstance(retry_results, list) and retry_results:
        failures.append(f"{task.get('id')}: security policy block should not create retry packets")

    expected_handoff_to = metadata.get("expected_handoff_to")
    if expected_handoff_to and handoff_path and Path(handoff_path).exists():
        handoff_payload = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
        if handoff_payload.get("to_role") != expected_handoff_to:
            failures.append(
                f"{task.get('id')}: expected handoff to {expected_handoff_to}, got {handoff_payload.get('to_role')}"
            )
    if expected_handoff_to and not handoff_path:
        failures.append(f"{task.get('id')}: expected a handoff artifact")
    return failures


def _validate_session_report_artifact(path: Path, label: str) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _validate_session_report_payload(payload, label)


def _validate_session_report_payload(payload: dict[str, object], label: str) -> list[str]:
    required_fields = [
        "task_id",
        "title",
        "session_id",
        "role",
        "role_gate",
        "context_check",
        "status",
        "summary",
        "changed_files",
        "verification",
        "blockers",
        "handoff_needed",
        "next_owner_role",
        "next_step",
        "artifacts",
        "report_completeness",
    ]
    failures = [f"{label}: session report missing {field}" for field in required_fields if field not in payload]
    completeness = payload.get("report_completeness", {})
    if not isinstance(completeness, dict):
        completeness = {}
    if completeness.get("complete") is not True:
        failures.append(f"{label}: session report completeness gate failed")
    role_gate = payload.get("role_gate", {})
    if not isinstance(role_gate, dict):
        role_gate = {}
    if "allowed_to_execute" not in role_gate or "decision" not in role_gate:
        failures.append(f"{label}: session report role_gate is incomplete")
    context_check = payload.get("context_check", {})
    if not isinstance(context_check, dict):
        context_check = {}
    if not context_check.get("checked_sources"):
        failures.append(f"{label}: session report context_check is incomplete")
    verification = payload.get("verification", {})
    if not isinstance(verification, dict):
        verification = {}
    if "status" not in verification or "checks" not in verification:
        failures.append(f"{label}: session report verification is incomplete")
    return failures


def _validate_handoff_artifact(path: Path, label: str) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _validate_handoff_payload(payload, label)


def _validate_handoff_payload(payload: dict[str, object], label: str) -> list[str]:
    required_fields = [
        "task_id",
        "from_session",
        "from_role",
        "to_role",
        "handoff_gate",
        "reason",
        "completed",
        "needs_continuation",
        "required_context",
        "related_files",
        "evidence",
        "recommended_next_step",
    ]
    failures = [f"{label}: handoff missing {field}" for field in required_fields if field not in payload]
    handoff_gate = payload.get("handoff_gate", {})
    if not isinstance(handoff_gate, dict):
        handoff_gate = {}
    if not handoff_gate.get("from_role") or not handoff_gate.get("to_role"):
        failures.append(f"{label}: handoff gate is incomplete")
    if not payload.get("reason"):
        failures.append(f"{label}: handoff reason is empty")
    return failures


def _validate_collaboration_templates(repo_root: Path) -> None:
    template_paths = [
        repo_root / "templates" / "leadership_brief.json",
        repo_root / "templates" / "task.yaml",
        repo_root / "templates" / "task_packet.json",
        repo_root / "templates" / "verification_report.json",
        repo_root / "templates" / "session_report.json",
        repo_root / "templates" / "handoff.json",
        repo_root / "templates" / "decision_log.json",
    ]
    for path in template_paths:
        if not path.exists():
            raise FileNotFoundError(f"Missing collaboration template: {path}")
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if path.name == "session_report.json":
                failures = _validate_session_report_payload(payload, path.name)
                if failures:
                    raise RuntimeError("; ".join(failures))
            if path.name == "handoff.json":
                failures = _validate_handoff_payload(payload, path.name)
                if failures:
                    raise RuntimeError("; ".join(failures))
        elif path.suffix in {".yaml", ".yml"}:
            yaml.safe_load(path.read_text(encoding="utf-8"))


def _validate_common_session_protocol(repo_root: Path) -> None:
    """Ensure every session has one shared protocol and template map."""
    protocol_path = repo_root / "OPERATING_RULES.md"
    if not protocol_path.exists():
        raise FileNotFoundError(f"Missing common session protocol: {protocol_path}")

    text = protocol_path.read_text(encoding="utf-8")
    required_terms = [
        "Universal Session Protocol",
        "Boot -> Sync -> Claim -> Work -> Verify -> Report or Handoff -> Dashboard",
        "Role Gate",
        "Report Completeness Gate",
        "If `session_role` does not match `assigned_role`, do not execute the task.",
        "Template map",
        "templates/leadership_brief.json",
        "templates/task.yaml",
        "templates/session_report.json",
        "templates/handoff.json",
        "templates/decision_log.json",
        "templates/verification_report.json",
        "templates/task_packet.json",
    ]
    missing = [term for term in required_terms if term not in text]
    if missing:
        raise RuntimeError("Common session protocol missing required terms: " + ", ".join(missing))


def _validate_role_curriculum(repo_root: Path) -> None:
    """Ensure core role sessions have active personas and first-class skills."""
    core_role_ids = [
        "product-manager-agent",
        "cto-agent",
        "lead-programmer-agent",
        "backend-agent",
        "frontend-agent",
        "fullstack-agent",
        "qa-lead-agent",
        "security-agent",
        "producer-agent",
        "ui-programmer-agent",
        "ux-designer-agent",
    ]
    required_global_skills = [
        "Skills/Global/onboard",
        "Skills/Global/start",
        "Skills/Global/project-stage-detect",
        "Skills/Global/scope-check",
    ]
    manifest_path = repo_root / "manifest.yaml"
    matrix_path = repo_root / "ROLE_SKILL_MATRIX.md"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    if not matrix_path.exists():
        raise FileNotFoundError(f"Missing role skill matrix: {matrix_path}")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    active_ids = set(manifest.get("active_agents", []))
    agents = {agent.get("id"): agent for agent in manifest.get("agents", [])}
    matrix_text = matrix_path.read_text(encoding="utf-8")
    failures: list[str] = []

    for role_id in core_role_ids:
        agent = agents.get(role_id)
        if not agent:
            failures.append(f"{role_id}: missing from manifest agents")
            continue
        if role_id not in active_ids:
            failures.append(f"{role_id}: not active in manifest")
        if role_id not in matrix_text:
            failures.append(f"{role_id}: missing from ROLE_SKILL_MATRIX.md")

        persona = agent.get("persona")
        if not persona or not (repo_root / persona).exists():
            failures.append(f"{role_id}: missing persona {persona}")

        for skill in agent.get("skills", []):
            if skill.startswith(".skills_pool/"):
                continue
            skill_path = repo_root / skill
            if not skill_path.exists() and not (skill_path / "SKILL.md").exists():
                failures.append(f"{role_id}: missing skill {skill}")

    for skill in required_global_skills:
        skill_path = repo_root / skill
        if not skill_path.exists() and not (skill_path / "SKILL.md").exists():
            failures.append(f"global: missing skill {skill}")

    if failures:
        raise RuntimeError("Role curriculum validation failed: " + "; ".join(failures))


def _int_arg(args: list[str], name: str, default: int) -> int:
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        raise ValueError(f"Missing value for {name}")
    return int(args[index + 1])


def _print_json(title: str, payload: dict[str, object]) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print(json.dumps(payload, indent=2, default=str))


def main() -> None:
    repo_root = Path(__file__).parent.resolve()
    args = sys.argv[1:]

    if not args or args[0] == "run":
        task_file = Path(args[1]) if len(args) > 1 else None
        cmd_run(repo_root, task_file)
    elif args[0] == "plan":
        task_file = Path(args[1]) if len(args) > 1 else None
        cmd_plan(repo_root, task_file)
    elif args[0] == "compile":
        include_pool = "--include-pool" in args
        cmd_compile(repo_root, include_pool=include_pool)
    elif args[0] == "audit":
        cmd_audit(repo_root)
    elif args[0] == "dashboard":
        cmd_dashboard(repo_root)
    elif args[0] == "prompt-sandbox":
        cmd_prompt_sandbox(repo_root)
    elif args[0] == "system-test":
        cmd_system_test(repo_root, args[1:])
    else:
        print(f"Unknown command: {args[0]}")
        print("Usage: python run_orchestrator.py [compile|plan [task.yaml]|run [task.yaml]|dashboard|audit|prompt-sandbox|system-test]")
        sys.exit(1)


if __name__ == "__main__":
    main()
