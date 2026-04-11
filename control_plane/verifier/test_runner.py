"""Run project tests and report stable structured results."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


class TestRunner:
    """Run tests and produce a structured verification result."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, test_paths: list[str] | None = None) -> dict[str, Any]:
        cmd = self._detect_test_command(test_paths)
        if not cmd:
            return {"name": "tests", "result": "skipped", "details": "No test command detected"}

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = proc.stdout or proc.stderr
            return {
                "name": "tests",
                "result": "passed" if proc.returncode == 0 else "failed",
                "details": output[-1200:],
                "returncode": proc.returncode,
                "failed_test": self._extract_failed_test(output),
                "command": cmd,
            }
        except subprocess.TimeoutExpired:
            return {"name": "tests", "result": "timeout", "details": "Test execution timed out (120s)"}
        except FileNotFoundError:
            return {"name": "tests", "result": "skipped", "details": f"Command not found: {cmd[0]}"}

    def _detect_test_command(self, test_paths: list[str] | None) -> list[str] | None:
        if (self.repo_root / "pytest.ini").exists() or (self.repo_root / "pyproject.toml").exists():
            cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
            if test_paths:
                cmd.extend(test_paths)
            return cmd
        if (self.repo_root / "package.json").exists():
            return ["npm", "test", "--", "--passWithNoTests"]
        return None

    def _extract_failed_test(self, output: str) -> str:
        pytest_match = re.search(r"([^\s]+::[^\s]+)\s+FAILED", output)
        if pytest_match:
            return pytest_match.group(1)
        return ""
