# dod-closure tasks

- [x] T1 (AC-1, AC-2): run both fixture suites and capture gate evidence; Output: `artifact-check.py --fixtures fixtures` → PASS fixtures: 6 cases matched expectations (broken errors as designed); `find-skill.py --fixtures fixtures/skills` → PASS: drift / empty / no-drift (3/3)
- [x] T2 (AC-3): verify L1 size budget and write_report residue; Output: `wc -l SKILL.md` → 72; `grep -rn write_report SKILL.md references/ scripts/ fixtures/` → 0 hits (exit 1)
- [x] T3 (AC-5): add probe self-test line to README verification block (🟢 sub-change, zero new files); Output: README verification block now carries `find-skill.py --fixtures fixtures/skills`; 1 file modified, 0 new files (the specs/dod-closure artifacts belong to this 🔴 chain, not the 🟢 sub-change); markdown-only change → GATE-NA(lint) / GATE-NA(format) declared chain-wide in spec
- [x] T4 (AC-4): check off §10 items with dated evidence; update frontmatter status; Output: §10 → 9/10 checked with 2026-11-03 evidence annotations, multi-turn drill left open per A2; frontmatter status → "implemented (v2.0.0–v2.2.4); design frozen 2026-10-23; DoD verified 2026-11-03"
- [x] T5 (AC-6): bump SKILL.md to 2.2.4 and add CHANGELOG entry; Output: SKILL.md `version: 2.2.4`; CHANGELOG v2.2.4 entry with Added / Left open / Changed sections
- [x] T6 (AC-6): close-out re-verification (full fixture suites) + derive-report view; Output: both suites re-run green (6/6 + 3/3) and `artifact-check.py specs/` → PASS on specs\dod-closure; `derive-report.py specs/dod-closure --base HEAD` derived the traceable view to stdout; GATE-NA(type) / GATE-NA(test) declared chain-wide (test slot fulfilled by the fixture suites); git status shows no report file

- [x] T7 (AC-7): normalize the exemption declaration to a `## Gate Exemptions` heading in the spec template and the gate-na fixture; Output: references/templates/spec.md and fixtures/gate-na/specs/gate-na/spec.md now use `## Gate Exemptions`; grep confirms capability-contract §3 + 3 adapters + intent template + SKILL.md §4 all reference the same name
- [x] T8 (AC-8): align the README fixture-count comment with the runner's actual output; Output: comment now reads "5 个产物用例全部符合预期（broken 预期报错；输出计数 6 = 5 用例 + 1 个跳过的探针目录）"; runner output "PASS fixtures: 6 cases matched expectations"
- [x] T9 (AC-9, AC-10): check the §10 multi-turn item (10/10), bump to 2.2.5, CHANGELOG, close-out re-verify; Output: §10 multi-turn item checked with this append as evidence; SKILL.md `version: 2.2.5`; CHANGELOG v2.2.5 entry; close-out: `artifact-check.py --fixtures fixtures` → 6 cases matched, `find-skill.py --fixtures fixtures/skills` → 3 PASS, `artifact-check.py specs/` → PASS; GATE-NA(lint) / GATE-NA(format) / GATE-NA(type) / GATE-NA(test) declared chain-wide in spec (test slot fulfilled by the fixture suites)

- [x] T10 (AC-11): trim the SKILL.md L0 description to ≤80 words, keeping trigger vocabulary; Output: 105 words → 76 words (`sed -n 5p SKILL.md | wc -w` minus the `description:` key); all trigger terms retained (feature/fix/refactor/code review/schema change/changes files on disk, harness-agnostic, proactive, ask-when-uncertain)
- [x] T11 (AC-12): reference the output-contract template from SKILL.md §6; Output: §6 now carries "Reply contract: `references/templates/output-contract.md` (per-channel depth + gate-evidence format)"; SKILL.md still 72 lines (inline addition, no new lines)
- [x] T12 (AC-13): bump to 2.2.6, CHANGELOG, close-out re-verify; Output: SKILL.md `version: 2.2.6`; CHANGELOG v2.2.6 entry; close-out: `artifact-check.py --fixtures fixtures` → 6 cases matched, `find-skill.py --fixtures fixtures/skills` → 3 PASS, `artifact-check.py specs/` → PASS; GATE-NA(lint) / GATE-NA(format) / GATE-NA(type) / GATE-NA(test) declared chain-wide in spec (test slot fulfilled by the fixture suites)

## Deferred
- [ ] D1: multi-turn continuation drill (same-slug task append + channel-upgrade backfill, §12) — trigger: the first real follow-up requirement landing on an existing chain; suggested follow-up: run it then and check the §10 item

## Review
- R1 [resolved]: README verification block lacked the probe self-test command (found in the 2026-11-03 audit) → fixed in T3
- R2 [open|minor]: the "onboarding passes first try" sub-criterion inside the §10 write_report item cannot be fully exercised without a real second harness — recorded here; converts to Deferred only if it ever blocks
