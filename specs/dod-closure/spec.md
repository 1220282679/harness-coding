# dod-closure spec

Requirement: Close the SDD-REFACTOR-DESIGN.md §10 DoD loop — check off acceptance items with dated evidence, running this closure itself as a real 🔴 dogfood drill.

Background: §10 has stayed unchecked since v2.0.0 (2026-10-24) even though machine assertions pass. The 2026-11-03 audit confirmed the doc set is consistent (only stale cross-refs, fixed in v2.2.3). Closing the loop now doubles as the project's first in-repo 🔴 sample.

Acceptance criteria:
- AC-1: `python scripts/artifact-check.py --fixtures fixtures` reports all cases matched expectations (broken errors as designed)
- AC-2: `python scripts/find-skill.py --fixtures fixtures/skills` reports 3 PASS (drift / no-drift / empty)
- AC-3: SKILL.md ≤ 80 lines, and `grep -rn write_report` over SKILL.md / references/ / scripts/ / fixtures/ has 0 hits
- AC-4: SDD-REFACTOR-DESIGN.md §10 items carry checkmarks + dated evidence; frontmatter status reflects implemented + accepted
- AC-5: README verification block includes the probe self-test command, added with zero new files
- AC-6: SKILL.md `version: 2.2.4` + CHANGELOG entry; both fixture suites re-run green at close-out <!-- satisfied at the 2026-11-03 first close-out; superseded for later releases by AC-10 -->
- AC-7: spec template and gate-na fixture declare exemptions under a `## Gate Exemptions` heading (matching capability-contract §3, the three adapters, and the intent template); artifact-check fixtures stay green
- AC-8: README fixture-count comment matches the runner's actual output semantics (5 artifact cases + 1 skipped probe dir = "6 cases matched") <!-- satisfied at the v2.2.5 close-out; count superseded by review-hardening AC-1 (v2.2.7: 7 artifact cases + 1 skipped = 8) -->
- AC-9: SDD-REFACTOR-DESIGN.md §10 multi-turn item checked with this append as real evidence — §10 stands at 10/10
- AC-10: SKILL.md `version: 2.2.5` + CHANGELOG entry; both fixture suites re-run green at this close-out <!-- satisfied at the v2.2.5 close-out; superseded for later releases by AC-13 -->
- AC-11: SKILL.md L0 description ≤ 80 words (design §11.1 L0 budget), preserving the trigger vocabulary (feature/fix/refactor/code review/schema change/changes files on disk)
- AC-12: `references/templates/output-contract.md` is referenced from SKILL.md §6 (close-out) so the L3 reply contract is discoverable per the layered-loading protocol
- AC-13: SKILL.md `version: 2.2.6` + CHANGELOG entry; both fixture suites re-run green at this close-out

Assumptions:
- A1: drill artifacts under `specs/dod-closure/` are committed to the repo as the first real 🔴 sample (user-confirmed 2026-11-03)
- A2: the multi-turn continuation drill stays open honestly — no synthetic simulation (user-confirmed 2026-11-03); recorded in CHANGELOG
- A3: the release commit is pushed to origin after close-out (user-confirmed 2026-11-03)
- A4: the follow-up "check the skill again" request (2026-11-03) is a same-chain requirement per §12 (topic continuous with the DoD closure) → appended here as new tasks, not a new slug; its release follows A3 (commit + push)

Non-goals: no methodology changes; no script code changes; no migration of historical artifacts.

## Gate Exemptions
- GATE-NA(lint): repo defines no linter for markdown-only changes; this repo's project-defined gates are the fixture suites — scope: chain-wide
- GATE-NA(format): no formatter configured for markdown in this repo — scope: chain-wide
- GATE-NA(type): python scripts untouched, no type surface changed — scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites (AC-1/AC-2), run in full at close-out — scope: chain-wide
