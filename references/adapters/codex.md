---
name: harness-coding-adapter-codex
description: The filled-in adapter layer for the OpenAI Codex CLI harness. Maps the 8 required + 4 optional capabilities from references/capability-contract.md to Codex's concrete tools (read_file / apply_patch / shell / rg / glob_file_search / list_dir / spawn_agent), and declares quality-gate commands, role mapping, and conditional-skill mapping. Read before loading harness-coding under Codex (SKILL.md prerequisites).
---

# Adapter Layer: OpenAI Codex CLI

> This is the filled-in adapter for the OpenAI Codex CLI execution harness. The methodology body (SKILL.md) and the capability contract (references/capability-contract.md) stay unchanged; this file answers exactly one question: **what concrete Codex mechanism implements each capability in the contract**.
>
> Generated from `references/adapters/_adapter-template.md`; the "how to generate" section has been removed.
>
> **Version note**: Codex's tool surface has evolved through 2026 (early builds routed grep/glob through `shell`, composing `rg`/`find`; native `rg`, `glob_file_search`, `list_dir`, `git` tools have existed since the 2025/2026 builds). The tool names and feature flags below were verified against the stable line at **v0.147 (Aug 2026)** — **last verified 2026-08-20**; the CLI ships several patch releases a month, so any version pin goes stale quickly. The table uses the current native names and marks the older/composed fallbacks. The authoritative set is the live tool catalogue of the current session (`codex --help`, the tool list, or `tool_search`) — never assume a tool exists without confirming.

---

## 1. Capability Mapping Table

> All 12 capabilities (8 required + 4 optional) map to Codex primitives as follows. Anything that can't be mapped is marked "unsupported" honestly — never invented.

| Capability | Implementation in Codex | Notes |
|------------|--------------------------|-------|
| `read` | **read_file** tool | Reads a single file's content. **Deviation**: directory reads are NOT supported → use **list_dir** (see §8). `shell` (`cat`) is a last-resort fallback |
| `write` | **apply_patch** (create / update) | No standalone overwrite-write tool: create via `*** Add File`, overwrite via `*** Update File` (full V4A diff). Read-before-overwrite is a contract convention, **not enforced** by Codex — follow it manually (see §8) |
| `edit` | **apply_patch** (update, V4A diff format) | The `*** Update File` hunk must match uniquely; an ambiguous hunk fails → narrow the context. Equivalent to the contract's unique-match rule |
| `glob` | **glob_file_search** tool | Native glob file search; on older builds fall back to `shell` + `find`/`ls` |
| `grep` | **rg** tool | Native ripgrep tool (regex, type filtering, context lines); on older builds fall back to `shell` + `rg`/`grep -rn` |
| `run_command` | **shell** / **shell_command** tool | The only channel for quality gates. Execution is gated by the harness's approval flow in the interactive TUI |
| `ask_user` | interactive TUI approval prompts (+ optional MCP elicitation) | **No structured 2~4-option primitive in the core.** Interactive mode: the user reviews/approves every command and file change via the TUI approval prompt. A Claude-Code-style AskUserQuestion can be added via the `mcp-ask-user-question` MCP server (interactive only). Headless `codex exec`: no human in the loop → degrade per §5 |
| `write_report` | **read_file** + **apply_patch** simulation | No dedicated report primitive → simulate per `references/templates/write-report.md` (locate `<!-- PHASE: x -->` marker → append content → replace that one line with `... DONE -->`) |
| `spawn_agent` | **spawn_agent** / **wait_agent** / **close_agent** (optional) | Requires the sub-agent feature: multi-agent went GA in CLI **0.115.0 (Mar 2026)** and is enabled by default on current builds, so setting `[features] multi_agent = true` in `~/.codex/config.toml` is usually unnecessary (and harmless). Subagents defined as TOML files in `~/.codex/agents/` (global) / `.codex/agents/` (project) (built-ins `default` / `explorer` / `worker`). Without the feature → inline per §5 |
| `create_branch` | **shell** `git checkout -b <name>`, or native **git** tool (optional) | No worktree primitive; a worktree = `shell` + `git worktree add` |
| `check_command` | **shell** `command -v <cmd>` (optional) | run once to decide |
| `run_quality_gate` | **shell** running the four gates serially (optional) | no bundled primitive; run each via shell and combine |

