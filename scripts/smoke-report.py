#!/usr/bin/env python3
"""Minimal smoke validation for the harness-coding reporting protocol (pure standard library, no third-party deps).

Imports the protocol helpers from `scripts/report_lib.py` (the single implementation source)
and asserts their behavior:

1. Per-task version resolution: the trailing `-v<N>` of the filename stem is the version and the `<slug>` before it identifies the task; `N` is resolved PER TASK (glob the task's own reports → largest pure-integer version +1, 0 for a fresh task) — different tasks have independent counters and the no-slug namespace (`<prefix>-v<N>`) is separate from slugged tasks; mixed names (v-test1) and leading-zero names (v010) don't participate
2. Marker append: init skeleton -> stage append -> marker replaced with DONE; repeated appends don't overwrite, they append a supplement sub-section ABOVE the DONE marker
3. Adjacent markers not copied: edit replaces only the target marker line
4. Output truncation: quality-gate output >100 lines keeps first 30 + last 30; agent output >500 lines keeps heading structure + a truncation marker (with a first 30 + last 30 fallback when the output has no headings)
5. Interruption recovery: resume from the first non-DONE stage; out-of-order gaps (a non-DONE marker before a later DONE) are surfaced as anomalies, never silently skipped
6. Report closing: the header status line `🔄 in progress` → `✅ passed` / `❌ rejected`, a metadata-line edit
7. Overwrite guardrail: must have read a file before writing over it
8. Report directory creation: a write into a missing report dir must mkdir first (no silent drop)
9. Inline mode: report.on_disk=false degrades to no persistence — stage order preserved, closing status kept only in the final summary, and an explicit `⚠️ report not persisted (inline-only)` marker is carried
10. Archive rule: when reports under report.dir exceed 20, archive all but the 2 most recently modified (ranked by mtime) into <report.dir>archive/
11. Collision guard: initializing a new report picks the first free per-task name (claim_filename), so same-task concurrent sessions don't overwrite each other; the caller creates the file exclusively and retries on collision

Usage: python scripts/smoke-report.py
All tests print PASS and exit 0; any failure prints FAIL and exits 1.
Note: on Windows consoles that garble text under GBK, set PYTHONIOENCODING=utf-8 first (this script already tries to force UTF-8 in main).
"""

from __future__ import annotations

import sys

from report_lib import (
    INLINE_MARKER,
    PHASE_RE,
    STEM_RE,
    append_phase,
    archive_candidates,
    claim_filename,
    close_report,
    emit_inline,
    max_task_version,
    next_version,
    parse_stem,
    resume_from,
    task_reports,
    truncate,
    truncate_agent,
)

# ---- Test cases ----


def test_task_version_resolution():
    files = [
        "harness-reports/harness-task-add-rerank-v0.md",
        "harness-reports/harness-task-add-rerank-v2.md",
        "harness-reports/harness-task-add-rerank-v-test.md",        # mixed name, excluded
        "harness-reports/harness-task-add-rerank-migrate-v10.md",   # a DIFFERENT task's report
        "harness-reports/harness-task-fix-typo-v1.md",              # another task
    ]
    assert max_task_version(files, slug="add-rerank") == 2, "per-task max over this slug's reports"
    assert next_version(files, slug="add-rerank") == 3, "next revision for this task"
    assert max_task_version(files, slug="fix-typo") == 1, "independent counter per task"
    assert max_task_version(files, slug="migrate") == 0, "slug 'add-rerank-migrate' != 'migrate'"
    assert next_version(files, slug="migrate") == 0, "first report for a task is v0"


def test_no_slug_namespace_separate():
    files = [
        "harness-reports/harness-task-v0.md",                  # no-slug namespace
        "harness-reports/harness-task-v2.md",
        "harness-reports/harness-task-add-rerank-v3.md",       # slugged task: different namespace
        "harness-reports/harness-task-v-test.md",              # mixed: excluded
    ]
    assert max_task_version(files, slug="") == 2, "no-slug namespace counts only bare <prefix>-v<N>"
    assert next_version(files, slug="") == 3
    assert max_task_version(files, slug="add-rerank") == 3, "slugged task untouched by no-slug files"


