---
name: harness-coding-adapter-opencode
description: The filled-in adapter layer for the opencode harness. Maps the 8 required + 4 optional capabilities from references/capability-contract.md to opencode's concrete tools (tool.read / tool.write / tool.edit / tool.apply_patch / tool.bash / tool.grep / tool.glob / tool.list / tool.question / tool.task / tool.skill), and declares quality-gate commands, role mapping, and conditional-skill mapping. Read before loading harness-coding under opencode (SKILL.md prerequisites).
---

# Adapter Layer: opencode

> This is the filled-in adapter for the opencode execution harness. The methodology body (SKILL.md) and the capability contract (references/capability-contract.md) stay unchanged; this file answers exactly one question: **what concrete opencode mechanism implements each capability in the contract**.
>
> Generated from `references/adapters/_adapter-template.md`; the "how to generate" section has been removed.
>
> **Version note**: opencode's tool surface and config schema evolve across releases; the tool names in this file (`tool.read` / `tool.write` / `tool.edit` / `tool.apply_patch` / `tool.bash` / `tool.grep` / `tool.glob` / `tool.list` / `tool.question` / `tool.task` / `tool.skill`) follow the current convention as of this writing. Directory-read behavior changed in **v1.1.60** (Feb 2026): `tool.read` lists directory contents natively — see §8 (**last verified 2026-08-20**). The authoritative set is the live tool catalogue of the current session (`opencode --help`, the tool list, or the tool catalogue) — never assume a tool exists without confirming.

---

## 1. Capability Mapping Table

> All 12 capabilities (8 required + 4 optional) map to opencode primitives as follows. Anything that can't be mapped is marked "unsupported" honestly — never invented. Tool names follow opencode's `tool.<name>` convention; per-tool permission (`allow` / `ask` / `deny`) is configured in the harness config (see §6).

