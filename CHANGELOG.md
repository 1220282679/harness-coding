---
name: harness-coding-changelog
description: Release history for the harness-coding skill. Tracks the initial release and the review-driven hardening passes across the reporting protocol, adapters, and validators.
---

# Changelog

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
