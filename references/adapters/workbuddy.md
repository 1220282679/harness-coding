---
name: harness-coding-adapter-workbuddy
description: The filled-in adapter layer for the WorkBuddy harness (v2). Maps the capability contract (7 required + 4 mapped optional) to WorkBuddy's concrete tools (Read / Write / Edit / Glob / Grep / Bash / PowerShell / AskUserQuestion / Agent / WebSearch / WebFetch / ToolSearch + Skill), and declares quality-gate commands and role mapping. `find_skill` resolves context-first per SKILL.md §7 and needs no adapter mapping. Read before loading harness-coding under WorkBuddy (SKILL.md prerequisites).
---

# Adapter Layer: WorkBuddy

> The filled-in adapter for the WorkBuddy execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete WorkBuddy mechanism implements each capability in the contract**.
>
> **Version note**: tool names verified against the **live WorkBuddy session authoring this adapter (2026-11-17)** — the strongest verification an adapter can carry. The authoritative set is still the live tool catalogue of the current session; never assume a tool exists without confirming.

---

## 1. Capability Mapping Table

> All capabilities except `find_skill` map to WorkBuddy primitives as follows (`find_skill` resolves context-first per SKILL.md §7 — no mapping needed). Anything that can't be mapped is marked "unsupported" honestly — never invented.

| Capability | Implementation in WorkBuddy | Notes |
|------------|------------------------------|-------|
| `read` | **Read** tool | Reads a single file with line numbers. **Deviation**: directory reads are NOT supported → use **Glob** (see §7); images via **ViewImage** |
| `write` | **Write** tool | Create / overwrite; the harness enforces "read before overwriting an existing file" |
| `edit` | **Edit** tool | Exact string replacement; `old` must match uniquely or the edit fails (narrow the context); supports `replace_all: true` |
| `glob` | **Glob** tool | Pattern-match to list file paths (e.g. `glob("specs/<slug>/*")` for a task's artifacts) |
| `grep` | **Grep** tool | ripgrep-based content search; matches with `file:line`, supports regex / glob filters |
| `run_command` | **Bash** tool (POSIX sh; Git Bash on Windows), **PowerShell** tool for Windows-native tasks | stdout/stderr/exit_code. The only channel for quality gates. Bash runs sandboxed by default; a command the sandbox rejects may be re-run with explicit user-approved escalation — treat that as an `ask_user` decision, never escalate silently |
| `ask_user` | **AskUserQuestion** tool | Supports **batch natively** (up to 4 questions per call, 2–4 options each, recommended first labeled "(Recommended)") — the contract's batch signature maps 1:1 |
| `spawn_agent` | **Agent** tool (optional) | role mapping in §3; sub-agents run in isolated context |
| `create_branch` | **Bash** `git checkout -b <name>` (optional) | no native worktree primitive; a worktree = Bash + `git worktree add` |
| `check_command` | Bash `command -v <cmd>` (optional) | run once to decide |
| `web_search` | **WebSearch** tool, **WebFetch** for detail pages (optional) | results entering a spec must carry source + retrieval time; AC stays locally executable; missing/degraded → record `not verified online` in spec Assumptions |

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

| Role | Agent type in WorkBuddy | Notes |
|------|--------------------------|-------|
| `explorer` | **Explore** sub-agent (read-only) | recon with file:line; output goes to `spec.md` Background (orchestrator **replaces** the placeholder) |
| `implementer` | **general-purpose** sub-agent | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | **general-purpose** sub-agent with the reviewer dispatch prompt | graded findings land in the `## Review` section |

> If a sub-agent type is not registered in the session → degrade to the generic agent or inline execution; responsibilities and output contracts stay unchanged. Dispatch prompts are role discipline + task pointer only — context flows through the artifacts, which the sub-agent reads itself (Agent tool has no shared-memory shortcut by design).

## 4. Degradation Rule Declarations

| Missing capability | Degradation behavior in WorkBuddy | Annotation |
|--------------------|-----------------------------------|------------|
| `ask_user` (headless / non-interactive run) | pick the most conservative option (fewest irreversible side effects) and record it; never pretend the user confirmed | `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | the orchestrator executes roles inline | `no sub-agent, inline execution` |
| `create_branch` | change directly on the main workspace | `not isolated (no branch capability)` |
| `check_command` | run once via Bash | none |
| `find_skill` | context-first per SKILL.md §7; no library at all → record `skill library unavailable` | environment flag when absent |
| `web_search` | record `not verified online` in spec Assumptions | none |
| Other (required capability missing) | fall back to a plain editing session; continue per the degradation rules | mark "unsupported capabilities" at the top of the adapter layer |

## 5. Permission Notes for the Validation Scripts

> WorkBuddy prompts for command permissions on first use; no repo-shipped permission file exists for it (`opencode.json` / `.claude/settings.json` cover the other two harnesses). When the skill is installed into a target project, approve `python scripts/artifact-check.py*`, `python scripts/derive-report.py*` and `python scripts/find-skill.py*` on first run or add equivalent allow rules in the session's permission settings if the surface provides one — never widen the allowlist beyond the three runtime scripts.

## 6. Capability-Contract Consistency Self-Check

| Required capability | Implementation in WorkBuddy | Status |
|---------------------|------------------------------|--------|
| read / write / edit / glob / grep | §1 table (Read / Write / Edit / Glob / Grep) | ☑ |
| run_command | §1 table (Bash / PowerShell) | ☑ |
| ask_user | §1 table (AskUserQuestion, batch native) | ☑ |

## 7. Known Deviations

| Contract semantics | WorkBuddy reality | Handling |
|--------------------|-------------------|----------|
| `read` on a directory returns an entry list | the Read tool errors on directories | directory listing via **Glob**; `read` semantics narrowed to files only |
| Artifacts are the only task state | WorkBuddy offers native task tools (TaskCreate / TaskUpdate / TaskList) | the harness task list may *mirror* progress for the user, but **never** becomes the source of truth — checkboxes in `tasks.md` / `intent.md` stay canonical; on recovery, read the artifacts, not the task list |
| `find_skill` resolution | native **Skill** tool + **ToolSearch** for deferred-tool discovery | context-first order: Skill / ToolSearch → `scripts/find-skill.py` probe (which already scans `~/.workbuddy/skills` in DEFAULT_ROOTS) → static table (SKILL.md §7) |
| Sandbox on `run_command` | Bash runs sandboxed; some commands need explicit user-approved escalation | escalation counts as an `ask_user` decision and is recorded; never escalate to bypass a failed gate |

> If a deviation becomes blocking for a required capability, annotate "unsupported capabilities" at the top of this file and continue per the degradation rules — never invent a mapping.
