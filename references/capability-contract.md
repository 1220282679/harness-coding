---
name: harness-coding-capability-contract
description: The harness capability contract for the harness-coding skill. Defines signatures for 8 required + 4 optional capabilities (read/write/edit/glob/grep/run_command/ask_user/write_report, etc.), the quality-gate abstraction, the role abstraction, degradation rules, and a checklist for onboarding a new harness. Read on demand when loading harness-coding; read before onboarding a new harness or verifying capability consistency.
---

# Harness Capability Contract

> This is the **single interface** between the `harness-coding` skill and any execution harness. The methodology body references only capability names from this contract and never references concrete tools, CLIs, or frameworks.
> Each harness maps capability names to its own implementation through one adapter layer (filled in as `adapters/<harness>.md` per `adapters/_adapter-template.md`).

---

## 1. Design Principles

1. **The capability name is the contract**: the body uses only capability names (e.g. `read` / `run_command`), never concrete nouns like a `Read` tool, `Bash`, `Agent`
2. **Required vs optional**: if a required capability is missing the skill cannot work—prompt to complete the adapter layer; if an optional capability is missing, degrade to serial/manual per the "degradation rules"
3. **Single source of truth**: onboarding a new harness only requires adding one adapter file; the methodology stays unchanged

## 2. Capability List

### Required capabilities (missing → skill unusable)

| # | Capability | Signature | Semantics |
|---|-----------|-----------|-----------|
| 1 | `read` | `read(path) -> str` | Read file / directory contents |
| 2 | `write` | `write(path, content) -> void` | Write / overwrite a file |
| 3 | `edit` | `edit(path, old, new) -> void` | Exact replacement of a file fragment (old must match uniquely) |
| 4 | `glob` | `glob(pattern) -> list[str]` | List file paths matching a pattern |
| 5 | `grep` | `grep(pattern, path?) -> list[Match]` | Content search, returns matches with file:line |
| 6 | `run_command` | `run_command(cmd) -> Output` | Run a shell command, returns stdout/stderr/exit_code |
| 7 | `ask_user` | `ask_user(question, options) -> Answer` | Ask the user a question with options for confirmation |
| 8 | `write_report` | `write_report(report_path, phase, phase_input?, phase_output?, metadata?) -> void` | Append stage content to the report file (skeleton in templates/report-template.md) |

