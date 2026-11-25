---
name: harness-coding-adapter-opencode
description: The filled-in adapter for the opencode harness. Maps the capability contract to opencode's live tool catalogue under a probe-first rule (probe order + fallback, never a promise that a tool exists), declares the single-entrypoint gate command and its pre-approval requirement via `opencode.json` permission globs, and carries the degradation annotation for each capability inline. Read a section lazily — only when a capability mismatch or a gate is actually reached.
---

# Adapter Layer: opencode

> Answers exactly one question: **what concrete opencode mechanism implements each capability**. The live tool catalogue of the current session is authoritative; this file supplies only probe order and fallback.
>
> **Read tiers**: §0–§1 before the first command (they decide every command); §2 at the first gate; §3 at dispatch; §4–§5 as reference.

## 0. Approval & Command Discipline (read before the first command)

opencode decides every `tool.bash` call against `permission.bash` in `opencode.json` — a map of **command glob → `allow` / `ask` / `deny`**. A command whose head matches no `allow` glob falls to `ask`. Approval state is part of the session's configuration surface, so an approval taken mid-run changes what the harness injects — treat it as a prefix change, and the whole context behind it as cold on the next turn.

1. **One entrypoint per project** — the exact gate string declared in §2, reused verbatim.
2. **Pre-approve it** — add the entrypoint glob (e.g. `"./gate *": "allow"`) to `opencode.json` **before** the session. Target: ≤3 approvals per session.
3. **No nested shells** — `bash -c "..."` does not match the entrypoint glob, so it prompts every time. Never wrap a command that way.
4. **No repeated preamble** — no per-call `export` / `cd` / `set -e`; bake it into the entrypoint script (§2). The same applies to `write` / `edit`: they are gated by the single `edit` permission key, so widen that key once rather than approving file by file.
5. **One command, one job** — no `;` / `&&` piles; a retyped one-liner is a new prefix every time.

## 1. Capability Mapping (probe order → fallback, annotation inline)

> `find_skill` is deliberately absent: per the contract it resolves context-first and the adapter carries no skill-loading logic.

| Capability | Probe order | Fallback + annotation |
|------------|-------------|-----------------------|
| `read` | **tool.read** (file content with line numbers) | required, no fallback → mark "unsupported capabilities" |
| `write` | **tool.write** | create/overwrite; read-before-overwrite is a convention, **not enforced** — follow it manually |
| `edit` | **tool.edit** (string replacement) → **tool.apply_patch** (unified diff) | unique-match rule: narrow the context until `old` matches once |
| `glob` | **tool.glob** → **tool.bash** `find` | pattern listing, e.g. `specs/<slug>/*` |
| `grep` | **tool.grep** (ripgrep-style) | returns `file:line`, regex + glob filters |
| `run_command` | **tool.bash** | required — the only gate channel |
| `ask_user` | **tool.question** (one question per call) | serial asks **within one clarification round**; unavailable (non-interactive) → conservative option + `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | **tool.task** (agents in `.opencode/agents/` or `~/.config/opencode/agents/`; `@<name>` mention) | inline serial → `no sub-agent, inline execution` |
| `create_branch` | **tool.bash** `git checkout -b` → `git worktree add` | main workspace → `not isolated (no branch capability)` |
| `check_command` | **tool.bash** `command -v` | treat as absent, no annotation |
| `web_search` | configured MCP search plugin → **tool.bash** + `curl` against an allowed API | `not verified online` in spec Assumptions |

> Directory entry lists come from **tool.read** on current builds and from **tool.list** on older ones — probe once, then stay with what answered. Sub-agents can use built-in tools only (MCP tools need a bridge plugin).

## 2. Quality-Gate Commands — one entrypoint, four verbs

> The project declares **one** entrypoint; the four gates are its verbs. Record the entrypoint once so the command string never drifts between runs (§0).

```text
<entrypoint> lint      # project-defined, e.g. ruff check . / eslint
<entrypoint> format    # check-only by default
<entrypoint> type      # e.g. mypy --strict . / tsc --noEmit
<entrypoint> test      # optional subset arg: <entrypoint> test <path>
```

- Pre-approve `<entrypoint>` in `opencode.json` `permission.bash` (§0 rule 2) so gate runs never prompt.
- Per task (🟡/🔴): lint / format / type in full + the **affected test subset**; the full suite is mandatory at close-out re-verification.
- Coverage sub-gate: only when the project declares a threshold (e.g. `[tool.coverage.report] fail_under`); none declared → plain pass/fail, never invent a number.
- Gate N/A: declare `- GATE-NA(<gate>): <reason + scope>` in spec/intent `Gate Exemptions` and reference `GATE-NA(<gate>):` in the task output — `artifact-check.py` enforces the pairing.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Probe | If absent |
|------|-------|-----------|
| `explorer` | built-in **`explore`** subagent (read / grep / glob / list) | inline; output still replaces the `spec.md` Background placeholder |
| `implementer` | built-in **`general`** → custom agent in `.opencode/agents/` | inline; still checks off tasks with pasted gate output |
| `reviewer` | custom read-only agent (`mode: subagent`, `bash` allowed for gate rechecks) → **`general`** + reviewer prompt | inline; graded findings still land in `## Review` |

> Custom agents are Markdown files with YAML frontmatter; the filename becomes the agent name (`opencode agent create` scaffolds one). The `task` permission key gates all dispatches.

## 4. Runtime Probe Checklist

> Run once at session start, before the first command. This is a runtime probe, never a build-time claim — the adapter is not "verified against version X".

- [ ] `read` / `write` / `edit` / `glob` / `grep` / `run_command` resolvable — otherwise stop and mark "unsupported capabilities"
- [ ] directory entry lists: `tool.read` or `tool.list`? probe once, stay with what answered
- [ ] `spawn_agent` (`task` permission not `deny`)? absent → inline (§3)
- [ ] `ask_user` (`question` available, interactive run)? absent → serial within one round, or the headless annotation
- [ ] `web_search` plugin configured? absent → record `not verified online`
- [ ] gate `<entrypoint>` glob already `allow`? if not, add it to `opencode.json` (§0) **before** running any gate

Record every failed probe as a deviation instead of silently taking the fallback.

## 5. Known Deviations

| Contract semantics | opencode reality | Handling |
|--------------------|------------------|----------|
| `read` on a directory returns an entry list | `tool.read` lists entries on current builds; older builds read a single file | current: `read`; older: **tool.list** |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must read the target before overwriting |
| `ask_user` batch signature | `tool.question` takes one question per call | serial asks inside the same clarification round — same round, not extra turns |
| sub-agent environment | subagents reach built-in tools only (MCP needs a bridge) | the three roles need built-in tools only |
| validation-script permissions | no bundled rule for the three runtime scripts | the repo ships `opencode.json` with the three allow globs; a project install must declare the same |

> A deviation that blocks a required capability is annotated at the top of this file and handled by the capability's fallback column — never invented away.
