---
name: harness-coding-adapter-opencode
description: The filled-in adapter layer for the opencode harness (v2). Maps the 7 required + 5 optional capabilities from references/capability-contract.md to opencode's concrete tools (tool.read / tool.write / tool.edit / tool.apply_patch / tool.bash / tool.grep / tool.glob / tool.list / tool.question / tool.task / tool.skill), and declares quality-gate commands, role mapping, and the static conditional-skill mapping. Read before loading harness-coding under opencode (SKILL.md prerequisites).
---

# Adapter Layer: opencode

> The filled-in adapter for the opencode execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete opencode mechanism implements each capability in the contract**.
>
> **Version note**: opencode's tool surface and config schema evolve across releases; the tool names below follow the convention as of this writing. Directory-read behavior changed in **v1.1.60** (Feb 2026): `tool.read` lists directory contents natively (**last verified 2026-08-20**). The authoritative set is the live tool catalogue of the current session — never assume a tool exists without confirming.

---

## 1. Capability Mapping Table

> All 12 capabilities (7 required + 5 optional) map to opencode primitives as follows. Anything that can't be mapped is marked "unsupported" honestly — never invented. Tool names follow opencode's `tool.<name>` convention; per-tool permission (`allow` / `ask` / `deny`) is configured in the harness config (see §6).

| Capability | Implementation in opencode | Notes |
|------------|-----------------------------|-------|
| `read` | **tool.read** | Returns file content tagged with line numbers; also lists directory contents on v1.1.60+ natively. **tool.list** remains available for explicit directory browsing (see §7) |
| `write` | **tool.write** | Create / overwrite a file; gated by the `edit` permission key. Read-before-overwrite is a contract convention, **not enforced** → follow it manually (see §7) |
| `edit` | **tool.edit** (string replacement) or **tool.apply_patch** (unified diff) | Unique-match rule: a `tool.edit` with multiple matches needs a narrower context. Both gated by the `edit` permission key |
| `glob` | **tool.glob** | pattern-match file listing (e.g. `specs/<slug>/*`) |
| `grep` | **tool.grep** | regex content search, ripgrep-style; matches with file:line |
| `run_command` | **tool.bash** | The only channel for quality gates. Permission `bash` supports an allow/ask/deny mode plus a command glob-pattern map |
| `ask_user` | **tool.question** | Asks the user mid-execution. Batch: `tool.question` handles one question per call → serial asks within the same clarification round (see §7). When unavailable (non-interactive run) → degrade per §5 |
| `spawn_agent` | **tool.task** (optional) | Spawns a subagent defined in `.opencode/agents/` (or `~/.config/opencode/agents/`); also invoked via `@<name>` mentions. Subagents can use only built-in tools (see §7) |
| `create_branch` | **tool.bash** `git checkout -b <name>` (optional) | no native worktree primitive; a worktree = `tool.bash` + `git worktree add` |
| `check_command` | **tool.bash** `command -v <cmd>` (optional) | run once to decide |
| `find_skill` | **tool.glob** over `.opencode/skills/*/SKILL.md` + `~/.config/opencode/skills/*/SKILL.md` (+ portable `.claude/skills/` / `.agents/skills/`), then **tool.read** each frontmatter `description` to match; load a hit via **tool.skill** (optional) | restart opencode after adding a skill |
| `web_search` | No bundled search primitive → via an MCP search plugin if configured, else **tool.bash** + `curl` against an allowed API (optional; verify at setup) | results entering a spec must carry source + retrieval time; AC stays locally executable; missing/degraded → record `not verified online` in spec Assumptions |

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

> Roles are dispatched via **tool.task**; subagents are gated by the `task` permission key. Custom agents are Markdown files with YAML frontmatter in `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md` (global); the filename becomes the agent name. Scaffold with `opencode agent create`.

