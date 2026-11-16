# scan-fixes intent

Intent: Fix the two actionable issues from the 2026-11-16 external scan -- (1) find-skill.py's docstring cited "harness-coding contract #11", a numbering that does not exist in capability-contract.md (organized §1-§6 only; same stale-reference class as the v2.2.3 adapter sweep); re-pointed to "capability-contract §2 optional capability / SKILL.md §7". (2) artifact-check.py silently skipped task lines shaped like `- [x] T2: do stuff` (missing the `(AC-x)` reference block): no "references no AC" error, no Output-evidence check, no AC<->T coverage participation; check_task_file now reports a "malformed task line" error for `- [<x>] T<n>`-prefixed lines failing TASK_RE, pinned by the new `malformed-task` fixture (expect fail + err= substring). Also fixed the docs drift the scan surfaced: design doc §11.3 probe-fixture list was missing short-query (added v2.2.9), and the README specs/ tree comment was missing dist-packaging (added v2.3.0).
Verify: python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py

## Intent Additions
<!-- multi-turn continuation (§12): new requirements of the same task chain append here, each with a verify command -->
(none -- first pass)

## Gate Exemptions
<!-- a non-applicable gate must be declared here with a reason + scope, never skipped silently; artifact-check enforces the pairing -->
- GATE-NA(lint): repo defines no linter; the project-defined gates are the fixture suites -- scope: chain-wide
- GATE-NA(format): no formatter configured in this repo -- scope: chain-wide
- GATE-NA(type): stdlib-only scripts, no type checker configured -- scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites (8 artifact cases + 4 probe cases) plus specs validation plus the build's self-verification, run in full at close-out -- scope: chain-wide

## Deferred
<!-- remaining risks as open checkboxes: unchecked = not done -->
- (none -- the consciously-open items from the scan are already recorded in their own chains: dist-packaging D1, dod-closure R2)

## Review
<!-- where review conclusions land (§5.2); an open blocker/major makes closing illegal -->
- R1 [resolved]: (minor) the malformed-line guard could false-positive on sub-task numbering like `- [x] T2.1: ...` -- accepted deliberately: that shape is not in any template, and the guard's strictness is the point (A1 scope)
- R2 [resolved]: (minor) T1's evidence in the malformed-task fixture cites the fixture run that reports the fixture itself as FAIL -- that is the design (expectation-matched failure, run exits 0); wording reviewed for clarity
