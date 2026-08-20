---
name: harness-coding-write-report
description: Self-contained minimal implementation guide for the write_report capability in harness-coding. Simulates the reporting protocol (locate marker → append → replace marker with DONE → truncate → fault tolerance → recovery → close status) with a read/write/edit combination; use this when the adapter layer has no dedicated report-writing tool. Read when loading harness-coding without an external harness-reporting-like skill.
---

# write_report Self-Contained Implementation (read / write / edit combination)

> This is the **reference implementation** of the `write_report` capability. The capability contract only defines the semantics; this file gives the minimal path that depends on no external skill. If you have a dedicated report-writing tool or an external harness-reporting, that implementation can replace this one—but its behavior must match this file.

---

## Prerequisites

- The required capabilities `read` / `write` / `edit` / `glob`, plus `run_command` for creating the report directory (skip it when the harness's `write` auto-creates parent directories)
- Report skeleton and phase-marker definitions in `templates/report-template.md`
- Naming and directory come from the capability-contract "runtime config" (`report.dir` / `report.prefix` / `report.on_disk`); the filename follows `<report.prefix>-<slug>-v<N>.md` (no-slug fallback `<report.prefix>-v<N>.md`), the version being the trailing `-v<N>` and `<slug>` a short kebab-case task identifier — **lowercased first**, then non-alphanumerics → `-`, collapse and trim `-`, omit when empty (e.g. `Add Rerank!` → `add-rerank`). `N` is resolved **per task**: `glob` this task's own reports (`<report.dir>/<report.prefix>-<slug>-*`; no-slug: `<report.dir>/<report.prefix>-v*`) → max pure-integer `-v<N>` + 1 (0 when none)

## Operation sequence (corresponds to contract §8)

```
write_report(report_path, phase, phase_input?, phase_output?, metadata?)
```

1. **Resolve `<report.dir>` against the project root**: it is a project-root-relative path — resolve it against the harness working directory (never the skill's own directory) to an absolute path before use. Then **ensure the report directory exists**: `run_command("mkdir -p <report.dir>")` (directory from the runtime config). If the directory cannot be created (read-only fs, no `run_command`), degrade to inline reporting (`report.on_disk=false` semantics) and warn explicitly with the `⚠️ report not persisted (inline-only)` marker in the reply — never silently drop the report
2. **Read the report**: `read(report_path)`. If the file doesn't exist → initialize: claim the filename **exclusively** (create-fail-if-exists; on collision — a concurrent session claimed it — re-resolve N per the Prerequisites and retry, never overwrite), then write the skeleton per the template first (`<!-- PHASE: init DONE -->`). If the file exists and its header still reads `**Final status**: 🔄 in progress` → **ask the user continue/abandon** (`ask_user` unavailable → default `abandon`): continue → resume from the first non-DONE marker (step 7); abandon → mark the in-progress report `❌ abandoned` (a header-status-line edit; stage content left untouched, so it no longer re-triggers the prompt) and re-resolve N and create `v<N+1>`. If the caller explicitly specified a report filename (e.g. drills/test scenarios), skip the continue/abandon question (treated as pre-decided by the user) and write to that name, recording a "report name specified by caller" deviation
3. **Locate the marker**: search the full text for the non-DONE `<!-- PHASE: <phase> -->` marker
   - A non-DONE marker found → insert the stage content **in place of the marker line**, keeping the marker (now DONE) as the **last line of the block** (content sits above it; the next phase's marker follows below) — see step 4
   - Already `... DONE -->` → don't overwrite, append a `### Append/Retry` sub-section **above the DONE marker line** (the marker is replaced with `### Append/Retry\n<content>\n<marker>`, so the DONE marker still ends the block) — see step 4
   - No matching marker → append to the end of the file (`## Stage N: <name>` + content)
4. **Edit to replace**: `edit(report_path, old marker line, new content block + new DONE marker line)` — the marker line is replaced with `[stage content]` + `<!-- PHASE: <phase> DONE -->`, so the DONE marker ends the block. **Replace only the target marker line; must not copy other adjacent marker lines after it** — otherwise later phase markers would be duplicated, breaking glob/incremental resolution
5. **Truncate**: quality-gate output >100 lines keeps first 30 + last 30 (write `... truncated, N lines total ...` in the middle); agent output >500 lines keeps the heading structure + truncation marker (if the output has no headings, keep first 30 + last 30 instead of dropping everything)
6. **Fault tolerance**: any step throws → exit the main flow silently, but print an explicit `⚠️ report not persisted — write anomaly` warning in the reply; 3 consecutive failures → append the same `⚠️ report not persisted — write anomaly` warning at the summary stage
7. **Recovery**: after a session interruption, resume from the first non-DONE marker (the earliest incomplete stage); a non-DONE marker before a later `DONE` is an out-of-order gap and is recorded as a recovery anomaly, never silently skipped
8. **Close** (at the summary stage): edit the header metadata line `**Final status**: 🔄 in progress` → `**Final status**: ✅ passed` / `**Final status**: ❌ rejected` (or `**Final status**: ❌ abandoned` when an in-progress report is abandoned at init) — a metadata-line edit, not a phase-marker append (the status line sits in the header, outside the phase markers); the merge stage then records how it was merged (append a `## Stage 10: merge` block per the marker rule)

## Key constraints when using `write`+`edit`

| Constraint | Reason |
|------------|--------|
| `edit` replaces only the target marker line, doesn't touch adjacent lines | Adjacent markers are the anchors for later phases; copying them leaves duplicates |
| A retry sub-section (`### Append/Retry`) sits **above** the stage's DONE marker, like the original stage content | keeps "the DONE marker ends the block" invariant; recovery/append stay deterministic |
| Must `read` before overwriting a file | Prevent accidental destruction of existing report content |
| Appends always go through `edit` (or read-all/write-all), never `write`-based append | `write` is overwrite semantics and would wipe existing stage content |
| Closing the report is a header-metadata-line `edit`, not a phase-marker append | the status line sits in the header, outside the phase markers; the marker-replacement rule doesn't apply to it |
| Init claims the report filename exclusively; on collision re-glob and retry with the next resolved version (the concurrent file now counts in the glob) | same-task concurrent init must never overwrite a concurrently-created report |

## Smoke validation

`scripts/smoke-report.py` simulates the rules above with the pure standard library and asserts them (version max resolution / marker append and DONE replacement / adjacent markers not copied / truncation for quality-gate and agent output / recovery / report closing / write guardrail / directory creation). `scripts/workflow-check.py` drives the same helpers through the full per-channel lifecycle (🟢/🟡/🔴/📋) and asserts each channel's report is well-formed. After implementing this capability, the adapter layer should run both scripts as the minimal regression.

## Relationship with an external harness-reporting

The capability contract doesn't force any external skill. When a mature harness-reporting exists, reuse it directly; when it doesn't, land it with the `write`+`edit` combination per this file, with matching behavior.
