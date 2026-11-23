#!/usr/bin/env python3
"""artifact-check.py -- validate harness-coding v2 artifacts (specs/<slug>/).

Usage:
    python scripts/artifact-check.py <specs_dir> [<specs_dir> ...]
    python scripts/artifact-check.py --fixtures fixtures/
    python scripts/artifact-check.py --migrate <specs_dir>... [--dry-run]
    python scripts/artifact-check.py --migrate-fixtures fixtures/migrate/

--migrate folds legacy inline GATE-NA usages into a proper `## Gate
Exemptions` section. Enforcement of the pairing hardened over time (v2.0.2
introduced the protocol, v2.2.7 scoped intent declarations to the section,
v2.3.3 stripped comments); chains that legally closed under an older
validator can fail retroactively. Migration is mechanical and honest: it
declares gates exactly as used, never invents a rationale, and is
idempotent (re-running changes nothing). Unknown gates are reported, never
rewritten into a valid gate.

.expect format (artifact fixtures, one file per case dir):
    line 1:  pass | fail -- the expected validation outcome
    line 2+: err=<substring> -- optional; each must appear in one of the
             reported error lines (per-error-class assertions: a single
             silent check regression can no longer hide behind other errors)

.expect format (migrate fixtures, run via --migrate-fixtures):
    line 1:  migrate
    line 2:  gates=<comma-separated gates the migration must declare>
             (empty after '=' when the chain is already compliant)
    line 3:  pass -- the chain must validate clean after migration; the
             second migration pass must be a no-op (idempotency assertion)

Pure standard library; zero third-party dependencies.
Exit codes: 0 = all pass, 1 = any failure.
"""

import re
import shutil
import sys
import tempfile
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
    rest = text[m.end() :]
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


MIGRATION_NOTE = (
    "legacy inline usage migrated by artifact-check --migrate; original rationale "
    "was not recorded at declaration time (chain closed before the pairing "
    "hardening, v2.2.7) -- declared as used, scope: chain-wide"
)


def undeclared_gate_uses(task_text: str, decl_text: str) -> tuple[set[str], set[str]]:
    """Gates used but undeclared, computed exactly as the pairing check does,
    so migration and validation can never disagree. Returns (migratable,
    unknown); unknown gates are never rewritten into a valid gate."""
    declared = set(GATE_NA_RE.findall(without_comments(decl_text)))
    body = without_sections(without_comments(task_text), {"Deferred", "Review"})
    migratable: set[str] = set()
    unknown: set[str] = set()
    for gate in GATE_NA_RE.findall(body):
        if gate not in GATES:
            unknown.add(gate)
        elif gate not in declared:
            migratable.add(gate)
    return migratable, unknown


def _exemption_section(gates: set[str], eol: str) -> str:
    lines = [
        "## Gate Exemptions",
        "<!-- a non-applicable gate must be declared here with a reason + scope, "
        "never skipped silently; artifact-check enforces the pairing -->",
    ]
    for gate in sorted(gates):
        lines.append(f"- GATE-NA({gate}): {MIGRATION_NOTE}")
    return eol.join(lines) + eol


def _add_declarations(text: str, gates: set[str]) -> str:
    """Fold declarations into the file. A missing `## Gate Exemptions` section
    is appended; an existing one receives the lines IN PLACE -- appending a
    second section would be invisible to the validator, which reads the first
    (real bug, caught by the partial-intent fixture on its first run)."""
    eol = "\r\n" if "\r\n" in text else "\n"
    m = re.search(r"^## Gate Exemptions\s*$", text, re.M)
    if not m:
        suffix = "" if text.endswith("\n") else eol
        return text + suffix + eol + _exemption_section(gates, eol)
    lines = [f"- GATE-NA({g}): {MIGRATION_NOTE}" for g in sorted(gates)]
    rest_start = m.end()
    nxt = re.search(r"^## ", text[rest_start:], re.M)
    insert_at = rest_start + nxt.start() if nxt else len(text)
    prefix, rest = text[:insert_at], text[insert_at:]
    if not prefix.endswith("\n"):
        prefix += eol
    return prefix + eol.join(lines) + eol + rest


