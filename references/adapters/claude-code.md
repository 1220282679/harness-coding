---
name: harness-coding-adapter-claude-code
description: The filled-in adapter layer for the Claude Code harness (v2). Maps the 7 required + 5 optional capabilities from references/capability-contract.md to Claude Code's concrete tools (Read / Write / Edit / Glob / Grep / Bash / AskUserQuestion / Agent / EnterWorktree / WebSearch), and declares quality-gate commands, role mapping, and the static conditional-skill mapping. Read before loading harness-coding under Claude Code (SKILL.md prerequisites).
---

# Adapter Layer: Claude Code

> The filled-in adapter for the Claude Code execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete Claude Code mechanism implements each capability in the contract**.

---

## 1. Capability Mapping Table

> All 12 capabilities (7 required + 5 optional) map to Claude Code primitives as follows. Anything that can't be mapped is marked "unsupported" honestly — never invented.

| Capability | Implementation in Claude Code | Notes |
|------------|-------------------------------|-------|
| `read` | **Read** tool | Reads a single file. **Deviation**: directory reads are NOT supported → use **Glob** (see §6) |
| `write` | **Write** tool | Overwrite-write; the harness enforces "read before overwriting an existing file" |
| `edit` | **Edit** tool | Exact string replacement; `old` must match uniquely or the edit fails (narrow the context); supports `replace_all: true` |
| `glob` | **Glob** tool | Pattern-match to list file paths (e.g. `glob("specs/<slug>/*")` for a task's artifacts) |
| `grep` | **Grep** tool | ripgrep-based content search; matches with `file:line`, supports regex / glob filters |
| `run_command` | **Bash** tool | Runs shell commands (Git Bash on Windows); stdout/stderr/exit_code. The only channel for quality gates |
| `ask_user` | **AskUserQuestion** tool | Supports **batch natively** (up to 4 questions per call) — the contract's batch signature maps 1:1. Mark the recommended option "(Recommended)" and place it first |
| `spawn_agent` | **Agent** tool (optional) | role mapping in §3 |
| `create_branch` | **EnterWorktree** tool, else `git checkout -b` via Bash (optional) | worktree isolation; fallback to a feature branch |
| `check_command` | Bash `command -v <cmd>` (optional) | run once to decide |
| `find_skill` | **Glob** over `.claude/skills/*/SKILL.md` + `~/.claude/skills/*/SKILL.md`, then **Read** each frontmatter `description` to match the query (optional) | a hit is loaded as a conditional skill (§4); no search primitive needed — glob + frontmatter read satisfies the semantics |
| `web_search` | **WebSearch** tool, **WebFetch** for detail pages (optional) | results entering a spec must carry source + retrieval time; AC stays locally executable; missing/degraded → record `not verified online` in spec Assumptions |

## 2. Quality-Gate Commands (project-defined)

> Four gates in a fixed order: lint → format → type → test. Commands are defined by the **project**; the Python stack below is the example toolchain — replace per project.

| Gate | Command | Notes |
|------|---------|-------|
| lint | `ruff check .` | e.g. eslint / gofmt -l |
| format | `ruff format --check .` | e.g. prettier --check |
| type | `mypy --strict .` | e.g. tsc --noEmit |
| test | `pytest --cov=<module>` | coverage sub-gate enforced only when the project declares a threshold (e.g. `[tool.coverage.report] fail_under`); none declared → plain pass/fail, never invent a number |

- Per-task (🟡/🔴): lint / format / type in full + **affected test subset** (e.g. `pytest tests/<module>/`); full test suite is mandatory at close-out re-verification
- Gate N/A: declare in spec/intent `## 门禁豁免` with a reason, reference `GATE-NA(<gate>):` in the task's pasted output — `artifact-check.py` enforces the pairing; never skip silently

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Agent type in Claude Code | Notes |
|------|---------------------------|-------|
| `explorer` | **Explore** agent (read-only) | output goes to `spec.md` Background (orchestrator **replaces** the placeholder) |
| `implementer` | **general-purpose** agent | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | **general-purpose** agent, or a dedicated code-reviewer agent type if registered | graded findings land in the `## Review` section |

> If an agent type is not registered → degrade to the generic agent or inline execution; responsibilities and output contracts stay unchanged.

## 4. Conditional Skill Mapping (static fallback for `find_skill`)

> When `find_skill` is unavailable or returns no hit, fall back to this static table.

| Abstract conditional skill | Loadable skill in Claude Code | Triggered stage |
|---------------------------|-------------------------------|-----------------|
| Isolation skill | `using-git-worktrees` (or **EnterWorktree** directly) | after plan confirmed → before implementation |
| Decision-record skill | `documentation-and-adrs` | after plan confirmed |
| Debugging skill | `systematic-debugging` | after quality-gate failure |
| Simplify skill | `simplify` | after quality-gate pass → before review |
| Security review | `security-review` | after review pass → before close-out re-verification (🔴) |
| Verification skill | `verification-before-completion` | after review pass → before close-out |
| Branch-finishing skill | `finishing-a-development-branch` | after close-out pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in Claude Code | Annotation |
|--------------------|-------------------------------------|------------|
| `ask_user` (headless, e.g. `claude -p`) | pick the most conservative option (fewest irreversible side effects) and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | the orchestrator executes roles inline | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace | `not isolated (no branch capability)` |
| `check_command` | run once via Bash | none |
| `find_skill` | static conditional-skill table (§4) | none |
| `web_search` | record `not verified online` in spec Assumptions | none |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Capability-Contract Consistency Self-Check

| Required capability | Implementation in Claude Code | Status |
|---------------------|-------------------------------|--------|
| read / write / edit / glob / grep | §1 table (Read / Write / Edit / Glob / Grep) | ☑ |
| run_command | §1 table (Bash) | ☑ |
| ask_user | §1 table (AskUserQuestion, batch native) | ☑ |

## 7. Known Deviations

| Contract semantics | Claude Code reality | Handling |
|--------------------|--------------------|----------|
| `read` on a directory returns an entry list | the Read tool errors on directories | directory listing via **Glob**; `read` semantics narrowed to files only |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
