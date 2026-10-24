#!/usr/bin/env python3
"""artifact-check.py -- validate harness-coding v2 artifacts (specs/<slug>/).

Usage:
    python scripts/artifact-check.py <specs_dir> [<specs_dir> ...]
    python scripts/artifact-check.py --fixtures fixtures/

Pure standard library; zero third-party dependencies.
Exit codes: 0 = all pass, 1 = any failure.
"""
import re
import sys
from pathlib import Path

AC_RE = re.compile(r"^\s*-\s*(AC-\d+)\s*:", re.M)
TASK_RE = re.compile(r"^\s*-\s*\[([ x])\]\s*(T\d+)\s*\(([^)]*)\)\s*:(.*)")
REVIEW_RE = re.compile(r"^\s*-\s*(R\d+)\s*\[([^\]]+)\]\s*:?(\s*.*)")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LEVELS = {"blocker", "major", "minor"}


def section(text, name):
    """Return the body of a '## <name>' section ('' when absent)."""
    m = re.search(rf"^## {re.escape(name)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def without_sections(text, names):
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


def check_review(text, errs, where):
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


def check_task_file(text, spec_acs, errs, where):
    body = without_sections(text, {"Deferred", "Review", "意图追加"})
    seen_tasks = False
    covered = set()
    for line in body.splitlines():
        m = TASK_RE.match(line)
        if not m:
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
        if checked == "x" and "输出:" not in desc and "输出：" not in desc:
            errs.append(f"{where}: {tid} is checked but has no '输出:' (evidence must accompany the check)")
    if spec_acs and seen_tasks:
        for ac in sorted(spec_acs - covered):
            errs.append(f"{where}: {ac} is not covered by any task (AC<->T closure broken)")
    return seen_tasks


def validate_task_dir(d):
    errs = []
    if not SLUG_RE.match(d.name):
        errs.append(f"{d}: slug '{d.name}' must be lowercase kebab-case")
    names = {p.name for p in d.iterdir() if p.is_file()}
    if "spec.md" in names:
        spec = (d / "spec.md").read_text(encoding="utf-8")
        if not re.search(r"^需求:", spec, re.M):
            errs.append(f"{d}/spec.md: missing '需求:' line")
        spec_acs = set(AC_RE.findall(spec))
        if not spec_acs:
            errs.append(f"{d}/spec.md: no acceptance criteria (AC-n) found")
        for req in ("plan.md", "tasks.md"):
            if req not in names:
                errs.append(f"{d}: full channel requires {req}")
        if "tasks.md" in names:
            tasks_text = (d / "tasks.md").read_text(encoding="utf-8")
            if not check_task_file(tasks_text, spec_acs, errs, f"{d}/tasks.md"):
                errs.append(f"{d}/tasks.md: no task lines found")
            check_review(tasks_text, errs, f"{d}/tasks.md")
    elif "intent.md" in names:
        intent = (d / "intent.md").read_text(encoding="utf-8")
        for field in ("意图:", "验证:"):
            if not re.search(rf"^{field}", intent, re.M):
                errs.append(f"{d}/intent.md: missing '{field}' line")
        check_task_file(intent, set(), errs, f"{d}/intent.md")
        check_review(intent, errs, f"{d}/intent.md")
    else:
        errs.append(f"{d}: no spec.md (full channel) or intent.md (standard channel) found")
    return errs


def run_fixtures(fixdir):
    failures = []
    cases = sorted(p for p in Path(fixdir).iterdir() if p.is_dir())
    if not cases:
        print(f"FAIL fixtures: no cases under {fixdir}")
        return 1
    for case in cases:
        expect = (case / ".expect").read_text(encoding="utf-8").strip()
        specs = case / "specs"
        errs = []
        if specs.is_dir():
            for task_dir in sorted(p for p in specs.iterdir() if p.is_dir()):
                errs.extend(validate_task_dir(task_dir))
        passed = not errs
        ok = passed == (expect == "pass")
        label = "PASS" if ok else "FAIL"
        print(f"[{label}] fixture {case.name} (expect {expect}, got {'pass' if passed else 'fail'})")
        for e in errs:
            print(f"       - {e}")
        if not ok:
            failures.append(case.name)
    if failures:
        print(f"FAIL fixtures: mismatched cases: {', '.join(failures)}")
        return 1
    print(f"PASS fixtures: {len(cases)} cases matched expectations")
    return 0


def main(argv):
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
            print(f"[{'PASS' if not errs else 'FAIL'}] {td}")
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
