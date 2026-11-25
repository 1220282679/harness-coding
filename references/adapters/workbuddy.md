---
name: harness-coding-adapter-workbuddy
description: The filled-in adapter for the WorkBuddy harness. Maps the capability contract to WorkBuddy's live tool catalogue under a probe-first rule (probe order + fallback, never a promise that a tool exists), declares the single-entrypoint gate command and how to pre-approve it when the surface has no permission file, and carries the degradation annotation for each capability inline. Read a section lazily — only when a capability mismatch or a gate is actually reached.
---

# Adapter Layer: WorkBuddy

> Answers exactly one question: **what concrete WorkBuddy mechanism implements each capability**. The live tool catalogue of the current session is authoritative; this file supplies only probe order and fallback.
>
> **Read tiers**: §0–§1 before the first command (they decide every command); §2 at the first gate; §3 at dispatch; §4–§5 as reference.

## 0. Approval & Command Discipline (read before the first command)

WorkBuddy prompts on the **first use of a command**, and it exposes **two** command tools — **Bash** (POSIX sh / Git Bash) and **PowerShell** (Windows-native). The same job expressed through the other shell is a different command, so mixing them multiplies the prompts. There is no repo-shipped permission file (unlike `.claude/settings.json` / `opencode.json`): approval is per session, and the approval state is part of what the harness injects — treat it as a prefix change.

1. **One entrypoint per project** — the exact gate string declared in §2, reused verbatim.
2. **Pre-approve it once** — approve the entrypoint and the three runtime scripts at session start (or add allow rules if the surface offers them). Target: ≤3 approvals per session; never widen the allowlist beyond the entrypoint + `scripts/{artifact-check,derive-report,find-skill}.py`.
3. **Pick one shell per project** — decide Bash *or* PowerShell for the gate entrypoint and never express the same gate the other way; two spellings are two prefixes and two prompts.
4. **No nested shells** — `bash -c "..."` / `powershell -Command "..."` / `cmd /c "..."` each mint a new command head and prompt again. Never wrap a command that way.
5. **No repeated preamble** — `[Console]::OutputEncoding`, `$ErrorActionPreference`, `chcp`, `set -e` belong inside the entrypoint script, not in front of every call. A sandbox-rejected command needs user-approved escalation: that counts as an `ask_user` decision, is recorded, and is never used to bypass a failed gate.

## 1. Capability Mapping (probe order → fallback, annotation inline)

> `find_skill` is deliberately absent: per the contract it resolves context-first (native **Skill** tool + **ToolSearch** for deferred discovery) and the adapter carries no skill-loading logic.

| Capability | Probe order | Fallback + annotation |
|------------|-------------|-----------------------|
| `read` | **Read** (file with line numbers; **ViewImage** for images) | required, no fallback → mark "unsupported capabilities" |
| `write` | **Write** | create/overwrite; the harness enforces read-before-overwrite |
| `edit` | **Edit** (exact match, `replace_all`) | narrow the context until `old` is unique |
| `glob` | **Glob** → Bash `find` | pattern listing, e.g. `specs/<slug>/*` |
| `grep` | **Grep** (ripgrep) → Bash `grep -rn` | returns `file:line`, regex + glob filters |
| `run_command` | **Bash** (POSIX, Git Bash) → **PowerShell** for Windows-native tasks | required — the only gate channel; Bash is sandboxed by default |
| `ask_user` | **AskUserQuestion** (batch native, ≤4 questions, 2–4 options each, recommended first) | headless → conservative option + `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | **Agent** (probe `Explore` for recon) | inline serial → `no sub-agent, inline execution` |
| `create_branch` | Bash `git checkout -b` → `git worktree add` | main workspace → `not isolated (no branch capability)` |
| `check_command` | Bash / PowerShell `command -v` / `Get-Command` | treat as absent, no annotation |
| `web_search` | **WebSearch** → **WebFetch** for detail pages | `not verified online` in spec Assumptions |

> Directory reads are not `read`: use **Glob** for an entry list. The native task tools (TaskCreate / TaskUpdate / TaskList) may mirror progress for the user but **never** become the source of truth — checkboxes in `tasks.md` / `intent.md` stay canonical.

## 2. Quality-Gate Commands — one entrypoint, four verbs

> The project declares **one** entrypoint; the four gates are its verbs. Record the entrypoint once so the command string never drifts between runs (§0).

```text
<entrypoint> lint      # project-defined, e.g. ruff check . / eslint
<entrypoint> format    # check-only by default
<entrypoint> type      # e.g. mypy --strict . / tsc --noEmit
<entrypoint> test      # optional subset arg: <entrypoint> test <path>
```

- Pre-approve `<entrypoint>` (§0 rule 2) so gate runs never prompt.
- Per task (🟡/🔴): lint / format / type in full + the **affected test subset**; the full suite is mandatory at close-out re-verification.
- Coverage sub-gate: only when the project declares a threshold (e.g. `[tool.coverage.report] fail_under`); none declared → plain pass/fail, never invent a number.
- Gate N/A: declare `- GATE-NA(<gate>): <reason + scope>` in spec/intent `Gate Exemptions` and reference `GATE-NA(<gate>):` in the task output — `artifact-check.py` enforces the pairing.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Probe | If absent |
|------|-------|-----------|
| `explorer` | **Explore** sub-agent (read-only) | inline; output still replaces the `spec.md` Background placeholder |
| `implementer` | **general-purpose** sub-agent | inline; still checks off tasks with pasted gate output |
| `reviewer` | **general-purpose** + reviewer dispatch prompt | inline; graded findings still land in `## Review` |

> Sub-agents run in an isolated context with no shared-memory shortcut — dispatch prompts carry a task pointer + role discipline only, and the sub-agent reads the artifacts itself.

## 4. Runtime Probe Checklist

> Run once at session start, before the first command. This is a runtime probe, never a build-time claim — the adapter is not "verified against version X".

- [ ] `read` / `write` / `edit` / `glob` / `grep` / `run_command` resolvable — otherwise stop and mark "unsupported capabilities"
- [ ] which shell owns the gate entrypoint — Bash or PowerShell? decide once (§0 rule 3)
- [ ] `spawn_agent` present? absent → inline (§3)
- [ ] `ask_user` available (interactive run)? absent → conservative option + annotation
- [ ] `web_search` enabled? absent → record `not verified online`
- [ ] gate `<entrypoint>` already approved? if not, approve it (§0) **before** running any gate

Record every failed probe as a deviation instead of silently taking the fallback.

## 5. Known Deviations

| Contract semantics | WorkBuddy reality | Handling |
|--------------------|-------------------|----------|
| `read` on a directory returns an entry list | **Read** errors on directories | **Glob** for entry lists; `read` narrowed to files |
| artifacts are the only task state | native Task tools exist and look authoritative | artifacts stay canonical; on recovery read `tasks.md`, not the task list |
| `run_command` is one channel | Bash **and** PowerShell, with different sandbox behavior | one shell per project (§0 rule 3); escalation is a recorded `ask_user` decision |
| validation-script permissions | no repo-shipped permission file; prompts on first use | approve the three scripts once per session, or add allow rules if the surface offers them |

> A deviation that blocks a required capability is annotated at the top of this file and handled by the capability's fallback column — never invented away.
