---
name: harness-coding-adapter-template
description: The generic adapter template for harness-coding (v2). When onboarding a new harness, copy this file to references/adapters/<harness>.md and fill in section by section, mapping the 12 capabilities from the capability contract (7 required + 5 optional) to the current harness's concrete tools/primitives, and declaring quality-gate commands, role mapping, the static conditional-skill mapping, and degradation rules. Read before loading harness-coding (SKILL.md prerequisites).
---

# Adapter Template (for filling in)

> This is the **fill-in template** for the only difference surface between `harness-coding` and an execution harness. The methodology body (SKILL.md) and the capability contract stay unchanged; this file answers exactly one question: **what concrete mechanism does the current harness use to implement each capability in the contract**.
>
> After filling it in, keep this file as the current harness's adapter layer under `references/adapters/<harness>.md`.

---

## How to Generate (delete this section after filling in)

1. Copy this file to `references/adapters/<harness>.md` (the filename identifies the harness)
2. Replace the placeholder content section by section (every "fill-in" cell), then delete this section
3. Self-check against §6: each of the **7 required capabilities** has an implementation
4. Run one lightweight requirement end-to-end (e.g. fix a typo): the 🟢 channel must complete **without creating any new file**; then run one 🔴 sample to verify artifacts + `artifact-check.py` pass

## 1. Capability Mapping Table

> Map all 12 capabilities (7 required + 5 optional) one by one; anything that can't be mapped must be honestly marked "unsupported" — never invent one.

| Capability | Implementation in this harness | Notes |
|------------|--------------------------------|-------|
| `read` | fill-in | read files |
| `write` | fill-in | overwrite-write; must read before overwriting |
| `edit` | fill-in | exact replacement, old must match uniquely |
| `glob` | fill-in | pattern-match to list paths |
| `grep` | fill-in | returns matches with file:line |
| `run_command` | fill-in | the only channel for quality gates |
| `ask_user` | fill-in | batch preferred (questions[] in one round); else serial within one clarification round; headless → conservative option + record |
| `spawn_agent` | fill-in (optional) | if missing, execute inline per the degradation rules |
| `create_branch` | fill-in (optional) | if missing, mark "not isolated" |
| `check_command` | fill-in (optional) | if missing, run once to decide |
| `find_skill` | fill-in (optional) | search local skill packages (glob + frontmatter read is valid); if missing → static table in §4 |
| `web_search` | fill-in (optional) | if missing → record `not verified online` in spec Assumptions |

## 2. Quality-Gate Commands (defined by the project)

> Four gates in a fixed order: lint → format → type → test. The commands are defined by the **project**, independent of this harness.

| Gate | Command | Notes |
|------|---------|-------|
| lint | fill-in | e.g. ruff check . / eslint / gofmt -l |
| format | fill-in | e.g. ruff format --check . / prettier --check |
| type | fill-in | e.g. mypy --strict . / tsc --noEmit |
| test | fill-in | e.g. pytest --cov=... (the coverage threshold belongs to this gate) |

> Full re-run before closing (🟡/🔴 close-out re-verification) is mandatory.

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Agent type in this harness | Notes |
|------|----------------------------|-------|
| `explorer` | fill-in | read-only recon; output → `spec.md` Background (orchestrator **replaces** the placeholder) |
| `implementer` | fill-in | implementation + tests + gates; checks off tasks with pasted gate output |
| `reviewer` | fill-in | graded findings → `## Review` section |

> If not registered → degrade to a generic subagent or inline execution in the orchestrator; responsibilities and output contracts stay unchanged.

## 4. Conditional Skill Mapping (static fallback for `find_skill`)

| Abstract conditional skill | Loadable skill in this harness | Triggered stage |
|---------------------------|--------------------------------|-----------------|
| Isolation skill | fill-in | after plan confirmed → before implementation |
| Decision-record skill | fill-in | after plan confirmed |
| Debugging skill | fill-in | after quality-gate failure |
| Simplify skill | fill-in | after quality-gate pass → before review |
| Security review | fill-in | after review pass → before close-out re-verification (🔴) |
| Verification skill | fill-in | after review pass → before close-out |
| Branch-finishing skill | fill-in | after close-out pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in this harness | Annotation |
|--------------------|--------------------------------------|------------|
| `ask_user` (headless / no interactive primitive) | pick the most conservative option (fewest irreversible side effects) and record it; never pretend the user confirmed | ⚠️ unable to ask the user; decided on the conservative option |
| `spawn_agent` | fill-in | no sub-agent, inline execution |
| `create_branch` | fill-in | not isolated (no branch capability) |
| `check_command` | fill-in | none |
| `find_skill` | fill-in — static conditional-skill table (§4) | none |
| `web_search` | fill-in — record `not verified online` in spec Assumptions | none |
| Other (required capability missing) | fill-in | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Capability-Contract Consistency Self-Check

| Required capability | Implementation in this harness | Status |
|---------------------|--------------------------------|--------|
| read / write / edit / glob / grep | §1 table | ☐ |
| run_command | §1 table | ☐ |
| ask_user | §1 table | ☐ |

> All checked → the adapter layer is ready; you can run the SKILL.md main flow.
