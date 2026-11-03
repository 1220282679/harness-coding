#!/usr/bin/env python3
"""find-skill.py -- cross-location skill discovery + drift probe (harness-coding v2.2.0).

Complements context-first resolution (SKILL.md sec 7): the host's native skill
mechanism remains the primary loader. This probe adds the one thing no single
host can see: the same skill installed at multiple locations with different
versions (drift). It also gives an explicit answer to "does a skill library
exist at all" -- an environment condition, distinct from a normal no-match.

Usage:
  python scripts/find-skill.py "<query>"                 # probe standard roots
  python scripts/find-skill.py "<query>" --roots A,B     # custom roots (testing)

Exit codes:
  0 = ok (matches found, or clean no-match, or library-missing recorded)
  1 = drift detected (same skill name, different versions across locations)
  2 = usage error

Standard library only -- no third-party dependencies.
"""
import re
import sys
from pathlib import Path

HOME = Path.home()
STANDARD_ROOTS = [
    HOME / ".agents" / "skills",
    HOME / ".claude" / "skills",
    HOME / ".codex" / "skills",
    HOME / ".config" / "opencode" / "skills",
    Path.cwd() / ".agents" / "skills",
    Path.cwd() / ".claude" / "skills",
    Path.cwd() / ".opencode" / "skills",
    Path.cwd() / ".codex" / "skills",
]

FM_KEYS = ("name", "version", "description")


def parse_frontmatter(path):
    """Minimal frontmatter parse: name / version / description as flat strings."""
    meta = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return meta
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        kv = re.match(rf"^({'|'.join(FM_KEYS)})\s*:\s*(.*)$", line)
        if kv:
            meta[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return meta


def scan(root):
    """All skills under one root: {dir_name: (path, meta)}."""
    found = {}
    if not root.is_dir():
        return found
    for skill_md in sorted(root.glob("*/SKILL.md")):
        meta = parse_frontmatter(skill_md)
        name = meta.get("name") or skill_md.parent.name
        found[skill_md.parent.name] = (skill_md, {**meta, "name": name})
    return found


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    roots_arg = None
    if "--roots" in argv:
        i = argv.index("--roots")
        if i + 1 >= len(argv):
            print("usage: find-skill.py <query> [--roots dirA,dirB]")
            return 2
        roots_arg = [Path(p) for p in argv[i + 1].split(",") if p.strip()]
    if not args:
        print(__doc__.strip().splitlines()[0])
        print('usage: find-skill.py "<query>" [--roots dirA,dirB]')
        return 2

    query = args[0].lower()
    roots = roots_arg if roots_arg is not None else STANDARD_ROOTS
    scanned = [(r, scan(r)) for r in roots]
    existing = [(r, skills) for r, skills in scanned if skills]

    if not existing:
        print("skill library unavailable: none of the standard locations exist")
        print("  probed: " + ", ".join(str(r) for r in roots))
        print("  (environment condition -- record it; distinct from a no-match)")
        return 0

    print(f"query: {args[0]}")
    matches = []
    for root, skills in existing:
        for dirname, (path, meta) in skills.items():
            hay = f"{dirname} {meta.get('name', '')} {meta.get('description', '')}".lower()
            if query in hay:
                matches.append((root, dirname, meta, path))

    if matches:
        for root, dirname, meta, path in matches:
            ver = meta.get("version", "?")
            desc = meta.get("description", "")[:100]
            print(f"  HIT  {dirname} v{ver}  [{root}]")
            if desc:
                print(f"       {desc}")
    else:
        print("  no match (normal condition -- fall back to the static table, SKILL.md sec 7)")

    drift = []
    by_name = {}
    for root, skills in existing:
        for dirname, (path, meta) in skills.items():
            by_name.setdefault(meta.get("name", dirname), []).append((root, meta.get("version", "?")))
    for name, locs in sorted(by_name.items()):
        versions = {v for _, v in locs}
        if len(versions) > 1:
            drift.append((name, locs))

    if drift:
        print("\nDRIFT WARNING: same skill, different versions across locations")
        for name, locs in drift:
            detail = "; ".join(f"v{v} @ {r}" for r, v in locs)
            print(f"  {name}: {detail}")
        print("  fix the copies (keep one source of truth); never silently pick one")
        return 1

    print(f"\nok: {sum(len(s) for _, s in existing)} skill(s) across {len(existing)} location(s), no drift")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