## 2. Quality-Gate Commands (project-defined)

> Four gates in a fixed order: lint → format → type → test. Commands are defined by the **project**, not by the harness — the Python stack below is the example toolchain from the contract; replace per project (e.g. eslint / prettier / tsc / vitest).

| Gate | Command | Notes |
|------|---------|-------|
| lint | `ruff check .` | e.g. eslint / gofmt -l |
| format | `ruff format --check .` | e.g. prettier --check |
| type | `mypy --strict .` | e.g. tsc --noEmit |
| test | `pytest --cov=<module>` | the coverage threshold belongs to this gate |

## 3. Role Mapping (optional `spawn_agent` capability)

> Requires the sub-agent feature (GA since CLI **0.115.0**, Mar 2026, enabled by default on current builds; `[features] multi_agent = true` in `~/.codex/config.toml` is usually unnecessary and harmless); otherwise the roles degrade to inline execution in the orchestrator (responsibilities and output contracts stay unchanged).

| Role | Agent type in Codex | Notes |
|------|----------------------|-------|
| `explorer` | **`explorer`** built-in subagent | read-only recon, output with file:line — matches the explorer's "read-only discipline" exactly |
| `implementer` | **`worker`** built-in subagent, or a custom TOML agent in `.codex/agents/` | implementation + tests + quality gates; pass the implementer dispatch prompt |
| `reviewer` | a custom read-only TOML subagent (e.g. `.codex/agents/reviewer.toml`), else **`default`** with the reviewer dispatch prompt | graded findings + quality-gate recheck; the reviewer agent must be allowed to run the gates |

> Custom subagents are TOML files in `~/.codex/agents/` (global) / `.codex/agents/` (project); restart Codex after adding one.

## 4. Conditional Skill Mapping (SKILL.md conditional-trigger table → loadable skills in Codex)

> Codex loads skills as SKILL.md packages (frontmatter `name` + `description`) from `~/.codex/skills/` (global), `.codex/skills/` (project), or `~/.agents/skills/` (cross-runtime Agent Skills Standard, shared with Copilot CLI / Gemini CLI), activated by naming, description match, or another skill's direction. The abstract conditional skills map to ports of the Claude Code skill into a `.codex/skills/` package; the trigger stages stay unchanged. Restart Codex after adding a skill.

| Abstract conditional skill | Loadable skill in Codex | Triggered stage |
|---------------------------|--------------------------|-----------------|
| Isolation skill | port `using-git-worktrees` → `.codex/skills/using-git-worktrees/SKILL.md` (or `shell` git worktree commands) | after plan confirmed → before implementation |
| Decision-record skill | port `documentation-and-adrs` → `.codex/skills/documentation-and-adrs/SKILL.md` | after plan confirmed |
| Debugging skill | port `systematic-debugging` → `.codex/skills/systematic-debugging/SKILL.md` | after quality-gate failure |
| Simplify skill | port `simplify` → `.codex/skills/simplify/SKILL.md` | after quality-gate pass → before review |
| Security review | port `security-review` → `.codex/skills/security-review/SKILL.md` | after review pass → before verification (Full) / before report (Standard) |
| Verification skill | port `verification-before-completion` → `.codex/skills/verification-before-completion/SKILL.md` | after review pass → before summary |
| Branch-finishing skill | port `finishing-a-development-branch` → `.codex/skills/finishing-a-development-branch/SKILL.md` | after summary pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in Codex | Report annotation |
|--------------------|-------------------------------|-------------------|
| `spawn_agent` | the orchestrator executes roles inline (also when `multi_agent` is off) | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace (or `shell` git branch) | `not isolated (no branch capability)` |
| `check_command` | run once to decide | none |
| `run_quality_gate` | run each gate via shell serially | none |
| `ask_user` (headless exec) | pick the most conservative option and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Runtime Config Overrides

