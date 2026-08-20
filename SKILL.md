---
name: harness-coding
description: Universal harness-agnostic coding orchestration skill. Turns a one-line requirement into a controlled change flow via session classification, tiered channels (🟢 light / 🟡 standard / 🔴 full), role dispatch (explorer / implementer / reviewer), quality gates, and a five-section report. Depends only on the capability contract and runs through any execution harness's adapter layer. Use when the user asks for new requirements, features, fixes, refactors, code review, schema changes, or any task needing on-disk changes—trigger proactively even if "harness" isn't mentioned explicitly; if uncertain, ask before deciding.
---

# Role: Universal Harness Coding Orchestrator (harness-coding)

The master control flow that turns a one-line requirement into a deliverable change. It does not write large implementations itself; it dispatches per-stage to roles and enforces architecture-decision confirmation points and quality gates. Works on any harness that implements this skill's capability contract.

> **Core idea**: the methodology is decoupled from the execution environment. The body uses only "capability" wording (read files / run commands / dispatch / ask / write reports); the concrete tools are decided by the adapter layer. Before loading this skill, identify the current harness's adapter layer.

## Prerequisites

1. The current harness satisfies the **required capabilities** of the capability contract (see `references/capability-contract.md`)
2. Load the current harness's adapter layer from `references/adapters/` (if missing, generate it from `_adapter-template.md`) and confirm the concrete tool for each capability
3. Confirm the project's quality-gate commands (lint / format / type / test, executed via the `run_command` capability)
4. Confirm the role agent types (explorer / implementer / reviewer) are registered in the harness; if not, degrade to generic subagents or inline execution in the orchestrator (see "Role Mapping" in the adapter; responsibilities and output contracts stay unchanged)

## Session Classification (mandatory first action)

> Must run before the first response of any session. Not skippable.

| Condition | Verdict | Follow-up |
|-----------|---------|-----------|
| Change code / fix bug / add feature / refactor / write tests / schema change / code review (produces Findings) / read-only evaluation that produces a formal Findings deliverable (even with no file changes) / any on-disk action | **Work task** | → initialize the report, go through the tiered channels below |
| Q&A / explanation / consultation / small talk / informal read-only look (no formal review deliverable, no file changes) | **Non-work task** | → interact normally, skip harness |
| Cannot tell whether code will change | **Unclear intent** | → **ask first, never guess** |

> `ask_user` degradation: when the current harness/context **cannot ask the user interactively** (no interactive question primitive, unattended), pick the most conservative option yourself and record it in the report as "⚠️ unable to ask the user; decided on the conservative option"; never pretend the user confirmed.

**Quick heuristic**: look at the verb first, then the noun. "Add/refactor/fix/change/replace/implement" → work task; "design/plan/evaluate" followed by a repo feature/module → work task **when the result is a formal deliverable (plan / Findings / implementation)**; only a purely consultative read-only look with no formal deliverable counts as non-work. When in doubt → ask.

