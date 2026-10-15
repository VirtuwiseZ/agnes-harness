"""D1 — Deterministic UTF-8 BOM & frontmatter integrity check for AGH Skills.

Scans all `.agh/skills/*/SKILL.md` files and verifies:
  1. File is non-empty and does NOT start with UTF-8 BOM (EF BB BF);
  2. File strictly starts with `---\\n` or `---\\r\\n` so AGH's
     parseSkillDocument frontmatter check never silently skips a skill.

Usage:
    python physics-agent/hooks/skill_bom_check.py [--skills-dir .agh/skills] [--fix]
"""
import argparse
import glob
import os
import sys

BOM = b"\xef\xbb\xbf"


def check_skills(skills_dir=".agh/skills", fix=False):
    pattern = os.path.join(skills_dir, "*", "SKILL.md")
    paths = sorted(glob.glob(pattern))
    if not paths:
        print(f"[FAIL] No SKILL.md files found under {skills_dir}")
        return 1

    bad_bom = []
    bad_frontmatter = []
    fixed = []

    for p in paths:
        with open(p, "rb") as f:
            raw = f.read()
        if raw.startswith(BOM):
            if fix:
                raw = raw[len(BOM):]
                with open(p, "wb") as fw:
                    fw.write(raw)
                fixed.append(p)
            else:
                bad_bom.append(p)
                continue
        if not (raw.startswith(b"---\n") or raw.startswith(b"---\r\n")):
            bad_frontmatter.append(p)

    if fixed:
        print(f"[FIXED] Stripped UTF-8 BOM from {len(fixed)} file(s): {', '.join(fixed)}")

    if bad_bom or bad_frontmatter:
        for p in bad_bom:
            print(f"[FAIL] UTF-8 BOM (EF BB BF) detected at start of: {p}")
        for p in bad_frontmatter:
            print(f"[FAIL] Missing strict '---' YAML frontmatter header at start of: {p}")
        print(
            "\nTo strip BOM automatically, run:\n"
            "  python physics-agent/hooks/skill_bom_check.py --fix"
        )
        return 1

    print(f"[PASS] All {len(paths)} SKILL.md files under '{skills_dir}' are BOM-free and have valid frontmatter headers.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check .agh/skills/*/SKILL.md for UTF-8 BOM and frontmatter header.")
    ap.add_argument("--skills-dir", default=".agh/skills", help="Path to .agh/skills directory.")
    ap.add_argument("--fix", action="store_true", help="Automatically strip UTF-8 BOM if found.")
    args = ap.parse_args(argv)
    return check_skills(args.skills_dir, fix=args.fix)


if __name__ == "__main__":
    sys.exit(main())
