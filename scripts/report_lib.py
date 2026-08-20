#!/usr/bin/env python3
"""Shared implementation of the harness-coding reporting protocol (pure standard library).

Single implementation source for the mechanical rules of the write_report semantics
(capability-contract §8 and templates/write-report.md). Imported by both
`scripts/smoke-report.py` (unit assertions) and `scripts/workflow-check.py`
(per-channel end-to-end lifecycle). Keeps the protocol in one place so the docs and
the validators cannot drift apart.

Rules encoded here:
- Per-task version resolution: the trailing `-v<N>` of the filename stem is the version;
  `N` is resolved PER TASK (glob the task's own reports -> largest pure-integer version +1,
  0 for a fresh task); mixed names (v-test1) and leading-zero names (v010) don't participate.
- Marker append: init skeleton -> stage append -> marker replaced with DONE; repeated appends
  don't overwrite, they append a `### Append/Retry` sub-section ABOVE the DONE marker
  (the DONE marker always ends the block; content sits above it).
- Output truncation: quality-gate output >100 lines keeps first 30 + last 30; agent output
  >500 lines keeps heading structure + a truncation marker (first 30 + last 30 fallback when
  the output has no headings).
- Interruption recovery: resume from the first non-DONE stage; out-of-order gaps (a non-DONE
  marker before a later DONE) are surfaced as anomalies, never silently skipped.
- Report closing: the header status line `**Final status**: 🔄 in progress` -> `✅ passed` /
  `❌ rejected` (or `❌ abandoned` when an in-progress report is abandoned at init), a metadata-line edit.
- Inline mode (report.on_disk=false): no persistence, stage order preserved, closing status
  kept only in the final summary, explicit `⚠️ report not persisted (inline-only)` marker.
- Archive rule: when reports under report.dir exceed 20, archive all but the 2 most recently
  modified (ranked by mtime) into <report.dir>archive/.
- Collision guard: initializing a new report picks the first free per-task name (claim_filename),
  so same-task concurrent sessions don't overwrite each other.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

# Default report prefix (capability-contract runtime config `report.prefix`).
PREFIX = "harness-task"
# Default report directory (capability-contract runtime config `report.dir`).
REPORT_DIR = "harness-reports/"
# Explicit "report not persisted" marker (capability-contract on_disk=false + write_report fault
# tolerance): inline-only or failed persistence must never look like a silently dropped report.
INLINE_MARKER = "⚠️ report not persisted (inline-only)"
# Truncation thresholds and the phase-marker format (must stay in sync with the docs).
# A marker is anchored to a standalone line (allowing surrounding whitespace) and the DONE flag
# is captured separately, so content that merely quotes a marker (a skeleton example, a code
# sample) is never mistaken for a real marker.
PHASE_RE = re.compile(r"^[ \t]*<!-- PHASE: (\S+?)( DONE)? -->[ \t]*$", re.MULTILINE)
# A markdown heading: 1-6 '#' at line start (up to 3 leading spaces) followed by whitespace or
# end-of-line. Excludes shebangs and '#'-prefixed comments that are not headings.
HEADING_RE = re.compile(r"^[ \t]{0,3}#{1,6}(?=\s|$)")

# Decompose <prefix>[-<slug>]-v<N>: the optional slug group backtracks to leave the trailing
# -v<N>, so the trailing version always wins and a no-slug report (harness-task-v10.md) parses
# as slug "" version 10, never as slug "v10".
STEM_RE = re.compile(r"^" + re.escape(PREFIX) + r"(?:-(.*))?-v(\d+)$")


def parse_stem(stem: str) -> tuple[str, int] | None:
    """Decompose a report stem into (slug, version); None when it is not a versioned report.
    slug is '' for the no-slug namespace (harness-task-v0.md). Mixed names (v-test1) and
    leading-zero versions (v010) return None: they don't participate in max resolution."""
    m = STEM_RE.match(stem)
    if not m:
        return None  # no trailing -v<N> (e.g. harness-task-notes): not a versioned report
    slug = m.group(1) or ""
    version = m.group(2)
    # Only "pure-integer" notation participates: mixed names like v-test1 and leading-zero
    # names like v010 are excluded (v010 and v10 would both parse to version 10, collapsing
    # two distinct files into one version identity)
    if len(version) > 1 and version.startswith("0"):
        return None
    return slug, int(version)


def task_reports(files: list[str], slug: str = "") -> list[tuple[str, int]]:
    """(slug, version) pairs for THIS task's versioned reports (slug '' = the no-slug namespace)."""
    out = []
    for f in files:
        p = parse_stem(Path(f).stem)
        if p is not None and p[0] == slug:
            out.append(p)
    return out


