---
name: harness-coding-adapter-template
description: The generic adapter template for harness-coding. When onboarding a new harness, copy this file to references/adapters/<harness>.md and fill in section by section, mapping the 12 capabilities from the capability contract (8 required + 4 optional) to the current harness's concrete tools/primitives, and declaring quality-gate commands, role mapping, conditional-skill mapping, and degradation rules. Read before loading harness-coding (SKILL.md prerequisites).
---

# Adapter Template (for filling in)

> This is the **fill-in template** for the only difference surface between `harness-coding` and an execution harness. The methodology body (SKILL.md) and the capability contract (references/capability-contract.md) stay unchanged; this file answers exactly one question: **what concrete mechanism does the current harness use to implement each capability in the contract**.
>
> After filling it in, keep this file as the current harness's adapter layer under `references/adapters/<harness>.md`.

---

## How to Generate (delete this section after filling in)

1. Copy this file to `references/adapters/<harness>.md` (filename is your choice, as long as it identifies the harness)
2. Replace the placeholder content section by section (every "fill-in" cell), then delete this section
3. Self-check against the checklist in `references/capability-contract.md` §7: each of the 8 required capabilities has an implementation
4. Run one lightweight requirement end-to-end (e.g. fix a typo) to verify the lowest channel works

## 1. Capability Mapping Table

> Map all 12 capabilities (8 required + 4 optional) one by one; anything that can't be mapped must be honestly marked "unsupported"—never invent one.

| Capability | Implementation in this harness | Notes |
|------------|--------------------------------|-------|
| `read` | fill-in | read files / directories / images |
| `write` | fill-in | overwrite-write; must read before overwriting |
| `edit` | fill-in | exact replacement, old must match uniquely |
| `glob` | fill-in | pattern-match to list paths |
| `grep` | fill-in | returns matches with file:line |
| `run_command` | fill-in | the only channel for quality gates |
| `ask_user` | fill-in | 2~4 mutually exclusive options + a recommended one |
| `write_report` | fill-in | when no dedicated primitive, simulate with write+edit per references/templates/write-report.md |
| `spawn_agent` | fill-in (optional) | if missing, execute inline per the degradation rules |
| `create_branch` | fill-in (optional) | if missing, mark "not isolated" |
| `check_command` | fill-in (optional) | if missing, run once to decide |
| `run_quality_gate` | fill-in (optional) | if missing, run each via run_command |

## 2. Quality-Gate Commands (defined by the project)

> Four gates in a fixed order: lint → format → type → test. The commands are defined by the **project**, independent of this harness; replace them with the matching toolchain for non-Python stacks.

| Gate | Command | Notes |
|------|---------|-------|
| lint | fill-in | e.g. ruff check . / eslint / gofmt -l |
| format | fill-in | e.g. ruff format --check . / prettier --check |
| type | fill-in | e.g. mypy --strict . / tsc --noEmit |
| test | fill-in | e.g. pytest --cov=... (the coverage threshold belongs to this gate) |

## 3. Role Mapping (optional `spawn_agent` capability)

| Role | Agent type in this harness | Notes |
|------|----------------------------|-------|
| `explorer` | fill-in | read-only recon, output with file:line |
| `implementer` | fill-in | implementation + tests + quality gates |
| `reviewer` | fill-in | graded findings + quality-gate recheck |

> If not registered → degrade to a generic subagent or inline execution in the orchestrator; responsibilities and output contracts stay unchanged.

## 4. Conditional Skill Mapping (SKILL.md conditional-trigger table → loadable skills in this harness)

| Abstract conditional skill | Loadable skill in this harness | Triggered stage |
|---------------------------|--------------------------------|-----------------|
| Isolation skill | fill-in | after plan confirmed → before implementation |
| Decision-record skill | fill-in | after plan confirmed |
| Debugging skill | fill-in | after quality-gate failure |
| Simplify skill | fill-in | after quality-gate pass → before review |
| Security review | fill-in | after review pass → before verification (Full) / before report (Standard) |
| Verification skill | fill-in | after review pass → before summary |
| Branch-finishing skill | fill-in | after summary pass |

## 5. Degradation Rule Declarations

| Missing capability | Degradation behavior in this harness | Report annotation |
|--------------------|--------------------------------------|-------------------|
| `spawn_agent` | fill-in | no sub-agent, inline execution |
| `create_branch` | fill-in | not isolated (no branch capability) |
| `check_command` | fill-in | none |
| `run_quality_gate` | fill-in | none |
| Other (required capability missing) | fill-in | mark "unsupported capabilities" at the top of the adapter layer |

## 6. Runtime Config Overrides (optional)

> Declare overrides of the capability-contract defaults here; delete this section if there are none.

| Config key | Default | Override in this harness |
|------------|---------|--------------------------|
| `report.dir` | `harness-reports/` | fill-in |
| `report.prefix` | `harness-task` | fill-in |
| `report.on_disk` | `true` | fill-in |

> `<report.dir>` is a project-root-relative path: resolve it against the harness working directory (never the skill's own directory) to an absolute path before the first write.

## 7. Capability-Contract Consistency Self-Check

| Required capability | Implementation in this harness | Status |
|---------------------|--------------------------------|--------|
| read / write / edit / glob / grep | §1 table | ☐ |
| run_command | §1 table | ☐ |
| ask_user | §1 table | ☐ |
| write_report | §1 table (default write+edit simulation) | ☐ |

> All checked → the adapter layer is ready; you can run the SKILL.md main flow.
