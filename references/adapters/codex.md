---
name: harness-coding-adapter-codex
description: The filled-in adapter layer for the OpenAI Codex CLI harness (v2). Maps the 7 required + 5 optional capabilities from references/capability-contract.md to Codex's concrete tools (read_file / apply_patch / shell / rg / glob_file_search / list_dir / spawn_agent), and declares quality-gate commands, role mapping, and the static conditional-skill mapping. Read before loading harness-coding under Codex (SKILL.md prerequisites).
---

# Adapter Layer: OpenAI Codex CLI

> The filled-in adapter for the OpenAI Codex CLI execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete Codex mechanism implements each capability in the contract**.
>
> **Version note**: Codex's tool surface evolves quickly (several patch releases a month). The names below were verified against the stable line at **v0.147 (Aug 2026)** — **last verified 2026-08-20**. The authoritative set is the live tool catalogue of the current session — never assume a tool exists without confirming.

---

## 1. Capability Mapping Table

> All 12 capabilities (7 required + 5 optional) map to Codex primitives as follows. Anything that can't be mapped is marked "unsupported" honestly — never invented.

| Capability | Implementation in Codex | Notes |
|------------|--------------------------|-------|
| `read` | **read_file** tool | Reads a single file's content. **Deviation**: directory reads NOT supported → use **list_dir** (see §6). `shell` (`cat`) is a last-resort fallback |
| `write` | **apply_patch** (create / update) | No standalone overwrite-write tool: create via `*** Add File`, overwrite via `*** Update File` (full V4A diff). Read-before-overwrite is a contract convention, **not enforced** → follow it manually (see §6) |
| `edit` | **apply_patch** (update, V4A diff format) | The `*** Update File` hunk must match uniquely; an ambiguous hunk fails → narrow the context. Equivalent to the contract's unique-match rule |
| `glob` | **glob_file_search** tool | Native glob file search (e.g. `specs/<slug>/*`); on older builds fall back to `shell` + `find`/`ls` |
| `grep` | **rg** tool | Native ripgrep tool; on older builds fall back to `shell` + `rg`/`grep -rn` |
| `run_command` | **shell** / **shell_command** tool | The only channel for quality gates. Execution gated by the harness's approval flow in the interactive TUI |
| `ask_user` | interactive TUI approval prompts (+ optional MCP elicitation) | **No structured batch question primitive in the core.** Interactive mode: the user reviews/approves every command and file change via the TUI approval prompt. A Claude-Code-style batch question can be added via the `mcp-ask-user-question` MCP server (interactive only); without it, serial asks within the same clarification round. Headless `codex exec`: no human in the loop → degrade per §5 |
| `spawn_agent` | **spawn_agent** / **wait_agent** / **close_agent** (optional) | Multi-agent GA since CLI **0.115.0 (Mar 2026)**, enabled by default on current builds. Subagents defined as TOML files in `~/.codex/agents/` (global) / `.codex/agents/` (project) (built-ins `default` / `explorer` / `worker`). Without the feature → inline per §5 |
| `create_branch` | **shell** `git checkout -b <name>`, or native **git** tool (optional) | No worktree primitive; a worktree = `shell` + `git worktree add` |
| `check_command` | **shell** `command -v <cmd>` (optional) | run once to decide |
| `find_skill` | **glob_file_search** over `~/.codex/skills/*/SKILL.md` + `.codex/skills/*/SKILL.md` (+ `~/.agents/skills/` per the cross-runtime Agent Skills Standard), then **read_file** each frontmatter `description` to match (optional) | a hit is loaded as a conditional skill (§4); restart Codex after adding a skill |
| `web_search` | Codex web search — enable `[tools] web_search = true` in `~/.codex/config.toml` on builds that support it (optional; verify at setup with the live tool catalogue) | results entering a spec must carry source + retrieval time; AC stays locally executable; missing/degraded → record `not verified online` in spec Assumptions |

## 2. Quality-Gate Commands (project-defined)

> Four gates in a fixed order: lint → format → type → test. Commands are defined by the **project**; the Python stack below is the example toolchain — replace per project.