**Classification record (auditable)**: every classification yields a one-line record `<verdict> — verb: <verb>; noun: <noun>; deliverable: <yes/no>` (e.g. `work task — verb: fix; noun: auth bug in login.py; deliverable: yes`). Work verdicts are recorded at the positioning phase (inline for 🟢); a work task whose verdict is not recorded in the report is a protocol violation. Classification is instruction-following, so the verb/noun evidence is the only way a later reader can verify why a task was (or wasn't) started.

**Multi-turn handling**: re-run the classification after every user message; intent upgrade → trigger report initialization; follow-up changes in the same task chain **reuse the already-open in-progress report** (append to the corresponding stage), do not re-init; when work ends → close the report.

## Reporting Protocol (`write_report` capability)

> A stage-by-stage, fully traceable report. Like `harness-reporting`, but bound to the capability contract rather than to specific tools.

1. **Naming**: `<report.prefix>-<slug>-v<N>.md`, default `harness-task-<slug>-v<N>.md` (no-slug fallback `harness-task-v<N>.md`); `N` in `v<N>` must be a **pure integer** (no leading zeros) and is resolved **per task** — `glob` this task's own reports and take max + 1 (0 for a fresh task), so different tasks have independent counters and `v<N>` means "the N-th report for this task", not a global serial; the optional `<slug>` is a short kebab-case task identifier (lowercase letters / digits / hyphens, sanitized; empty → omitted). Mixed suffixes like `v-test1` are forbidden—max-version resolution depends on integer increments (glob pattern and directory come from the capability-contract runtime config, default `harness-reports/harness-task-<slug>-*`, resolved against the harness working directory / project root — never the skill's own directory); mixed names break max resolution. If the caller explicitly specifies a report filename (e.g. drills/test scenarios), write to that name and **skip the "in-progress question"** (treated as pre-decided by the user), recording a "report name specified by caller" deviation at the top of the report
2. **Initialize**: `glob` this task's historical reports (`<report.dir>/<report.prefix>-<slug>-*`, no-slug: `<report.dir>/<report.prefix>-v*`) → take the max version N (N=0 if none); if the newest report **for this task** has `final status="🔄 in progress"` → **ask the user whether to continue or abandon first**, never silently overwrite; **when `ask_user` is unavailable, default to abandon** (continuing into a possibly-stale session is the riskier guess); **continue → resume the existing `v<N>` report (recovery per step 5); abandon → mark the in-progress report `❌ abandoned`** (a header-status-line edit; stage content left untouched, so it no longer re-triggers this prompt) **and create `v<N+1>.md`** with the skeleton (title / metadata / phase markers, `init` phase marked complete). Create the new file **exclusively** (create-fail-if-exists); on collision (a concurrent session claimed the same name) re-glob and retry with the **next resolved version** — never silently overwrite a concurrently-created report
3. **Incremental append**: after each stage completes, replace the corresponding phase marker with the stage content + a trailing `DONE` marker (content sits above the marker line, which ends the block); if the marker doesn't exist, append to the end
4. **Fault tolerance first**: silent write failure, not blocking the main flow; but must explicitly print a `⚠️ report not persisted — write anomaly` warning in the reply. Quality-gate output >100 lines → keep first 30 + last 30; if the stage already has content append a `### Append/Retry` sub-section, don't overwrite; 3 consecutive write failures → append the same `⚠️ report not persisted — write anomaly` warning at the summary stage
5. **Recovery**: after a session interruption, resume from the first non-DONE marker (the earliest incomplete stage); a non-DONE marker before a later `DONE` is an out-of-order gap and is recorded as a recovery anomaly, never silently skipped
6. **Close**: at the summary stage turn `🔄 in progress` → `✅ passed` / `❌ rejected`; the merge stage records how it was merged
7. **Template**: see `references/templates/report-template.md`

> The report is for traceability only; it does not affect task execution. Archive: when reports exceed 20, remind to move them into `<report.dir>archive/` (default `harness-reports/archive/`, derived per the report template, keeping the 2 most recently modified).
>
> **On-disk switch**: with capability-contract config `report.on_disk=false`, the report is inline-only, not written to disk—suited for the 🟢 light channel or temporary sessions; `write_report` degrades to no persistence and instead emits the stage content inline in the reply in stage order (versioning/recovery no longer apply; the closing status is kept in the final summary), the reporting protocol stays unchanged. Inline-only output must carry an explicit `⚠️ report not persisted (inline-only)` marker in the reply so a missing file is never mistaken for a silently dropped report. In inline-only mode there is **no on-disk skeleton**: skipped-stage markers follow the channel's report depth (omitted in the 🟢 simplified summary, retained in full-depth channels) and are emitted in stage order alongside the executed stages.

## Tiered Channels

> **Classify first, then dispatch**—pick the channel by change size to avoid heavy flows for small changes.

| Tier | Applies to |
|------|-----------|
| 🟢 **Light** | typo / import fix / single-line config / formatting / docstring tweak |
| 🟡 **Standard** | substantive single-file / single-function change or small 2-file change, no new port / event / table schema |
| 🔴 **Full** | cross-file refactor / new feature / architecture change / involves port, event, or table schema |
| 📋 **Findings-only** | code review / read-only evaluation whose deliverable is a graded Findings document (no code changes) |

**Verdict rule**: a change matching the 🟢 category list (typo / import fix / single-line config / formatting / docstring tweak), ≤1 file, no architecture impact → 🟢; any other single-file or small 2-file change → 🟡; a change of 3+ files or an architecture decision → 🔴 (exception: a change matching a 🟢 category item with no architecture impact escalates only to 🟡 regardless of file count — a multi-file typo/import fix is not a full-flow change); a review / evaluation task whose deliverable is a Findings document (not code changes) → 📋, and so does a plan/design deliverable with no code changes (the plan becomes the review-stage output). Confirm the tier at session classification and record it at the positioning stage (🟢 has no standalone positioning step — the tier is recorded inline in the positioning phase marker).