> **What "required" means for `write_report`**: what is required is the **reporting-protocol semantics** (phase-marker append / silent fault tolerance / truncation / versioning / recovery / closing), not a standalone tool—when no dedicated primitive exists, simulating it with `write`+`edit` satisfies the requirement (see §8 and the self-contained implementation in `templates/write-report.md`).
>
> **What "required" means for `edit`**: likewise, what is required is the **unique exact-replacement semantics**, not a dedicated tool. A harness with only `read`+`write` can satisfy `edit` by composition—read the full file → replace the fragment in memory → write the whole file back. What must be preserved is the *unique-match* rule: never fall back to silent first-match-wins; raise and let the caller narrow the context. This is the same read-all/write-all substitution that the `write_report` simulation (§8) relies on.
>
> **What "required" means for `ask_user`**: what is required is the *interaction* at decision points, not a specific structured-2~4-option primitive. A harness with only per-action approval prompts (e.g. Codex's interactive TUI) still satisfies it in interactive mode; a **headless** harness with no human in the loop degrades per SKILL.md's conservative-decision rule (pick the least side-effect option and record "⚠️ unable to ask the user; decided on the conservative option") — the adapter declares this in its §5 degradation table.

### Optional capabilities (missing → handled per degradation rules)

| # | Capability | Signature | Semantics | Degradation rule |
|---|-----------|-----------|-----------|------------------|
| 9 | `spawn_agent` | `spawn_agent(role, prompt) -> AgentReport` | Spawn a sub-agent and collect a structured report | None → the orchestrator executes that role inline (serially), responsibilities unchanged |
| 10 | `create_branch` | `create_branch(name) -> void` | Create an isolated branch/worktree | None → work directly on the main workspace, record "not isolated" in the report |
| 11 | `check_command` | `check_command(cmd) -> bool` | Only verify a command is available (which) | None → run once to decide |
| 12 | `run_quality_gate` | `run_quality_gate(commands) -> GateResult` | Run all four quality gates at once (lint/format/type/test) | None → run each via run_command |

## 3. Capability Signatures in Detail

### 1. `read`
Read a single file and return its full content; reading a directory returns an entry list. Reports / configs / code can all be read.

### 2. `write`
Create a new file or overwrite one entirely. **Never for appends** (appends belong to `write_report`). The target must have been `read` before overwriting (to prevent accidental destruction).

### 3. `edit`
Exact text replacement. `old` must be unique within the file; if not unique, raise and let the caller narrow the context. Supports `replace_all` semantics.

> When no dedicated primitive exists, a `read`+`write` composition (read-all → replace in memory → write-all) satisfies the requirement; preserve the unique-match rule (see the note after the capability table).

### 4. `glob`
Pattern-match file paths. Used to locate a task's report files (`glob("<report.dir>/<report.prefix>-<slug>-*")`, default like `glob("harness-reports/harness-task-<slug>-*")`) and to survey the directory skeleton.

### 5. `grep`
Regex content search, returns a match list, each item with file:line. Used to locate symbols / references across files.

### 6. `run_command`
Run any shell command. **This is the only channel for quality gates** (lint/format/type/test all go through it). Returns full stdout/stderr/exit_code; the caller must paste the key output as evidence, never claim "passed" from memory.

### 7. `ask_user`
User-facing decision confirmation. Must present 2~4 mutually exclusive options + a recommended one; used for architecture decisions, channel tier, merge method, and other points **only the user can decide**.

### 8. `write_report`
The mechanical implementation of the reporting protocol. Locate the `<!-- PHASE: <phase> -->` marker → replace it with the stage content + a trailing `<!-- PHASE: <phase> DONE -->` line (content sits above the marker; adjacent markers untouched); if the marker doesn't exist, append to the end. Any exception exits silently but warns explicitly in the reply.

> **Composition-simulation semantics**: when implementing this capability with a `write`+`edit` combination, `edit` must replace only the target marker line (`<!-- PHASE: x -->` → `<!-- PHASE: x DONE -->`) and **must not copy other adjacent marker lines after it**—otherwise later phase markers would be duplicated, breaking glob/incremental resolution.

Robustness requirements (derived from the source harness-reporting behavior rules):
- **Init continue/abandon**: before initializing a new report for a task whose highest-version report still has `**Final status**: 🔄 in progress`, ask the user continue/abandon first (`ask_user` unavailable → default `abandon`); continue → resume the in-progress report, abandon → mark it `❌ abandoned` (a header-status-line edit; stage content left untouched) and start a fresh `v<N+1>`; never silently overwrite an in-progress report. If the caller explicitly specifies a report filename (e.g. drills/test scenarios), skip the continue/abandon question (treated as pre-decided by the user) and write to that name, recording a "report name specified by caller" deviation
- **Directory creation**: before the first write, ensure the report directory exists (via `run_command` mkdir, or rely on the harness auto-creating parent directories); if the directory cannot be created, degrade to inline reporting and warn explicitly, never silently drop the report
- **Content truncation**: quality-gate output >100 lines keeps first 30 + last 30; agent output >500 lines keeps the heading structure + a truncation marker (if the output has no headings, keep first 30 + last 30 instead of dropping everything)
- **No duplicate writes**: when a stage already has content, append a `### Append/Retry` sub-section instead of overwriting
- **Failure warning**: 3 consecutive write failures accumulate a count in `metadata.failures`; the summary stage appends the warning "⚠️ report not persisted — write anomaly" (the report may be incomplete; the literal marker is always the short form above)
- **Recovery**: after a session interruption, resume from the first non-DONE marker (the earliest incomplete stage); a non-DONE marker appearing before a later `DONE` is an out-of-order gap (a stage jumped over without being completed or marked skipped) and is recorded as a recovery anomaly, never silently skipped
- **Close**: at the summary stage, edit the header metadata line `**Final status**: 🔄 in progress` → `✅ passed` / `❌ rejected` / `❌ abandoned`; the merge stage records how it was merged
- **Archive**: when reports under `<report.dir>` exceed 20, the orchestrator reminds to move all but the 2 most recently modified (mtime-ranked) into `<report.dir>archive/` (trailing-slash path, default `harness-reports/archive/`)
- **`metadata` contents**: populated by the orchestrator per stage; carries `duration`, `retry_count`, `skills_log` (feeds the summary's Skill Usage Log), and `failures` (consecutive write-failure count)

> Implementation note: this capability is about **report semantics** (phase-marker append / silent fault tolerance / truncation / versioning / recovery / closing), not a required dedicated primitive—the adapter layer can simulate it with `write`+`edit`; the self-contained implementation is in `templates/write-report.md`. "Required" means the reporting-protocol semantics must be satisfied, not that a dedicated tool must exist.

## Runtime Configuration (defaults the adapter layer can override)

| Config key | Default | Description |
|------------|---------|-------------|
| `report.dir` | `harness-reports/` | Report directory — a **project-root-relative** path (resolved against the harness working directory, never the skill's own directory); the adapter layer resolves it to an absolute path against the project root before use (see the base-resolution note below). Distinct from the project's own `docs/` so runtime reports never mix with real documentation |
| `report.prefix` | `harness-task` | Report filename base; the version suffix `-v<N>` is always appended at the end, with an optional task slug in between: `<prefix>-<slug>-v<N>.md`, no-slug fallback `<prefix>-v<N>.md` (e.g. `harness-task-add-rerank-v3.md` / `harness-task-v3.md`). `N` is resolved **per task** (see below) |
| `report.on_disk` | `true` | Whether to persist to disk; `false` → inline-only output, `write_report` degrades to no persistence (suited for the 🟢 light channel or temporary sessions). Inline-only output must carry the explicit `⚠️ report not persisted (inline-only)` marker, and failed persistence the `⚠️ report not persisted — write anomaly` marker, in the reply — never look like a silently dropped report |

> **Path constraint**: `report.dir` must end with a `/` (as the defaults do). The archive path concatenates as `<report.dir>archive/`, so an override without the trailing slash silently produces `reportsarchive/` instead of `reports/archive/` — the adapter layer must keep the trailing slash on any override, and an override without one should be normalized before use.
>
> **Base resolution**: `<report.dir>` always resolves against the **harness working directory (the project root where the session runs)**, never against the skill's own directory (e.g. `.claude/skills/harness-coding/`). The adapter layer must resolve it to an **absolute path against the project root** before the first write — glob and file paths alike. When the skill runs inside its own repository (skill development), the working directory IS the skill repo, so reports land in `<skill-repo>/harness-reports/` (gitignored by the skill bundle); for normal use the skill is installed into the target project and reports land in `<project>/harness-reports/`. If the resolved absolute path would fall inside the skill's own directory while the working directory differs, that is a misconfiguration to surface, not a silent redirect.

> Version resolution (per task): the version is the **trailing** `-v<N>` of the filename stem, where N must be a **pure integer** (no leading zeros — `v010` is not pure and does not participate in max). `N` is resolved **per task**, not globally: a slugged task queries `glob(report.dir + report.prefix + "-<slug>-*")` and takes max +1 over its own reports; a no-slug task queries `glob(report.dir + report.prefix + "-v*")`, counting only files whose stem is exactly `<prefix>-v<N>` (its namespace is separate from slugged tasks). `v<N>` therefore means "the N-th report for this task", and sessions working on different tasks never collide. The optional `<slug>` between prefix and version is a short kebab-case task identifier (lowercase letters / digits / hyphens, sanitized; empty → omitted). Naming rules and glob patterns change with the config; the methodology body and templates must not hardcode specific paths or project names.
>
> **Collision guard**: initializing a new report resolves N per task, then creates the file **exclusively** (create-fail-if-exists); if the exclusive create fails because a concurrent session claimed the same name, re-glob and retry with the **next resolved version** (the concurrent session's file now counts in the glob, so the next candidate advances past the claimed name) — never overwrite a concurrently-created report. This makes same-task concurrent init safe. Exclusive-create is realized **per adapter**: a write tool that fails on an existing unread target (Claude Code), a create-exclusive `run_command` (e.g. a shell `open(path, 'x')`), or best-effort check-before-write + retry where neither exists. The retry loop is exercised by `scripts/smoke-report.py` (`claim_filename`).
>
> The adapter layer can declare overrides for these three items at the top of the adapter file (e.g. a team repo standardizing reports under `reports/`). Smoke validation of the reporting protocol: `scripts/smoke-report.py`. Per-channel end-to-end lifecycle validation (the protocol behind the tiered channels): `scripts/workflow-check.py`. Cross-document consistency of the skill itself (frontmatter / internal references / capability usage / role templates / phase set / protocol invariants): `scripts/consistency-check.py`.

## 4. Quality-Gate Abstraction (not a capability, a protocol)

The quality gate is not a single capability but a **fixed call sequence** over `run_command`:

```text
lint → format --check → type check --strict → test (including the coverage threshold)
```

- Concrete commands are defined by the project (e.g. `ruff check .` / `ruff format --check .` / `mypy --strict .` / `pytest --cov=...`), written into the adapter's `gate.commands`; the examples are the Python stack—non-Python projects define the four gates per their own toolchain (e.g. eslint / prettier / tsc / vitest, or the matching language tools)
- All four must be **green** before done; any failure → locate the root cause → fix → re-run from the failed gate
- A quick-feedback variant may truncate as needed (e.g. only run changed modules), but the full run is mandatory before commit

## 5. Role Abstraction (role registration for the optional `spawn_agent` capability)

| Role | Input | Output contract |
|------|-------|-----------------|
| `explorer` | Recon target + scope | Location results / call chains / reusable patterns / open questions (with file:line) |
| `implementer` | A task with a clear location | Change list / verification results / self-test checklist / remaining risks (four-part) |
| `reviewer` | Review scope (diff/file list) | Review verdict / graded Findings / quality-gate recheck / highlights |

> Without the `spawn_agent` capability, the orchestrator plays the role itself, but **must follow the corresponding role's input/output contract** (templates in `templates/`).

## 6. Degradation Rules Summary

| Missing capability | Behavior | Report annotation |
|--------------------|----------|-------------------|
| `spawn_agent` | The orchestrator plays the role inline | `no sub-agent, inline execution` |
| `create_branch` | Change directly on the main workspace | `not isolated (no branch capability)` |
| `check_command` | Run once to decide | none |
| `run_quality_gate` | Run each via run_command serially | none |

## 7. Onboarding a New Harness (Adapter Checklist)

1. Check capability by capability: map each of the 8 required capabilities to that harness's tools/primitives (fill-in placeholders in `adapters/_adapter-template.md` §1)
2. Copy and generate `adapters/<harness>.md` per `adapters/_adapter-template.md`: capability-name → implementation table + quality-gate commands + role mapping + conditional-skill mapping + degradation-rule declarations; after filling, delete the template's "how to generate" section
3. If a required capability cannot be satisfied → annotate "unsupported capabilities" at the top of the adapter layer; the skill continues per the degradation rules when loading
4. Run one lightweight requirement end-to-end (e.g. fix a typo) to verify the lowest channel works