def max_task_version(files: list[str], slug: str = "") -> int:
    """Largest pure-integer version among this task's reports; 0 when the task has none."""
    best = 0
    for _, v in task_reports(files, slug):
        best = max(best, v)
    return best


def next_version(files: list[str], slug: str = "") -> int:
    """The next report version for this task: max + 1 when the task already has reports,
    else 0 (the very first report for a task is v0)."""
    if not task_reports(files, slug):
        return 0
    return max_task_version(files, slug) + 1


# The documented slug form (write-report.md): a short kebab-case task identifier — lowercase
# letters, digits, and single hyphens. Enforced in claim_filename as defense-in-depth: an
# unsanitized slug (e.g. "../../evil") would otherwise escape the report directory.
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _safe_slug(slug: str) -> str:
    if not slug:
        return slug
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(
            "untrusted slug {!r}: only lowercase letters, digits, and single hyphens are allowed".format(slug)
        )
    return slug


def claim_filename(
    files: list[str],
    slug: str = "",
    exists_fn: Callable[[str], bool] | None = None,
    report_dir: str = REPORT_DIR,
) -> str:
    """Pick the next report filename for this task (as a full path under `report_dir`, the
    report.dir default), skipping any name a concurrent session has already claimed (checked
    via `exists_fn`, default: nothing exists). The caller then creates the file EXCLUSIVELY;
    if that create fails because the path now exists, re-run this against the fresh glob
    (bumping N) and retry. Versioning stays per-task."""
    exists = exists_fn or (lambda p: False)
    # report.dir must end with a trailing slash (capability-contract runtime config); normalize a
    # missing one so an override like "harness-reports" can never silently produce a bad filename.
    report_dir = report_dir if report_dir.endswith("/") else report_dir + "/"
    slug = _safe_slug(slug)  # defense-in-depth: reject path traversal via the slug
    n = next_version(files, slug)
    while True:
        name = "{}{}-{}-v{}.md".format(report_dir, PREFIX, slug, n) if slug else "{}{}-v{}.md".format(report_dir, PREFIX, n)
        if not exists(name):
            return name
        n += 1  # a concurrent session claimed this name: advance and retry


def _marker_lines(lines: list[str]):
    """Yield (index, match) for each standalone phase-marker line, skipping fenced code blocks.

    Fenced blocks (``` / ~~~) are where a doc quotes a skeleton example; a marker on its own
    line inside a fence is content, not a real marker. The whole-line-anchored PHASE_RE already
    excludes markers embedded mid-line in prose."""
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = PHASE_RE.search(line)
        if m:
            yield i, m


def append_phase(text: str, phase: str, content: str) -> str:
    """Locate the non-DONE marker -> append content -> replace the marker with DONE; already DONE
    -> append a `### Append/Retry` sub-section ABOVE the marker (the DONE marker always ends the
    block; content sits above it).

    Replaces only the target marker line, doesn't copy adjacent markers (contract §8 composition-simulation semantics).
    """
    lines = text.splitlines()
    for i, m in _marker_lines(lines):
        if m.group(1) == phase:
            # DONE state comes from the captured group, not `line.endswith`: a hand-edited report
            # may carry trailing whitespace after a DONE marker, which would otherwise be misread
            # as non-DONE and re-expand an already-completed block.
            if m.group(2) is None:
                block = content.rstrip("\n") + "\n" + lines[i].replace(" -->", " DONE -->")
                lines[i] = block
            else:
                # already DONE: don't overwrite. The retry sub-section sits ABOVE the marker line
                # like regular stage content, so the DONE marker keeps ending the block.
                lines[i] = "### Append/Retry\n" + content.rstrip("\n") + "\n" + lines[i]
            return "\n".join(lines)
    # No matching marker: append to the end
    return text.rstrip("\n") + "\n\n" + content.rstrip("\n") + "\n"


def truncate(text: str, limit: int = 100, head: int = 30, tail: int = 30) -> str:
    """Quality-gate output >100 lines keeps first 30 + last 30, with a truncation marker in the middle."""
    lines = text.rstrip("\n").splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    marker = "\n... truncated, {} lines total ...\n".format(len(lines))
    return "\n".join(lines[:head]) + marker + "\n".join(lines[-tail:])


