---
name: harness-coding-changelog
description: Release history for the harness-coding skill. Covers the v2 artifact-driven rewrite (SDD), the dispatch-protocol hardening, and the quality-gate scenario-adaptation pass (Gate N/A, incremental gates, coverage source, characterization baseline).
---

# Changelog

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
