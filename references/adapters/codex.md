---
name: harness-coding-adapter-codex
description: The filled-in adapter for the OpenAI Codex CLI. Maps the capability contract to Codex's live tool catalogue under a probe-first rule (probe order + fallback, never a promise that a tool exists), declares the single-entrypoint gate command and its pre-approval requirement, and carries the degradation annotation for each capability inline. Read a section lazily — only when a capability mismatch or a gate is actually reached.
---

# Adapter Layer: OpenAI Codex CLI

> Answers exactly one question: **what concrete Codex mechanism implements each capability**. The live tool catalogue of the current session is authoritative; this file supplies only probe order and fallback. Tool names churn across patch releases — probe, never assume.
>
> **Read tiers**: §0–§1 at load (they decide every command); §2–§5 only when that step is actually reached.

## 0. Approval & Command Discipline (read before the first command)

Codex asks for approval on every **new** command prefix and writes each approval back into the session's world state, which sits near the front of the prompt. An approval mid-session therefore invalidates the cache for the whole conversation: the next turn re-bills the entire context at full price. Measured on a 371-turn session: cache read fell from ~116k to 3.7k on the turn after each approval, ~$0.24 each, 27 approvals ≈ 58% of all wasted tokens.

1. **One entrypoint per project** — the exact gate string declared in §2, reused verbatim, never retyped with variations.
2. **Pre-approve it** — register the entrypoint in the approved-prefix list / sandbox allowlist before the session starts. Target: ≤3 approvals per session.
3. **No nested shells** — `powershell.exe -Command "..."`, `cmd /c "..."`, `bash -c "..."` each mint a new prefix and therefore a new approval. Never wrap a command that way.
4. **No repeated preamble** — do not re-declare `[Console]::OutputEncoding` or `$ErrorActionPreference` per call; bake them into the entrypoint script.
5. **One command, one job** — no `;` / `&&` piles of unrelated steps. A 900-character one-liner is a brand-new prefix every time it is retyped.

## 1. Capability Mapping (probe order → fallback, annotation inline)

> `find_skill` is deliberately absent: per the contract it resolves context-first and the adapter carries no skill-loading logic.

| Capability | Probe order | Fallback + annotation |
|------------|-------------|-----------------------|
| `read` | native file reader → `shell` reading one file | required, no fallback → mark "unsupported capabilities" |
| `write` | `apply_patch` `*** Add File` → `shell` redirect | required, no fallback |
| `edit` | `apply_patch` `*** Update File` (unique hunk) | read+write composition in one turn (contract §2) |
| `glob` | native glob tool → `rg --files` | `shell` + `find` / `ls` |
| `grep` | native ripgrep tool → `shell rg` | `Select-String` / `grep -rn` |
| `run_command` | `shell` / `shell_command` / `exec_command` | required — the only gate channel |
| `ask_user` | TUI approval prompt → `mcp-ask-user-question` | serial asks in one round; headless → `⚠️ unable to ask the user; decided on the conservative option` |
| `spawn_agent` | `spawn_agent` → `wait_agent` (probe once) | inline, serial → `no sub-agent, inline execution` |
| `create_branch` | native git tool → `shell git checkout -b` | main workspace → `not isolated (no branch capability)` |
| `check_command` | `shell` + `command -v` | treat as absent, no annotation |
| `web_search` | built-in web search, if enabled for the build | `not verified online` in spec Assumptions |

> Directory reads are not `read`: use `list_dir` when present, else `shell` listing. `write`/`edit` have no dedicated tool — both go through `apply_patch`, where unique-match means an unambiguous hunk.

## 2. Quality-Gate Commands — one entrypoint, four verbs

> The project declares **one** entrypoint; the four gates are its verbs. The adapter records the entrypoint once and the gate table carries only verbs, so the command string never drifts between runs (§0).

```text
<entrypoint> lint      # project-defined, e.g. ruff check . / eslint
<entrypoint> format    # check-only by default
<entrypoint> type      # e.g. mypy --strict . / tsc --noEmit
<entrypoint> test      # optional subset arg: <entrypoint> test <path>
```

- Pre-approve `<entrypoint>` (§0 rule 2) so gate runs never raise an approval prompt.
- Per task (🟡/🔴): lint / format / type in full + the **affected test subset**; the full suite is mandatory at close-out re-verification.
- Coverage sub-gate: only when the project declares a threshold (e.g. `[tool.coverage.report] fail_under`); none declared → plain pass/fail, never invent a number.
- Gate N/A: declare `- GATE-NA(<gate>): <reason + scope>` in spec/intent `Gate Exemptions` and reference `GATE-NA(<gate>):` in the task output — `artifact-check.py` enforces the pairing.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Probe | If absent |
|------|-------|-----------|
| `explorer` | `explorer` built-in → read-only custom agent | inline; output still replaces the `spec.md` Background placeholder |
| `implementer` | `worker` built-in → custom TOML agent | inline; still checks off tasks with pasted gate output |
| `reviewer` | read-only custom agent (`.codex/agents/reviewer.toml`) → `default` + reviewer prompt | inline; graded findings still land in `## Review` |

> Custom subagents are TOML files under `~/.codex/agents/` (global) or `.codex/agents/` (project); restart Codex after adding one. Responsibilities and output contracts are unchanged either way.

## 4. Runtime Probe Checklist

> Run once at session start, before the first command. This is a runtime probe, never a build-time claim — the adapter is not "verified against version X".

- [ ] `read` / `write` / `edit` / `glob` / `grep` / `run_command` resolvable — otherwise stop and mark "unsupported capabilities"
- [ ] `spawn_agent` present? absent → inline (§3)
- [ ] `ask_user` batch primitive present? absent → serial, or the headless annotation
- [ ] `web_search` enabled? absent → record `not verified online`
- [ ] gate `<entrypoint>` already approved? if not, get it pre-approved (§0) **before** running any gate

Record every failed probe as a deviation instead of silently taking the fallback.

## 5. Known Deviations

| Contract semantics | Codex reality | Handling |
|--------------------|---------------|----------|
| `read` on a directory returns an entry list | the native reader errors on directories | `list_dir`; `read` narrowed to files |
| `write` / `edit` are dedicated tools | both realized via `apply_patch` | `*** Add File` / `*** Update File`, unique hunk = unambiguous hunk |
| read-before-overwrite guardrail | not enforced by the harness | the orchestrator must read the target before overwriting |
| `ask_user` batch signature | no core batch primitive | TUI approvals; `mcp-ask-user-question`; else serial within one round |

> A deviation that blocks a required capability is annotated at the top of this file and handled by the capability's fallback column — never invented away.
