"""CLI entrypoint for the Agents-of-SHIELD v2 control plane.

Usage:
    python run_orchestrator.py compile           # Compile all knowledge indexes
    python run_orchestrator.py plan <task.yaml>  # Build packet + runtime plan only
    python run_orchestrator.py run <task.yaml>   # Execute a task end-to-end
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from control_plane.orchestrator import Orchestrator, OrchestratorConfig
from control_plane.compiler.build_indexes import build_all


def _make_config(repo_root: Path) -> OrchestratorConfig:
    return OrchestratorConfig(
        repo_root=repo_root,
        runtime_dir=repo_root / "runtime",
        knowledge_dir=repo_root / "knowledge",
        hub_dir=repo_root / ".hub",
    )


def cmd_compile(repo_root: Path) -> None:
    """Compile all knowledge source → indexes."""
    build_all(repo_root)


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

    import json
    print("\n" + "=" * 60)
    print("  Orchestrator Result")
    print("=" * 60)
    print(json.dumps(result, indent=2, default=str))

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

    import json
    print("\n" + "=" * 60)
    print("  Orchestrator Result")
    print("=" * 60)
    print(json.dumps(result, indent=2, default=str))


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
        cmd_compile(repo_root)
    else:
        print(f"Unknown command: {args[0]}")
        print("Usage: python run_orchestrator.py [compile|plan [task.yaml]|run [task.yaml]]")
        sys.exit(1)


if __name__ == "__main__":
    main()
