---
name: harness-coding-changelog
description: Release history for the harness-coding skill. Covers the v2 artifact-driven rewrite (SDD), the dispatch-protocol hardening, and the quality-gate scenario-adaptation pass (Gate N/A, incremental gates, coverage source, characterization baseline).
---

# Changelog

## v2.3.6 — 2026-11-17

Found by comparing the live v2.3.4 release against a local build of the same tag: the two zips differed by sha256 despite identical content. Byte-level root cause: `ZipInfo.create_system` defaults to the running platform (0 on Windows, 3 on Unix), so CI-built and Windows-built zips could never match. Diagnosis honesty note: a grep-based line-ending survey first pointed the wrong way; the byte-level Python audit (worktree / blob / zip entry all CRLF=0) disproved it before anything shipped (dist-packaging R5).

### Fixed

- **`create_system` pinned to 3 in `write_zip`** (build-dist.py): zip entry metadata no longer depends on the building platform; combined with the existing fixed timestamps / external_attr / forward-slash entries, same-content zips are expected to be byte-identical across machines. Locally executable check ships as AC-8 (infolist assertion); the final cross-machine proof lands by comparing the next tag-push build against a Windows build (residual variance: zlib's deflate output — hook recorded in the docstring)
- **Defensive CRLF→LF normalization in `build_bundle`/`verify_bundle`**: the bundle becomes independent of the working tree's line-ending state (byte-level audit 2026-11-17: every current tree, blob and zip is already LF-only, so this is a no-op today — recorded as such, not as the fix); the self-verification now compares against normalized source and asserts zero CRLF survived

### Changed

- dist-packaging chain continued per §12: AC-2/AC-3 carry supersede annotations re-pointing to AC-8; T7 landed; two new resolved review entries (R5 diagnosis honesty, R6 a briefly mis-edited historical T6 record caught and reverted within the round)
- SKILL.md `version: 2.3.6`

## v2.3.5 — 2026-11-17

Closes the design-intent gap the probe already covered: `find-skill.py` scans `~/.workbuddy/skills` (DEFAULT_ROOTS since v2.2.x), but `references/adapters/` shipped no workbuddy.md — the skill was designed for WorkBuddy yet not onboarded onto it.

### Added

- **`references/adapters/workbuddy.md`**: the fourth filled-in adapter, per `_adapter-template.md`, structured like the claude-code/opencode siblings. Maps the 7 required capabilities (Read / Write / Edit / Glob / Grep / Bash+PowerShell / AskUserQuestion — **batch native**, up to 4 questions per call) and the 4 mapped optional ones (Agent → Explore/general-purpose sub-agents / git-branch / command probe / WebSearch+WebFetch). Tool names verified against the **live WorkBuddy session authoring the adapter (2026-11-17)** — the strongest verification an adapter can carry
- WorkBuddy-specific deviations recorded (§7): directory reads → Glob; harness task tools may mirror but never replace artifact state; find_skill resolution order Skill/ToolSearch → probe → static table; sandbox escalation is an `ask_user` decision, never a silent way past a failed gate
- dogfood chain `specs/workbuddy-adapter/` (🟡) — the fifth chain under continuous artifact-check validation (specs/ now validates 5 chains: 3 🔴 + 2 🟡)

### Changed

- README directory-tree adapters comment (claude-code / codex / opencode / workbuddy / _template)
- SKILL.md `version: 2.3.5`. The bundle allowlist copies `references/**` wholesale, so the new adapter ships with no build-script change (verified in the build listing)

## v2.3.4 — 2026-11-17

Discharges scan-fixes Deferred D1 on the occasion it prescribed: the first tag-push release. The release workflow gets supply-chain hardening, then v2.3.4 becomes the first real tag cut — the CI run validates the workflow and the hardening in one go.

### Changed

- **Actions pinned to commit SHAs** (release.yml): `actions/checkout@11d5960a…` (v4.4.0), `actions/setup-python@a26af69…` (v5.6.0), `softprops/action-gh-release@3bb12739…` (v2.6.2). SHAs verified via `git ls-remote` against each action's official repository (TLS) — not search results; all three tags are lightweight, so the listed SHA is the commit. The verification method + date live as a comment in release.yml so the next upgrade repeats it
- **Runner Python pinned to 3.12** (was floating `"3.x"` — D1's suggested follow-up); stdlib-only scripts, no compatibility risk

### Closed

- scan-fixes Deferred D1 checked off with a completion annotation; the discharge is recorded as a third Intent Addition on the same 🟡 chain (§12), including the "which chain owns this" decision (R6: where recorded, not where the file lives)
- scan-fixes Gate Exemptions test-slot prose synced (8 → 9 artifact cases, missed in v2.3.3)

### Changed

- SKILL.md `version: 2.3.4`

## v2.3.3 — 2026-11-17

Second scan-fixes round (same 🟡 chain, §12 append): the five actionable findings from the 2026-11-17 external scan. The scan's sixth finding (CI action SHA pinning) is consciously left open — see Deferred D1.

### Fixed

- **Permission-hint script drift** (README install note + build-dist.py closing output): both hints listed only `artifact-check.py` and `derive-report.py` while `.claude/settings.json` / `opencode.json` actually allow three scripts — `find-skill.py` was missing; same drift class as the v2.2.8 opencode-adapter fix (review F7). Both hints now list all three and point to the config files as the source of truth
- **Commented-out ACs no longer count** (artifact-check.py): AC extraction ran `AC_RE` over the raw spec text, so AC lines inside a multi-line HTML comment block were collected as declared ACs and then flagged "is not covered by any task" — a comment is not a requirement. AC extraction now strips HTML comments first (the `without_comments` helper from the v2.2.8 GATE-NA fix — symmetric with it). New fixture `comment-ac` pins the regression (expect pass; under the old code it fails with the false "is not covered" errors on the commented AC-2/AC-3). Side effect (accepted, comment-ac R1): a task citing a commented AC now errors "references unknown AC-\<n\>" — desired strictness, same shape as the v2.3.1 malformed-line guard
- **Exit-code table incomplete** (find-skill.py docstring): exit 3 (`--fixtures` self-test failure) was returned but never documented — added
- **Validator error paths mixed separators** (artifact-check.py): on Windows the errors read `fixtures\broken\specs\broken/tasks.md` — `validate_task_dir` now normalizes paths via `as_posix()`
- **Docs drift**: README directory tree was missing `.github/workflows/release.yml` (added v2.3.2, mentioned in prose only); README fixture counts 8 → 9 (tree comment + verification block); design doc §11.3 fixture table gains the `comment-ac` row

### Left open (by design)

- `release.yml` pins actions by floating major tag instead of commit SHA — the SHAs cannot be verified offline and a wrong SHA breaks tag-push releases; recorded in scan-fixes Deferred D1 with the adoption condition (pin at the next release cut, verified against upstream)

### Changed

- SKILL.md `version: 2.3.3`; specs/scan-fixes gains its first Intent Additions paragraph (the §12 continuation drill now has a second real round)

## v2.3.2 — 2026-11-16

Discharges the repo's last consciously-open Deferred item: dist-packaging D1, the tag-push release CI. The workflow runs the exact commands the repo already validates by hand — no new tooling, no secrets.

### Added

- **`.github/workflows/release.yml`**: on `v*` tag push — fixture gates (artifact-check 8 cases + find-skill 4 cases) + specs validation, then the self-verifying reproducible build (`python scripts/build-dist.py`), then the zip is attached to the tag's GitHub Release via softprops/action-gh-release@v2 (`permissions: contents: write`). The bundle allowlist already excludes `.github/` — dev files cannot leak into the release artifact
- dist-packaging chain reopened per §12: AC-7 appended (append-only), T6 landed, Deferred D1 checked off

### Changed

- SKILL.md `version: 2.3.2`; README install section documents the GitHub Releases download path
- dist-packaging spec Non-goals carries a supersede annotation for the retired "no CI workflow" clause

## v2.3.1 — 2026-11-16

Fixes the two actionable issues from the 2026-11-16 external scan (the scan's other findings are consciously-recorded open items in their own chains): one stale cross-reference and one validator blind spot. Lands as the first 🟡 dogfood chain under specs/ (`scan-fixes`).

### Fixed

- **Stale docstring reference** (find-skill.py): "harness-coding contract #11" → "capability-contract §2 optional capability / SKILL.md §7" — the contract is organized §1–§6 and has no numbered item #11; same stale-reference class as the v2.2.3 adapter sweep
- **Malformed task lines now error** (artifact-check.py): a line shaped like a task (`- [x] T2: do stuff` — no `(AC-x)` reference block) was silently skipped by `check_task_file`: no "references no AC", no Output-evidence check, no AC↔T coverage participation. Lines matching the `- [<x>] T<n>` prefix but failing the full TASK_RE now report a "malformed task line" error (scope: Deferred D-lines and Review R-lines unaffected — spec A1 in the fixture). New fixture `malformed-task` pins the regression: expect fail + `err=` substring; under the old code it would have validated clean despite containing the broken line
- **Docs drift caught by the same scan**: design doc §11.3's probe-fixture list was missing short-query (added v2.2.9 — README was synced then, the design-doc line was not); the README specs/ tree comment was missing dist-packaging (added v2.3.0)

### Changed

- SKILL.md `version: 2.3.1` (line count and L0 description budget held); README fixture counts 7 → 8 in the tree comment and the verification block
- design doc §11.3 fixture table += `malformed-task` row
- specs/ gains its first 🟡 chain (`scan-fixes`) — `artifact-check.py specs/` now validates 4 chains (3 🔴 + 1 🟡)

## v2.3.0 — 2026-11-16

Adds the release mechanism the v2.2.9 .gitignore comment promised: one command packages the repo into a slim, installable skill bundle; dev-only files can never leak.

### Added

- **scripts/build-dist.py** (pure stdlib): allowlist copy of the runtime surface (SKILL.md + references/** + the three runtime scripts + LICENSE) into `dist/harness-coding/`, a byte-identical verification pass (every file compared to source; missing/extra tree check), and a reproducible release zip `dist/harness-coding-v<version>.zip` (version from SKILL.md frontmatter; fixed zip timestamps and forward-slash entries — two builds of the same tree produce the same sha256; `--no-zip` to skip). Safety: only `dist/harness-coding/` is ever cleaned, `--out` must resolve inside the repo, and the packager excludes itself — the blast radius of a misdirected `--out` is a stray subdir, not lost source. Prints the per-harness install paths on success
- dogfood chain `specs/dist-packaging/` — the third 🔴 sample under continuous artifact-check validation (specs/ now validates 3 chains)

### Changed

- SKILL.md `version: 2.3.0`; README install section documents the build command and the directory tree lists the new script

## v2.2.9 — 2026-11-16

Closes the three consciously-open edge cases from v2.2.8 (review-hardening Deferred D2) — the probe's short-query filter, the exit-2 diagnosis, and the stale .gitignore comment. Each fixed as observed, none as invented.

### Fixed

- **Probe short-query filter** (D2a): match terms of length >= 2 are kept ("go"/"py" are real skill names; the old `len(t) > 2` silently dropped them); if every term is filtered out but the query is non-empty, the raw query is used as a single term so 1-char queries still match. New probe fixture `short-query` proves the regression: a library findable only via its 2-char name returns exit 1 under the old filter, exit 0 now; probe `.expect` supports a per-case `query=` override
- **Exit-2 diagnosis split** (D2b): "no library found at all" and "N root(s) present but no parseable SKILL.md" now print distinct messages (exit code stays 2 — no usable library either way, so the fallback contract is unchanged); the operator can tell a missing library from a broken layout/frontmatter
- **Stale .gitignore comment** (D2c): the `harness-reports/` entry is kept but its comment no longer cites the removed v1 `report.dir` config — it now states the design-doc fact (v1 reports archived, unmigrated by design) and the removal condition; the unrelated uncommitted local `dist/` addition is untouched by this commit

### Changed

- SKILL.md `version: 2.2.9`; README probe-fixture count 3 → 4
- review-hardening Deferred D2 checked off (T15–T18)

## v2.2.8 — 2026-11-16

P3 sweep from the 2026-11-16 review (the review-hardening chain's Deferred D1) — nine small consistency fixes; three edge cases consciously left open (see Left open).

### Fixed

- **derive-report 🟡 view**: intent chains no longer print "(no task entries)" — the view now shows the intent's `Verify:` command and each Intent Additions bullet as verification entries (review F5)
- **Runner output wording**: `PASS fixtures: N artifact cases matched expectations (M non-artifact dir(s) skipped)` — skipped probe dirs are no longer counted as "matched" (review F13); README comment synced
- **Comment-located exemptions don't count**: GATE-NA scanning now strips HTML comments on both sides (declarations and usages) — a commented-out declaration can no longer satisfy the pairing; `broken`'s spec gains a commented trap line and its `err=` assertion guards the regression (review F14a)
- **Adapter/template doc drift** (review F7/F8/F9/F10): opencode §5 now lists the `find-skill.py` allowlist entry; claude-code adapter gains a "last verified" note (parity with codex/opencode); adapter template §4 gains the missing `find_skill` degradation row; the implementer dispatch's coverage line is now threshold-conditional ("never invent a number" parity)
- **Stale estimates & tree** (review F6/F12): design doc G4 / §5.1 / §7 line-count estimates annotated with actuals (validator/probe/view ≈ 246/201/107); README directory tree now lists `specs/`; this entry also records the previously unlogged README Chinese translation (commit e17de01, after v2.2.0)

### Left open (by design)

- Probe short-query filtering (terms ≤ 2 chars dropped), exit 2/1 semantics for a root with no parseable SKILL.md, and the v1-era `harness-reports/` .gitignore entry (entangled with an unrelated uncommitted local change) — recorded in review-hardening Deferred as known limitations

### Changed

- SKILL.md `version: 2.2.8`

## v2.2.7 — 2026-11-16

Review-driven self-consistency pass: the 2026-11-16 per-file review (27 files, all validation scripts re-run) surfaced 4 P2 gaps — all in the validator's own safety net, none in the methodology itself.

### Fixed

- **Exemption-section shape (3 files)**: the v2.2.5 normalization placed `## Gate Exemptions` before `Non-goals:` in the spec template and the gate-na fixture, structurally absorbing Non-goals into the section — both reordered (Non-goals first, exemptions last). The repo's own 🔴 sample `specs/dod-closure/spec.md` still used the pre-normalization inline `Gate Exemptions:` label — normalized to the `## Gate Exemptions` heading (the sample is the copy source future users will actually reach for)
- **Stale debt item**: dod-closure `D1` (multi-turn continuation drill) was completed as the v2.2.5 same-chain append (T7–T9, AC-9) but left unchecked — now checked off with a completion annotation
- **Fixture assertion granularity**: `.expect` gains optional `err=<substring>` lines, each required to appear in one of the reported error lines — `broken` now asserts all 5 error classes (6 error lines). Previously the case asserted only overall pass/fail, so a single silent check regression could hide behind other errors
- **🟡 pairing check was vacuous (real bug, found by the new fixture on its first run)**: for the intent channel, `check_gate_exemptions` scanned the full intent for declarations — the same text the usages live in, so every `GATE-NA(<gate>)` usage auto-declared itself and the pairing check could never fire (the v2.0.3 "full-text scan" fix widened the usage scan but left declarations unscoped). Intent declarations are now scoped to the `## Gate Exemptions` section. Two fixtures close the coverage gap symmetrically: `broken-intent-na` (undeclared usage → must error) and `intent-gate-na` (declared usage → must pass)

### Changed

- README: fixture count 5 → 7（输出计数 8 = 7 用例 + 1 个跳过的探针目录）; fixtures line notes the `err=` assertion format
- SDD-REFACTOR-DESIGN.md §11.3: fixture table synced (gate-na / broken-intent-na rows, per-error-class note, probe-fixtures note)
- New chain `specs/review-hardening/` (spec/plan/tasks) records this pass as a real 🔴 sample; dod-closure stays as the DoD-closure historical chain (AC-8 carries a supersede annotation for the count change)
- SKILL.md `version: 2.2.7`

## v2.2.6 — 2026-11-03

Full-sweep fixes: layered-loading budget compliance + orphaned L3 template.

### Fixed

- **L0 budget violation**: SKILL.md frontmatter description had grown to 105 words across v2.2.x (grill-me wiring, context-first wording), exceeding the §11.1 L0 budget (≤80 words, resident in every session). Trimmed to 76 words with the trigger vocabulary fully preserved (feature/fix/refactor/code review/schema change/changes files on disk, harness-agnostic, proactive trigger, ask-when-uncertain)
- **Orphaned L3 template**: `references/templates/output-contract.md` (the close-out reply contract) was referenced by nothing — unreachable under the layered-loading protocol, which requires upper layers to point to lower ones by path. SKILL.md §6 now carries the reference (per-channel depth + gate-evidence format)
- SDD-REFACTOR-DESIGN.md §10: L0–L3 evidence annotation updated with the word-budget re-check result

### Changed

- SKILL.md `version: 2.2.6`

## v2.2.5 — 2026-11-03

First same-chain continuation (§12 drill completed) + Gate N/A declaration-site normalization.

### Fixed

- **Gate N/A declaration-site drift**: the spec template and the gate-na fixture declared exemptions under an inline `Gate exemptions:` label, while capability-contract §3, all three adapters, the intent template, and SKILL.md §4 all reference a `## Gate Exemptions` section — a template-vs-docs naming drift introduced when v2.0.2 added the exemption protocol. Both now use the `## Gate Exemptions` heading; validation is unaffected (artifact-check full-text scans the spec), but copied-from-template artifacts now match the documented shape
- README verification comment: the fixtures run prints "6 cases matched expectations" (5 artifact cases + 1 skipped probe dir); the comment now says so instead of the stale "5 用例"

### Changed

- §10 of SDD-REFACTOR-DESIGN.md: the multi-turn chain drill item is now checked — this release is itself the first real same-slug continuation of `specs/dod-closure` (follow-up "check the skill again" appended as T7–T9 with AC-7–AC-10, append-only + one supersede annotation). §10 stands at 10/10
- SKILL.md `version: 2.2.5`

## v2.2.4 — 2026-11-03

DoD closure: the §10 acceptance checklist of SDD-REFACTOR-DESIGN.md is finally discharged — with the closure itself run as the project's first in-repo 🔴 dogfood drill.

### Added

- §10 acceptance record: 9/10 items checked with dated evidence. Machine assertions re-run green (`artifact-check.py --fixtures fixtures` 6/6; `find-skill.py --fixtures fixtures/skills` 3/3; SKILL.md 72 lines ≤ 80; `write_report` 0 hits). Manual drills covered by this release's own 🔴 chain `specs/dod-closure/`: clarification gate batch-asked once (3 fuzzy points, single round, answers → spec A1–A3 / plan AD-1–AD-2), merge decision rode ask_user, close-out re-verification re-ran both fixture suites, `derive-report.py` view derived to stdout, no report file written
- `specs/dod-closure/` artifacts committed as the repo's first real 🔴 sample (kept and re-validatable via `artifact-check.py specs/`)
- README verification block: probe self-test command added (`find-skill.py --fixtures fixtures/skills`)

### Left open (by design)

- §10 multi-turn chain drill (same-slug task append + channel-upgrade backfill, §12): stays unchecked until the first real follow-up requirement lands on an existing chain — honest gap, no synthetic simulation (user-confirmed); tracked as D1 in the chain's Deferred

### Changed

- SDD-REFACTOR-DESIGN.md frontmatter status: frozen → implemented (v2.0.0–v2.2.4); DoD verified 2026-11-03
- SKILL.md `version: 2.2.4`

## v2.2.3 — 2026-11-03

Post-release audit pass: stale section cross-references from the v2.2.0 renumbering.

### Fixed

- Adapter cross-references pointed at the wrong section after the v2.2.0 renumbering (which deleted the old §4 conditional-skill tables and shifted everything up): `opencode.md` said `see §6` four times where the target content lives in §7 Known Deviations (directory browsing via `tool.list`, read-before-overwrite, `ask_user` serial batch, subagent built-in tools only), and `codex.md` said `see §5` twice where the target lives in §6 Known Deviations (directory reads via `list_dir`, read-before-overwrite). `claude-code.md` was already correct. All six pointers now resolve to the Known Deviations section; `version: 2.2.3`

## v2.2.2 — 2026-11-03

Post-deployment audit pass: probe dedup + doc sync.

### Fixed

- `find-skill.py`: copies resolving to the same real path (junction/symlink aliases of one physical library, the now-recommended deployment) are counted once — previously every skill was listed twice and drift logic saw phantom duplicate roots. Drift detection across genuinely distinct directories is unchanged
- README: clarification gate now mentions the `grill-me` conditional-skill delegation (§2 parity); dropped the fragile SKILL.md line-count annotation; probe description notes dedup
- SKILL.md §7 static fallback wording aligned with sibling entries; `version: 2.2.2`

## v2.2.1 — 2026-11-03

Clarification-gate conditional skill wired in; deployment drift eliminated via junctions.

### Added

- Companion skill `grill-me` v1.0.0 (installed in `~/.agents/skills`): sharp-question **technique library** for the clarification gate — owns *how to ask* (decision-forcing, bounded questions with declared landing spots; ≤ 7 per batch; assumptions listed for veto), while the gate (SKILL.md §2) keeps *filtering* (assumption vs question) and *collection* (one round, answers → AC/AD)
- SKILL.md §2: clarification gate may delegate question drafting to a question-technique skill found via `find_skill`; §7 static fallback gains a `grill-me` row (clarification gate, 🟡/🔴 scope fuzzy); `version: 2.2.1`

### Fixed (deployment, outside the repo)

- Skill-library drift root-caused: `~/.claude/skills` is now a junction → `~/.agents/skills`, and `~/.agents/skills/harness-coding` is a junction → this git repo — single source of truth, both hosts always see the repo version (old v1.0.0/v2.1.0 copies kept as backups outside the library: `~/.claude/skills.bak-v1.0.0-20261103`, `~/.agents/skills-backups/`)
- `find-skill.py` probe re-verified post-fix: no drift warning, both hosts resolve `harness-coding` v2.2.x

## v2.2.0 — 2026-11-03

Skill-loading architecture: **context-first resolution**. The optional capabilities `find_skill` / `web_search` become semantic anchors resolved against the live conversation context; adapters no longer carry any skill-loading logic.

### Changed

- SKILL.md §7 rewritten: context-first resolution rule (the live tool list wins over adapter hints; deviations recorded) + the static conditional-skill table moves here from the adapters; `version: 2.2.0`
- Capability contract: `find_skill` = three-tier resolution (native skill mechanism → `scripts/find-skill.py` probe → explicit failure); degradation now distinguishes **library absent** (recorded as `skill library unavailable`, an environment flag) from **no match** (straight to the static table) — previously both degraded silently and indistinguishably
- Contract adds the context-first resolution principle: capability names are semantic anchors, never implementations; on conflict the live context wins

### Removed (from adapters)

- All `find_skill` capability-mapping rows (glob paths + frontmatter-read recipes). These were the only contract rows referencing **machine-local state** — and the documented copies had already drifted in deployment (a stale v1.0.0 copy shadowing the current v2.x in another location)
- §4 conditional-skill mapping tables from all three adapters and the template (content moved to SKILL.md §7); sections renumbered
- Kept deliberately: `web_search` rows — genuinely harness-specific setup knowledge (Codex `config.toml` flag, opencode MCP/curl fallback)

### Added

- `scripts/find-skill.py` (~210 lines): context-first fallback probe — scans standard skill-library locations (`~/.agents/skills`, harness dirs, project dirs), matches a query against frontmatter, and reports **same-name/version drift** (exit 0 hit / 1 no match / 2 no library). Verified live: flags the exact `harness-coding` v2.1.0-vs-v1.0.0 split observed in deployment
- `fixtures/skills/`: probe self-test (drift / no-drift / empty cases); `artifact-check.py --fixtures` now skips non-artifact fixture dirs instead of crashing on them
- Permission allowlists: `find-skill.py` added (opencode.json; `.claude/settings.json` restored — it had gone missing)

### Migration (custom adapters)

Delete your adapter's `find_skill` mapping row and §4 table. Harness-specific conditional skills worth keeping: either install them into the host's skill library (so the native mechanism / probe finds them) or keep an optional override note in the adapter — the default table lives in SKILL.md §7.

## v2.1.0 — 2026-10-24

**Full English pass** — all Chinese removed from the project (docs, templates, scripts, fixtures). Protocol-identifier change: **breaking for artifacts created under ≤2.0.x** (they fail validation until migrated).

### Changed (breaking for existing artifacts)

- Artifact protocol identifiers are now English: `需求:` → `Requirement:`, `意图:` / `验证:` → `Intent:` / `Verify:`, `输出:` → `Output:`, `## 门禁豁免` → `## Gate Exemptions`, `## 意图追加` → `## Intent Additions`, `## 特征测试基线` → `## Characterization baseline`
- `artifact-check.py` parses the English identifiers; error messages fully English
- `derive-report.py` output headings English (`Traceable view` / `Requirement` / `Change List` / `Verification Results` / `Remaining Risks (Deferred)`)
- All four artifact templates, all fixtures, and all docs (README, SDD design doc, CHANGELOG references) translated
- refactor-flow fixture now carries a baseline AC (AC-3) + matching task, making it a protocol-correct 🔴 refactor sample
- SKILL.md `version: 2.1.0`

### Migration

Artifacts created under ≤2.0.x: rename the protocol fields per the mapping above (or re-draft from the current templates); then `artifact-check.py specs/` must pass.

## v2.0.3 — 2026-10-24

Post-v2.0.2 consistency sweep: fixes the drift that pass introduced, plus two real gaps in the Gate N/A protocol. Non-breaking patch.

### Fixed

- **Explorer append/replace contradiction (7 files)**: the spec template's Background placeholder is **replaced**, but SKILL.md, contract §4, dispatch-explorer.md, all three adapters and the adapter template still said "append". All synchronized to replace.
- **SKILL.md §3 vs dispatch templates**: the Context step is now stated as `spawn_agent`-only with the inline-mode exception, matching the templates.
- **Gate N/A scope semantics**: declarations must state scope — chain-wide exemptions apply at close-out re-verification too; task-scoped ones do not (the full run still executes that gate). When in doubt, treat as task-scoped. Output-contract shows how exempted gates appear in the closing reply.
- **🟡 GATE-NA validation blind spot**: `check_gate_exemptions` now scans full artifact text (minus Deferred/Review), not just `T<n>` lines — intent-channel exemption usages can no longer escape the pairing check.
- `derive-report.py`: dropped the `-- .` path restriction so the diff is correct regardless of the caller's working directory.
- Version/frontmatter drift: SKILL.md `version: 2.0.3`; README fixture count (5), SKILL.md line count, explorer replace semantics, and the new gate mechanisms synced.

### Added

- plan template: characterization-baseline section (mandatory for behavior-preserving refactors, delete otherwise) — the baseline now has a concrete home.

## v2.0.2 — 2026-10-24

Quality-gate scenario adaptation + inline-mode dispatch fix. Non-breaking patch over v2.0.1.

### Fixed

- **Inline-mode dispatch contradiction**: the mandatory Context step (v2.0.1) now scopes to `spawn_agent` dispatches only — in inline mode the orchestrator already wrote/holds the artifacts, forcing it to re-read them was pure waste. All three dispatch templates carry the scope note.

### Added

- **Gate N/A protocol** (contract §3, spec/intent Gate Exemptions section, artifact-check pairing): a non-applicable gate is never silently skipped — declare `- GATE-NA(<gate>): <reason>` in the spec/intent, reference `GATE-NA(<gate>):` in the task output; `artifact-check.py` errors on an undeclared skip. Fixes the "modifying SQL forces type-check" overload.
- **Incremental per-task gates** (🟡/🔴): lint/format/type in full + affected test subset; full suite stays mandatory at close-out re-verification. Fixes the "5-task flow = 30 gate calls" time cost.
- **Coverage threshold source**: project-declared (e.g. `fail_under` in `pyproject.toml`), referenced in adapter gate tables; none declared → plain pass/fail, never invented. Fixes the "patch on an old codebase fails whole-repo coverage" deadlock.
- **Characterization-test baseline** for behavior-preserving refactors (🔴): plan must build the baseline first; one AC = "baseline tests pass unchanged". Closes the missing "behavior did not change" gate.
- `fixtures/gate-na`: legal-exemption case; `broken` gains an undeclared-exemption error (6 error classes now covered).

### Changed

- spec template: Background placeholder semantics clarified (explorer **replaces** the placeholder, not appends); gate-exemption section added; refactor AC requirement noted.
- `.gitattributes` added (`* text=auto eol=lf`) to stop CRLF churn on Windows.

## v2.0.1 — 2026-10-24

Dispatch-protocol hardening: close a real gap where a sub-agent could start work without reading the artifacts, missing already-confirmed assumptions/ACs/non-goals. Non-breaking patch over v2.0.0.

### Added

- **Mandatory Context step** at the head of all three dispatch templates (`dispatch-explorer.md` / `dispatch-implementer.md` / `dispatch-reviewer.md`): the sub-agent must `read` the relevant artifacts before any work, with role-differentiated targets:
  - explorer: `read specs/<slug>/spec.md` (Background still empty is expected, not an error)
  - implementer: `read` all three artifacts + same-layer same-shape files; task id must be present in `tasks.md` else refuse
  - reviewer: `read` all three artifacts + cross-check diff against the AC ids claimed; 📋 plan-validation reads the plan document directly
- SKILL.md §3 strengthened: explicit statement that context flows through artifacts, never through parent-session summaries — the `spawn_agent(role, prompt)` prompt carries only a task pointer + role discipline

### Why not summaries

Summaries are lossy (the model decides "what's key"), unverifiable (no machine check for completeness), and break context isolation by leaking parent-session content into the sub-agent's window. Artifacts are the single source of truth: structured, id-addressable (AC/T/R/D), and continuously fresh across continuation turns.

## v2.0.0 — 2026-10-24

Artifact-driven rewrite (SDD), per `SDD-REFACTOR-DESIGN.md` (frozen). Breaking change: the v1 reporting protocol and its reports are not migrated.

### Changed

- SKILL.md rewritten 174 → 61 lines: session classification + channel×artifact matrix + continuation protocol; methodology references only capability names
- Capability contract: 7 required (`write_report` deleted) + 5 optional — `find_skill` / `web_search` added, `run_quality_gate` removed, `ask_user` extended to batch `questions[]` with serial-round degradation
- Adapters slimmed: report config rows removed; `find_skill` / `web_search` mappings added; static conditional-skill table repurposed as the `find_skill` fallback; closing rule (open blocker/major blocks closing) declared
- Dispatch templates: roles get artifact homes (explorer → spec Background; implementer → tasks checkboxes with pasted output; reviewer → `## Review` section)

### Added

- Artifact layer: `specs/<slug>/` with `spec.md` / `plan.md` / `tasks.md` (🔴) and single-file `intent.md` (🟡); AC/T/R/D id conventions; Deferred = remaining risks as open checkboxes
- `scripts/artifact-check.py` (~170 lines): artifact schema, AC↔T closure, evidence-with-check, Review open-blocker closing guard; `--fixtures` runner
- `fixtures/`: 4 cases (fix-typo / add-validation / refactor-flow / deliberately broken) with `.expect` markers
- `scripts/derive-report.py`: on-demand traceable view from tasks + merge-base diff (stdout, never persisted)
- Clarification gate (assumptions vs questions, batch one-round ask) + info-gathering layer; continuation protocol (slug ownership, channel-upgrade backfill, AC append-only)
- Close-out re-verification (full gates before closing) and merge ask_user restored from v1 steps 8/10

### Removed

- The v1 reporting protocol state machine and its machinery: `scripts/report_lib.py`, `scripts/smoke-report.py`, `scripts/consistency-check.py`, `scripts/workflow-check.py`; `templates/write-report.md`, `templates/report-template.md`; runtime config `report.dir` / `report.prefix` / `report.on_disk`; per-task report versioning, collision guard, archive, inline-only mode

## v1.0.0 — 2026-08-20

Initial release of the universal harness-agnostic coding orchestration skill (MIT license).

### Added

- Session classification, tiered channels (🟢 light / 🟡 standard / 🔴 full / 📋 findings-only), role dispatch (explorer / implementer / reviewer), quality gates, and a five-section traceable report
- Capability contract (8 required + 4 optional capabilities) with adapter layers for Claude Code, opencode, and OpenAI Codex, plus an onboarding template
- Report protocol: per-task versioning, DONE phase markers, interruption recovery, archiving, inline-only mode, and same-task concurrent-init collision guard
- Validation scripts (pure standard library, zero third-party deps): `smoke-report.py`, `workflow-check.py`, `consistency-check.py`
- MIT license

### Fixed (review-driven hardening)

- `resume_from` misread hand-edited DONE markers carrying trailing whitespace as incomplete
- `append_phase` / `resume_from` could target report content that merely quoted a phase marker; matching is now anchored to standalone lines and fenced code blocks are skipped
- `truncate_agent` kept `#`-prefixed shell comments as "heading structure" at the expense of real content
- `claim_filename` accepted a report_dir missing its trailing slash and unsanitized (path-traversal) slugs; both are now normalized/rejected
- `emit_inline` close-only path dropped the explicit inline-only report marker
- Plan/design deliverables are mapped to the findings-only channel with an explicit plan-validation flow
- Multi-turn cross-channel intent escalation now closes the lower-channel report as abandoned and starts a fresh one at the new channel
- Channel-skip marker literal unified to the concrete `(<channel> skipped)` form; change-list literal unified to "none — findings-only"
- `ask_user` "required" semantics clarified for headless harnesses; degradation rows added to the adapter template and adapters
