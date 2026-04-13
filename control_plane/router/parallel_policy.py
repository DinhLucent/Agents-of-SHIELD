"""Parallel Policy — Decides solo / paired / directed_swarm execution mode.

Conservative by default. Never opens multi-agent unless risk, complexity,
or release sensitivity demands it.
"""
from __future__ import annotations

import re
from typing import Any


class ParallelPolicy:
    """
    Decide whether a task should run in solo, paired, or directed_swarm mode.
    Keep this conservative by default to avoid context/token waste.
    """

    def decide(
        self,
        task: dict[str, Any],
        classification: dict[str, Any],
        routing: dict[str, Any],
    ) -> dict[str, Any]:
        task_type = classification.get("task_type", "unknown")
        risk_level = classification.get("risk_level", "medium")
        description = (task.get("description") or "").lower()
        constraints = task.get("constraints", [])
        related_paths = task.get("inputs", {}).get("related_paths", [])

        multi_module = len({self._top_level_group(p) for p in related_paths if p}) > 1
        mentions_security = self._mentions_any(
            description, ["security", "auth", "permission", "token"]
        )
        mentions_release = self._mentions_any(
            description, ["release", "deploy", "production", "rollout"]
        )
        many_constraints = len(constraints) >= 4 and risk_level in {"medium", "high"}

        # ── Directed swarm: release or high-risk multi-module ────
        if mentions_release or (risk_level == "high" and multi_module):
            return {
                "mode": "directed_swarm",
                "primary_role": routing["primary_role"],
                "secondary_roles": self._merge_roles(
                    routing.get("secondary_roles", []),
                    ["reviewer", "qa", "security"],
                ),
                "reason": "high-risk multi-module or release-sensitive work",
            }

        # ── Paired: high risk, security, refactor, or many constraints ─
        if (
            risk_level == "high"
            or mentions_security
            or task_type in {"refactor", "incident"}
            or many_constraints
        ):
            return {
                "mode": "paired",
                "primary_role": routing["primary_role"],
                "secondary_roles": self._merge_roles(
                    routing.get("secondary_roles", []),
                    ["reviewer"],
                ),
                "reason": "moderate/high-risk task requiring independent review",
            }

        # ── Solo: default conservative execution ─────────────────
        return {
            "mode": "solo",
            "primary_role": routing["primary_role"],
            "secondary_roles": [],
            "reason": "default conservative execution",
        }

    # ── Helpers ──────────────────────────────────────────────

    def _merge_roles(self, base: list[str], extra: list[str]) -> list[str]:
        seen: list[str] = []
        for role in [*base, *extra]:
            if role not in seen:
                seen.append(role)
        return seen

    def _top_level_group(self, path: str) -> str:
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "control_plane":
            return "/".join(parts[:2])
        if parts:
            return parts[0]
        return path

    def _mentions_any(self, text: str, terms: list[str]) -> bool:
        for term in terms:
            pattern = r"(?<![a-z0-9_-])" + re.escape(term.lower()) + r"(?![a-z0-9_-])"
            if re.search(pattern, text):
                return True
        return False

    # Legacy compat — old code calls evaluate()
    def evaluate(self, classification: dict[str, Any], routing: dict[str, Any]) -> dict[str, Any]:
        """Thin wrapper for backward compatibility."""
        return self.decide(task={}, classification=classification, routing=routing)
