---
name: harness-coding
version: 2.3.0
license: MIT
description: Turn a one-line coding request into a controlled change flow. Use when the user asks for a new feature, a fix, a refactor, code review, a schema change, or any task that changes files on disk — classify intent, pick a channel (light/standard/full/findings-only), clarify fuzzy scope, dispatch roles (explorer/implementer/reviewer), enforce quality gates, and close out with a traceable summary derived from markdown artifacts (spec/plan/tasks) — no report files. Harness-agnostic; trigger proactively; ask before deciding when uncertain.
---

# harness-coding — Artifact-Driven Coding Orchestrator (v2)

Methodology decoupled from the harness: this body uses only capability names (required: `read` / `write` / `edit` / `glob` / `grep` / `run_command` / `ask_user`; optional: `spawn_agent` / `create_branch` / `check_command` / `find_skill` / `web_search` — each with a degradation rule). On load: read `references/capability-contract.md` (L2) and the current harness's adapter in `references/adapters/` (generate from `_adapter-template.md` if missing).

## 1. Session Classification (mandatory first action, every channel)

| Condition | Verdict | Follow-up |
|-----------|---------|-----------|
| Change code / fix bug / add feature / refactor / write tests / schema change / review producing Findings / any on-disk action | work task | → pick channel below |
| Q&A / consultation / informal read-only look, no formal deliverable | non-work task | → interact normally, skip |
| Cannot tell whether code will change | unclear | → ask first ("do we do it?"), never guess |

Record one line per verdict: `<verdict> — verb: <…>; noun: <…>; deliverable: <yes/no>` (🟢 records it in the closing reply). Headless (no `ask_user`) → most conservative option + record; never pretend confirmed.

## 2. Channel × Artifact Matrix (single source of flow truth)

| Channel | Artifacts | Flow | Close-out |
|---------|-----------|------|-----------|
| 🟢 light | **zero files** | implement → lint/format | inline summary |
| 🟡 standard | `intent.md` | locate → clarify → implement → gates → review → full re-verify | reply (merge ask_user) |
| 🔴 full | `specs/<slug>/{spec,plan,tasks}.md` | info-gathering → draft spec → clarify gate → plan → per-task implement+gates → review → full re-verify | reply (merge ask_user) + on-demand view |
| 📋 findings-only | spec/plan **IS the deliverable** | locate → review/validate | validation verdict |

- Hard constraints: 🟢 zero new files; 🔴 three artifacts; **AC only added, never rewritten** (supersede to re-point, §12 of the design doc)
- Clarification gate (🟡/🔴, scope fuzzy): split unclear points into **Assumptions** (low-risk, self-decided, recorded as A-ids) vs **Questions** (batch via `ask_user`, one round — never serial across turns); answers become AC/AD entries. Question drafting may delegate to a question-technique skill (e.g. `grill-me`) found via `find_skill` — the gate keeps filtering and one-round discipline. Info-gathering first: `find_skill` (local skills) / `web_search` (external facts; cite source + time; AC stays locally executable)
- Close-out re-verification (🟡/🔴): full gates re-run before closing — per-task green ≠ repo green; failure → back to the task loop. Merge decision (PR / merge / iterate) via `ask_user` at close-out
- Continuation: slug comes from the first requirement; follow-ups append tasks by default (🟡: append intent paragraphs); channel upgrade backfills missing artifacts, never downgrades; explicit "new task" or unrelated topic → new slug; existing dir outside this chain → reject and rename

## 3. Roles & Dispatch (`spawn_agent` optional → inline; templates in `references/templates/dispatch-*.md`)

explorer: read-only recon → orchestrator **replaces** the Background placeholder in `spec.md` with the results (not appends). implementer: lands code + tests, checks off its tasks in `tasks.md` with pasted gate output. reviewer: graded findings (blocker/major/minor) → `## Review` section. **Closing rule: an open blocker/major makes closing illegal** (artifact-check enforces).

Each role's `spawn_agent` dispatch begins with a mandatory **Context step**: read the relevant artifacts (`spec.md` / `plan.md` / `tasks.md`) before any work. Inline mode (no spawn_agent) skips it — the orchestrator already holds the artifacts. **Context flows through artifacts, never through parent-session summaries** — the `spawn_agent(role, prompt)` prompt carries only a task pointer + role discipline; the sub-agent `read`s the artifacts itself to get the full picture.

## 4. Quality Gates (`run_command`)

lint → format → type → test, fixed order, project-defined commands (adapter §2). Evidence pasted, never from memory; failure → root cause → fix → re-run; never delete assertions or relax checks to go green. 🟢: lint + format mandatory; type/test on demand with reason recorded.

- Per-task (🟡/🔴): lint/format/type in full + **affected test subset**; the **full suite runs at close-out re-verification** (mandatory) — per-task green ≠ repo green
- **Gate N/A** (never skip silently): declare `- GATE-NA(<gate>): <reason + scope>` in spec/intent `Gate Exemptions`, reference `GATE-NA(<gate>):` in the task output — artifact-check enforces the pairing. Scope: **chain-wide** exemptions also apply at close-out re-verification; **task-scoped** exemptions do not — the full suite still runs that gate at close-out
- **Coverage threshold**: project-declared (adapter §2); none declared → plain test pass/fail, never invent a number
- **Refactoring (behavior-preserving)**: build a characterization-test baseline in plan first; one AC = "baseline tests pass unchanged"

## 5. Artifacts & Validation

Templates: `references/templates/{spec,plan,tasks,intent}.md`. Checked tasks must carry `Output:` (pasted evidence). `## Deferred` = remaining risks as open checkboxes. Validate before closing: `python scripts/artifact-check.py specs/` (schema + AC↔T closure + review guard).

## 6. Close-out

The closing reply is derived from artifacts + diff — never from memory: requirement positioning / verification evidence / remaining risks (open Deferred). Reply contract: `references/templates/output-contract.md` (per-channel depth + gate-evidence format). On-demand view: `python scripts/derive-report.py specs/<slug> [--base <ref>]` (stdout, never persisted; **no report file is ever written**).

## 7. Optional Capabilities: Context-First Resolution

`find_skill` / `web_search` are **semantic anchors, not implementations** — resolve each against the tools actually present in this conversation (native skill/search mechanisms first). Adapter mapping rows are hints; live context wins — record the deviation.

- `web_search`: cite source + retrieval time; AC stays locally executable; if the repo can answer, do not search. No tool available → record `not verified online` in spec Assumptions
- `find_skill` (🟡/🔴, scope fuzzy; after classification, before drafting): prefer the native skill mechanism; else `python scripts/find-skill.py "<query>"` probes the standard library locations (`~/.agents/skills` + harness dirs) and flags same-name/version drift. Exit 2 = no library → record `skill library unavailable` in Assumptions
- Static fallback (no dynamic hit): question-technique, e.g. grill-me (clarification gate, 🟡/🔴 scope fuzzy) / isolation (after plan) / decision record (after plan) / debugging (after gate failure) / simplify (after gates) / security review (before close-out re-verify, 🔴) / verification (before close-out) / branch finishing (after close-out)

## Constraints

1. Ask before guessing: intent-unclear → "do we do it"; scope-fuzzy → clarification gate
2. Architecture decisions (new port / event / table schema / aggregate behavior) confirmed via `ask_user` before code
3. No skipped gates, no hidden failures; closing with open blocker/major is illegal
4. The orchestrator never writes large implementations or tests itself (implementer role)