def test_version_edge_cases():
    # Leading-zero names (v010) are not pure-integer notation: excluded, so v9 stays the max
    assert max_task_version(["harness-reports/harness-task-v010.md", "harness-reports/harness-task-v9.md"], slug="") == 9
    # A slug ending in -vN does not confuse resolution: the trailing -v3 wins
    assert max_task_version(["harness-reports/harness-task-support-v2-v3.md"], slug="support-v2") == 3
    # A file without a trailing version is not a versioned report
    assert max_task_version(["harness-reports/harness-task-notes.md"], slug="notes") == 0
    # The very first report for a fresh task is v0, not v1
    assert next_version([], slug="add-rerank") == 0


def test_append_and_done_marker():
    skeleton = (
        "# Harness Task Report\n\n"
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: implementation -->\n"
    )
    text = append_phase(skeleton, "implementation", "## Stage 5: implementation\nchange list: A")
    assert "## Stage 5: implementation" in text
    assert "<!-- PHASE: implementation DONE -->" in text, "marker should be replaced with DONE"
    assert text.count("<!-- PHASE: implementation") == 1, "no non-DONE marker should remain"
    # Repeated append: don't overwrite, append a supplement sub-section ABOVE the DONE marker;
    # the DONE marker still ends the block, so the retry content precedes the marker line.
    text2 = append_phase(text, "implementation", "supplement content")
    assert "### Append/Retry" in text2
    assert "supplement content" in text2
    assert text2.count("<!-- PHASE: implementation DONE -->") == 1, "DONE marker must not be duplicated"
    marker_line = text2.index("<!-- PHASE: implementation DONE -->")
    assert "### Append/Retry" in text2[:marker_line], "retry sub-section sits ABOVE the DONE marker"
    assert text2[:marker_line].index("supplement content") > text2[:marker_line].index("### Append/Retry")


def test_adjacent_marker_not_copied():
    skeleton = (
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: implementation -->\n"
        "<!-- PHASE: quality-gate -->\n"
    )
    text = append_phase(skeleton, "implementation", "content")
    assert text.count("<!-- PHASE: quality-gate -->") == 1, "adjacent marker must not be copied"
    assert text.count("<!-- PHASE: implementation DONE -->") == 1


def test_append_missing_marker_appends_to_end():
    skeleton = "<!-- PHASE: init DONE -->\n"
    text = append_phase(skeleton, "merge", "## Stage 10: merge\nmethod: direct merge")
    assert "## Stage 10: merge" in text
    assert "<!-- PHASE: init DONE -->" in text


def test_truncate():
    long = "\n".join("line {}".format(i) for i in range(120))
    out = truncate(long)
    lines = out.splitlines()
    assert len(lines) == 30 + 1 + 30, "100+ lines keep first 30 + last 30 + truncation marker"
    assert out.startswith("line 0") and out.endswith("line 119")
    assert "truncated, 120 lines total" in out
    short = "\n".join("x" for _ in range(80))
    assert truncate(short) == short, "under 100 lines, no truncation"


