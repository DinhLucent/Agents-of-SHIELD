"""Create persisted runtime execution plans from execution modes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ExecutionPlanner:
    """Translate execution modes into concrete runtime plans."""

    def __init__(self, runtime_dir: Path) -> None:
        self.plan_dir = runtime_dir / "state" / "agent_runs"
        self.plan_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        task: dict[str, Any],
        routing: dict[str, Any],
        execution_mode: dict[str, Any],
    ) -> tuple[dict[str, Any], Path]:
        mode = execution_mode["mode"]
        primary_role = execution_mode["primary_role"]
        secondary_roles = execution_mode.get("secondary_roles", [])

        if mode == "paired":
            steps = [
                {"name": "primary_execute", "role": primary_role, "status": "pending"},
                {
                    "name": "secondary_review",
                    "role": secondary_roles[0] if secondary_roles else "reviewer",
                    "status": "pending",
                },
            ]
            verification_profile = "reviewed"
            next_action = "execute_primary_then_review"
        elif mode == "directed_swarm":
            steps = [{"name": "primary_execute", "role": primary_role, "status": "pending"}]
            for role in secondary_roles:
                steps.append({"name": f"parallel_{role}", "role": role, "status": "pending"})
            verification_profile = "swarm"
            next_action = "dispatch_parallel_agents"
        else:
            steps = [{"name": "primary_execute", "role": primary_role, "status": "pending"}]
            verification_profile = "standard"
            next_action = "execute_primary"

        assigned_roles = [primary_role, *secondary_roles]
        runtime_plan = {
            "task_id": task["id"],
            "mode": mode,
            "routing_mode": routing.get("mode", mode),
            "steps": steps,
            "assigned_roles": assigned_roles,
            "review_required": mode != "solo",
            "verification_profile": verification_profile,
            "next_action": next_action,
            "status": "ready",
        }

        out_path = self.plan_dir / f"{task['id']}.runtime_plan.json"
        out_path.write_text(json.dumps(runtime_plan, indent=2, ensure_ascii=False), encoding="utf-8")
        return runtime_plan, out_path
