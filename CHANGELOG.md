---
name: harness-coding-changelog
description: Release history for the harness-coding skill. Tracks the initial release and the review-driven hardening passes across the reporting protocol, adapters, and validators.
---

# Changelog

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
