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


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def pick_base():
    for ref in BASE_CANDIDATES:
        if git("rev-parse", "--verify", "--quiet", ref).returncode == 0:
            return ref
    return None


def field(text, name):
    m = re.search(rf"^{name}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()].strip() if nxt else rest.strip()


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main(argv=None):
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
    tasks = read(d / "tasks.md") or intent

    print(f"# 追溯视图: {d.name}")
    print("\n## 需求定位")
    req = field(spec, "需求") or field(intent, "意图")
    print(f"- {req or '(未找到)'}")

    print("\n## 变更清单")
    base = args.base or pick_base()
    mb = git("merge-base", "HEAD", base) if base else None
    if mb and mb.returncode == 0:
        stat = git("diff", "--stat", mb.stdout.strip(), "--", ".")
        body = stat.stdout.strip() or "(无代码变更)"
        print(body)
    else:
        print(f"(未找到基线 ref，跳过 diff -- 传入 --base <ref> 以启用)")

    print("\n## 验证结果")
    task_lines = [l.strip() for l in tasks.splitlines() if re.match(r"\s*- \[[ x]\]\s*T\d+", l)]
    if task_lines:
        for l in task_lines:
            print(f"- {l}")
    else:
        print("- (无任务条目)")

    print("\n## 剩余风险 (Deferred)")
    deferred = section(tasks, "Deferred")
    print(deferred or "- 无")

    return 0


if __name__ == "__main__":
    sys.exit(main())
