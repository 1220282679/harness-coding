---
name: harness-coding-adapter-codex
description: The filled-in adapter layer for the OpenAI Codex CLI harness (v2). Maps the capability contract (7 required + 4 mapped optional) to Codex's concrete tools (read_file / apply_patch / shell / rg / glob_file_search / list_dir / spawn_agent), and declares quality-gate commands and role mapping. `find_skill` resolves context-first per SKILL.md §7 and needs no adapter mapping. Read before loading harness-coding under Codex (SKILL.md prerequisites).
---

# Adapter Layer: OpenAI Codex CLI

> The filled-in adapter for the OpenAI Codex CLI execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete Codex mechanism implements each capability in the contract**.
>
> **Version note**: Codex's tool surface evolves quickly (several patch releases a month). The names below were verified against the stable line at **v0.147 (Aug 2026)** — **last verified 2026-08-20**. The authoritative set is the live tool catalogue of the current session — never assume a tool exists without confirming.

---

## 1. Capability Mapping Table

> All capabilities except `find_skill` map to Codex primitives as follows (`find_skill` resolves context-first per SKILL.md §7 — no mapping needed). Anything that can't be mapped is marked "unsupported" honestly — never invented.

| Capability | Implementation in Codex | Notes |
|------------|--------------------------|-------|
| `read` | **read_file** tool | Reads a single file's content. **Deviation**: directory reads NOT supported → use **list_dir** (see §6). `shell` (`cat`) is a last-resort fallback |
| `write` | **apply_patch** (create / update) | No standalone overwrite-write tool: create via `*** Add File`, overwrite via `*** Update File` (full V4A diff). Read-before-overwrite is a contract convention, **not enforced** → follow it manually (see §6) |
| `edit` | **apply_patch** (update, V4A diff format) | The `*** Update File` hunk must match uniquely; an ambiguous hunk fails → narrow the context. Equivalent to the contract's unique-match rule |
| `glob` | **glob_file_search** tool | Native glob file search (e.g. `specs/<slug>/*`); on older builds fall back to `shell` + `find`/`ls` |
| `grep` | **rg** tool | Native ripgrep tool; on older builds fall back to `shell` + `rg`/`grep -rn` |
| `run_command` | **shell** / **shell_command** tool | The only channel for quality gates. Execution gated by the harness's approval flow in the interactive TUI |
| `ask_user` | interactive TUI approval prompts (+ optional MCP elicitation) | **No structured batch question primitive in the core.** Interactive mode: the user reviews/approves every command and file change via the TUI approval prompt. A Claude-Code-style batch question can be added via the `mcp-ask-user-question` MCP server (interactive only); without it, serial asks within the same clarification round. Headless `codex exec`: no human in the loop → degrade per §4 |
| `spawn_agent` | **spawn_agent** / **wait_agent** / **close_agent** (optional) | Multi-agent GA since CLI **0.115.0 (Mar 2026)**, enabled by default on current builds. Subagents defined as TOML files in `~/.codex/agents/` (global) / `.codex/agents/` (project) (built-ins `default` / `explorer` / `worker`). Without the feature → inline per §4 |
| `create_branch` | **shell** `git checkout -b <name>`, or native **git** tool (optional) | No worktree primitive; a worktree = `shell` + `git worktree add` |
| `check_command` | **shell** `command -v <cmd>` (optional) | run once to decide |
| `web_search` | Codex web search — enable `[tools] web_search = true` in `~/.codex/config.toml` on builds that support it (optional; verify at setup with the live tool catalogue) | results entering a spec must carry source + retrieval time; AC stays locally executable; missing/degraded → record `not verified online` in spec Assumptions |

## 2. Quality-Gate Commands (project-defined)

> Four gates in a fixed order: lint → format → type → test. Commands are **project-defined** — replace all four rows per project; the Notes column lists cross-stack examples, never a harness mandate.

| Gate | Command | Notes |
|------|---------|-------|
| lint | `<project-defined>` | Python e.g. `ruff check .`; JS: eslint; Go: gofmt -l |
| format | `<project-defined>` | Python e.g. `ruff format --check .`; JS: prettier --check |
| type | `<project-defined>` | Python e.g. `mypy --strict .`; JS: tsc --noEmit |
| test | `<project-defined>` | Python e.g. `pytest --cov=<module>` (coverage sub-gate enforced only when the project declares a threshold, e.g. `[tool.coverage.report] fail_under`; none declared → plain pass/fail, never invent a number) |

- Per-task (🟡/🔴): lint / format / type in full + **affected test subset** (e.g. `pytest tests/<module>/`); full test suite is mandatory at close-out re-verification
- Gate N/A: declare in spec/intent `## Gate Exemptions` with a reason, reference `GATE-NA(<gate>):` in the task's pasted output — `artifact-check.py` enforces the pairing; never skip silently

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Agent type in Codex | Notes |
|------|----------------------|-------|
| `explorer` | **`explorer`** built-in subagent | read-only recon; output goes to `spec.md` Background (orchestrator **replaces** the placeholder) |
| `implementer` | **`worker`** built-in subagent, or a custom TOML agent in `.codex/agents/` | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | a custom read-only TOML subagent (e.g. `.codex/agents/reviewer.toml`), else **`default`** with the reviewer dispatch prompt | graded findings land in the `## Review` section; the reviewer agent must be allowed to run the gates |

> Custom subagents are TOML files in `~/.codex/agents/` (global) / `.codex/agents/` (project); restart Codex after adding one.

## 4. Degradation Rule Declarations

| Missing capability | Degradation behavior in Codex | Annotation |
|--------------------|-------------------------------|------------|
| `ask_user` (headless exec) | pick the most conservative option and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | the orchestrator executes roles inline (also when `multi_agent` is off) | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace (or `shell` git branch) | `not isolated (no branch capability)` |
| `check_command` | run once via shell | none |
| `find_skill` | context-first per SKILL.md §7; no library at all → record `skill library unavailable` | environment flag when absent |
| `web_search` | record `not verified online` in spec Assumptions | none |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 5. Capability-Contract Consistency Self-Check

| Required capability | Implementation in Codex | Status |
|---------------------|--------------------------|--------|
| read / write / edit / glob / grep | §1 table (read_file / apply_patch / rg / glob_file_search) | ☑ |
| run_command | §1 table (shell / shell_command) | ☑ |
| ask_user | §1 table (interactive TUI + optional MCP elicitation; batch via MCP, else serial within one round) | ☐* — interactive only; headless degrades per §4 |

## 6. Known Deviations

| Contract semantics | Codex reality | Handling |
|--------------------|---------------|----------|
| `read` on a directory returns an entry list | `read_file` errors on directories | directory listing via **list_dir**; `read` semantics narrowed to files only |
| `write` / `edit` are dedicated tools | both realized via **apply_patch** (V4A diff) | create via `*** Add File`, update via `*** Update File`; unique-match = an unambiguous hunk |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must `read` the target before overwriting |
| `ask_user` batch signature | no core batch primitive | interactive TUI approvals; `mcp-ask-user-question` for structured questions; else serial within one clarification round; headless → degrade per §4 |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
