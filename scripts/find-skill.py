#!/usr/bin/env python3
"""find-skill.py -- skill-library probe for the find_skill capability.

Context-first fallback (capability-contract §2 optional capability / SKILL.md §7): when the
harness has no native skill-search primitive in the conversation context,
this script probes the standard skill-library locations, matches a query
against skill frontmatter, and reports same-name/version drift between
locations.

Semantics (exit codes):
  0 = hit(s) found
  1 = library present, no match -> use the static conditional table (SKILL.md §7)
  2 = no skill library found at all -> record `skill library unavailable`
  3 = --fixtures self-test mode only: at least one fixture case failed

Drift detection: the same skill `name` found in multiple locations with
different `version` values is reported as a DRIFT warning on stderr -- trust
none of the copies until resolved (observed failure class: a stale v1.0.0
copy shadowing the current v2.x in another location).

Usage:
  python scripts/find-skill.py "<query>"                # probe default roots
  python scripts/find-skill.py "<query>" --root DIR     # probe extra roots only
  python scripts/find-skill.py --fixtures fixtures/skills/   # self-test

Pure standard library; zero third-party dependencies.
"""

import argparse
import re
import sys
from pathlib import Path

DEFAULT_ROOTS = [
    "~/.agents/skills",  # cross-runtime Agent Skills Standard
    "~/.claude/skills",  # Claude Code
    "~/.codex/skills",  # OpenAI Codex
    "~/.config/opencode/skills",  # opencode
    "~/.workbuddy/skills",  # WorkBuddy
]
PROJECT_ROOTS = [
    ".agents/skills",
    ".claude/skills",
    ".codex/skills",
    ".opencode/skills",
]

FIXTURE_QUERY = "validation demo"  # fixed query for --fixtures self-test

Entry = dict[str, str]  # parsed SKILL.md frontmatter: {name, version, description, ...}
Library = dict[str, list[Entry]]  # skill name -> copies across locations

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.S)
FIELD_RES = {k: re.compile(rf"^{k}:\s*(.+)$", re.M) for k in ("name", "version", "description")}