**Escalation clause**: a single-file change exceeding 50 lines of business logic → auto-escalate to 🟡 (never 🟢, even if it resembles a 🟢 category item); if it also involves an architecture decision → escalate to 🔴.

### Steps per channel

- 🟢 **Light**: 3 steps (implement → quality gate → report). Skips: exploration, plan, isolation, review, verification, merge (positioning has no standalone step on 🟢 — the tier is recorded inline in the positioning phase marker); **the orchestrator must still self-check** — lint + format are mandatory and actually executed with pasted output; type + test run only when the change touches type-relevant or logic/test-relevant code, with the reason recorded (an import fix that changes types runs type; a logic change runs test); no new un-commented type:ignore/noqa, no cross-layer dependency leak
- 🟡 **Standard**: 6 steps (positioning+exploration → implement → quality gate → review → report → merge). Skips: plan, isolation, verification.
- 🔴 **Full**: 10 steps (see the main workflow table).
- 📋 **Findings-only**: 3 steps (positioning → review → summary). Skips: plan, isolation, implementation, quality-gate, verification, merge — written as "(📋 skipped)" `DONE` markers (exploration is optional: dispatch the explorer first when the review scope itself is unclear). The review step dispatches the reviewer role **directly on the review target**; the graded Findings ARE the deliverable and go into the report (the reviewer may run quality gates as recheck evidence, not required). Architecture decisions surfaced by the review are recorded in the report and deferred to a follow-up change task — never changed silently.

> **Skipped stages go on record**: stages skipped by the 🟢/🟡/📋 channels are written in the report as "(🟢/🟡/📋 skipped)" and marked `DONE`, without expanded content; the skeleton keeps the full phase set and every stage the channel does not execute gets the skipped marker. The one exception is **positioning under 🟢**: the tier verdict is recorded inline in the positioning phase marker (tier + one-line rationale, marked `DONE`) rather than as `(🟢 skipped)` — it is the one phase every channel records.

> **Two artifacts**: the on-disk report always keeps the full phase skeleton with skipped stages written as "(🟢/🟡/📋 skipped)" markers (traceability artifact); the final summary delivered to the user is trimmed per channel depth (🟢 simplified / 🟡 full five sections / 🔴 full five sections + review verdict + security review / 📋 full five sections with the change list reading "none", see the Output Contract). They coexist: the on-disk report guarantees traceability, the delivered summary guarantees conciseness.

> **Light-task trade-offs**: when the change point cannot be settled (e.g. "fix the typo" but no clear error found)—prefer `ask_user` to confirm the target; if nobody can be asked, pick the candidate with the **strongest evidence** (cross-file comparison / non-standard phrase / internal inconsistency), and honestly record the candidate-sifting process and rationale in the report; never pretend to have found it or skip reporting.

> Architecture decisions involved (new port / new event / table schema / aggregate-behavior change) → write the plan to the report first, use `ask_user` to get confirmation before touching code; never skip the confirmation.

> **Cost note**: dispatching sub-agents + four quality gates carry token and latency costs. On 🟢/🟡 channels avoid repeated full runs and repeated dispatch; reuse quality-gate output where the same round can; don't escalate the channel without reason.

## Main Workflow (🔴 Full channel, 10 steps)

| Step | Action | Dispatch / condition |
|------|--------|----------------------|
| 1 positioning | Parse the requirement, decide the tier, confirm ownership and architecture decisions | — |
| 2 exploration | Dispatch the explorer role to locate change points + reusable patterns | Explorer role |
| 3 plan | When architecture decisions are involved, write the plan to the report, confirm with `ask_user` | — |
| 4 isolation | Code changes involved → branch / worktree / directory snapshot | Isolation capability |
| 5 implementation | Dispatch the implementer role; add tests for core logic if missing | Implementer role |
| 6 quality gate | lint + format + type + test. Failure → debug → back to step 5 | Quality gate |
| 7 review | Dispatch the reviewer role; blocker/major rejected → loop back 5→6→7; security review if involved | Reviewer role |
| 8 verification | Re-run quality gates for fresh evidence; never claim "passed" from memory | Verification |
| 9 summary | Deliver the final report per the output contract, close the report | — |
| 10 merge | Ask the user: PR / merge / keep iterating | — |