| Capability | Implementation in opencode | Notes |
|------------|-----------------------------|-------|
| `read` | **tool.read** | Returns file content tagged with line numbers; also lists directory contents on opencode v1.1.60+ (the contract's directory-read semantics is met natively). **tool.list** remains available for explicit directory browsing (see §8) |
| `write` | **tool.write** | Create / overwrite a file; gated by the `edit` permission key. Read-before-overwrite is a contract convention, **not enforced** by opencode → follow it manually (see §8) |
| `edit` | **tool.edit** (string replacement) or **tool.apply_patch** (unified diff) | Unique-match rule: a `tool.edit` with multiple matches needs a narrower context; `tool.apply_patch` accepts a full diff. Both gated by the `edit` permission key |
| `glob` | **tool.glob** | pattern-match file listing |
| `grep` | **tool.grep** | regex content search, ripgrep-style; returns matches with file:line |
| `run_command` | **tool.bash** | The only channel for quality gates. Permission `bash` supports an allow/ask/deny mode plus a command glob-pattern map; `ask` → the user approves each command |
| `ask_user` | **tool.question** | Asks the user a question mid-execution. Combined with the `ask` approval mode for commands/edits. When `question` is unavailable (e.g. non-interactive run) → degrade per §5 |
| `write_report` | **tool.read** + **tool.edit** simulation | No dedicated report primitive → simulate per `references/templates/write-report.md` (locate `<!-- PHASE: x -->` marker → append content → replace that one line with `... DONE -->`) |
| `spawn_agent` | **tool.task** (optional) | Spawns a subagent defined in `.opencode/agents/` (or `~/.config/opencode/agents/`); agents are also invoked via `@<name>` mentions. Subagents can use only built-in tools (no MCP directly — see §8) |
| `create_branch` | **tool.bash** `git checkout -b <name>` (optional) | no native worktree primitive; a worktree = `tool.bash` + `git worktree add` |
| `check_command` | **tool.bash** `command -v <cmd>` (optional) | run once to decide |
| `run_quality_gate` | **tool.bash** running the four gates serially (optional) | no bundled primitive; run each via bash and combine |

## 2. Quality-Gate Commands (project-defined)

> Four gates in a fixed order: lint → format → type → test. Commands are defined by the **project**, not by the harness — the Python stack below is the example toolchain from the contract; replace per project (e.g. eslint / prettier / tsc / vitest).

| Gate | Command | Notes |
|------|---------|-------|
| lint | `ruff check .` | e.g. eslint / gofmt -l |
| format | `ruff format --check .` | e.g. prettier --check |
| type | `mypy --strict .` | e.g. tsc --noEmit |
| test | `pytest --cov=<module>` | the coverage threshold belongs to this gate |

## 3. Role Mapping (optional `spawn_agent` capability)

> Roles are dispatched via **tool.task**; subagents are gated by the `task` permission key. Custom agents are Markdown files with YAML frontmatter (`description` / `mode` / `model` / `permission`) in `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md` (global); the filename becomes the agent name. Scaffold with `opencode agent create`.

| Role | Agent type in opencode | Notes |
|------|-------------------------|-------|
| `explorer` | built-in **`explore`** subagent | read-only: read / grep / glob / list — matches the explorer's "read-only discipline" exactly |
| `implementer` | built-in **`general`** subagent, or a custom agent in `.opencode/agents/` | all built-in tools (minus todowrite); implementation + tests + quality gates; pass the implementer dispatch prompt |
| `reviewer` | a custom read-only reviewer agent (e.g. `.opencode/agents/reviewer.md`, `mode: subagent`, `permission` allows `bash` for gate rechecks), else **`general`** with the reviewer dispatch prompt | graded findings + quality-gate recheck |

## 4. Conditional Skill Mapping (SKILL.md conditional-trigger table → loadable skills in opencode)

> opencode loads skills as SKILL.md packages (frontmatter `name` + `description`) from `.opencode/skills/` (project) and `~/.config/opencode/skills/` (global), and also reads the portable `.claude/skills/` and `.agents/skills/` paths. Skills are invoked via the **tool.skill** tool, by mentioning the name, or from the tool catalogue. Because opencode reads `.claude/skills/`, existing Claude Code skill packages can be reused as-is; otherwise port the skill into `.opencode/skills/`. Trigger stages stay unchanged.

| Abstract conditional skill | Loadable skill in opencode | Triggered stage |
|---------------------------|----------------------------|-----------------|
| Isolation skill | port `using-git-worktrees` → `.opencode/skills/using-git-worktrees/SKILL.md` (or `tool.bash` git worktree) | after plan confirmed → before implementation |
| Decision-record skill | port `documentation-and-adrs` → `.opencode/skills/documentation-and-adrs/SKILL.md` | after plan confirmed |
| Debugging skill | port `systematic-debugging` → `.opencode/skills/systematic-debugging/SKILL.md` | after quality-gate failure |
| Simplify skill | port `simplify` → `.opencode/skills/simplify/SKILL.md` | after quality-gate pass → before review |
| Security review | port `security-review` → `.opencode/skills/security-review/SKILL.md` | after review pass → before verification (Full) / before report (Standard) |
| Verification skill | port `verification-before-completion` → `.opencode/skills/verification-before-completion/SKILL.md` | after review pass → before summary |
| Branch-finishing skill | port `finishing-a-development-branch` → `.opencode/skills/finishing-a-development-branch/SKILL.md` | after summary pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in opencode | Report annotation |
|--------------------|----------------------------------|-------------------|
| `spawn_agent` | the orchestrator executes roles inline (also when the `task` permission denies) | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace (or `tool.bash` git branch) | `not isolated (no branch capability)` |
| `check_command` | run once to decide | none |
| `run_quality_gate` | run each gate via tool.bash serially | none |
| `ask_user` (`question` unavailable / non-interactive run) | pick the most conservative option and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Runtime Config Overrides

> None — the capability-contract defaults apply: `report.dir=harness-reports/`, `report.prefix=harness-task`, `report.on_disk=true`. (Set `report.on_disk=false` for the 🟢 light channel or temporary sessions; see the capability-contract runtime config.)
>
> **Path base**: `<report.dir>` is project-root-relative — resolve it against the harness working directory (the project root where the session runs, never the skill's own directory) to an absolute path before the first write.
>
> Harness config lives in `.opencode/config.json` (V1) / `opencode.json` (V2, schema `https://opencode.ai/config.json`); the `permission` block sets per-tool / per-skill approval modes (`allow` / `ask` / `deny`). The report config is independent of it.
>
> **Permission config for the validation scripts**: the repo ships an `opencode.json` at the repo root with `permission.bash` allow patterns for `scripts/smoke-report.py` / `scripts/workflow-check.py` / `scripts/consistency-check.py` (plus the `echo exit` exit-code readback) — the opencode equivalent of `.claude/settings.json` under Claude Code.

## 7. Capability-Contract Consistency Self-Check

| Required capability | Implementation in opencode | Status |
|---------------------|-----------------------------|--------|
| read / write / edit / glob / grep | §1 table (tool.read / tool.write / tool.edit + tool.apply_patch / tool.glob / tool.grep) | ☑ |
| run_command | §1 table (tool.bash) | ☑ |
| ask_user | §1 table (tool.question + `ask` approval mode) | ☑ |
| write_report | §1 table (tool.read + tool.edit simulation per templates/write-report.md) | ☑ |

> All checked → the adapter layer is ready; you can run the SKILL.md main flow.

## 8. Known Deviations

| Contract semantics | opencode reality | Handling |
|--------------------|------------------|----------|
| `read` on a directory returns an entry list | `tool.read` lists directory contents on v1.1.60+ (opencode PR #13090); older builds read a single file only | the contract's directory-read semantics is met natively on current builds; on older builds fall back to **tool.list** for directory browsing |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must `read` the target before overwriting; record it in the report if skipped |
| sub-agent environment | subagents can use only built-in tools (MCP tools need a bridge plugin) | the three roles only need built-in tools, so no workaround is required |
| `ask_user` with structured 2~4 options | `tool.question` asks mid-execution; structured option lists depend on the harness version | map `question` → the contract's ask; when unavailable, degrade per §5 |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
