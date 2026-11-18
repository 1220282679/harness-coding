#!/usr/bin/env python3
"""artifact-check.py -- validate harness-coding v2 artifacts (specs/<slug>/).

Usage:
    python scripts/artifact-check.py <specs_dir> [<specs_dir> ...]
    python scripts/artifact-check.py --fixtures fixtures/

.expect format (artifact fixtures, one file per case dir):
    line 1:  pass | fail -- the expected validation outcome
    line 2+: err=<substring> -- optional; each must appear in one of the
             reported error lines (per-error-class assertions: a single
             silent check regression can no longer hide behind other errors)

Pure standard library; zero third-party dependencies.
Exit codes: 0 = all pass, 1 = any failure.
"""
import re
import sys
from pathlib import Path

AC_RE = re.compile(r"^\s*-\s*(AC-\d+)\s*:", re.M)
TASK_RE = re.compile(r"^\s*-\s*\[([ x])\]\s*(T\d+)\s*\(([^)]*)\)\s*:(.*)")
TASK_LIKE_RE = re.compile(r"^\s*-\s*\[[ x]\]\s*T\d+")  # shaped like a task line but may fail the full format
REVIEW_RE = re.compile(r"^\s*-\s*(R\d+)\s*\[([^\]]+)\]\s*:?(\s*.*)")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
GATE_NA_RE = re.compile(r"GATE-NA\((\w+)\)")
GATES = {"lint", "format", "type", "test"}
LEVELS = {"blocker", "major", "minor"}