def parse_skill(skill_md: Path) -> Entry | None:
    """Parse SKILL.md frontmatter -> {name, version, description} or None."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    block = m.group(1)
    fields = {}
    for key, rx in FIELD_RES.items():
        fm = rx.search(block)
        if fm:
            fields[key] = fm.group(1).strip().strip('"')
    if "name" not in fields:
        return None
    fields.setdefault("version", "unknown")
    fields.setdefault("description", "")
    return fields


def scan_roots(roots: list[str]) -> tuple[Library, int]:
    """Scan roots -> (library: {name: [entry]}, locations_seen: int).

    entry = {name, version, description, root, path}.
    Copies resolving to the same real path (junction/symlink aliases of one
    physical library) are counted once -- the first root in order wins.
    """
    library: Library = {}
    locations_seen, seen_real = 0, set()
    for root_dir in roots:
        root = Path(root_dir).expanduser()
        if not root.is_dir():
            continue
        locations_seen += 1
        for skill_md in sorted(root.glob("*/SKILL.md")):
            real = skill_md.resolve()
            if real in seen_real:
                continue
            seen_real.add(real)
            fields = parse_skill(skill_md)
            if not fields:
                continue
            entry = dict(fields, root=str(root), path=str(skill_md))
            library.setdefault(fields["name"], []).append(entry)
    return library, locations_seen


def match(library: Library, query: str) -> list[tuple[int, Entry]]:
    """Score entries against query terms; return [(score, entry)] desc.

    Terms of length >= 2 are kept (2-char terms like "go"/"py" are real
    skill names); only empty splits are dropped. If every term was
    filtered out but the query is non-empty, fall back to the raw query
    as a single term so 1-char queries still match (fixed v2.2.9: the old
    len(t) > 2 filter silently dropped short queries entirely).
    """
    terms = [t for t in re.split(r"\W+", query.lower()) if t]
    if not any(len(t) >= 2 for t in terms) and terms:
        terms = [query.lower().strip()]
    else:
        terms = [t for t in terms if len(t) >= 2]
    scored = []
    for entries in library.values():
        for e in entries:
            name_hay = e["name"].lower()
            desc_hay = e["description"].lower()
            score = sum(2 for t in terms if t in name_hay)
            score += sum(1 for t in terms if t in desc_hay)
            if score > 0:
                scored.append((score, e))
    scored.sort(key=lambda se: -se[0])
    return scored


def drift_warnings(library: Library) -> list[str]:
    """Same skill name in multiple locations with differing versions."""
    warns = []
    for name, entries in sorted(library.items()):
        if len(entries) < 2:
            continue
        versions = {e["version"] for e in entries}
        if len(versions) > 1:
            detail = " vs ".join(f"v{e['version']} ({e['root']})" for e in entries)
            warns.append(f"DRIFT: '{name}' {detail} -- trust none until resolved")
    return warns


def print_hits(scored: list[tuple[int, Entry]]) -> None:
    for score, e in scored:
        print(f"{e['name']}  v{e['version']}  [score {score}]  {e['path']}")
        if e["description"]:
            desc = e["description"][:110] + ("..." if len(e["description"]) > 110 else "")
            print(f"    {desc}")


def run(query: str, roots: list[str]) -> int:
    library, locations_seen = scan_roots(roots)
    for w in drift_warnings(library):
        print(w, file=sys.stderr)
    if not library:
        if locations_seen:
            # Roots exist but hold no parseable SKILL.md -- distinct from
            # "no library at all" so the operator knows where to look
            # (exit code stays 2: no usable library either way).
            print(
                f"{locations_seen} skill-library root(s) present but no "
                "parseable SKILL.md in any of them -- check dir layout "
                "(<skill>/SKILL.md) and frontmatter",
                file=sys.stderr,
            )
        else:
            print("no skill library found in any standard location", file=sys.stderr)
        return 2
    scored = match(library, query)
    if not scored:
        print(f"no match for '{query}' -- fall back to the static table (SKILL.md §7)")
        return 1
    print_hits(scored)
    return 0


def run_fixtures(fixtures_dir: Path) -> int:
    """Self-test: each case dir holds synthetic library roots + .expect
    (lines: exit=<0|1|2>, optional drift=warn|none, optional query=<terms>
    overriding the default FIXTURE_QUERY)."""
    ok = True
    for case in sorted(p for p in fixtures_dir.iterdir() if p.is_dir()):
        expect = {}
        exp_file = case / ".expect"
        if exp_file.exists():
            for line in exp_file.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    expect[k.strip()] = v.strip()
        roots = [str(d) for d in sorted(case.iterdir()) if d.is_dir()]
        query = expect.get("query", FIXTURE_QUERY)
        library, _ = scan_roots(roots)
        warns = drift_warnings(library)
        if not library:
            code = 2
        elif match(library, query):
            code = 0
        else:
            code = 1
        want_exit = int(expect.get("exit", -1))
        want_drift = expect.get("drift", "none")
        got_drift = "warn" if warns else "none"
        passed = code == want_exit and got_drift == want_drift
        ok = ok and passed
        print(
            f"{'PASS' if passed else 'FAIL'}: {case.name} "
            f"(exit={code} want {want_exit}; drift={got_drift} want {want_drift})"
        )
    return 0 if ok else 3


def main() -> None:
    ap = argparse.ArgumentParser(description="Skill-library probe (find_skill fallback)")
    ap.add_argument("query", nargs="?", help="search terms, e.g. 'clarification questions'")
    ap.add_argument("--root", action="append", default=[], help="probe these library roots instead of the defaults")
    ap.add_argument("--fixtures", type=Path, metavar="DIR", help="self-test mode: run fixture cases under DIR and exit")
    args = ap.parse_args()
    if args.fixtures:
        sys.exit(run_fixtures(args.fixtures))
    if not args.query:
        ap.error("a query is required unless --fixtures is used")
    roots = args.root if args.root else DEFAULT_ROOTS + PROJECT_ROOTS
    sys.exit(run(args.query, roots))


if __name__ == "__main__":
    main()