def migrate_chain(d: Path, dry_run: bool = False) -> list[str]:
    """Fold legacy inline GATE-NA usages into a `## Gate Exemptions` section.
    Returns human-readable action lines (empty = nothing to do). Idempotent:
    a second pass finds no undeclared usages and writes nothing."""
    actions: list[str] = []
    used: set[str] = set()
    unknown: set[str] = set()
    names = {p.name for p in d.iterdir() if p.is_file()}
    if "intent.md" in names:
        path = d / "intent.md"
        text = path.read_text(encoding="utf-8")
        used, unknown = undeclared_gate_uses(text, section(text, "Gate Exemptions"))
        if used:
            actions.append(f"{d.as_posix()}: intent declares {', '.join(f'GATE-NA({g})' for g in sorted(used))}")
        for gate in sorted(unknown):
            actions.append(
                f"{d.as_posix()}: SKIPPED unknown gate GATE-NA({gate}) (cannot migrate; validator still errors)"
            )
        if used and not dry_run:
            path.write_text(_add_declarations(text, used), encoding="utf-8")
    elif "spec.md" in names:
        spec_path = d / "spec.md"
        spec = spec_path.read_text(encoding="utf-8")
        if "tasks.md" in names:
            tasks = (d / "tasks.md").read_text(encoding="utf-8")
            # 🔴 declarations are full-spec scanned, so undeclared usages are
            # those missing from the spec as a whole -- the section is still
            # where they belong per the documented shape.
            spec_used, spec_unknown = undeclared_gate_uses(tasks, spec)
            used |= spec_used
            unknown |= spec_unknown
        if used:
            actions.append(f"{d.as_posix()}: spec declares {', '.join(f'GATE-NA({g})' for g in sorted(used))}")
        for gate in sorted(unknown):
            actions.append(
                f"{d.as_posix()}: SKIPPED unknown gate GATE-NA({gate}) (cannot migrate; validator still errors)"
            )
        if used and not dry_run:
            spec_path.write_text(_add_declarations(spec, used), encoding="utf-8")
    return actions


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
        if expect == "migrate":
            # Migration fixture -- exercised by --migrate-fixtures, which owns
            # the stronger assertions (gates declared + post-migration pass +
            # idempotency). Skipped here so the artifact suite stays pure.
            print(f"[SKIP] {case.name}: migrate fixture (run via --migrate-fixtures)")
            skipped += 1
            continue
        want_errs = [e[len("err=") :] for e in lines[1:] if e.startswith("err=")]
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
    print(
        f"PASS fixtures: {matched} artifact cases matched expectations "
        f"({skipped} non-artifact dir{'s' if skipped != 1 else ''} skipped)"
    )
    return 0


def run_migrate_fixtures(fixdir: str) -> int:
    """Migration self-test: each case runs migrate twice (idempotency),
    validates clean, and must declare exactly the expected gate set.
    Cases run on a temp copy -- migration writes files, and a self-test
    must never mutate the repository it lives in."""
    failures = []
    cases = sorted(p for p in Path(fixdir).iterdir() if p.is_dir())
    if not cases:
        print(f"FAIL migrate-fixtures: no cases under {fixdir}")
        return 1
    matched = 0
    for case in cases:
        expect_file = case / ".expect"
        if not expect_file.exists():
            print(f"[SKIP] {case.name}: no .expect")
            continue
        lines = [line.strip() for line in expect_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines or lines[0] != "migrate":
            print(f"[SKIP] {case.name}: not a migrate fixture")
            continue
        want_gates = set(
            g for g in next((e[len("gates=") :] for e in lines if e.startswith("gates=")), "").split(",") if g
        )
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / case.name
            shutil.copytree(case, work)
            specs = work / "specs"
            chains = sorted(p for p in specs.iterdir() if p.is_dir()) if specs.is_dir() else []
            actions = [a for td in chains for a in migrate_chain(td)]
            got_gates = set(re.findall(r"GATE-NA\((\w+)\)", " ".join(actions)))
            errs = [e for td in chains for e in validate_task_dir(td)]
            rerun = [a for td in chains for a in migrate_chain(td)]
        ok = got_gates == want_gates and not errs and not rerun
        label = "PASS" if ok else "FAIL"
        print(
            f"[{label}] migrate fixture {case.name} "
            f"(expect gates {sorted(want_gates) or '[]'}, got {sorted(got_gates) or '[]'})"
        )
        for a in actions:
            print(f"       - {a}")
        for e in errs:
            print(f"       - validation error after migration: {e}")
        if rerun:
            print(f"       - NOT idempotent: second pass still changed {len(rerun)} thing(s)")
        if ok:
            matched += 1
        else:
            failures.append(case.name)
    if failures:
        print(f"FAIL migrate-fixtures: mismatched cases: {', '.join(failures)}")
        return 1
    print(f"PASS migrate-fixtures: {matched} cases matched (gates declared + post-migration pass + idempotent)")
    return 0


def main(argv: list[str]) -> int:
    if "--fixtures" in argv:
        i = argv.index("--fixtures")
        if i + 1 >= len(argv):
            print("usage: artifact-check.py --fixtures <dir>")
            return 1
        return run_fixtures(argv[i + 1])
    if "--migrate-fixtures" in argv:
        i = argv.index("--migrate-fixtures")
        if i + 1 >= len(argv):
            print("usage: artifact-check.py --migrate-fixtures <dir>")
            return 1
        return run_migrate_fixtures(argv[i + 1])
    if "--migrate" in argv:
        dry_run = "--dry-run" in argv
        dirs = [a for a in argv if a not in ("--migrate", "--dry-run")]
        if not dirs:
            print("usage: artifact-check.py --migrate <specs_dir>... [--dry-run]")
            return 1
        total: list[str] = []
        for arg in dirs:
            d = Path(arg)
            if not d.is_dir():
                print(f"  - {arg}: directory not found")
                continue
            for td in sorted(p for p in d.iterdir() if p.is_dir()):
                total.extend(migrate_chain(td, dry_run=dry_run))
        for a in total:
            print(f"  - {a}")
        if dry_run:
            print(f"DRY RUN: {len(total)} action(s), no files written")
        elif total:
            print(f"{len(total)} action(s) applied -- re-run artifact-check to validate")
        else:
            print("nothing to migrate (all chains already declare their GATE-NA usages)")
        return 0
    if not argv:
        print("usage: artifact-check.py <specs_dir>... | --fixtures <dir> | --migrate <specs_dir>... [--dry-run]")
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