| Role | Agent type in opencode | Notes |
|------|-------------------------|-------|
| `explorer` | built-in **`explore`** subagent | read-only: read / grep / glob / list; output goes to `spec.md` Background (orchestrator **replaces** the placeholder) |
| `implementer` | built-in **`general`** subagent, or a custom agent in `.opencode/agents/` | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | a custom read-only reviewer agent (e.g. `.opencode/agents/reviewer.md`, `mode: subagent`, `permission` allows `bash` for gate rechecks), else **`general`** with the reviewer dispatch prompt | graded findings land in the `## Review` section |

## 4. Conditional Skill Mapping (static fallback for `find_skill`)

> opencode loads skills as SKILL.md packages from `.opencode/skills/` (project) and `~/.config/opencode/skills/` (global), and also reads the portable `.claude/skills/` and `.agents/skills/` paths — existing Claude Code skill packages can be reused as-is. Skills are invoked via the **tool.skill** tool. When `find_skill` is unavailable or returns no hit, fall back to this static table.

| Abstract conditional skill | Loadable skill in opencode | Triggered stage |
|---------------------------|----------------------------|-----------------|
| Isolation skill | port `using-git-worktrees` → `.opencode/skills/using-git-worktrees/SKILL.md` (or `tool.bash` git worktree) | after plan confirmed → before implementation |
| Decision-record skill | port `documentation-and-adrs` → `.opencode/skills/documentation-and-adrs/SKILL.md` | after plan confirmed |
| Debugging skill | port `systematic-debugging` → `.opencode/skills/systematic-debugging/SKILL.md` | after quality-gate failure |
| Simplify skill | port `simplify` → `.opencode/skills/simplify/SKILL.md` | after quality-gate pass → before review |
| Security review | port `security-review` → `.opencode/skills/security-review/SKILL.md` | after review pass → before close-out re-verification (🔴) |
| Verification skill | port `verification-before-completion` → `.opencode/skills/verification-before-completion/SKILL.md` | after review pass → before close-out |
| Branch-finishing skill | port `finishing-a-development-branch` → `.opencode/skills/finishing-a-development-branch/SKILL.md` | after close-out pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in opencode | Annotation |
|--------------------|----------------------------------|------------|
| `ask_user` (`question` unavailable / non-interactive run) | pick the most conservative option and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | the orchestrator executes roles inline (also when the `task` permission denies) | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace (or `tool.bash` git branch) | `not isolated (no branch capability)` |
| `check_command` | run once via tool.bash | none |
| `find_skill` | static conditional-skill table (§4) | none |
| `web_search` | record `not verified online` in spec Assumptions | none |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Permission Config for the Validation Scripts

> The repo ships an `opencode.json` at the repo root with `permission.bash` allow patterns for `scripts/artifact-check.py` / `scripts/derive-report.py` (plus the `echo exit` exit-code readback) — the opencode equivalent of `.claude/settings.json` under Claude Code. When the skill is installed into a target project, declare the same allow patterns in that project's own config.

## 7. Capability-Contract Consistency Self-Check

| Required capability | Implementation in opencode | Status |
|---------------------|-----------------------------|--------|
| read / write / edit / glob / grep | §1 table (tool.read / tool.write / tool.edit + tool.apply_patch / tool.glob / tool.grep) | ☑ |
| run_command | §1 table (tool.bash) | ☑ |
| ask_user | §1 table (tool.question; serial within one clarification round) | ☑ |

## 8. Known Deviations

| Contract semantics | opencode reality | Handling |
|--------------------|------------------|----------|
| `read` on a directory returns an entry list | `tool.read` lists directory contents on v1.1.60+; older builds read a single file only | met natively on current builds; older builds fall back to **tool.list** |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must `read` the target before overwriting |
| `ask_user` batch signature | `tool.question` handles one question per call | serial asks within the same clarification round; when unavailable, degrade per §5 |
| sub-agent environment | subagents can use only built-in tools (MCP tools need a bridge plugin) | the three roles only need built-in tools |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
