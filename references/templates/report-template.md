---
name: harness-coding-template-report
description: The stage-report skeleton template for harness-coding. Report file naming, init skeleton, per-stage append format, fix-loop table, and closing format. Reused by the write_report capability and every adapter layer; read when the orchestrator initializes/appends a report.
---

# Stage Report Template

> Reused by the `write_report` capability and every adapter layer. The "reporting protocol" in the methodology body is realized per this template.
> Report file naming convention: `<report.dir>/<report.prefix>-<slug>-v<N>.md`, default `harness-reports/harness-task-<slug>-v<N>.md`; a task without a slug falls back to `harness-reports/harness-task-v<N>.md` (directory/prefix from the capability-contract "runtime config"; the adapter layer can override). `N` is resolved **per task**: glob this task's reports (`harness-task-<slug>-*`; no-slug: `harness-task-v*`) and take max +1, starting from 0 if none — `v<N>` means "the N-th report for this task", not a global serial. The `<slug>` is a short kebab-case task identifier (lowercase letters / digits / hyphens, sanitized; empty → omitted), and the version is always the **trailing** `-v<N>`.

---

## Skeleton (created at the init stage)

```markdown
# Harness Task Report: <one-sentence requirement summary>

> **Task ID**: harness-task-<slug>-v<N>
> **Started**: YYYY-MM-DD HH:MM:SS
> **Ownership**: <to be determined>
> **Architecture decision**: <to be determined>
> **Final status**: 🔄 in progress

---

<!-- PHASE: init DONE -->
<!-- PHASE: positioning -->
<!-- PHASE: exploration -->
<!-- PHASE: plan -->
<!-- PHASE: isolation -->
<!-- PHASE: implementation -->
<!-- PHASE: quality-gate -->
<!-- PHASE: review -->
<!-- PHASE: verification -->
<!-- PHASE: summary -->
<!-- PHASE: merge -->
```

> **Skipped-stage markers**: stages skipped by the 🟢/🟡/📋 channels are written as "(🟢/🟡/📋 skipped)" and marked `DONE`, without expanded content; the skeleton keeps the full phase set and every stage the channel does not execute gets the skipped marker.

## Per-stage append format

Each stage writes at the corresponding `<!-- PHASE: xxx -->` marker — the marker line is replaced with the stage content + a trailing `<!-- PHASE: xxx DONE -->` line, so the DONE marker ends the block — uniformly following:

```markdown
## Stage N: <name> (<role>, model: <model>)
<!-- omit the parentheses when no role was involved -->

**Input** / **dispatch context** (optional):
> "<content>"

**Output** (optional):

<the role's returned report, indented one level>

> <metadata: duration / retry_count / skills_log, etc.>

---
```

> **Retry sub-sections**: when a stage already has content, appends go into a `### Append/Retry` sub-section **above** the stage's DONE marker (same position as the original stage content), never overwriting it — the DONE marker always ends the block.

## Stage → Content to Write

| phase | corresponding step | content to write |
|-------|--------------------|------------------|
| `init` | report initialization | take the max version N over **this task's** reports (per-task naming, see the header note); newest such report has `final status=🔄 in progress` → **ask the user continue/abandon** (`ask_user` unavailable → default `abandon`, leaving the in-progress report untouched): continue → resume the existing report (recovery), abandon → create `v<N+1>`; create the new file **exclusively** (create-fail-if-exists; on collision — a concurrent session claimed it — retry with `v<N+2>`, never overwrite); create the skeleton (title/metadata/phase markers); on interruption recovery, resume from the earliest non-DONE stage and append a recovery note (out-of-order gaps — a non-DONE marker before a later `DONE` — recorded as anomalies) |
| `positioning` | 1 positioning | input = user's original requirement, output = tier verdict + ownership + architecture decision |
| `exploration` | 2 exploration | input = dispatch prompt, output = explorer report |
| `plan` | 3 plan | when an architecture decision is involved, output plan highlights + user confirmation; otherwise write "no architecture decision, skipped" |
| `isolation` | 4 isolation | output branch/worktree path; write "skipped" if no code changes |
| `implementation` | 5 implementation | input = dispatch prompt, output = implementer's four-part report (change list + verification + self-test checklist + remaining) |
| `quality-gate` | 6 quality gate | summary of the four quality-gate command outputs (code block); on failure append the fix-loop table |
| `review` | 7 review | input = review scope, output = reviewer Findings; on rejection append the loop table |
| `verification` | 8 verification | fresh quality-gate output + `✅ gate passed / ❌ not passed` |
| `summary` | 9 summary | the full report per the Output Contract (positioning / changes / verification / remaining risks / skill usage log) + closing status |
| `merge` | 10 merge | merge method (PR / direct merge / keep iterating) |

> **Findings-only tasks (📋 channel)**: the review stage's Findings are the deliverable; plan / isolation / implementation / quality-gate / verification / merge are written as "(📋 skipped)" `DONE` markers without expanded content. The reviewer may run quality gates as recheck evidence, but there is no dedicated quality-gate stage.

## Fix-loop table (when the quality-gate / review stage fails)

```markdown
| Round | Failure | Root cause | Fix | Result |
|-------|---------|-----------|-----|--------|
| 1 | <which gate / which finding> | <reason> | <what changed> | <passed/rejected> |
```

## Closing (summary stage)

```markdown
> 📊 Stats: total duration | role calls X | quality-gate retries X | review rejections X
> 📅 Completed: YYYY-MM-DD
> **Final status**: ✅ passed / ❌ rejected
```

> Archive: when reports under `<report.dir>` (default `harness-reports/`) exceed 20, the orchestrator reminds to move them into `<report.dir>archive/` (default `harness-reports/archive/`, keeping the 2 most recently modified) at the summary stage. `<report.dir>` must end with a trailing slash (as the defaults do) so the archive path concatenates correctly. The report is for traceability only; it does not affect task execution.
