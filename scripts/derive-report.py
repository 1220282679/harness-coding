#!/usr/bin/env python3
"""derive-report.py -- on-demand traceable view for a harness-coding task chain.

Usage:
    python scripts/derive-report.py <specs/<slug>> [--base <ref>]

Generates the traceable view from task artifacts + a merge-base diff and
prints it to stdout. Read-only: this script never writes anything.
Exit codes: 0 = view generated, 1 = task directory not found.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

BASE_CANDIDATES = ("origin/main", "origin/master", "main", "master")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def pick_base() -> str | None:
    for ref in BASE_CANDIDATES:
        if git("rev-parse", "--verify", "--quiet", ref).returncode == 0:
            return ref
    return None


def field(text: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def section(text: str, name: str) -> str:
    m = re.search(rf"^## {re.escape(name)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end() :]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()].strip() if nxt else rest.strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="on-demand traceable view (stdout only, never persisted)")
    ap.add_argument("task_dir", help="specs/<slug> directory (spec/plan/tasks or intent)")
    ap.add_argument("--base", help="base ref for the diff (default: merge-base with main/master)")
    args = ap.parse_args(argv)

    d = Path(args.task_dir)
    if not d.is_dir():
        print(f"error: task directory not found: {d}", file=sys.stderr)
        return 1

    spec = read(d / "spec.md")
    intent = read(d / "intent.md")
    tasks_path = d / "tasks.md"
    using_intent = not tasks_path.exists()
    tasks = read(tasks_path) or intent

    print(f"# Traceable view: {d.name}")
    print("\n## Requirement")
    req = field(spec, "Requirement") or field(intent, "Intent")
    print(f"- {req or '(not found)'}")

    print("\n## Change List")
    base = args.base or pick_base()
    mb = git("merge-base", "HEAD", base) if base else None
    if mb and mb.returncode == 0:
        stat = git("diff", "--stat", (mb.stdout or "").strip())
        body = (stat.stdout or "").strip() or "(no code changes)"
        print(body)
    else:
        print("(no base ref found, diff skipped -- pass --base <ref> to enable)")

    print("\n## Verification Results")
    task_lines = [line.strip() for line in tasks.splitlines() if re.match(r"\s*- \[[ x]\]\s*T\d+", line)]
    if not task_lines and using_intent:
        # 🟡 intent chains carry no T-lines (v2.2.8): show the intent's
        # verify command and Intent Additions bullets instead of "(no task entries)".
        verify = field(intent, "Verify")
        if verify:
            task_lines.append(f"intent verify: {verify}")
        for line in section(intent, "Intent Additions").splitlines():
            line = line.strip()
            if line.startswith("- "):
                task_lines.append(f"intent addition: {line[2:]}")
    if task_lines:
        for line in task_lines:
            print(f"- {line}")
    else:
        print("- (no task entries)")

    print("\n## Remaining Risks (Deferred)")
    deferred = section(tasks, "Deferred")
    print(deferred or "- none")

    return 0


if __name__ == "__main__":
    sys.exit(main())
