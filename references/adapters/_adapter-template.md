---
name: harness-coding-adapter-template
description: The generic adapter template for harness-coding (v2). When onboarding a new harness, copy this file to references/adapters/<harness>.md and fill in section by section - capability mapping under a probe-first rule (probe order + fallback, never a promise that a tool exists), the single-entrypoint gate command and its pre-approval requirement, role mapping, and the degradation annotation per capability. Mark read tiers so the harness only pays for what it reads. Read lazily — a section at a time, only when a capability mismatch or a gate is actually reached.
---

# Adapter Template (for filling in)

> This is the **fill-in template** for the only difference surface between `harness-coding` and an execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete mechanism does the current harness use to implement each capability in the contract**.
>
> **Probe-first, never assert.** Every mapping is a probe order plus a fallback. A tool name written here is a hint about what to try, never a claim that it exists in this session.

---

## How to Generate (delete this section after filling in)

1. Copy this file to `references/adapters/<harness>.md` (the filename identifies the harness)
2. Replace the placeholder content section by section (every "fill-in" cell), then delete this section
3. Add the read-tier line: §0–§1 before the first command, §2 at the first gate, §3 at dispatch, §4–§5 as reference — nothing else is read at load
4. Run one lightweight requirement end-to-end (e.g. fix a typo): the 🟢 channel must complete **without creating any new file**; then run one 🔴 sample to verify artifacts + `artifact-check.py` pass

## 0. Approval & Command Discipline (read before the first command)

> Why this section exists: an approval that lands mid-session rewrites the harness's world state, which sits near the front of the prompt — the whole prompt prefix then misses cache and the next turn re-bills the entire context at full price. Fill in this section for the target harness; keep it to ≤5 rules.

| Question to answer | Notes |
|--------------------|-------|
| Does the harness prompt per **new command prefix**? | if yes, command-string stability is a cost lever, not a style choice |
| Where is the approval recorded? | if it is written into any prompt-injected state, an approval = a cache reset |
| Can the gate entrypoint be pre-approved / allowlisted? | record the exact mechanism so the target is ≤3 approvals per session |
| Does wrapping a command (`<shell> -c "..."`) mint a new prefix? | if yes, ban nesting explicitly |
| Per-call preamble (encoding / error policy) | bake it into the entrypoint script, never repeat it per command |

## 1. Capability Mapping (probe order → fallback, annotation inline)

> Map all capabilities one by one (`find_skill` is excluded — it resolves context-first per SKILL.md and the adapter carries no skill-loading logic). Anything that can't be probed must be honestly marked "unsupported" — never invent one.

| Capability | Probe order | Fallback + annotation |
|------------|-------------|-----------------------|
| `read` | fill-in (native tool → shell) | required, no fallback → mark "unsupported capabilities" |
| `write` | fill-in | overwrite-write; must read before overwriting |
| `edit` | fill-in | exact replacement, old must match uniquely |
| `glob` | fill-in | pattern-match to list paths |
| `grep` | fill-in | returns matches with file:line |
| `run_command` | fill-in | required — the only channel for quality gates |
| `ask_user` | fill-in | batch preferred (questions[] in one round); else serial within one clarification round; headless → conservative option + record |
| `spawn_agent` | fill-in (optional) | inline serial → `no sub-agent, inline execution` |
| `create_branch` | fill-in (optional) | `not isolated (no branch capability)` |
| `check_command` | fill-in (optional) | treat as absent |
| `web_search` | fill-in (optional) | `not verified online` in spec Assumptions |

## 2. Quality-Gate Commands — one entrypoint, four verbs

> The project declares **one** entrypoint; the four gates are its verbs. Record the entrypoint once so the command string never drifts between runs (§0).

```text
<entrypoint> lint      # fill-in
<entrypoint> format    # check-only by default
<entrypoint> type      # fill-in
<entrypoint> test      # optional subset arg
```

- Pre-approve `<entrypoint>` (§0) so gate runs never raise an approval prompt.
- Coverage sub-gate: only when the project declares a threshold; none declared → plain pass/fail, never invent a number.
- Gate N/A: declare `- GATE-NA(<gate>): <reason + scope>` in spec/intent `Gate Exemptions` and reference it in the task output — `artifact-check.py` enforces the pairing.
- Full re-run before closing (🟡/🔴 close-out re-verification) is mandatory.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Probe | If absent |
|------|-------|-----------|
| `explorer` | fill-in | read-only recon; output → `spec.md` Background (orchestrator **replaces** the placeholder) |
| `implementer` | fill-in | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | fill-in | graded findings → `## Review` section |

> Missing `spawn_agent` degrades to inline execution; responsibilities and output contracts stay unchanged.

## 4. Runtime Probe Checklist

> Run once at session start, before the first command. A runtime probe, never a build-time claim — the adapter is not "verified against version X".

- [ ] required capabilities resolvable — otherwise stop and mark "unsupported capabilities"
- [ ] optional capabilities: record which are absent, with their annotations
- [ ] gate `<entrypoint>` already approved? if not, get it pre-approved (§0) **before** running any gate

## 5. Known Deviations

| Contract semantics | Harness reality | Handling |
|--------------------|-----------------|----------|
| fill-in | fill-in | fill-in |

> A deviation that blocks a required capability is annotated at the top of the adapter and handled by that capability's fallback column — never invented away.
