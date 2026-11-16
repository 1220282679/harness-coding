# review-hardening spec

Requirement: Fix the 4 P2 findings from the 2026-11-16 per-file review — normalize the Gate Exemptions section shape (spec template, gate-na fixture, dod-closure spec), upgrade fixture assertions to per-error-class, close the 🟡 exemption-pairing coverage gap — plus the stale D1 debt item in dod-closure.

Background: The 2026-11-16 external review (27 files read, all validation scripts re-run) found: the v2.2.5 exemption-heading normalization squeezed `Non-goals:` into the `## Gate Exemptions` section in the spec template and gate-na fixture, and missed the repo's own dogfood spec (specs/dod-closure/spec.md:30 still inline); `broken`'s `.expect` asserts only overall pass/fail, so a single silent check regression is invisible; the 🟡 GATE-NA pairing check (v2.0.3) had no fixture coverage; dod-closure D1 was completed in v2.2.5 but left unchecked.

Acceptance criteria:
- AC-1: `python scripts/artifact-check.py --fixtures fixtures` → PASS fixtures: 8 cases matched expectations (7 artifact cases: broken with all 5 err= per-class assertions matched, broken-intent-na failing as designed, intent-gate-na passing; +1 skipped probe dir) <!-- satisfied at the v2.2.7 close-out; runner output wording superseded by AC-8 (v2.2.8) -->
- AC-2: `python scripts/find-skill.py --fixtures fixtures/skills` → 3 PASS (drift / empty / no-drift)
- AC-3: `python scripts/artifact-check.py specs/` → PASS on specs\dod-closure and specs\review-hardening
- AC-4: `Non-goals:` precedes `## Gate Exemptions` in references/templates/spec.md and fixtures/gate-na/specs/gate-na/spec.md (section shape normalized)
- AC-5: specs/dod-closure/spec.md declares exemptions under a `## Gate Exemptions` heading (no inline `Gate Exemptions:` label left)
- AC-6: specs/dod-closure/tasks.md D1 is checked with a completion annotation referencing the v2.2.5 append
- AC-7: SKILL.md `version: 2.2.7` + CHANGELOG entry; README fixture-count comment matches the runner output (8 = 7 + 1); design doc §11.3 lists all 7 artifact cases <!-- satisfied at the v2.2.7 close-out; release tracking superseded by AC-13 (v2.2.8) -->
- AC-8: `python scripts/artifact-check.py --fixtures fixtures` → PASS fixtures: 7 artifact cases matched expectations (1 non-artifact dir skipped) — skipped probe dirs no longer counted as "matched" (v2.2.8)
- AC-9: `python scripts/derive-report.py fixtures/add-validation/specs/add-validation` → Verification Results shows "intent verify:" + "intent addition:" entries (no "(no task entries)")
- AC-10: opencode adapter §5 lists `scripts/find-skill.py`; claude-code adapter carries a version note; adapter template §4 includes the `find_skill` row; implementer dispatch coverage line is threshold-conditional
- AC-11: design doc G4/§5.1/§7 estimates annotated with actuals; README tree lists `specs/`
- AC-12: GATE-NA scanning strips HTML comments on both sides — broken spec's commented declaration trap does not satisfy the pairing (the undeclared-exemption error persists; guarded by its `err=declares no matching` assertion)
- AC-13: SKILL.md `version: 2.2.8` + CHANGELOG entry; both fixture suites + specs validation re-run green at close-out <!-- satisfied at the v2.2.8 close-out; release tracking superseded by AC-17 (v2.2.9) -->
- AC-14: `python scripts/find-skill.py --fixtures fixtures/skills` → 4 PASS including short-query (query=go, library findable only via its 2-char name — under the old len(t) > 2 filter this case would return exit 1) <!-- v2.2.9, D2a -->
- AC-15: `find-skill.py "x" --root <empty-dir>` prints "1 skill-library root(s) present but no parseable SKILL.md..." and exits 2; `--root <nonexistent>` prints "no skill library found in any standard location" and exits 2 — same code, distinct diagnosis <!-- v2.2.9, D2b -->
- AC-16: .gitignore's harness-reports/ comment no longer cites the removed v1 report.dir config; the entry itself is kept (v1 reports stay archived/unmigrated by design); the unrelated local dist/ addition is not in this commit <!-- v2.2.9, D2c -->
- AC-17: SKILL.md `version: 2.2.9` + CHANGELOG entry; both fixture suites + specs validation re-run green at close-out <!-- v2.2.9 -->

Assumptions:
- A1: this review-driven pass opens a new chain (review-hardening) instead of appending to dod-closure — the topic (validator self-consistency from an external review) is distinct from the DoD-closure chain per §12
- A2: normalizing dod-closure's own spec format does not violate AC append-only — the constraint guards AC semantics, not section formatting

Non-goals: no P3 fixes (recorded as Deferred); no methodology changes; no find-skill.py / derive-report.py changes; no commit/push (left to the user) <!-- scope extended by user request in v2.2.8 (P3 sweep, T8–T14) and v2.2.9 (Deferred D2 close-out, T15–T18); v2.2.9 does commit (push explicitly deferred by the user) -->

## Gate Exemptions
- GATE-NA(lint): repo defines no linter for markdown/python changes; the project-defined gates are the fixture suites — scope: chain-wide
- GATE-NA(format): no formatter configured in this repo — scope: chain-wide
- GATE-NA(type): stdlib-only scripts, no type checker configured; validator behavior is covered by the fixture suites — scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites (AC-1/AC-2), run in full at close-out — scope: chain-wide