def test_truncate_agent_headings():
    long = "\n".join(
        "# Section {}".format(i // 50) if i % 50 == 0 else "body line {}".format(i)
        for i in range(600)
    )
    out = truncate_agent(long)
    assert "truncated, 600 lines total" in out
    assert "# Section" in out
    assert "body line" not in out, "agent truncation keeps only the heading structure"
    short = "\n".join("x" for _ in range(400))
    assert truncate_agent(short) == short, "under 500 lines, no truncation"


def test_truncate_agent_no_headings():
    # No heading lines: fall back to first 30 + last 30, never drop all content
    long = "\n".join("body line {}".format(i) for i in range(600))
    out = truncate_agent(long)
    lines = out.splitlines()
    assert len(lines) == 30 + 1 + 30, "no-heading fallback keeps first 30 + last 30 + marker"
    assert out.startswith("body line 0") and out.endswith("body line 599")
    assert "truncated, 600 lines total" in out
    assert "body line 300" not in out, "the middle is dropped, not the whole output"


def test_truncate_agent_all_headings():
    # Pathological edge: every one of >500 lines is a heading. Keeping them all would defeat
    # truncation, so the heading list itself is capped to first 30 + last 30 + marker.
    long = "\n".join("# H{}".format(i) for i in range(600))
    out = truncate_agent(long)
    lines = out.splitlines()
    assert len(lines) == 30 + 1 + 30, "all-heading output still truncates to first 30 + last 30 + marker"
    assert out.startswith("# H0") and out.endswith("# H599")
    assert "truncated, 600 lines total" in out
    assert "# H300" not in out, "middle headings dropped"


def test_append_trailing_whitespace_done_marker():
    # A DONE marker with trailing whitespace (hand-edited report) must still be treated as DONE:
    # the retry sub-section goes ABOVE the marker and the marker is never re-expanded.
    text = (
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: implementation DONE --> \n"  # trailing space after the marker
    )
    out = append_phase(text, "implementation", "supplement")
    assert "### Append/Retry" in out
    assert "supplement" in out
    assert out.count("<!-- PHASE: implementation DONE -->") == 1, "DONE marker must not be duplicated"
    marker_line = out.index("<!-- PHASE: implementation DONE -->")
    assert "### Append/Retry" in out[:marker_line], "retry sub-section sits ABOVE the DONE marker"


def test_resume_from_last_done():
    text = (
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: positioning DONE -->\n"
        "<!-- PHASE: exploration DONE -->\n"
        "<!-- PHASE: implementation -->\n"
        "<!-- PHASE: quality-gate -->\n"
    )
    phase, anomalies = resume_from(text)
    assert phase == "implementation", "continue from the first non-DONE stage"
    assert anomalies == [], "a well-formed report has no out-of-order gap"


def test_resume_from_out_of_order():
    # A non-DONE phase before a later DONE is an out-of-order gap: resume at the
    # earliest incomplete stage and surface the gap as an anomaly, never silently
    # skipping the jumped-over stage.
    text = (
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: positioning DONE -->\n"
        "<!-- PHASE: exploration DONE -->\n"
        "<!-- PHASE: implementation -->\n"
        "<!-- PHASE: quality-gate DONE -->\n"
        "<!-- PHASE: review -->\n"
    )
    phase, anomalies = resume_from(text)
    assert phase == "implementation", "resume at the earliest incomplete stage, not after the last DONE"
    assert any("implementation" in a for a in anomalies), "the out-of-order gap must be surfaced as an anomaly"
    text = (
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: positioning DONE -->\n"
        "<!-- PHASE: exploration DONE -->\n"
        "<!-- PHASE: implementation -->\n"
        "<!-- PHASE: quality-gate -->\n"
    )
    phase, anomalies = resume_from(text)
    assert phase == "implementation", "continue from the first non-DONE stage"
    assert anomalies == [], "no gap in a sequential report"


def test_resume_from_all_done():
    text = (
        "<!-- PHASE: init DONE -->\n"
        "<!-- PHASE: summary DONE -->\n"
    )
    phase, anomalies = resume_from(text)
    assert phase == "<none>", "no incomplete stage left to resume"
    assert anomalies == [], "no gap when every stage is DONE"


def test_close_status():
    open_report = (
        "# Harness Task Report\n\n"
        "> **Final status**: 🔄 in progress\n"
        "> **Architecture decision**: none\n"
    )
    closed = close_report(open_report, "✅ passed")
    assert "**Final status**: ✅ passed" in closed
    assert "🔄 in progress" not in closed
    assert "**Architecture decision**: none" in closed, "close must not touch other header lines"
    try:
        close_report("no status line here", "✅ passed")
        raised = False
    except ValueError:
        raised = True
    assert raised, "closing a report without an open status line must raise"


def test_write_requires_read():
    # Contract §2: must have read a file before writing over it (prevent accidental destruction). Fake tools simulate the guardrail.
    class FakeStore:
        def __init__(self) -> None:
            self.files: dict[str, str] = {"harness-reports/harness-task-v1.md": "old"}
            self.reads: set[str] = set()

        def read(self, path: str) -> str:
            self.reads.add(path)
            return self.files.get(path, "")

        def write(self, path: str, content: str) -> None:
            assert path not in self.files or path in self.reads, "write over an existing file requires a prior read"
            self.files[path] = content

    store = FakeStore()
    try:
        store.write("harness-reports/harness-task-v1.md", "new content")
        blocked = False
    except AssertionError:
        blocked = True
    assert blocked, "writing without a prior read should be blocked by the guardrail"
    store.read("harness-reports/harness-task-v1.md")
    store.write("harness-reports/harness-task-v1.md", "new content")
    assert store.files["harness-reports/harness-task-v1.md"] == "new content"
    # Creating a new file (doesn't exist) requires no read
    store.write("harness-reports/harness-task-v2.md", "first")
    assert store.files["harness-reports/harness-task-v2.md"] == "first"


def test_report_dir_creation():
    # Contract §8 / templates/write-report.md: the report directory must exist before the
    # first write. A filesystem that does not auto-create parent dirs (e.g. apply_patch-based
    # harnesses) requires an explicit mkdir first; a write into a missing dir must not
    # silently drop the report. Simulate that guardrail.
    class Fs:
        def __init__(self) -> None:
            self.dirs: set[str] = set()
            self.files: dict[str, str] = {}

        def mkdir(self, path: str) -> None:
            self.dirs.add(path)

        def write(self, path: str, content: str) -> None:
            parent = path.rsplit("/", 1)[0]
            assert parent in self.dirs, "write into a missing report dir must mkdir first"
            self.files[path] = content

    fs = Fs()
    try:
        fs.write("harness-reports/harness-task-v1.md", "content")
        blocked = False
    except AssertionError:
        blocked = True
    assert blocked, "writing before creating the report dir should be blocked"
    fs.mkdir("harness-reports")
    fs.write("harness-reports/harness-task-v1.md", "content")
    assert fs.files["harness-reports/harness-task-v1.md"] == "content"


def test_inline_mode_no_disk():
    # report.on_disk=false (capability-contract runtime config): write_report degrades to
    # no persistence — stage content emitted inline in the reply in stage order;
    # versioning/recovery don't apply, and the closing status lives only in the final summary.
    stages: list[tuple[str, str]] = []
    emit_inline(stages, "init", "# Harness Task Report skeleton")
    emit_inline(stages, "implementation", "## Change List\n- added a")
    emit_inline(stages, "summary", "## Final Report\n- Quality gates: pass", close="✅ passed")

    assert [p for p, _ in stages] == ["init", "implementation", "summary"], "inline mode emits stages in order"
    assert "**Final status**: ✅ passed" in stages[-1][1], "closing status is kept only in the final summary"
    assert len(stages) == 3, "no persisted file / versioned path is ever produced"
    assert INLINE_MARKER in stages[0][1], "inline mode carries the explicit report-not-persisted marker"


def test_archive_rule():
    # report-template / capability-contract: when reports under <report.dir> exceed 20,
    # archive them into <report.dir>archive/ keeping the 2 most recently modified (by mtime).
    files = ["harness-reports/harness-task-v{}.md".format(i) for i in range(22)]
    mtime = {f: float(i) for i, f in enumerate(files)}  # inject deterministic mtimes
    to_archive = archive_candidates(files, keep=2, getmtime=lambda f: mtime[f])
    assert len(to_archive) == 20, "all but the 2 newest are archived"
    assert "harness-reports/harness-task-v20.md" not in to_archive, "newest kept"
    assert "harness-reports/harness-task-v21.md" not in to_archive, "newest kept"
    assert "harness-reports/harness-task-v0.md" in to_archive, "oldest archived first"
    assert archive_candidates(files[:20], getmtime=lambda f: mtime[f]) == [], "20 or fewer: no archiving"
    assert archive_candidates(files[:21], getmtime=lambda f: mtime[f]) == files[:19], "21 reports: keep 2, archive 19"


def test_archive_ranks_by_recency_not_version():
    # Per-task version numbers are not chronological recency: a stale task's high v<N> must
    # be archived before a fresh task's low v<N>. Recency = mtime, not version.
    files = [
        "harness-reports/harness-task-stale-v9.md",  # high version, old mtime
        "harness-reports/harness-task-fresh-v0.md",  # low version, recent mtime
        "harness-reports/harness-task-new-v1.md",    # recent mtime
    ]
    mtime = {
        "harness-reports/harness-task-stale-v9.md": 1.0,
        "harness-reports/harness-task-fresh-v0.md": 100.0,
        "harness-reports/harness-task-new-v1.md": 101.0,
    }
    padded = files + ["harness-reports/harness-task-pad-v{}.md".format(i) for i in range(19)]
    mtime.update({"harness-reports/harness-task-pad-v{}.md".format(i): 10.0 + i for i in range(19)})
    to_archive = archive_candidates(padded, keep=2, getmtime=lambda f: mtime[f])
    assert "harness-reports/harness-task-fresh-v0.md" not in to_archive, "fresh low-version report kept"
    assert "harness-reports/harness-task-new-v1.md" not in to_archive, "newest kept"
    assert "harness-reports/harness-task-stale-v9.md" in to_archive, "stale high-version report archived despite v9"


def test_claim_filename_avoids_concurrent_collision():
    # Two concurrent sessions glob the same task state; session A exclusively creates v2,
    # session B's create of v2 fails -> it re-claims and lands on v3 (never overwrites).
    files = ["harness-reports/harness-task-add-rerank-v0.md", "harness-reports/harness-task-add-rerank-v1.md"]
    taken: dict[str, bool] = {}
    exists = lambda p: taken.get(p, False)
    # both sessions compute the same candidate
    candidate = claim_filename(files, slug="add-rerank", exists_fn=exists)
    assert candidate == "harness-reports/harness-task-add-rerank-v2.md"
    taken[candidate] = True  # session A's exclusive create wins
    retry = claim_filename(files, slug="add-rerank", exists_fn=exists)
    assert retry == "harness-reports/harness-task-add-rerank-v3.md", "retry advances past the claimed name"


def main() -> int:
    # Windows consoles default to GBK and garble non-ASCII; force stdout to UTF-8 (ignore if unavailable)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    tests = [
        ("per-task version resolution", test_task_version_resolution),
        ("no-slug namespace separate from slugged tasks", test_no_slug_namespace_separate),
        ("version edge cases (leading zero / trailing -vN / unversioned / fresh task)", test_version_edge_cases),
        ("marker append and DONE replacement", test_append_and_done_marker),
        ("adjacent markers not copied", test_adjacent_marker_not_copied),
        ("missing marker appends to end", test_append_missing_marker_appends_to_end),
        ("output truncation", test_truncate),
        ("agent-output heading truncation (>500 lines)", test_truncate_agent_headings),
        ("agent-output no-heading fallback truncation", test_truncate_agent_no_headings),
        ("agent-output all-heading truncation edge", test_truncate_agent_all_headings),
        ("DONE marker with trailing whitespace stays DONE", test_append_trailing_whitespace_done_marker),
        ("interruption recovery", test_resume_from_last_done),
        ("interruption recovery (out-of-order DONE gap)", test_resume_from_out_of_order),
        ("interruption recovery (all stages done)", test_resume_from_all_done),
        ("report closing status", test_close_status),
        ("overwrite guardrail read-first", test_write_requires_read),
        ("report directory creation", test_report_dir_creation),
        ("inline mode (on_disk=false) no persistence", test_inline_mode_no_disk),
        ("archive rule (>20 keep 2, mtime-ranked)", test_archive_rule),
        ("archive ranks by recency not version", test_archive_ranks_by_recency_not_version),
        ("collision guard (concurrent same-task init)", test_claim_filename_avoids_concurrent_collision),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("  PASS  {}".format(name))
        except AssertionError as e:
            failed += 1
            print("  FAIL  {}: {}".format(name, e))
    print("---")
    if failed:
        print("{} test(s) failed".format(failed))
        return 1
    print("all passed ({} tests)".format(len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
