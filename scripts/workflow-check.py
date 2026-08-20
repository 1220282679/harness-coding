#!/usr/bin/env python3
"""End-to-end channel lifecycle validation for the harness-coding reporting protocol (pure standard library).

Simulates the full report lifecycle for every tiered channel (🟢 light / 🟡 standard / 🔴 full /
📋 findings-only) using the helpers in `scripts/report_lib.py`:

1. For each channel, build the skeleton (per `references/templates/report-template.md`), then walk the
   phase markers in order: executed phases get stage content, skipped phases get a "(<channel> skipped)"
   DONE marker — the mechanical protocol behind SKILL.md's "skipped stages go on record".
2. Assert the resulting report is well-formed: every marker is DONE, `resume_from` reports <none> with
   no out-of-order anomalies, the status line closes, executed phases carry their content, skipped
   phases carry their skip marker.
3. Cross-validate the channel skip-sets encoded here against the "Skips:" statements in SKILL.md — if
   the methodology body and this validator drift apart, the check fails.

Usage: python scripts/workflow-check.py
All tests print PASS and exit 0; any failure prints FAIL and exits 1.
Note: on Windows consoles that garble text under GBK, set PYTHONIOENCODING=utf-8 first (this script already tries to force UTF-8 in main).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from report_lib import PHASE_RE, append_phase, close_report, resume_from

REPO = Path(__file__).resolve().parent.parent

# The skeleton's full phase set (report-template.md), in order.
PHASES = [
    "init",
    "positioning",
    "exploration",
    "plan",
    "isolation",
    "implementation",
    "quality-gate",
    "review",
    "verification",
    "summary",
    "merge",
]
PHASE_SET = set(PHASES)

# Channel -> mandatory executed phases + optionally-executed phases, derived from SKILL.md
# "Tiered Channels" (executed sets are the complement of the "Skips:" lists; 📋 lists exploration
# as optional, not as a skip). 🔴 executes every phase.
CHANNELS = {
    "🟢": {
        "executed": {"init", "positioning", "implementation", "quality-gate", "summary"},
        "optional": set(),
    },
    "🟡": {
        "executed": {"init", "positioning", "exploration", "implementation", "quality-gate", "review", "summary", "merge"},
        "optional": set(),
    },
    "🔴": {"executed": set(PHASES), "optional": set()},
    "📋": {"executed": {"init", "positioning", "review", "summary"}, "optional": {"exploration"}},
}


def skeleton() -> str:
    """The init-stage skeleton from report-template.md (init already DONE)."""
    lines = ["# Harness Task Report", "", "> **Final status**: 🔄 in progress", "", "---", ""]
    for phase in PHASES:
        marker = "<!-- PHASE: {} DONE -->".format(phase) if phase == "init" else "<!-- PHASE: {} -->".format(phase)
        lines.append(marker)
    return "\n".join(lines)


def run_lifecycle(channel: str, exploration: bool) -> str:
    """Walk the phases of `channel` in skeleton order: executed phases get stage content, skipped
    phases get a "(<channel> skipped)" DONE marker. Returns the final report text."""
    cfg = CHANNELS[channel]
    executed = set(cfg["executed"])
    if exploration and "exploration" in cfg["optional"]:
        executed.add("exploration")
    text = skeleton()
    for phase in PHASES:
        if phase == "init":
            continue  # already DONE in the skeleton
        content = "## Stage: {}\ncontent for {}".format(phase, phase) if phase in executed else "({} skipped)".format(channel)
        text = append_phase(text, phase, content)
    return text


def assert_well_formed(text: str, channel: str) -> None:
    """A finished report: every marker DONE, no out-of-order gaps, closable status line."""
    for m in PHASE_RE.finditer(text):
        assert m.group(0).endswith("DONE -->"), "{}: marker not closed: {}".format(channel, m.group(0))
    phase, anomalies = resume_from(text)
    assert phase == "<none>", "{}: incomplete stage remains: {}".format(channel, phase)
    assert anomalies == [], "{}: out-of-order anomalies: {}".format(channel, anomalies)
    closed = close_report(text, "✅ passed")
    assert "**Final status**: ✅ passed" in closed, "{}: status line did not close".format(channel)


def assert_channel_content(text: str, channel: str, exploration: bool) -> None:
    """Executed phases carry their content; skipped phases carry their skip marker."""
    cfg = CHANNELS[channel]
    executed = set(cfg["executed"])
    if exploration and "exploration" in cfg["optional"]:
        executed.add("exploration")
    for phase in PHASES:
        if phase == "init":
            continue
        if phase in executed:
            assert "content for {}".format(phase) in text, "{}: executed phase {} lost its content".format(channel, phase)
        else:
            assert "({} skipped)".format(channel) in text, "{}: skipped phase {} missing its skip marker".format(channel, phase)


def skill_skip_sets() -> dict[str, set[str]]:
    """Parse the 'Skips:' statements out of SKILL.md's tiered-channel rows. A channel row starting
    with the emoji and containing 'Skips:' yields the phase names up to the first delimiter."""
    text = (REPO / "SKILL.md").read_text(encoding="utf-8")
    result: dict[str, set[str]] = {}
    for channel in CHANNELS:
        # channel rows are markdown list items ("- 🟢 **Light**: ..."), so strip a leading "- " too
        row = next(
            (ln for ln in text.splitlines() if ln.lstrip(" \t-").startswith(channel) and "Skips:" in ln),
            None,
        )
        if row is None:
            continue
        m = re.search(r"Skips:\s*(.*)", row)
        raw = m.group(1).split("—", 1)[0].split("(", 1)[0].split(")", 1)[0].split(".", 1)[0]
        names = set(re.findall(r"[\w-]+", raw)) & PHASE_SET
        result[channel] = names
    return result


# ---- Test cases ----


def test_all_channels_lifecycle():
    for channel in CHANNELS:
        text = run_lifecycle(channel, exploration=False)
        assert_well_formed(text, channel)
        assert_channel_content(text, channel, exploration=False)
        print("  PASS  {} channel lifecycle ({} stages)".format(channel, len(PHASES)))


def test_findings_exploration_variants():
    # 📋 lists exploration as OPTIONAL (dispatch only when the review scope is unclear), so both
    # the exploration-executed and exploration-skipped lifecycles must be well-formed.
    with_exploration = run_lifecycle("📋", exploration=True)
    assert_well_formed(with_exploration, "📋")
    assert "content for exploration" in with_exploration, "📋 with exploration: exploration ran"
    without = run_lifecycle("📋", exploration=False)
    assert_well_formed(without, "📋")
    assert "(📋 skipped)" in without, "📋 without exploration: exploration recorded as skipped"


def test_skill_skip_set_cross_check():
    # The channel skip-sets encoded here must match SKILL.md's "Skips:" statements; if the
    # methodology body drifts (e.g. a phase added to a channel's skips in one place only), fail.
    skips = skill_skip_sets()
    for channel in CHANNELS:
        expected = PHASE_SET - CHANNELS[channel]["executed"] - CHANNELS[channel]["optional"]
        if not expected:
            assert channel not in skips, "{}: SKILL.md declares skips but the channel executes everything".format(channel)
        else:
            assert channel in skips, "SKILL.md has no 'Skips:' statement for {}".format(channel)
            assert skips[channel] == expected, (
                "{}: SKILL.md skips {} != encoded {}".format(
                    channel, sorted(skips[channel]), sorted(expected)
                )
            )


def main() -> int:
    # Windows consoles default to GBK and garble non-ASCII; force stdout to UTF-8 (ignore if unavailable)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    tests = [
        ("channel lifecycles (🟢/🟡/🔴/📋)", test_all_channels_lifecycle),
        ("findings-only exploration variants", test_findings_exploration_variants),
        ("channel skip-sets vs SKILL.md", test_skill_skip_set_cross_check),
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
