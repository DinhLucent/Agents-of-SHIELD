"""Retrieve compiled fragments, module hints, and lightweight task context."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeRetriever:
    """Retrieve context fragments, files, tests, and handoffs for a task."""

    def __init__(self, repo_root: Path, knowledge_dir: Path, hub_dir: Path) -> None:
        self.repo_root = repo_root
        self.knowledge_dir = knowledge_dir
        self.hub_dir = hub_dir
        self.fragments_dir = knowledge_dir / "compiled" / "context_fragments"
        self.module_index_path = knowledge_dir / "compiled" / "module_index.json"
        self.module_index = self._load_module_index()

    def retrieve(
        self,
        task: dict[str, Any],
        classification: dict[str, Any],
        routing: dict[str, Any],
    ) -> dict[str, Any]:
        domain = classification["domain"]
        inputs = task.get("inputs", {})
        explicit_files = self._merge_unique([], inputs.get("related_paths", []))
        explicit_tests = self._merge_unique([], inputs.get("related_tests", []))
        handoff_refs = self._merge_unique([], inputs.get("related_handoffs", []))
        modules = self._infer_modules(task, classification, explicit_files)
        small_task = self._is_small_task(task, explicit_files, modules)

        if not handoff_refs and self._should_autoload_handoffs(
            small_task=small_task,
            explicit_files=explicit_files,
            explicit_tests=explicit_tests,
            modules=modules,
        ):
            handoff_refs = self._find_recent_handoffs(limit=2)

        files = explicit_files if explicit_files else self._paths_for_modules(modules, include_entrypoints=True)
        tests = explicit_tests if explicit_tests or small_task else self._tests_for_modules(modules)
        fragments = self._select_fragments(domain, modules)
        dashboard_snapshot = self._read_dashboard_snapshot()

        return {
            "domain": domain,
            "modules": modules,
            "files": files,
            "tests": tests,
            "handoffs": handoff_refs,
            "fragments": fragments,
            "dashboard_snapshot": dashboard_snapshot,
            "role": routing["primary_role"],
        }

    def _load_module_index(self) -> dict[str, Any]:
        if not self.module_index_path.exists():
            return {}
        return json.loads(self.module_index_path.read_text(encoding="utf-8"))

    def _select_fragments(self, domain: str, modules: list[str]) -> list[dict[str, str]]:
        """Select the smallest useful fragment set."""
        results = self._core_fragments()

        domain_fragment = self.fragments_dir / f"{domain}.summary.json"
        if domain != "general" and domain_fragment.exists():
            results.append({
                "id": domain_fragment.stem,
                "type": "module_summary",
                "path": str(domain_fragment.relative_to(self.repo_root)),
            })

        for module in self._most_specific_modules(modules):
            summary_path = self.module_index.get(module, {}).get("summary_fragment")
            if not summary_path:
                continue
            fragment_id = Path(summary_path).stem
            if any(existing["id"] == fragment_id for existing in results):
                continue
            results.append({
                "id": fragment_id,
                "type": "module_summary",
                "path": summary_path,
            })

        return results

    def _core_fragments(self) -> list[dict[str, str]]:
        fragments: list[dict[str, str]] = []
        for file_name in ("operating_rules.summary.json", "soul.summary.json"):
            path = self.fragments_dir / file_name
            if path.exists():
                fragments.append({
                    "id": path.stem,
                    "type": "module_summary",
                    "path": str(path.relative_to(self.repo_root)),
                })
        return fragments

    def _find_recent_handoffs(self, limit: int = 2) -> list[str]:
        """Find recent handoff files in .hub/handoffs/."""
        handoffs_dir = self.hub_dir / "handoffs"
        if not handoffs_dir.exists():
            return []
        files = [*handoffs_dir.glob("*.json"), *handoffs_dir.glob("*.md")]
        recent = sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)
        return [str(path.relative_to(self.repo_root)) for path in recent[:limit]]

    def _read_dashboard_snapshot(self) -> dict[str, Any] | None:
        """Read the canonical dashboard snapshot if available."""
        summary_dir = self.repo_root / "runtime" / "cache" / "summaries"
        for file_name in ("dashboard_snapshot.json", "current_dashboard.json"):
            snapshot_path = summary_dir / file_name
            if snapshot_path.exists():
                return json.loads(snapshot_path.read_text(encoding="utf-8"))
        return None

    def _infer_modules(
        self,
        task: dict[str, Any],
        classification: dict[str, Any],
        related_paths: list[str],
    ) -> list[str]:
        inferred: list[str] = []
        explicit_modules = task.get("inputs", {}).get("related_modules", [])
        inferred.extend(explicit_modules)

        for path in related_paths:
            normalized = path.replace("\\", "/")
            for module_name, metadata in self.module_index.items():
                module_paths = metadata.get("paths", [])
                if any(normalized.startswith(module_path.replace("\\", "/")) for module_path in module_paths):
                    inferred.append(module_name)

        domain = classification.get("domain")
        if domain in self.module_index:
            inferred.append(domain)

        return self._most_specific_modules(self._merge_unique([], inferred))

    def _paths_for_modules(self, modules: list[str], include_entrypoints: bool) -> list[str]:
        paths: list[str] = []
        for module in modules:
            metadata = self.module_index.get(module, {})
            paths.extend(metadata.get("paths", []))
            if include_entrypoints:
                paths.extend(metadata.get("entrypoints", []))
        return self._merge_unique([], paths)

    def _tests_for_modules(self, modules: list[str]) -> list[str]:
        tests: list[str] = []
        for module in modules:
            tests.extend(self.module_index.get(module, {}).get("related_tests", []))
        return self._merge_unique([], tests)

    def _is_small_task(self, task: dict[str, Any], explicit_files: list[str], modules: list[str]) -> bool:
        description = (task.get("description") or "").lower()
        high_risk_words = ("release", "deploy", "rollout", "migration", "multi-module")
        if any(word in description for word in high_risk_words):
            return False
        return len(explicit_files) <= 2 and len(modules) <= 1

    def _should_autoload_handoffs(
        self,
        small_task: bool,
        explicit_files: list[str],
        explicit_tests: list[str],
        modules: list[str],
    ) -> bool:
        """Only backfill handoffs when the task is not already self-contained."""
        if small_task and (explicit_files or explicit_tests or modules):
            return False
        return True

    def _most_specific_modules(self, modules: list[str]) -> list[str]:
        ordered = sorted(self._merge_unique([], modules), key=lambda module: module.count("/"), reverse=True)
        chosen: list[str] = []
        for module in ordered:
            if any(existing == module or existing.startswith(f"{module}/") for existing in chosen):
                continue
            chosen.append(module)
        return chosen

    def _merge_unique(self, base: list[str], extra: list[str]) -> list[str]:
        merged: list[str] = []
        for item in [*base, *extra]:
            if item and item not in merged:
                merged.append(item)
        return merged
