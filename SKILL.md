---
name: harness-coding
version: 2.5.0
license: MIT
description: Turn a one-line coding request into a controlled change flow. Use when the user asks for a feature, a fix, a refactor, a review, a schema change, or any on-disk change: classify intent, pick a channel (light/standard/full/findings-only), clarify fuzzy scope, dispatch explorer/implementer/reviewer, enforce quality gates, and close out from markdown artifacts (spec/plan/tasks) — never a report file. Harness-agnostic; trigger proactively; ask rather than guess.
---

# harness-coding — Artifact-Driven Coding Orchestrator (v2)

Capability names only; `references/capability-contract.md` is the source of truth for each one's signature and degradation rule.

## 0. Load Protocol

Read **this file only** at load. Fetch the rest at the step that needs it; never re-read what is already in context.

- adapter, before the first `run_command` — approval rules, probe order, gate table; never an adapter for a harness you are not on
- `capability-contract.md` §3 at the first gate (§5 only on degradation)
- `flow.md` at the clarification gate and at close-out (🟡/🔴)
- `conditional-skills.md` only when `find_skill` misses

## 1. Classify (mandatory first action)

| Condition | Verdict |
|-----------|---------|
| Code / bug / feature / refactor / tests / schema / review with Findings / any on-disk action | **work task** → §2 |
| Q&A, consultation, informal read-only look, no deliverable | **non-work** → answer, stop |
| Cannot tell whether files will change | **unclear** → ask "do we do it?"; never guess |

Record `<verdict> — verb: <…>; noun: <…>; deliverable: <yes/no>`. Headless (no `ask_user`) → most conservative option, recorded; never claim a confirmation you did not get.

## 2. Flow Routing (single source of flow truth)

| Channel | When | Artifacts | Flow |
|---------|------|-----------|------|
| 🟢 light | one file, obvious, no design call | **zero files** | implement → lint/format |
| 🟡 standard | one-paragraph intent, several files | `intent.md` | locate → clarify → implement → gates → review → re-verify |
| 🔴 full | feature / schema / API / refactor, or needs a plan and a reviewer | `specs/<slug>/{spec,plan,tasks}.md` | info → spec → clarify → plan → per-task → review → re-verify |
| 📋 findings-only | the verdict is the deliverable | spec/plan **is** the deliverable | locate → review → verdict |

**Hard constraints**: 🟢 creates zero files; 🔴 produces all three artifacts; an AC is **only added, never rewritten** (supersede by re-pointing).

- **Clarification gate** (🟡/🔴, fuzzy): Assumptions (`A-<n>`, self-decided, logged) vs Questions (one `ask_user` round, never serial); answers → AC/AD. Architecture calls (new port / event / table schema / aggregate behavior) always ask.
- **Continuation is bounded**: follow-ups append tasks, but each phase boundary is a checkpoint and ~60 turns is the ceiling — then hand over to a fresh session, same slug, artifacts carrying the context.
- Unrelated topic or explicit "new task" → new slug; never append into another chain's artifacts.

Detail and edge cases: `references/flow.md`.

## 3. Roles (`spawn_agent` optional → orchestrator plays the role inline)

explorer: read-only recon → orchestrator **replaces** the Background placeholder in `spec.md`. implementer: lands code + tests, checks off tasks with pasted gate output. reviewer: graded findings → `## Review` in `tasks.md`. **An open blocker/major makes closing illegal.** The orchestrator never writes the large implementation or tests itself.

**Context flows through artifacts, never through parent-session summaries** — a dispatch carries a task pointer, the sub-agent reads the artifacts. Per-role discipline: `references/templates/dispatch-*.md`.

## 4. Quality Gates (`run_command`)

lint → format → type → test, fixed order, commands from the adapter's gate table. Evidence pasted, never from memory; failure → root cause → fix → re-run. Per-task green ≠ repo green. 🟢: lint + format mandatory, type/test on demand with the reason recorded.

Per-task (🟡/🔴): lint/format/type in full + the **affected test subset**; the full suite belongs to close-out. **Gate N/A is never a silent skip**: declare `- GATE-NA(<gate>): <reason + scope>` under `## Gate Exemptions` in spec/intent and cite it in the task output — the pairing is enforced. Coverage source, scope semantics, refactor baseline: `references/capability-contract.md` §3.

## 5. Artifacts & Validation

Templates: `references/templates/{spec,plan,tasks,intent}.md`. Every checked task carries `Output:` (pasted evidence). `## Deferred` = remaining risks as open checkboxes. Validate before closing: `python scripts/artifact-check.py specs/`.

## 6. Close-out

Derived from artifacts + diff, never from memory: requirement positioning / verification evidence / remaining risks (open Deferred). Reply contract: `references/templates/output-contract.md`. On-demand trace: `python scripts/derive-report.py specs/<slug> [--base <ref>]` (stdout only — **no report file is ever written**).

## 7. Conditional Capabilities (context-first)

`find_skill` / `web_search` are **anchors, not implementations**: resolve each against the tools present, native mechanism first; adapter rows are hints and the live context wins (record any deviation). `web_search` → cite source + time, AC stays locally executable; no tool → `not verified online` in Assumptions.

`find_skill` miss → `scripts/find-skill.py "<query>"` probes the standard library locations (exit 2 = no library → `skill library unavailable`), then the static table: `references/conditional-skills.md`.

## 8. Session Discipline

An approval or a re-read rewrites the prompt prefix; everything behind it stops hitting the cache. Load-bearing, not tidiness.

| Never | Instead |
|-------|---------|
| Improvise a command, retype the gate, compose a one-off | the adapter's gate entry verbatim — pre-approved, ≤3 approvals per session |
| Nest shells (`bash -c "…"`, `powershell -Command "…"`) | call the entrypoint directly; nesting mints a new prefix |
| Re-declare encoding / error policy / `cd` / `export` per call | bake it into the entrypoint script |
| Pile steps with `;` / `&&` | one command, one job |
| Read `AGENTS.md` / `CLAUDE.md` | already injected — never read it |
| Re-read a file to confirm one checkbox | `grep` the location, read a line range |
| Load a 300-line `tasks.md` | split into `tasks/T0<n>.md`, read the active one |
| Exceed ~12 tool calls in a turn | checkpoint and yield |
| Dump a whole file to inspect it | locate first, then read the range |
| Push past ~100k context or a phase boundary | write state back to `tasks.md`/`plan.md`, continue fresh |
