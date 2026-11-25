---
name: harness-coding-adapter-claude-code
description: The filled-in adapter for the Claude Code harness. Maps the capability contract to Claude Code's live tool catalogue under a probe-first rule (probe order + fallback, never a promise that a tool exists), declares the single-entrypoint gate command and its pre-approval requirement via `.claude/settings.json`, and carries the degradation annotation for each capability inline. Read a section lazily — only when a capability mismatch or a gate is actually reached.
---

# Adapter Layer: Claude Code

> Answers exactly one question: **what concrete Claude Code mechanism implements each capability**. The live tool catalogue of the current session is authoritative; this file supplies only probe order and fallback.
>
> **Read tiers**: §0–§1 before the first command (they decide every command); §2 at the first gate; §3 at dispatch; §4–§5 as reference.

## 0. Approval & Command Discipline (read before the first command)

Claude Code matches every `Bash` invocation against the allow patterns in `.claude/settings.json` (project) / `~/.claude/settings.json` (user). **Prefix patterns, not commands**: `Bash(python scripts/artifact-check.py*)` covers any suffix, but a command with a different head does not match and asks. The permission set is injected into the session, so an allow rule added mid-session changes that block — treat every approval as a prefix change, and the whole context behind it as cold on the next turn.

1. **One entrypoint per project** — the exact gate string declared in §2, reused verbatim.
2. **Pre-approve it** — add `Bash(<entrypoint>:*)` to `.claude/settings.json` **before** the session. Target: ≤3 approvals per session. Never rely on "yes, and don't ask again" mid-task: that rule lands halfway through the run.
3. **No nested shells** — `bash -c "..."` / `sh -c "..."` do not match the entrypoint pattern, so each one prompts. Never wrap a command that way.
4. **No repeated preamble** — no per-call `export`, `cd`, `set -e` or env prefix; bake it into the entrypoint script (§2).
5. **One command, one job** — no `;` / `&&` piles. A retyped 900-character one-liner is a new prefix every time.

## 1. Capability Mapping (probe order → fallback, annotation inline)

> `find_skill` is deliberately absent: per the contract it resolves context-first and the adapter carries no skill-loading logic.

| Capability | Probe order | Fallback + annotation |
|------------|-------------|-----------------------|
| `read` | **Read** → `Bash` reading one file | required, no fallback → mark "unsupported capabilities" |
| `write` | **Write** | overwrite-write; the harness enforces read-before-overwrite |
| `edit` | **Edit** (exact match, `replace_all`) | narrow the context until `old` is unique — an ambiguous match fails the edit |
| `glob` | **Glob** → `Bash` `find` / `ls` | pattern listing, e.g. `specs/<slug>/*` |
| `grep` | **Grep** (ripgrep) → `Bash rg` | returns `file:line`, regex + glob filters |
| `run_command` | **Bash** (Git Bash on Windows) | required — the only gate channel |
| `ask_user` | **AskUserQuestion** (batch native, ≤4 questions per call) | headless → conservative option + `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | **Agent** (probe `Explore` for recon) | inline serial → `no sub-agent, inline execution` |
| `create_branch` | **EnterWorktree** → `Bash` `git checkout -b` | main workspace → `not isolated (no branch capability)` |
| `check_command` | `Bash` `command -v` | treat as absent, no annotation |
| `web_search` | **WebSearch** → **WebFetch** for detail pages | `not verified online` in spec Assumptions |

> Directory reads are not `read`: **Read** errors on a directory — use **Glob** for an entry list. Mark the recommended option "(Recommended)" and put it first in an `ask_user` batch.

## 2. Quality-Gate Commands — one entrypoint, four verbs

> The project declares **one** entrypoint; the four gates are its verbs. Record the entrypoint once so the command string never drifts between runs (§0).

```text
<entrypoint> lint      # project-defined, e.g. ruff check . / eslint
<entrypoint> format    # check-only by default
<entrypoint> type      # e.g. mypy --strict . / tsc --noEmit
<entrypoint> test      # optional subset arg: <entrypoint> test <path>
```

- Pre-approve `<entrypoint>:*` in `.claude/settings.json` (§0 rule 2) so gate runs never prompt.
- Per task (🟡/🔴): lint / format / type in full + the **affected test subset**; the full suite is mandatory at close-out re-verification.
- Coverage sub-gate: only when the project declares a threshold (e.g. `[tool.coverage.report] fail_under`); none declared → plain pass/fail, never invent a number.
- Gate N/A: declare `- GATE-NA(<gate>): <reason + scope>` in spec/intent `Gate Exemptions` and reference `GATE-NA(<gate>):` in the task output — `artifact-check.py` enforces the pairing.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Probe | If absent |
|------|-------|-----------|
| `explorer` | **Explore** (read-only) → general-purpose with a recon prompt | inline; output still replaces the `spec.md` Background placeholder |
| `implementer` | **general-purpose** → custom agent type | inline; still checks off tasks with pasted gate output |
| `reviewer` | dedicated code-reviewer agent type → **general-purpose** + reviewer prompt | inline; graded findings still land in `## Review` |

> Sub-agents run in an isolated context and cannot see the parent's conversation — dispatch prompts carry a task pointer + role discipline only, and the sub-agent reads the artifacts itself.

## 4. Runtime Probe Checklist

> Run once at session start, before the first command. This is a runtime probe, never a build-time claim — the adapter is not "verified against version X".

- [ ] `read` / `write` / `edit` / `glob` / `grep` / `run_command` resolvable — otherwise stop and mark "unsupported capabilities"
- [ ] `spawn_agent` present? absent → inline (§3)
- [ ] `ask_user` unavailable headless (`claude -p`)? → conservative option + annotation
- [ ] `web_search` enabled? absent → record `not verified online`
- [ ] gate `<entrypoint>:*` already allowed? if not, add it to `.claude/settings.json` (§0) **before** running any gate

Record every failed probe as a deviation instead of silently taking the fallback.

## 5. Known Deviations

| Contract semantics | Claude Code reality | Handling |
|--------------------|---------------------|----------|
| `read` on a directory returns an entry list | **Read** errors on directories | **Glob** for entry lists; `read` narrowed to files |
| `ask_user` batch signature | native batch, but capped at 4 questions per call | split into rounds of ≤4 — still one clarification round, never serial turns |
| read-before-overwrite guardrail | enforced by the harness | no action needed — unlike the other adapters |
| `create_branch` isolation | **EnterWorktree** may be unavailable in some surfaces | `git checkout -b` via **Bash**, annotation `not isolated` only when neither exists |

> A deviation that blocks a required capability is annotated at the top of this file and handled by the capability's fallback column — never invented away.