def truncate_agent(text: str, limit: int = 500, head: int = 30, tail: int = 30) -> str:
    """Agent output >500 lines keeps the heading structure + a truncation marker (the rest is dropped).
    If the output has no heading lines, fall back to keeping the first `head` + last `tail` lines so
    content is never reduced to just the marker."""
    lines = text.rstrip("\n").splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    # Only markdown-heading-shaped lines count as headings: a shebang or a '#'-prefixed comment
    # (e.g. shell/Python output) is not a heading and must not be kept at the expense of content.
    headings = [ln for ln in lines if HEADING_RE.search(ln)]
    if headings:
        marker = "\n... truncated, {} lines total (headings only kept) ...\n".format(len(lines))
        if len(headings) > limit:
            # Pathological edge: every line is a heading — keeping them all would defeat
            # truncation, so the heading list itself is capped to first `head` + last `tail`.
            return "\n".join(headings[:head]) + marker + "\n".join(headings[-tail:])
        return "\n".join(headings) + marker
    marker = "\n... truncated, {} lines total ...\n".format(len(lines))
    return "\n".join(lines[:head]) + marker + "\n".join(lines[-tail:])


def resume_from(text: str) -> tuple[str, list[str]]:
    """Return the next phase to run plus any recovery anomalies.

    The resume point is the FIRST non-DONE phase marker (the earliest incomplete stage),
    not merely the stage after the last DONE marker. In a well-formed report the first
    non-DONE phase sits exactly after the last DONE; a non-DONE phase appearing before a
    later DONE means the report is out of order — a stage was jumped over without being
    completed or marked skipped. That gap is returned as an anomaly so the recovery note
    can record it instead of silently dropping the stage."""
    lines = text.splitlines()
    todo: list[tuple[int, str]] = []  # (line index, phase)
    done_idx: list[int] = []
    for i, m in _marker_lines(lines):
        # DONE state comes from the captured group (not `line.endswith`): a hand-edited report
        # may carry trailing whitespace after a DONE marker, which would otherwise be misread as
        # non-DONE and resume at an already-completed stage. Mirrors append_phase.
        if m.group(2) is not None:
            done_idx.append(i)
        else:
            todo.append((i, m.group(1)))
    last_done = done_idx[-1] if done_idx else -1
    anomalies = [
        "{}: non-DONE before a later DONE (line {})".format(phase, i)
        for i, phase in todo
        if i < last_done
    ]
    if not todo:
        return "<none>", anomalies
    return todo[0][1], anomalies


def close_report(text: str, status: str) -> str:
    """Close the report at the summary stage: replace the header metadata status line
    (`🔄 in progress` -> `✅ passed` / `❌ rejected`, or `❌ abandoned` when an in-progress
    report is abandoned per the init continue/abandon rule). This is a metadata-line edit,
    not a phase-marker append — the status line sits in the header, outside the phase markers."""
    old = "**Final status**: 🔄 in progress"
    new = "**Final status**: {}".format(status)
    if old not in text:
        raise ValueError("no open 'in progress' status line to close")
    return text.replace(old, new, 1)


def emit_inline(
    stages: list[tuple[str, str]],
    phase: str,
    content: str,
    close: str | None = None,
) -> None:
    """report.on_disk=false path (capability-contract runtime config): no persistence, stage
    content is emitted inline in the reply, in stage order. Versioning/recovery do not apply
    (no files, no -v<N> resolution); `close` (summary stage) carries the final status inline.
    The first emitted stage carries the explicit `INLINE_MARKER`, so an inline-only report is
    never mistaken for a silently dropped one."""
    if close is None:
        payload = "{}\n\n{}".format(INLINE_MARKER, content) if not stages else content
        stages.append((phase, payload))
    else:
        payload = "{}\n**Final status**: {}".format(content, close)
        if not stages:
            # close-only path (e.g. a single-stage inline summary): still carry the explicit
            # inline-only marker so an unpersisted report is never mistaken for a dropped one.
            payload = "{}\n\n{}".format(INLINE_MARKER, payload)
        stages.append((phase, payload))


def archive_candidates(
    files: list[str],
    keep: int = 2,
    getmtime: Callable[[str], float] | None = None,
) -> list[str]:
    """Archive rule: when reports under <report.dir> exceed 20, move them into
    <report.dir>archive/ keeping the `keep` (default 2) MOST RECENTLY MODIFIED reports.
    Returns the files to archive (empty when 20 or fewer). Recency is the file mtime —
    the orchestrator ranks by real modification time; tests inject a fake getmtime."""
    if len(files) <= 20:
        return []
    getmtime = getmtime or os.path.getmtime
    ranked = sorted(files, key=getmtime)  # oldest (lowest mtime) first
    return ranked[: len(ranked) - keep]