> Quality-gate failure loop: locate the root cause before fixing (no blind attempts) → back to implementation → re-run. Within the chosen channel, no skipping steps and no hiding failures (the 🟢/🟡/📋 step trims are channel design, not skipped steps).

> **Isolation degradation**: if worktree/branch creation fails (e.g. corrupted venv under Windows+uv, no git permission) → degrade to a feature branch on the main repo, or work directly on the main workspace; mark the report `not isolated (<reason>)` (e.g. `not isolated (venv corruption)`), matching the contract's `not isolated (no branch capability)` form; environment blockers don't stop the flow.

## Roles (`spawn_agent` capability, degradable to inline)

| Role | Responsibility | When to dispatch |
|------|----------------|------------------|
| Explorer | Read-only recon: locate implementations / call chains / reusable patterns, output with file:line | Location unclear / before cross-file changes |
| Implementer | Land the implementation + add tests + pass quality gates, four-part report | After location is clear |
| Reviewer | Compliance / correctness / quality-gate recheck, output graded findings | After implementation (code changes); on 📋 findings-only tasks, directly on the review target |

> Dispatch templates in `references/templates/`. Harnesses without the `spawn_agent` capability execute inline in the orchestrator; role responsibilities stay unchanged.

## Quality Gates (`run_command` capability)

All four green before done, fixed order:

```text
lint   → format   → type check   → test
```

- Concrete commands are defined by the project (e.g. ruff / ruff format --check / mypy --strict / pytest); this skill does not bind any
- **Must actually be executed and the output pasted as evidence**, never claim "passed" from memory
- A coverage threshold, if any, belongs to the same test gate (e.g. ≥70%)
- On failure → locate the root cause before fixing; never delete assertions / relax existing ones to go green
- **🟢 exception**: on the light channel only lint + format are mandatory (see Tiered Channels); type + test run on demand when the change touches type-relevant or logic/test-relevant code, with the reason recorded

## Conditional Triggers

| Conditional skill | Triggered stage | Condition |
|-------------------|-----------------|-----------|
| Isolation skill | After plan confirmed → before implementation | Code changes involved |
| Decision-record skill | After plan confirmed | An architecture decision was confirmed |
| Debugging skill | After quality-gate failure | Standard/Full channel (🟢 gate failures are fixed inline; a debug skill may still be used when the failure is non-trivial) |
| Simplify skill | After quality-gate pass → before review | Standard/Full channel |
| Security review | After review pass → before verification (Full) / before report (Standard) | Token / auth / permission / crypto / external integration involved |
| Verification skill | After review pass → before summary | Full channel |
| Branch-finishing skill | After summary pass | Standard/Full channel |

> How these abstract conditional skills map to loadable skills under a concrete harness is defined in the current adapter's "Conditional Skill Mapping" table (fill-in instructions in `references/adapters/_adapter-template.md` §4).
>
> Security-review findings are recorded in the review stage (a security addendum on Full) or the summary's Verification Results (Standard); there is no dedicated security-review phase marker — the summary's output contract carries the verdict. The summary's Skill Usage Log covers conditional skills loaded through the summary stage; branch-finishing (post-summary) usage is recorded in the merge stage.

## Output Contract

```markdown
## Requirement Positioning
- Classification: <work task / non-work task — verb: <…>; noun: <…>; deliverable: <yes/no>>
- Ownership: <…>; architecture decision: <none / yes — plan highlights and confirmation result>

## Change List
- <list of added / modified files, each with file:line and a one-line description>

## Verification Results
- Quality gates: <summary of lint / format / type / test>; review: <verdict, rejection count>

## Remaining Risks
- <uncovered edges, todos, items needing manual verification; write "none" if there are none>

## Skill Usage Log
- <conditional skills this skill loaded and their trigger stages>
```

> Template in `references/templates/output-contract.md`.

## Constraints

1. On receiving a requirement, first decide the tier and ownership; if information is insufficient, ask first, never guess
2. Architecture decisions require `ask_user` confirmation before touching code
3. All quality gates green before review; a rejected review runs the full loop, no skipped steps
4. The orchestrator must not write large implementations and tests itself (implementation and tests belong to the implementer role)
5. Never hide quality-gate / test failures; the output contract must be delivered per the channel's report depth (🟢 simplified / 🟡 full five sections / 🔴 full five sections + review verdict + security review / 📋 full five sections with the change list reading "none" — see references/templates/output-contract.md)
