# malformed-task spec

Requirement: the validator must flag task lines shaped like tasks but missing the full format, instead of silently skipping them
Background: the 2026-11-16 external scan found that a line like `- [x] T2: do stuff` (no `(AC-x)` reference block) escaped every task check in check_task_file -- no "references no AC" error, no Output-evidence check, no AC<->T coverage participation

Acceptance criteria:
<!-- each ID unique, written as an executable command where possible; AC are append-only, mark superseded entries when re-pointing (§12) -->
- AC-1: `python scripts/artifact-check.py --fixtures fixtures/` reports `[FAIL] fixture malformed-task (expect fail, got fail)` with a "malformed task line" error line, and the run exits 0 (expectation matched)

Assumptions:
<!-- low-risk self-decided parts of fuzzy scope (§5.3 clarification-gate output) -->
- A1: only lines matching the `- [x] T<n>` prefix trigger the malformed-line guard; Deferred D-lines and Review R-lines are intentionally out of scope (they carry their own shapes and checks)

Non-goals: no changes to the .expect format, the task-line format itself, or any other validator check

## Gate Exemptions
<!-- a non-applicable gate must be declared here with a reason + scope, never skipped silently (contract §3 Gate N/A protocol); tasks reference it via GATE-NA(<gate>):, artifact-check enforces the pairing -->
- GATE-NA(lint): repo defines no linter; the project-defined gates are the fixture suites -- scope: chain-wide
- GATE-NA(format): no formatter configured in this repo -- scope: chain-wide
- GATE-NA(type): stdlib-only scripts, no type checker configured -- scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites plus specs validation, run in full at close-out -- scope: chain-wide
