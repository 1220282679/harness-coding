---
name: harness-coding-adapter-claude-code
description: The filled-in adapter layer for the Claude Code harness. Maps the 8 required + 4 optional capabilities from references/capability-contract.md to Claude Code's concrete tools (Read / Write / Edit / Glob / Grep / Bash / AskUserQuestion / Agent / EnterWorktree), and declares quality-gate commands, role mapping, and conditional-skill mapping. Read before loading harness-coding under Claude Code (SKILL.md prerequisites).
---

# Adapter Layer: Claude Code

> This is the filled-in adapter for the Claude Code execution harness. The methodology body (SKILL.md) and the capability contract (references/capability-contract.md) stay unchanged; this file answers exactly one question: **what concrete Claude Code mechanism implements each capability in the contract**.
>
> Generated from `references/adapters/_adapter-template.md`; the "how to generate" section has been removed.

---

## 1. Capability Mapping Table

> All 12 capabilities (8 required + 4 optional) map to Claude Code primitives as follows. Anything that can't be mapped is marked "unsupported" honestly — never invented.

| Capability | Implementation in Claude Code | Notes |
|------------|-------------------------------|-------|
| `read` | **Read** tool | Reads a single file (full content) or an image/PDF. **Deviation**: `read` on a *directory* is NOT supported by the Read tool — use **Glob** to list a directory's contents (see §8 note) |
| `write` | **Write** tool | Overwrite-write. The harness enforces "read before overwriting an existing file" — writing an unread file that already exists fails |
| `edit` | **Edit** tool | Exact string replacement. `old` must match uniquely or the edit fails (narrow the context); supports `replace_all: true` |
| `glob` | **Glob** tool | Pattern-match to list file paths (e.g. `glob("harness-reports/harness-task-<slug>-*")` for a task's reports) |
| `grep` | **Grep** tool | ripgrep-based content search; returns matches with `file:line`, supports regex / glob filters |
| `run_command` | **Bash** tool | Runs shell commands (Git Bash on Windows); returns stdout / stderr / exit_code. The only channel for quality gates |
| `ask_user` | **AskUserQuestion** tool | Presents 2~4 mutually exclusive options; mark the recommended one "(Recommended)" and place it first |
| `write_report` | **Read** + **Edit** simulation | No dedicated report primitive in Claude Code → simulate per `references/templates/write-report.md` (locate `<!-- PHASE: x -->` marker → append content → replace that one line with `... DONE -->`) |
| `spawn_agent` | **Agent** tool (optional) | role mapping in §3 |
| `create_branch` | **EnterWorktree** tool, else `git checkout -b` via Bash (optional) | worktree isolation; fallback to a feature branch |
| `check_command` | Bash `command -v <cmd>` (optional) | run once to decide |
| `run_quality_gate` | Bash running the four gates serially (optional) | no bundled primitive; run each via Bash and combine |

## 2. Quality-Gate Commands (project-defined)

> Four gates in a fixed order: lint → format → type → test. Commands are defined by the **project**, not by the harness — the Python stack below is the example toolchain from the contract; replace per project (e.g. eslint / prettier / tsc / vitest).

| Gate | Command | Notes |
|------|---------|-------|
| lint | `ruff check .` | e.g. eslint / gofmt -l |
| format | `ruff format --check .` | e.g. prettier --check |
| type | `mypy --strict .` | e.g. tsc --noEmit |
| test | `pytest --cov=<module>` | the coverage threshold belongs to this gate |

## 3. Role Mapping (optional `spawn_agent` capability)

> The Agent tool supports named agent types; register the three roles as follows.

| Role | Agent type in Claude Code | Notes |
|------|---------------------------|-------|
| `explorer` | **Explore** agent (read-only) | read-only recon, output with file:line — matches the explorer's "read-only discipline" exactly |
| `implementer` | **general-purpose** agent | implementation + tests + quality gates |
| `reviewer` | **general-purpose** agent, or a dedicated code-reviewer agent type if registered | graded findings + quality-gate recheck |

> If an agent type is not registered → degrade to the generic agent or inline execution in the orchestrator; responsibilities and output contracts stay unchanged.

## 4. Conditional Skill Mapping (SKILL.md conditional-trigger table → loadable skills in Claude Code)

| Abstract conditional skill | Loadable skill in Claude Code | Triggered stage |
|---------------------------|-------------------------------|-----------------|
| Isolation skill | `using-git-worktrees` (or **EnterWorktree** directly) | after plan confirmed → before implementation |
| Decision-record skill | `documentation-and-adrs` | after plan confirmed |
| Debugging skill | `systematic-debugging` | after quality-gate failure |
| Simplify skill | `simplify` | after quality-gate pass → before review |
| Security review | `security-review` | after review pass → before verification (Full) / before report (Standard) |
| Verification skill | `verification-before-completion` | after review pass → before summary |
| Branch-finishing skill | `finishing-a-development-branch` | after summary pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in Claude Code | Report annotation |
|--------------------|-------------------------------------|-------------------|
| `ask_user` (headless, e.g. `claude -p`) | pick the most conservative option (fewest irreversible side effects) and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | the orchestrator executes roles inline | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace | `not isolated (no branch capability)` |
| `check_command` | run once to decide | none |
| `run_quality_gate` | run each gate via Bash serially | none |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Runtime Config Overrides

> None — the capability-contract defaults apply: `report.dir=harness-reports/`, `report.prefix=harness-task`, `report.on_disk=true`. (Set `report.on_disk=false` for the 🟢 light channel or temporary sessions; see the capability-contract runtime config.)
>
> **Path base**: `<report.dir>` is project-root-relative — resolve it against the harness working directory (the project root where the session runs, never the skill's own directory) to an absolute path before the first write.

## 7. Capability-Contract Consistency Self-Check

| Required capability | Implementation in Claude Code | Status |
|---------------------|-------------------------------|--------|
| read / write / edit / glob / grep | §1 table | ☑ |
| run_command | §1 table (Bash) | ☑ |
| ask_user | §1 table (AskUserQuestion) | ☑ |
| write_report | §1 table (Read + Edit simulation per templates/write-report.md) | ☑ |

> All checked → the adapter layer is ready; you can run the SKILL.md main flow.

## 8. Known Deviations

| Contract semantics | Claude Code reality | Handling |
|--------------------|--------------------|----------|
| `read` on a directory returns an entry list | the Read tool errors on directories | directory listing is performed via **Glob**; `read` semantics are narrowed to files only |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