def section(text: str, name: str) -> str:
    """Return the body of a '## <name>' section ('' when absent)."""
    m = re.search(rf"^## {re.escape(name)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def without_sections(text: str, names: set[str]) -> str:
    out = []
    skip = None
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            skip = m.group(1) if m.group(1) in names else None
            continue
        if not skip:
            out.append(line)
    return "\n".join(out)


def without_comments(text: str) -> str:
    """HTML comments never count (v2.2.8): a commented-out exemption
    declaration or usage is not an active one."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def check_review(text: str, errs: list[str], where: str) -> None:
    body = section(text, "Review")
    for line in body.splitlines():
        m = REVIEW_RE.match(line)
        if not m:
            continue
        rid, tag, _tail = m.groups()
        parts = [p.strip().lower() for p in tag.split("|")]
        status = parts[0]
        level = parts[1] if len(parts) > 1 else None
        if status not in ("open", "resolved"):
            errs.append(f"{where}: {rid} unknown status '{status}' (use [open|<level>] or [resolved])")
            continue
        if status == "open" and level not in LEVELS:
            errs.append(f"{where}: {rid} open finding needs a level (blocker/major/minor)")
            continue
        if status == "open" and level in ("blocker", "major"):
            errs.append(
                f"{where}: {rid} open {level} finding -- closing is illegal; "
                "fix it and mark resolved, or record it in Deferred first"
            )


def check_gate_exemptions(task_text: str, decl_text: str, errs: list[str], where: str) -> None:
    """Gate N/A protocol: every GATE-NA(<gate>) used anywhere in the task
    artifacts must have a matching declaration in the spec/intent Gate
    exemptions section. Full-text scan (not just T-lines) so the 🟡 intent
    channel -- which has no T-lines -- cannot escape the pairing check.
    decl_text source: the 🔴 spec is scanned in full; the 🟡 intent only in
    its `## Gate Exemptions` section -- a full-intent scan would let every
    usage self-declare (usage and declaration share one text) and the
    pairing check would be vacuous (fixed v2.2.7). HTML comments are
    stripped from both sides first (v2.2.8): commented-out declarations
    and usages never count."""
    declared = set(GATE_NA_RE.findall(without_comments(decl_text)))
    body = without_sections(without_comments(task_text), {"Deferred", "Review"})
    for line in body.splitlines():
        for gate in GATE_NA_RE.findall(line):
            if gate not in GATES:
                errs.append(f"{where}: GATE-NA({gate}) -- unknown gate (use lint/format/type/test)")
            elif gate not in declared:
                errs.append(
                    f"{where}: uses GATE-NA({gate}) but spec/intent declares no matching "
                    "Gate exemptions entry (never skip a gate silently)"
                )


def check_task_file(text: str, spec_acs: set[str], errs: list[str], where: str) -> bool:
    body = without_sections(text, {"Deferred", "Review", "Intent Additions"})
    seen_tasks = False
    covered = set()
    for line in body.splitlines():
        m = TASK_RE.match(line)
        if not m:
            # Task-shaped lines that fail the full format must not escape
            # silently (fixed v2.3.1): without this guard, "- [x] T2: do
            # stuff" (no (AC-x) refs block) skipped every task check --
            # no "references no AC", no Output evidence check, no AC<->T
            # coverage participation.
            if TASK_LIKE_RE.match(line):
                errs.append(
                    f"{where}: malformed task line (expected '- [x] T<n> (AC-x): <desc>; "
                    f"verify: <cmd>') -- silently skipped otherwise: {line.strip()}"
                )
            continue
        seen_tasks = True
        checked, tid, refs, desc = m.groups()
        ac_refs = set(re.findall(r"AC-\d+", refs))
        if not ac_refs:
            errs.append(f"{where}: {tid} references no AC")
        for ac in ac_refs:
            if spec_acs and ac not in spec_acs:
                errs.append(f"{where}: {tid} references unknown {ac}")
            covered.add(ac)
        if checked == "x" and "Output:" not in desc and "output:" not in desc:
            errs.append(f"{where}: {tid} is checked but has no 'Output:' (evidence must accompany the check)")
    if spec_acs and seen_tasks:
        for ac in sorted(spec_acs - covered):
            errs.append(f"{where}: {ac} is not covered by any task (AC<->T closure broken)")
    return seen_tasks


def validate_task_dir(d: Path) -> list[str]:
    errs = []
    w = d.as_posix()  # normalize separators (Windows backslashes mixed with '/' otherwise)
    if not SLUG_RE.match(d.name):
        errs.append(f"{w}: slug '{d.name}' must be lowercase kebab-case")
    names = {p.name for p in d.iterdir() if p.is_file()}
    if "spec.md" in names:
        spec = (d / "spec.md").read_text(encoding="utf-8")
        if not re.search(r"^Requirement:", spec, re.M):
            errs.append(f"{w}/spec.md: missing 'Requirement:' line")
        # ACs live in HTML comments don't count (v2.3.3, symmetric with the
        # v2.2.8 GATE-NA comment-stripping): a commented-out AC block
        # (multi-line <!-- ... --> with AC lines on their own lines) used to
        # be collected as a declared AC and then flagged "not covered by
        # any task" -- a comment is not a requirement.
        spec_acs = set(AC_RE.findall(without_comments(spec)))
        if not spec_acs:
            errs.append(f"{w}/spec.md: no acceptance criteria (AC-n) found")
        for req in ("plan.md", "tasks.md"):
            if req not in names:
                errs.append(f"{w}: full channel requires {req}")
        if "tasks.md" in names:
            tasks_text = (d / "tasks.md").read_text(encoding="utf-8")
            if not check_task_file(tasks_text, spec_acs, errs, f"{w}/tasks.md"):
                errs.append(f"{w}/tasks.md: no task lines found")
            check_review(tasks_text, errs, f"{w}/tasks.md")
            check_gate_exemptions(tasks_text, spec, errs, f"{w}/tasks.md")
    elif "intent.md" in names:
        intent = (d / "intent.md").read_text(encoding="utf-8")
        for field_name in ("Intent:", "Verify:"):
            if not re.search(rf"^{field_name}", intent, re.M):
                errs.append(f"{w}/intent.md: missing '{field_name}' line")
        check_task_file(intent, set(), errs, f"{w}/intent.md")
        check_review(intent, errs, f"{w}/intent.md")
        # 🟡 declarations must live in the ## Gate Exemptions section: scanning
        # the full intent would let every usage self-declare (usage and
        # declaration share one text), making the pairing check vacuous.
        check_gate_exemptions(intent, section(intent, "Gate Exemptions"), errs, f"{w}/intent.md")
    else:
        errs.append(f"{w}: no spec.md (full channel) or intent.md (standard channel) found")
    return errs


def run_fixtures(fixdir: str) -> int:
    failures = []
    cases = sorted(p for p in Path(fixdir).iterdir() if p.is_dir())
    if not cases:
        print(f"FAIL fixtures: no cases under {fixdir}")
        return 1
    matched, skipped = 0, 0
    for case in cases:
        expect_file = case / ".expect"
        if not expect_file.exists():
            # Not an artifact-fixture case (e.g. fixtures/skills/ for the
            # find-skill probe) -- skip quietly instead of crashing.
            print(f"[SKIP] {case.name}: no .expect (not an artifact fixture)")
            skipped += 1
            continue
        lines = [line.strip() for line in expect_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        expect = lines[0] if lines else ""
        want_errs = [e[len("err="):] for e in lines[1:] if e.startswith("err=")]
        specs = case / "specs"
        errs = []
        if specs.is_dir():
            for task_dir in sorted(p for p in specs.iterdir() if p.is_dir()):
                errs.extend(validate_task_dir(task_dir))
        passed = not errs
        missing = [w for w in want_errs if not any(w in e for e in errs)]
        ok = passed == (expect == "pass") and not missing
        label = "PASS" if ok else "FAIL"
        print(f"[{label}] fixture {case.name} (expect {expect}, got {'pass' if passed else 'fail'})")
        for e in errs:
            print(f"       - {e}")
        for w in missing:
            print(f"       - expected error substring not reported: {w}")
        if not ok:
            failures.append(case.name)
        else:
            matched += 1
    if failures:
        print(f"FAIL fixtures: mismatched cases: {', '.join(failures)}")
        return 1
    print(f"PASS fixtures: {matched} artifact cases matched expectations "
          f"({skipped} non-artifact dir{'s' if skipped != 1 else ''} skipped)")
    return 0


def main(argv: list[str]) -> int:
    if "--fixtures" in argv:
        i = argv.index("--fixtures")
        if i + 1 >= len(argv):
            print("usage: artifact-check.py --fixtures <dir>")
            return 1
        return run_fixtures(argv[i + 1])
    if not argv:
        print("usage: artifact-check.py <specs_dir>... | --fixtures <dir>")
        return 1
    all_errs = []
    for arg in argv:
        d = Path(arg)
        if not d.is_dir():
            all_errs.append(f"{d}: directory not found")
            continue
        task_dirs = sorted(p for p in d.iterdir() if p.is_dir())
        if not task_dirs:
            print(f"PASS {d}: no task artifacts (light channel leaves nothing behind)")
            continue
        for td in task_dirs:
            errs = validate_task_dir(td)
            print(f"[{'PASS' if not errs else 'FAIL'}] {td.as_posix()}")
            all_errs.extend(errs)
    for e in all_errs:
        print(f"  - {e}")
    if all_errs:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