| Gate | Command | Notes |
|------|---------|-------|
| lint | `ruff check .` | e.g. eslint / gofmt -l |
| format | `ruff format --check .` | e.g. prettier --check |
| type | `mypy --strict .` | e.g. tsc --noEmit |
| test | `pytest --cov=<module>` | the coverage threshold belongs to this gate |

Full re-run before closing (🟡/🔴 close-out re-verification) is mandatory.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Agent type in Codex | Notes |
|------|----------------------|-------|
| `explorer` | **`explorer`** built-in subagent | read-only recon; output goes to `spec.md` Background (append) |
| `implementer` | **`worker`** built-in subagent, or a custom TOML agent in `.codex/agents/` | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | a custom read-only TOML subagent (e.g. `.codex/agents/reviewer.toml`), else **`default`** with the reviewer dispatch prompt | graded findings land in the `## Review` section; the reviewer agent must be allowed to run the gates |

> Custom subagents are TOML files in `~/.codex/agents/` (global) / `.codex/agents/` (project); restart Codex after adding one.

## 4. Conditional Skill Mapping (static fallback for `find_skill`)

> Codex loads skills as SKILL.md packages from `~/.codex/skills/` (global), `.codex/skills/` (project), or `~/.agents/skills/` (cross-runtime Agent Skills Standard). When `find_skill` is unavailable or returns no hit, fall back to this static table. Restart Codex after adding a skill.

| Abstract conditional skill | Loadable skill in Codex | Triggered stage |
|---------------------------|--------------------------|-----------------|
| Isolation skill | port `using-git-worktrees` → `.codex/skills/using-git-worktrees/SKILL.md` (or `shell` git worktree commands) | after plan confirmed → before implementation |
| Decision-record skill | port `documentation-and-adrs` → `.codex/skills/documentation-and-adrs/SKILL.md` | after plan confirmed |
| Debugging skill | port `systematic-debugging` → `.codex/skills/systematic-debugging/SKILL.md` | after quality-gate failure |
| Simplify skill | port `simplify` → `.codex/skills/simplify/SKILL.md` | after quality-gate pass → before review |
| Security review | port `security-review` → `.codex/skills/security-review/SKILL.md` | after review pass → before close-out re-verification (🔴) |
| Verification skill | port `verification-before-completion` → `.codex/skills/verification-before-completion/SKILL.md` | after review pass → before close-out |
| Branch-finishing skill | port `finishing-a-development-branch` → `.codex/skills/finishing-a-development-branch/SKILL.md` | after close-out pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in Codex | Annotation |
|--------------------|-------------------------------|------------|
| `ask_user` (headless exec) | pick the most conservative option and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | the orchestrator executes roles inline (also when `multi_agent` is off) | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace (or `shell` git branch) | `not isolated (no branch capability)` |
| `check_command` | run once via shell | none |
| `find_skill` | static conditional-skill table (§4) | none |
| `web_search` | record `not verified online` in spec Assumptions | none |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Capability-Contract Consistency Self-Check

| Required capability | Implementation in Codex | Status |
|---------------------|--------------------------|--------|
| read / write / edit / glob / grep | §1 table (read_file / apply_patch / rg / glob_file_search) | ☑ |
| run_command | §1 table (shell / shell_command) | ☑ |
| ask_user | §1 table (interactive TUI + optional MCP elicitation; batch via MCP, else serial within one round) | ☐* — interactive only; headless degrades per §5 |

## 7. Known Deviations

| Contract semantics | Codex reality | Handling |
|--------------------|---------------|----------|
| `read` on a directory returns an entry list | `read_file` errors on directories | directory listing via **list_dir**; `read` semantics narrowed to files only |
| `write` / `edit` are dedicated tools | both realized via **apply_patch** (V4A diff) | create via `*** Add File`, update via `*** Update File`; unique-match = an unambiguous hunk |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must `read` the target before overwriting |
| `ask_user` batch signature | no core batch primitive | interactive TUI approvals; `mcp-ask-user-question` for structured questions; else serial within one clarification round; headless → degrade per §5 |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
