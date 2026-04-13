import sys
import shutil
from pathlib import Path

def install():
    if len(sys.argv) < 2:
        print("Usage: python install_shield.py <target_directory_path>")
        sys.exit(1)
        
    source = Path(__file__).parent.resolve()
    target = Path(sys.argv[1]).resolve()
    
    if not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            print(f"Created target directory {target}")
        except Exception as e:
            print(f"Error: Target directory {target} does not exist and could not be created ({e}).")
            sys.exit(1)

    print(f"Installing SHIELD V2 Control Plane to {target} ...\n")

    # 1. Copy exact directories
    dirs_to_copy = ["control_plane", "tools", "templates", "Skills"]
    for d in dirs_to_copy:
        src_d = source / d
        dst_d = target / d
        if src_d.exists():
            if dst_d.exists():
                shutil.rmtree(dst_d)
            # ignore cache folders if any sneak in
            shutil.copytree(src_d, dst_d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            print(f"  [OK] Copied directory: {d}/")

    # 2. Copy exact files
    files_to_copy = [
        "PROMPT_PACK.md", 
        "ONBOARDING.md", 
        "OPERATING_RULES.md", 
        "ROLE_SKILL_MATRIX.md", 
        "CTO_PRODUCT_WORKFLOW.md",
        "CHEATSHEET.md",
        "GUIDE_FIRSTGUY.md",
        "BOOTSTRAP_SHIELD.md",
        "manifest.yaml", 
        "run_orchestrator.py",
    ]
    for f in files_to_copy:
        src_f = source / f
        dst_f = target / f
        if src_f.exists():
            shutil.copy2(src_f, dst_f)
            print(f"  [OK] Copied file: {f}")

    # 3. Create or update DASHBOARD.md safely
    dashboard = target / "DASHBOARD.md"
    if not dashboard.exists():
        dashboard.write_text(
            "# DASHBOARD\n\n"
            "## Project Goal\n"
            "TODO: Describe the primary goal of your project here.\n\n"
            "## Focus Modules\n"
            "TODO: List the main modules/directories your AI should care about.\n\n"
            "## Active Tasks\n"
            "| Task ID | Title | Role |\n"
            "|---|---|---|\n"
            "| (None yet) | Use the Short Prompt Adapter to create tasks! | |\n", 
            encoding="utf-8"
        )
        print("  [OK] Created initial DASHBOARD.md")
    else:
        print("  [-] DASHBOARD.md already exists, skipping.")

    # 4. Update .gitignore
    gitignore = target / ".gitignore"
    ignore_lines = [
        "\n# SHIELD Protocol artifacts\n", 
        ".hub/\n", 
        "runtime/\n", 
        "knowledge/compiled/\n", 
        ".skills_pool/\n"
    ]
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if "# SHIELD Protocol artifacts" not in content:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.writelines(ignore_lines)
            print("  [OK] Appended SHIELD rules to existing .gitignore")
        else:
            print("  [-] .gitignore already contains SHIELD artifacts, skipping.")
    else:
        with open(gitignore, "w", encoding="utf-8") as f:
            f.writelines(ignore_lines)
        print("  [OK] Created .gitignore with SHIELD rules")

    print(f"\nInstall complete! Next steps:")
    print(f"  1. cd {target}")
    print(f"  2. Edit DASHBOARD.md to describe your existing project.")
    print(f"  3. Run: python run_orchestrator.py compile")
    print(f"  4. Open an AI chat and paste a Short Prompt (e.g. 'thêm tính năng X').")

if __name__ == '__main__':
    install()
