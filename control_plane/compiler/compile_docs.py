"""Compile markdown docs into project_index.json and context fragments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DOC_FILES: list[str] = [
    "README.md",
    "OPERATING_RULES.md",
    "DASHBOARD.md",
    "SOUL.md",
    "ONBOARDING.md",
    "REFERENCE.md",
    "CHEATSHEET.md",
    "GENERAL.md",
    "GIT_WORKFLOW.md",
    "RECRUITMENT.md",
    "OFFBOARDING.md",
]


def compile_docs(repo_root: Path) -> list[Path]:
    """Compile markdown docs into JSON summaries and fragments."""
    compiled_dir = repo_root / "knowledge" / "compiled"
    fragments_dir = compiled_dir / "context_fragments"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    fragments_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    project_summary: dict[str, Any] = {
        "project_name": "Agents-of-SHIELD",
        "description": "AI agent company with local-driven control-plane architecture",
        "documents": [],
    }

    for file_name in _DOC_FILES:
        path = repo_root / file_name
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        summary = _extract_summary(text)
        sections = _extract_sections(text)

        fragment: dict[str, Any] = {
            "source": file_name,
            "summary": summary,
            "sections": sections,
            "line_count": len(text.splitlines()),
        }

        out_path = fragments_dir / f"{path.stem.lower()}.summary.json"
        out_path.write_text(json.dumps(fragment, indent=2, ensure_ascii=False), encoding="utf-8")
        outputs.append(out_path)

        project_summary["documents"].append({
            "source": file_name,
            "summary": summary,
            "fragment_path": str(out_path.relative_to(repo_root)),
        })

    project_index_path = compiled_dir / "project_index.json"
    project_index_path.write_text(
        json.dumps(project_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    outputs.append(project_index_path)
    return outputs


def _extract_summary(text: str) -> str:
    """Extract first non-empty, non-heading lines as a summary."""
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return " ".join(lines[:8])[:500]


def _extract_sections(text: str) -> list[dict[str, str]]:
    """Extract level-two headings as a flat list of section names."""
    sections: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            title = stripped.lstrip("# ").strip()
            sections.append({"heading": title})
    return sections


if __name__ == "__main__":
    results = compile_docs(Path(".").resolve())
    for result in results:
        print(f"  -> {result}")
