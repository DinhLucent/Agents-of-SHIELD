"""Run lint checks and return stable structured results."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


class LintRunner:
    """Run lint checks and return structured results."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, files: list[str] | None = None) -> dict[str, Any]:
        cmd = self._detect_lint_command(files)
        if not cmd:
            return {"name": "lint", "result": "skipped", "details": "No linter detected"}

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "name": "lint",
                "result": "passed" if proc.returncode == 0 else "failed",
                "details": proc.stdout[-800:] if proc.stdout else proc.stderr[-800:],
                "command": cmd,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return {"name": "lint", "result": "skipped", "details": str(exc)}

    def _detect_lint_command(self, files: list[str] | None) -> list[str] | None:
        targets = files or ["."]
        if any((self.repo_root / config).exists() for config in ("ruff.toml", "pyproject.toml", ".flake8")):
            return ["python", "-m", "ruff", "check", *targets]
        if (self.repo_root / ".eslintrc.json").exists() or (self.repo_root / ".eslintrc.js").exists():
            return ["npx", "eslint", *targets]
        return None
