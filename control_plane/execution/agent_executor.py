"""Execute task packets through a local command-driven agent loop."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AgentExecutor:
    """Run task commands locally and persist execution artifacts."""

    def __init__(self, repo_root: Path, runtime_dir: Path) -> None:
        self.repo_root = repo_root
        self.run_dir = runtime_dir / "state" / "agent_runs"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_path = runtime_dir / "reports" / "command_audit.jsonl"
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        task: dict[str, Any],
        packet: dict[str, Any],
        runtime_plan: dict[str, Any],
        attempt: int = 1,
    ) -> dict[str, Any]:
        """Execute the runtime plan and return a structured execution result."""
        role_gate = packet.get("role_gate", {})
        if role_gate.get("allowed_to_execute") is False:
            return self._role_gate_blocked_result(task, packet, runtime_plan, attempt, role_gate)

        execution_config = self._execution_config(task, attempt)
        candidate_paths = self._candidate_paths(packet, execution_config)
        baseline_snapshot = self._snapshot_paths(candidate_paths)

        step_results: list[dict[str, Any]] = []

        primary_result = self._run_primary_step(
            task=task,
            packet=packet,
            execution_config=execution_config,
            attempt=attempt,
        )
        step_results.append(primary_result)

        changed_files = self._detect_changed_files(
            candidate_paths=candidate_paths,
            baseline_snapshot=baseline_snapshot,
            execution_config=execution_config,
        )

        if primary_result["result"] == "passed":
            for step in runtime_plan.get("steps", [])[1:]:
                follow_up = self._run_follow_up_step(
                    step=step,
                    packet=packet,
                    execution_config=execution_config,
                    attempt=attempt,
                    changed_files=changed_files,
                )
                step_results.append(follow_up)

        else:
            for step in runtime_plan.get("steps", [])[1:]:
                step_results.append({
                    "name": step["name"],
                    "role": step["role"],
                    "result": "skipped",
                    "status": "skipped",
                    "details": "Skipped because primary execution failed",
                    "commands": [],
                })

        failed_step = next((step for step in step_results if step["result"] == "failed"), None)
        status = "failed" if failed_step else "passed"
        stack_trace = primary_result.get("stderr_tail") if primary_result["result"] == "failed" else ""
        satisfied_criteria = self._satisfied_criteria(task, execution_config, status == "passed")
        execution_result = {
            "task_id": task["id"],
            "attempt": attempt,
            "status": status,
            "mode": runtime_plan.get("mode", packet.get("mode", "solo")),
            "step_results": step_results,
            "changed_files": changed_files,
            "output_files": execution_config.get("output_files", []),
            "satisfied_criteria": satisfied_criteria,
            "test_paths": packet.get("tests", []),
            "run_tests": bool(packet.get("tests")),
            "stack_trace": stack_trace,
            "details": failed_step.get("details", "") if failed_step else "Execution completed successfully",
        }
        execution_result["execution_report_path"] = str(
            self._write_execution_report(task["id"], attempt, execution_result)
        )
        return execution_result

    def _role_gate_blocked_result(
        self,
        task: dict[str, Any],
        packet: dict[str, Any],
        runtime_plan: dict[str, Any],
        attempt: int,
        role_gate: dict[str, Any],
    ) -> dict[str, Any]:
        details = (
            "Role gate blocked execution: "
            f"packet_role={role_gate.get('packet_role')} "
            f"task_assigned_role={role_gate.get('task_assigned_role')}"
        )
        step_result = {
            "name": "primary_execute",
            "role": packet.get("role", task.get("assigned_role", "unknown")),
            "result": "failed",
            "status": "blocked",
            "details": details,
            "commands": [],
            "stdout_tail": "",
            "stderr_tail": details,
        }
        execution_result = {
            "task_id": task["id"],
            "attempt": attempt,
            "status": "failed",
            "mode": runtime_plan.get("mode", packet.get("mode", "solo")),
            "step_results": [step_result],
            "changed_files": [],
            "output_files": [],
            "satisfied_criteria": [],
            "test_paths": packet.get("tests", []),
            "run_tests": False,
            "stack_trace": "",
            "details": details,
        }
        execution_result["execution_report_path"] = str(
            self._write_execution_report(task["id"], attempt, execution_result)
        )
        return execution_result

    def _run_primary_step(
        self,
        task: dict[str, Any],
        packet: dict[str, Any],
        execution_config: dict[str, Any],
        attempt: int,
    ) -> dict[str, Any]:
        commands = execution_config.get("primary_commands", [])
        if not commands:
            return {
                "name": "primary_execute",
                "role": packet.get("role", task.get("assigned_role", "backend")),
                "result": "failed",
                "status": "failed",
                "details": "No execution commands configured for primary_execute",
                "commands": [],
                "stdout_tail": "",
                "stderr_tail": "",
            }
        return self._run_command_step(
            step_name="primary_execute",
            role=packet.get("role", task.get("assigned_role", "backend")),
            commands=commands,
            execution_config=execution_config,
            cwd=execution_config.get("cwd"),
            env=execution_config.get("env", {}),
            task_id=task["id"],
            attempt=attempt,
            packet_path=packet.get("task_packet_path", ""),
        )

    def _run_follow_up_step(
        self,
        step: dict[str, Any],
        packet: dict[str, Any],
        execution_config: dict[str, Any],
        attempt: int,
        changed_files: list[str],
    ) -> dict[str, Any]:
        step_name = step["name"]
        commands = self._commands_for_step(step_name, execution_config)
        if commands:
            return self._run_command_step(
                step_name=step_name,
                role=step["role"],
                commands=commands,
                execution_config=execution_config,
                cwd=execution_config.get("cwd"),
                env=execution_config.get("env", {}),
                task_id=packet["task_id"],
                attempt=attempt,
                packet_path="",
            )
        return self._default_review_step(
            step_name=step_name,
            role=step["role"],
            changed_files=changed_files,
            packet=packet,
        )

    def _run_command_step(
        self,
        step_name: str,
        role: str,
        commands: list[str],
        execution_config: dict[str, Any],
        cwd: str | None,
        env: dict[str, str],
        task_id: str,
        attempt: int,
        packet_path: str,
    ) -> dict[str, Any]:
        command_results: list[dict[str, Any]] = []
        step_status = "passed"
        combined_details: list[str] = []
        stdout_tail = ""
        stderr_tail = ""
        resolved_cwd = self._resolve_cwd(cwd)
        timeout_seconds = self._timeout_for_step(step_name, attempt, execution_config)

        blocked, reason = self._blocked_by_workspace(resolved_cwd)
        if blocked:
            details = f"Security policy blocked command: {reason}"
            self._record_command_audit(
                task_id=task_id,
                attempt=attempt,
                step_name=step_name,
                command="; ".join(commands),
                cwd=resolved_cwd,
                status="blocked",
                reason=reason,
            )
            return {
                "name": step_name,
                "role": role,
                "result": "failed",
                "status": "blocked",
                "details": details,
                "commands": [{
                    "command": "; ".join(commands),
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": details,
                    "duration_seconds": 0.0,
                    "blocked": True,
                    "block_reason": reason,
                }],
                "stdout_tail": "",
                "stderr_tail": details,
            }

        for command in commands:
            blocked, reason = self._blocked_command(command, resolved_cwd)
            if blocked:
                details = f"Security policy blocked command: {reason}"
                self._record_command_audit(
                    task_id=task_id,
                    attempt=attempt,
                    step_name=step_name,
                    command=command,
                    cwd=resolved_cwd,
                    status="blocked",
                    reason=reason,
                )
                command_results.append({
                    "command": command,
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": details,
                    "duration_seconds": 0.0,
                    "blocked": True,
                    "block_reason": reason,
                })
                step_status = "blocked"
                stderr_tail = details
                combined_details.append(details)
                break
            started_at = time.time()
            proc = subprocess.run(
                self._shell_command(command),
                cwd=str(resolved_cwd),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=self._command_env(env, task_id, attempt, packet_path),
            )
            stdout_tail = (proc.stdout or "")[-1200:]
            stderr_tail = (proc.stderr or "")[-1200:]
            command_results.append({
                "command": command,
                "returncode": proc.returncode,
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
                "duration_seconds": round(time.time() - started_at, 3),
            })
            self._record_command_audit(
                task_id=task_id,
                attempt=attempt,
                step_name=step_name,
                command=command,
                cwd=resolved_cwd,
                status="completed" if proc.returncode == 0 else "failed",
                reason=stderr_tail if proc.returncode != 0 else "",
            )
            if stdout_tail:
                combined_details.append(stdout_tail)
            if stderr_tail:
                combined_details.append(stderr_tail)
            if proc.returncode != 0:
                step_status = "failed"
                break

        return {
            "name": step_name,
            "role": role,
            "result": "failed" if step_status in {"failed", "blocked"} else "passed",
            "status": "blocked" if step_status == "blocked" else ("completed" if step_status == "passed" else "failed"),
            "details": "\n".join(detail for detail in combined_details if detail).strip(),
            "commands": command_results,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
        }

    def _default_review_step(
        self,
        step_name: str,
        role: str,
        changed_files: list[str],
        packet: dict[str, Any],
    ) -> dict[str, Any]:
        expected_patch = "patch" in packet.get("expected_outputs", [])
        review_notes: list[str] = []
        result = "passed"

        if expected_patch and not changed_files:
            result = "failed"
            review_notes.append("No changed files recorded for a patch-producing task")
        else:
            review_notes.append(
                f"Reviewed {len(changed_files)} changed file(s) for role {role}"
            )
            if packet.get("tests"):
                review_notes.append(
                    f"Related tests queued: {len(packet.get('tests', []))}"
                )

        return {
            "name": step_name,
            "role": role,
            "result": result,
            "status": "completed" if result == "passed" else "failed",
            "details": " | ".join(review_notes),
            "commands": [],
        }

    def _execution_config(self, task: dict[str, Any], attempt: int) -> dict[str, Any]:
        metadata = task.get("metadata", {})
        execution = metadata.get("execution", {})
        primary_commands = execution.get("primary_commands") or execution.get("commands") or []
        if attempt > 1 and execution.get("retry_commands"):
            primary_commands = execution.get("retry_commands", [])

        output_files = execution.get("output_files", [])
        if attempt > 1 and execution.get("retry_output_files"):
            output_files = execution.get("retry_output_files", [])

        satisfied_criteria = execution.get("satisfied_criteria", [])
        if attempt > 1 and execution.get("retry_satisfied_criteria"):
            satisfied_criteria = execution.get("retry_satisfied_criteria", [])

        changed_files = execution.get("changed_files", [])
        if attempt > 1 and execution.get("retry_changed_files"):
            changed_files = execution.get("retry_changed_files", [])

        return {
            "primary_commands": self._string_list(primary_commands),
            "review_commands": self._string_list(execution.get("review_commands", [])),
            "parallel_commands": self._string_list(execution.get("parallel_commands", [])),
            "cwd": execution.get("cwd"),
            "env": {
                str(key): str(value) for key, value in execution.get("env", {}).items()
            },
            "output_files": self._normalize_paths(output_files),
            "changed_files": self._normalize_paths(changed_files),
            "satisfied_criteria": self._string_list(satisfied_criteria),
            "timeout_seconds": int(execution.get("timeout_seconds", 180)),
            "retry_timeout_seconds": int(execution.get("retry_timeout_seconds", 60)),
            "review_timeout_seconds": int(execution.get("review_timeout_seconds", 60)),
            "parallel_timeout_seconds": int(execution.get("parallel_timeout_seconds", 90)),
        }

    def _commands_for_step(self, step_name: str, execution_config: dict[str, Any]) -> list[str]:
        if step_name == "secondary_review":
            return execution_config.get("review_commands", [])
        if step_name.startswith("parallel_"):
            return execution_config.get("parallel_commands", [])
        return []

    def _candidate_paths(
        self,
        packet: dict[str, Any],
        execution_config: dict[str, Any],
    ) -> list[str]:
        paths = list(packet.get("files", []))
        paths.extend(execution_config.get("output_files", []))
        paths.extend(execution_config.get("changed_files", []))
        return self._normalize_paths(paths)

    def _snapshot_paths(self, paths: list[str]) -> dict[str, str | None]:
        snapshot: dict[str, str | None] = {}
        for path in paths:
            full_path = self.repo_root / path
            if full_path.exists() and full_path.is_file():
                snapshot[path] = self._hash_file(full_path)
            else:
                snapshot[path] = None
        return snapshot

    def _detect_changed_files(
        self,
        candidate_paths: list[str],
        baseline_snapshot: dict[str, str | None],
        execution_config: dict[str, Any],
    ) -> list[str]:
        changed: list[str] = []
        for path in candidate_paths:
            full_path = self.repo_root / path
            before = baseline_snapshot.get(path)
            after = self._hash_file(full_path) if full_path.exists() and full_path.is_file() else None
            if before != after:
                changed.append(path)

        for path in execution_config.get("changed_files", []):
            if path not in changed:
                changed.append(path)
        for path in execution_config.get("output_files", []):
            full_path = self.repo_root / path
            if full_path.exists() and path not in changed:
                changed.append(path)
        return changed

    def _satisfied_criteria(
        self,
        task: dict[str, Any],
        execution_config: dict[str, Any],
        success: bool,
    ) -> list[str]:
        if not success:
            return []
        explicit = execution_config.get("satisfied_criteria", [])
        if explicit:
            return explicit
        return list(task.get("acceptance_criteria", []))

    def _write_execution_report(
        self,
        task_id: str,
        attempt: int,
        result: dict[str, Any],
    ) -> Path:
        out_path = self.run_dir / f"{task_id}.attempt-{attempt}.execution.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path

    def _resolve_cwd(self, cwd: str | None) -> Path:
        if not cwd:
            return self.repo_root
        candidate = Path(cwd)
        if candidate.is_absolute():
            return candidate
        return (self.repo_root / candidate).resolve()

    def _timeout_for_step(
        self,
        step_name: str,
        attempt: int,
        execution_config: dict[str, Any],
    ) -> int:
        if attempt > 1:
            return int(execution_config.get("retry_timeout_seconds", 60))
        if step_name == "secondary_review":
            return int(execution_config.get("review_timeout_seconds", 60))
        if step_name.startswith("parallel_"):
            return int(execution_config.get("parallel_timeout_seconds", 90))
        return int(execution_config.get("timeout_seconds", 180))

    def _command_env(
        self,
        extra_env: dict[str, str],
        task_id: str,
        attempt: int,
        packet_path: str,
    ) -> dict[str, str]:
        env = dict(os.environ)
        env.update(extra_env)
        env["AGENT_TASK_ID"] = task_id
        env["AGENT_TASK_ATTEMPT"] = str(attempt)
        if packet_path:
            env["AGENT_TASK_PACKET_PATH"] = packet_path
        env.setdefault("AGENT_TIMEOUT_SECONDS", "180")
        env.setdefault("AGENT_RETRY_TIMEOUT_SECONDS", "60")
        env.setdefault("AGENT_REVIEW_TIMEOUT_SECONDS", "60")
        env.setdefault("AGENT_PARALLEL_TIMEOUT_SECONDS", "90")
        return env

    def _shell_command(self, command: str) -> list[str]:
        if os.name == "nt":
            return ["powershell", "-NoProfile", "-Command", command]
        return ["bash", "-lc", command]

    def _hash_file(self, path: Path) -> str:
        return hashlib.sha1(path.read_bytes()).hexdigest()

    def _normalize_paths(self, paths: list[str]) -> list[str]:
        normalized: list[str] = []
        for path in paths:
            candidate = str(path).replace("\\", "/")
            if candidate and candidate not in normalized:
                normalized.append(candidate)
        return normalized

    def _string_list(self, values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        return [str(value) for value in values if str(value).strip()]

    def _blocked_by_workspace(self, cwd: Path) -> tuple[bool, str]:
        try:
            cwd.resolve().relative_to(self.repo_root.resolve())
        except ValueError:
            return True, f"Workspace boundary blocked command: cwd {cwd} is outside repo_root"
        return False, ""

    def _blocked_command(self, command: str, cwd: Path) -> tuple[bool, str]:
        blocked, reason = self._blocked_by_workspace(cwd)
        if blocked:
            return True, reason

        lowered = command.strip()
        destructive_reason = self._blocked_destructive_path(lowered)
        if destructive_reason:
            return True, destructive_reason

        danger_patterns = [
            (r"(?i)\brm\s+-rf\s+/", "Dangerous recursive delete"),
            (r"(?i)\brm\s+-rf\s+\*", "Dangerous recursive delete"),
            (r"(?i)\bdel\s+/s\s+/q\s+[a-z]:\\", "Dangerous recursive delete"),
            (r"(?i)\bremove-item\s+-recurse\s+-force\s+[a-z]:\\", "Dangerous recursive delete"),
            (r"(?i)\bformat(-volume)?\b", "Disk formatting command"),
            (r"(?i)\bdiskpart\b", "Disk partitioning command"),
            (r"(?i)\bmkfs\b", "Filesystem formatting command"),
            (r"(?i)\bdd\s+if=", "Raw disk write command"),
            (r"(?i)\bshutdown\b", "System shutdown command"),
            (r"(?i)\breboot\b", "System reboot command"),
            (r"(?i)\binvoke-expression\b|\biex\b", "Dangerous shell evaluation"),
            (r"(?i)\b(curl|wget)\b.+\|\s*(bash|sh|pwsh|powershell)\b", "Remote shell pipe"),
            (r"(?i)\bgit\s+reset\s+--hard\b", "Destructive git reset"),
            (r"(?i)\bgit\s+clean\s+-f", "Destructive git clean"),
        ]
        for pattern, reason in danger_patterns:
            if re.search(pattern, lowered):
                return True, reason

        escape_patterns = [
            r"(?i)\bcd\s+\.\.",
            r"(?i)\bset-location\s+\.\.",
            r"(?i)\bpushd\s+\.\.",
            r"(?i)\bcd\s+\/",
        ]
        for pattern in escape_patterns:
            if re.search(pattern, lowered):
                return True, "Workspace boundary blocked command: directory traversal"

        abs_cd = re.search(r"(?i)\b(cd|set-location|pushd)\s+['\"]?([a-z]:\\[^'\"\s]+)", lowered)
        if abs_cd:
            target = Path(abs_cd.group(2))
            try:
                target.resolve().relative_to(self.repo_root.resolve())
            except ValueError:
                return True, f"Workspace boundary blocked command: cd to {target}"
        return False, ""

    def _blocked_destructive_path(self, command: str) -> str:
        if not re.search(r"(?i)\b(rm|del|erase|remove-item|rmdir|rd)\b", command):
            return ""

        if re.search(r"(?i)(\.\.[/\\])", command):
            return "Destructive command targets parent traversal"

        for match in re.finditer(r"(?i)([a-z]:\\[^'\"\s]+)", command):
            reason = self._block_if_outside_repo(match.group(1))
            if reason:
                return reason

        for match in re.finditer(r"(?i)(/[^'\"\s]+)", command):
            reason = self._block_if_outside_repo(match.group(1))
            if reason:
                return reason

        return ""

    def _block_if_outside_repo(self, raw_path: str) -> str:
        try:
            candidate = Path(raw_path).resolve()
        except (OSError, RuntimeError):
            return "Destructive command targets invalid path"
        try:
            candidate.relative_to(self.repo_root.resolve())
        except ValueError:
            return f"Destructive command targets path outside repo_root: {candidate}"
        return ""

    def _record_command_audit(
        self,
        task_id: str,
        attempt: int,
        step_name: str,
        command: str,
        cwd: Path,
        status: str,
        reason: str,
    ) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "attempt": attempt,
            "step_name": step_name,
            "command": command,
            "cwd": str(cwd),
            "status": status,
            "reason": reason,
        }
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
