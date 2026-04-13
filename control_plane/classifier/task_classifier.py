"""Task Classifier — Classifies tasks by type, domain, and risk level.

Uses rule-based heuristics on task title/description/domain to produce
a classification dict consumed by the router and retriever.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# Keywords that signal specific task types
_TYPE_KEYWORDS: dict[str, list[str]] = {
    "bugfix": ["fix", "bug", "error", "crash", "broken", "regression", "hotfix"],
    "refactor": ["refactor", "cleanup", "restructure", "simplify", "reorganize"],
    "test": [
        "add test", "add tests", "write test", "write tests", "run tests",
        "test coverage", "coverage", "spec", "e2e", "unit test",
        "integration test", "failing test",
    ],
    "documentation": ["document", "docs", "readme", "changelog", "wiki"],
    "security": ["security", "vulnerability", "cve", "pen test", "audit"],
    "feature": ["add", "implement", "create", "build", "new", "feature"],
}

_EXPLICIT_TASK_TYPES = {
    *list(_TYPE_KEYWORDS.keys()),
    "planning",
    "review",
    "verification",
    "architecture",
    "incident",
    "bugfix_review",
    "audit",
    "sprint",
}

# Keywords that raise risk level
_HIGH_RISK_KEYWORDS: list[str] = [
    "payment", "security", "auth", "production", "critical", "token",
    "credential", "database migration", "breaking change", "deploy",
]

# Keywords that map to domains
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "auth": ["auth", "login", "logout", "token", "session", "permission", "rbac"],
    "api": ["api", "endpoint", "rest", "graphql", "route"],
    "database": ["database", "migration", "schema", "model", "orm", "query"],
    "frontend": ["ui", "component", "page", "css", "layout", "react", "vue"],
    "infra": ["deploy", "docker", "ci", "cd", "pipeline", "k8s", "terraform"],
}


class TaskClassifier:
    """Classify a task dict into type, domain, and risk metadata."""

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir

    def classify(self, task: dict[str, Any]) -> dict[str, Any]:
        title = (task.get("title") or "").lower()
        description = (task.get("description") or "").lower()
        text = f"{title}\n{description}"

        task_type = self._detect_type(task, text)
        domain = self._detect_domain(text, task.get("domain", "general"))
        risk_level = self._detect_risk(text, task_type)

        return {
            "task_type": task_type,
            "domain": domain,
            "risk_level": risk_level,
            "requires_parallel_review": risk_level == "high",
            "likely_roles": self._likely_roles(task_type, domain),
            "required_tools": self._required_tools(task_type),
            "likely_artifacts": self._likely_artifacts(task_type),
        }

    # ── Private helpers ──────────────────────────────────────

    def _detect_type(self, task: dict[str, Any], text: str) -> str:
        explicit = (
            task.get("task_type")
            or task.get("type")
            or task.get("metadata", {}).get("task_type")
        )
        if isinstance(explicit, str):
            normalized = explicit.strip().lower().replace("-", "_").replace(" ", "_")
            if normalized in _EXPLICIT_TASK_TYPES:
                return normalized

        for task_type, keywords in _TYPE_KEYWORDS.items():
            if any(self._contains_keyword(text, kw) for kw in keywords):
                return task_type
        return "feature"

    def _detect_domain(self, text: str, explicit: str) -> str:
        if explicit != "general":
            return explicit
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            if any(self._contains_keyword(text, kw) for kw in keywords):
                return domain
        return "general"

    def _detect_risk(self, text: str, task_type: str) -> str:
        if task_type in {"security", "incident"}:
            return "high"
        if any(self._contains_keyword(text, kw) for kw in _HIGH_RISK_KEYWORDS):
            return "high"
        if task_type in {
            "refactor",
            "feature",
            "planning",
            "review",
            "verification",
            "architecture",
            "audit",
            "bugfix_review",
            "sprint",
        }:
            return "medium"
        return "low"

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        """Match keywords as terms/phrases, not arbitrary substrings."""
        pattern = r"(?<![a-z0-9_-])" + re.escape(keyword.lower()) + r"(?![a-z0-9_-])"
        return re.search(pattern, text) is not None

    def _likely_roles(self, task_type: str, domain: str) -> list[str]:
        roles: list[str] = []
        if task_type in ("bugfix", "feature", "refactor"):
            roles.append("backend" if domain != "frontend" else "frontend")
        elif task_type == "test":
            roles.append("qa")
        elif task_type == "documentation":
            roles.append("docs")
        elif task_type == "security":
            roles.extend(["security", "backend"])
        elif task_type in {"verification", "bugfix_review"}:
            roles.append("qa")
        elif task_type == "review":
            roles.append("reviewer")
        elif task_type in {"planning", "architecture", "sprint"}:
            roles.extend(["product", "cto"])
        elif task_type == "audit":
            roles.extend(["security", "reviewer"])
        return roles or ["backend"]

    def _required_tools(self, task_type: str) -> list[str]:
        base = ["knowledge_retriever"]
        if task_type in ("bugfix", "feature", "refactor"):
            base.extend(["code_retriever", "test_runner", "lint_runner"])
        elif task_type == "test":
            base.append("test_runner")
        elif task_type == "security":
            base.extend(["security_checker", "code_retriever"])
        elif task_type in {"planning", "architecture"}:
            base.extend(["code_retriever"])
        elif task_type in {"review", "verification", "bugfix_review", "audit"}:
            base.extend(["code_retriever", "test_runner"])
        return base

    def _likely_artifacts(self, task_type: str) -> list[str]:
        return ["task_packet", "verification_report"]