> None — the capability-contract defaults apply: `report.dir=harness-reports/`, `report.prefix=harness-task`, `report.on_disk=true`. (Set `report.on_disk=false` for the 🟢 light channel or temporary sessions; see the capability-contract runtime config.)
>
> **Path base**: `<report.dir>` is project-root-relative — resolve it against the harness working directory (the project root where the session runs, never the skill's own directory) to an absolute path before the first write.
>
> **First-run setup (one-time, machine-level)**: the harness config lives in `~/.codex/config.toml` (global) or project `.codex/config.toml`; the report config is independent of it. To run the full harness flow under Codex:
>
> 1. **Enable sub-agent dispatch** — multi-agent is GA and enabled by default since CLI **0.115.0 (Mar 2026)**; on older builds set `[features] multi_agent = true` in `~/.codex/config.toml` (harmless either way). `shell_tool` is a stable default-on feature — no need to touch it. Without the feature, `spawn_agent` degrades to inline execution per §5
> 2. **Structured `ask_user` (interactive only)** — `codex mcp add ask-user-question -- npx -y mcp-ask-user-question` (verify the server name and command at setup time with `codex mcp list` — the exact package may change); headless `codex exec` has no human in the loop → degrade per §5
> 3. **Restart Codex** after editing `config.toml` or adding skills / agents — changes only take effect on restart
>
> **Permission note**: Codex's per-command allowlisting lives in **execpolicy rules**, not in the `approval_policy` config key (a single string like `"on-request"`, with no command patterns). To run the validation scripts without pausing in the interactive TUI, write Starlark rules to `~/.codex/rules/default.rules`:
>
> ```python
> # ~/.codex/rules/default.rules
> prefix_rule(pattern = ["python", "scripts/consistency-check.py"], decision = "allow", justification = "harness-coding dev-time validator")
> prefix_rule(pattern = ["python", "scripts/smoke-report.py"], decision = "allow", justification = "harness-coding dev-time validator")
> prefix_rule(pattern = ["python", "scripts/workflow-check.py"], decision = "allow", justification = "harness-coding dev-time validator")
> ```
>
> Test with `codex execpolicy check --rules ~/.codex/rules/default.rules -- python scripts/consistency-check.py`. Note: execpolicy is still in preview and its API may change; without such rules, running the validators pauses for approval as usual.

## 7. Capability-Contract Consistency Self-Check

| Required capability | Implementation in Codex | Status |
|---------------------|--------------------------|--------|
| read / write / edit / glob / grep | §1 table (read_file / apply_patch / rg / glob_file_search) | ☑ |
| run_command | §1 table (shell / shell_command) | ☑ |
| ask_user | §1 table (interactive TUI approval prompts + optional MCP elicitation) | ☐* — interactive only, no structured 2~4-option primitive in the core; headless `codex exec` degrades per §5 (see §8) |
| write_report | §1 table (read_file + apply_patch simulation per templates/write-report.md) | ☑ |

> All checked → the adapter layer is ready; you can run the SKILL.md main flow.

## 8. Known Deviations

| Contract semantics | Codex reality | Handling |
|--------------------|---------------|----------|
| `read` on a directory returns an entry list | `read_file` errors on directories | directory listing is performed via **list_dir**; `read` semantics are narrowed to files only |
| `write` / `edit` are dedicated tools | both are realized via **apply_patch** (V4A diff format) | create via `*** Add File`, update via `*** Update File`; the unique-match rule = an unambiguous hunk, otherwise narrow the context |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must `read` the target before overwriting; record it in the report if skipped |
| `ask_user` with structured 2~4 options | no core primitive; interactive-only + optional MCP elicitation | interactive TUI approval prompts; `mcp-ask-user-question` for a structured question; headless → degrade per §5 |
| `spawn_agent` | requires the sub-agent feature (`[features] multi_agent = true`; recent builds may enable it by default) | annotate `multi_agent not enabled` in the report when degraded |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
