# scan-fixes intent

Intent: Fix the two actionable issues from the 2026-11-16 external scan -- (1) find-skill.py's docstring cited "harness-coding contract #11", a numbering that does not exist in capability-contract.md (organized §1-§6 only; same stale-reference class as the v2.2.3 adapter sweep); re-pointed to "capability-contract §2 optional capability / SKILL.md §7". (2) artifact-check.py silently skipped task lines shaped like `- [x] T2: do stuff` (missing the `(AC-x)` reference block): no "references no AC" error, no Output-evidence check, no AC<->T coverage participation; check_task_file now reports a "malformed task line" error for `- [<x>] T<n>`-prefixed lines failing TASK_RE, pinned by the new `malformed-task` fixture (expect fail + err= substring). Also fixed the docs drift the scan surfaced: design doc §11.3 probe-fixture list was missing short-query (added v2.2.9), and the README specs/ tree comment was missing dist-packaging (added v2.3.0).
Verify: python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py

## Intent Additions
<!-- multi-turn continuation (§12): new requirements of the same task chain append here, each with a verify command -->

### 2026-11-17 second external scan (v2.3.3)

Intent: Fix the five findings from the 2026-11-17 external scan -- (1) the permission hints in README (install note) and build-dist.py's closing output listed only artifact-check.py and derive-report.py while `.claude/settings.json` / `opencode.json` actually allow three scripts (find-skill.py missing) -- the same drift class v2.2.8 fixed in the opencode adapter (review F7); both hints now list all three and state the config files are the source of truth. (2) The README directory tree was missing `.github/workflows/release.yml` (added v2.3.2; mentioned in prose once, never in the tree). (3) artifact-check.py collected acceptance criteria from the raw spec text, so AC lines inside a multi-line HTML comment block were declared ACs and then flagged "not covered by any task" -- comment-stripping now applied to AC extraction (the without_comments helper from the v2.2.8 GATE-NA fix), symmetric with that fix; pinned by the new `comment-ac` fixture (expect pass; under the old code it fails with the false "is not covered" error on the commented AC-2/AC-3). (4) find-skill.py's docstring exit-code table omitted exit 3 (--fixtures self-test failure); documented. (5) Validator error paths mixed Windows backslashes with forward slashes (`fixtures\broken\specs\broken/tasks.md`) -- validate_task_dir now normalizes via as_posix(). The scan's sixth finding (release.yml pins actions by floating major tag instead of commit SHA) is NOT changed: the correct SHAs cannot be verified offline and a wrong SHA breaks the release CI; recorded as Deferred D1 with the adoption condition.
Verify: python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py

### 2026-11-17 D1 discharge (v2.3.4)

Intent: Discharge this chain's Deferred D1 -- pin release.yml's actions to commit SHAs instead of floating major tags, and fix the runner Python to a minor version. SHAs verified against each action's official repository via `git ls-remote` (TLS) rather than search results: actions/checkout v4.4.0 = 11d5960a326750d5838078e36cf38b85af677262, actions/setup-python v5.6.0 = a26af69be951a213d495a4c3e4e4022e16d87065, softprops/action-gh-release v2.6.2 = 3bb12739c298aeb8a4eeaf626c5b8d85266b0e65 (all three tags lightweight -- the listed SHA is the commit; the file's 6 `^{}` lines belong to older annotated tags of gh-release, v2.6.2 has none). The verification method and date are recorded as a comment in release.yml itself so the next upgrade can repeat it. python-version pinned to "3.12" (D1's suggested follow-up). The discharge doubles as the first real tag-push of the release workflow: v2.3.4 is the first tag cut after the pinning, so the CI run validates both the workflow and its supply-chain hardening in one go.
Verify: python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py

## Gate Exemptions
<!-- a non-applicable gate must be declared here with a reason + scope, never skipped silently; artifact-check enforces the pairing -->
- GATE-NA(lint): repo defines no linter; the project-defined gates are the fixture suites -- scope: chain-wide
- GATE-NA(format): no formatter configured in this repo -- scope: chain-wide
- GATE-NA(type): stdlib-only scripts, no type checker configured -- scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites (9 artifact cases + 4 probe cases) plus specs validation plus the build's self-verification, run in full at close-out -- scope: chain-wide

## Deferred
<!-- remaining risks as open checkboxes: unchecked = not done -->
<!-- first pass carried no Deferred (its consciously-open items live in their own chains: dist-packaging D1 -- discharged v2.3.2, dod-closure R2) -->
- [x] D1: release.yml pins actions by floating major tag (`@v4`/`@v5`/`@v2`, `python-version: "3.x"`) instead of commit SHA -- a supply-chain hardening item, consciously left open: the correct SHAs cannot be verified offline and a wrong SHA silently breaks tag-push releases; suggested follow-up: pin each action to its commit SHA (verified against the upstream repo) the next time a release is cut, and consider a fixed minor Python version <!-- discharged v2.3.4 (2026-11-17): SHAs verified via git ls-remote against the official repos, python pinned to 3.12; see the "D1 discharge" Intent Addition -->

## Review
<!-- where review conclusions land (§5.2); an open blocker/major makes closing illegal -->
- R1 [resolved]: (minor) the malformed-line guard could false-positive on sub-task numbering like `- [x] T2.1: ...` -- accepted deliberately: that shape is not in any template, and the guard's strictness is the point (A1 scope)
- R2 [resolved]: (minor) T1's evidence in the malformed-task fixture cites the fixture run that reports the fixture itself as FAIL -- that is the design (expectation-matched failure, run exits 0); wording reviewed for clarity
- R3 [resolved]: (minor) comment-stripping on AC extraction also stops commented ACs from being referenceable targets -- a task citing a commented AC now errors "references unknown AC-<n>"; accepted deliberately (same strictness shape as the v2.3.1 malformed-line guard, pinned in comment-ac R1)
- R4 [resolved]: (minor) the scan-fixes intent's first-pass Deferred placeholder ("none") needed replacing rather than appending when D1 arrived -- placeholder semantics kept simple: an explicit "(none)" line is replaced, real entries are never silently dropped
- R5 [open|minor]: README fixture-count prose now says 9 artifact cases while fixture dirs total 10 (9 artifact + 1 probe dir skipped) -- wording already disambiguates ("另有 1 个非产物探针目录跳过"), recorded only
- R6 [resolved]: (minor) the D1 discharge reuses the scan-fixes chain rather than dist-packaging (which owns the release workflow, AC-7) -- kept where the item was recorded ("consciously-open items live in their own chains" cuts both ways); dist-packaging's AC set is unchanged, its workflow file simply got hardened
