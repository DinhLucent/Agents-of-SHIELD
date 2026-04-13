"""Build indexes and cached summaries for the control plane."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from control_plane.compiler.compile_docs import compile_docs
from control_plane.compiler.compile_roles import compile_roles
from control_plane.compiler.compile_skills import compile_skills
from control_plane.compiler.dashboard_snapshot import build_dashboard_snapshot
from control_plane.compiler.local_indexes import build_local_indexes
from control_plane.contracts import DEFAULT_CONTRACT_VALIDATOR


DEFAULT_SOURCE_DIRS = ("src", "app", "services", "packages", "lib", "control_plane")
DEFAULT_TEST_DIRS = ("tests", "test")


def build_module_index(repo_root: Path) -> Path:
    """Scan source/test directories to produce module_index.json."""
    compiled_dir = repo_root / "knowledge" / "compiled"
    fragments_dir = compiled_dir / "context_fragments"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    fragments_dir.mkdir(parents=True, exist_ok=True)

    modules: dict[str, Any] = {}
    source_roots = [repo_root / d for d in DEFAULT_SOURCE_DIRS if (repo_root / d).exists()]
    test_roots = [repo_root / d for d in DEFAULT_TEST_DIRS if (repo_root / d).exists()]

    for source_root in source_roots:
        root_module_name = source_root.name
        root_entrypoints = _find_entrypoints(repo_root, source_root)
        root_related_tests = _find_related_tests(repo_root, root_module_name, test_roots)
        if root_entrypoints:
            modules[root_module_name] = _build_module_record(
                repo_root=repo_root,
                fragments_dir=fragments_dir,
                module_name=root_module_name,
                module_paths=[str(source_root.relative_to(repo_root))],
                related_tests=root_related_tests,
                entrypoints=root_entrypoints,
            )

        for child in source_root.iterdir():
            if not child.is_dir() or child.name.startswith("__"):
                continue

            module_name = (
                child.name if source_root.name != "control_plane" else f"control_plane/{child.name}"
            )
            module_paths = [str(child.relative_to(repo_root))]
            related_tests = _find_related_tests(repo_root, module_name, test_roots)
            entrypoints = _find_entrypoints(repo_root, child)
            modules[module_name] = _build_module_record(
                repo_root=repo_root,
                fragments_dir=fragments_dir,
                module_name=module_name,
                module_paths=module_paths,
                related_tests=related_tests,
                entrypoints=entrypoints,
            )

    out_path = compiled_dir / "module_index.json"
    DEFAULT_CONTRACT_VALIDATOR.validate("module_index", modules)
    out_path.write_text(json.dumps(modules, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def _build_module_record(
    repo_root: Path,
    fragments_dir: Path,
    module_name: str,
    module_paths: list[str],
    related_tests: list[str],
    entrypoints: list[str],
) -> dict[str, Any]:
    fragment_name = module_name.replace("/", "__")
    summary_fragment = fragments_dir / f"{fragment_name}.summary.json"
    if not summary_fragment.exists():
        summary_fragment.write_text(
            json.dumps({
                "module": module_name,
                "summary": f"Auto-generated summary placeholder for {module_name}.",
                "paths": module_paths,
                "entrypoints": entrypoints,
                "related_tests": related_tests,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return {
        "paths": module_paths,
        "owners": _infer_owners(module_name),
        "entrypoints": entrypoints,
        "related_tests": related_tests,
        "dependencies": [],
        "risk_level": _infer_risk(module_name),
        "summary_fragment": str(summary_fragment.relative_to(repo_root)),
    }


def _find_related_tests(repo_root: Path, module_name: str, test_roots: list[Path]) -> list[str]:
    matches: list[str] = []
    module_tokens = module_name.replace("\\", "/").split("/")

    for test_root in test_roots:
        for path in test_root.rglob("*"):
            if not path.is_file():
                continue

            normalized = path.as_posix().lower()
            if any(token.lower() in normalized for token in module_tokens if token):
                matches.append(str(path.relative_to(repo_root)))

    return sorted(set(matches))


def _find_entrypoints(repo_root: Path, module_dir: Path) -> list[str]:
    candidates: list[str] = []
    for path in module_dir.rglob("*.py"):
        name = path.name.lower()
        if name in {"main.py", "__init__.py"} or any(
            kw in name for kw in ("service", "controller", "api", "router", "handler", "orchestrator")
        ):
            candidates.append(str(path.relative_to(repo_root)))
    return sorted(set(candidates))[:10]


def _infer_owners(module_name: str) -> list[str]:
    sensitive = {"auth", "billing", "payments", "security", "admin"}
    module_tokens = set(module_name.replace("\\", "/").split("/"))
    if module_tokens & sensitive:
        return ["backend", "qa", "security"]
    if module_name.startswith("control_plane/"):
        return ["backend", "qa"]
    return ["backend", "qa"]


def _infer_risk(module_name: str) -> str:
    high = {"auth", "billing", "payments", "security", "admin"}
    module_tokens = set(module_name.replace("\\", "/").split("/"))
    return "high" if module_tokens & high else "medium"


def build_all(repo_root: Path, include_pool: bool = False) -> dict[str, str]:
    """Run every compiler and return a manifest of generated files.

    Args:
        include_pool: If True, include .skills_pool/ in skill compilation.
    """
    print("=" * 60)
    print("  Agents-of-SHIELD - Knowledge Compiler v2")
    print("=" * 60)

    results: dict[str, str] = {}
    errors: list[str] = []
    total_steps = 6

    print(f"\n[1/{total_steps}] Compiling roles from manifest.yaml ...")
    try:
        role_path = compile_roles(repo_root)
        results["role_index"] = str(role_path)
        print(f"  [OK] {role_path}")
    except Exception as exc:
        errors.append(f"roles: {exc}")
        print(f"  [FAIL] {exc}")

    print(f"\n[2/{total_steps}] Compiling skills from Skills/ ...")
    try:
        skill_path = compile_skills(repo_root, include_pool=include_pool)
        results["skill_index"] = str(skill_path)
        pool_note = " (+ .skills_pool)" if include_pool else " (Skills/ only)"
        print(f"  [OK] {skill_path}{pool_note}")
    except Exception as exc:
        errors.append(f"skills: {exc}")
        print(f"  [FAIL] {exc}")

    print(f"\n[3/{total_steps}] Compiling docs ...")
    try:
        doc_paths = compile_docs(repo_root)
        for path in doc_paths:
            results[path.stem] = str(path)
            print(f"  [OK] {path}")
    except Exception as exc:
        errors.append(f"docs: {exc}")
        print(f"  [FAIL] {exc}")

    print(f"\n[4/{total_steps}] Building dashboard snapshot ...")
    try:
        dashboard_path = build_dashboard_snapshot(repo_root)
        results["dashboard_snapshot"] = str(dashboard_path)
        print(f"  [OK] {dashboard_path}")
    except Exception as exc:
        errors.append(f"dashboard_snapshot: {exc}")
        print(f"  [FAIL] {exc}")

    print(f"\n[5/{total_steps}] Building module index ...")
    try:
        module_path = build_module_index(repo_root)
        results["module_index"] = str(module_path)
        print(f"  [OK] {module_path}")
    except Exception as exc:
        errors.append(f"module_index: {exc}")
        print(f"  [FAIL] {exc}")

    print(f"\n[6/{total_steps}] Building local indexes ...")
    try:
        idx_results = build_local_indexes(repo_root)
        results.update(idx_results)
        for name, path in idx_results.items():
            print(f"  [OK] {path}")
    except Exception as exc:
        errors.append(f"local_indexes: {exc}")
        print(f"  [FAIL] {exc}")

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "compiler_version": "2.0",
        "outputs": results,
    }
    manifest_path = repo_root / "knowledge" / "compiled" / "build_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  Build complete: {len(results)} artifacts")
    print(f"  Manifest: {manifest_path}")
    print(f"{'=' * 60}")

    if errors:
        raise RuntimeError("Compile failed: " + "; ".join(errors))

    return results


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    build_all(root)
