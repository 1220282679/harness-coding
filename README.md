# harness-coding

**Universal harness coding-orchestration skill (v2 · artifact-driven)**

Turn a one-line request into a controlled change flow. The core shift in v2: **state lives in artifacts, history lives in git, evidence lives in gate output, and a report is only an on-demand view** — no report files, no private protocol state machine.

> Session classification decides the intent → a tiered channel (🟢 light / 🟡 standard / 🔴 full / 📋 findings-only) picks the flow depth → the front pipeline (info-gathering + clarification gate) → role dispatch (explorer / implementer / reviewer) → quality gates → close-out reply + on-demand traceable view.

## Core ideas

1. **Artifacts as state**: task state lives in plain markdown artifacts (`specs/<slug>/` with `spec.md` / `plan.md` / `tasks.md`; 🟡 single-file `intent.md`) — resume = read files, versioning = git, concurrency = git branches
2. **The capability name is the contract**: the methodology body references only capability names (7 required + 5 optional, every optional one with a degradation rule); concrete tools are decided by the adapter layer
3. **Discipline → structure**: v1 begged for discipline via prompt clauses ("never claim pass from memory"); v2 guarantees it structurally (a check must carry output, an open blocker/major blocks closing, `artifact-check.py` enforces mechanically)
4. **Single source of truth**: onboarding a new harness requires exactly one adapter file

## Channel × artifact matrix (single source of flow truth)

| Channel | Artifacts | Flow | Close-out |
|---------|-----------|------|-----------|
| 🟢 light | **zero files** | implement → lint/format | inline summary |
| 🟡 standard | `intent.md` | locate → clarify → implement → gates → review → full re-verify | close-out reply (merge ask_user) |
| 🔴 full | `specs/<slug>/` with `spec.md` / `plan.md` / `tasks.md` | info-gathering → spec draft → clarification gate → plan → per-task implement+gates → review → full re-verify | close-out reply + on-demand traceable view |
| 📋 findings-only | spec/plan **IS the deliverable** | locate → review/validate | validation verdict |

- **Front pipeline** (🟡/🔴, when scope is fuzzy): info-gathering (`find_skill` local skill search / `web_search` external verification) → clarification gate (fuzzy points split into **assumptions**/A-ids vs **questions**/batch one-round ask) → artifacts finalized
- **Close-out re-verification** (🟡/🔴): per-task green ≠ repo green; a full gate re-run is mandatory before closing; merge decision (PR / merge / iterate) rides the close-out ask_user
- **Continuation**: slug comes from the first requirement; follow-ups append tasks by default (🟡 = append intent paragraphs); channel upgrades backfill artifacts and never downgrade; **AC are append-only** (re-point with a supersede mark)

## Roles & artifact homes

| Role | Duty | Output home |
|------|------|-------------|
| Explorer | read-only recon (file:line) | `spec.md` Background (orchestrator **replaces the placeholder**, does not append) |
| Implementer | implement + test + gates | `tasks.md` check + pasted `Output:` |
| Reviewer | graded findings | `## Review` section (`R<n> [open\|level]` / `[resolved]`) |

**Closing rule: an open blocker/major makes closing illegal** — review rejection mechanically returns to the implementation loop.

Each role's `spawn_agent` dispatch begins with a mandatory Context step (read the artifacts before any work); inline mode skips it. **Context flows through artifacts, never through parent-session summaries.**

## Quality gates

```text
lint → format → type → test
```

Fixed order, project-defined commands (adapter §2); evidence must be pasted, never claimed from memory; on failure locate the root cause before fixing. 🟢 mandates lint + format only; type/test on demand with a recorded reason.

- **Gate N/A exemption protocol**: a non-applicable gate is never silently skipped — declare `GATE-NA(<gate>): <reason + scope>` in the spec/intent `Gate Exemptions` section, reference the same marker in the task output; `artifact-check.py` enforces the pairing (full-text scan on 🟡/🔴). Chain-wide exemptions apply at close-out re-verification too; task-scoped ones do not
- **Incremental per-task gates**: lint/format/type in full + the affected test subset; the full test suite is mandatory at close-out re-verification
- **Coverage threshold is project-declared** (source referenced in adapter §2): none declared → plain pass/fail, never invent a number
- **Refactor baseline**: behavior-preserving refactors build a characterization baseline in plan first; one AC = "baseline passes unchanged"

## Directory layout

```
harness-coding/
├── SKILL.md                        # methodology body (v2: 68 lines)
├── SDD-REFACTOR-DESIGN.md          # v2 refactor design doc (frozen)
├── references/
│   ├── capability-contract.md      # capability contract (7 required + 5 optional)
│   ├── adapters/                   # adapter layer (claude-code / codex / opencode / _template)
│   └── templates/                  # spec / plan / tasks / intent artifact templates + 3 dispatch templates + close-out contract
├── scripts/
│   ├── artifact-check.py           # artifact validator (schema / AC↔T closure / review closing guard / Gate N/A pairing)
│   └── derive-report.py            # on-demand traceable view (merge-base baseline, stdout, never persisted)
└── fixtures/                       # 5 validation cases (incl. deliberately broken, legal-exemption gate-na)
```

## Install

| Harness | Path |
|---------|------|
| Claude Code | `<project>/.claude/skills/harness-coding/` (or `~/.claude/skills/`) |
| opencode | `<project>/.opencode/skills/harness-coding/` (or `~/.config/opencode/skills/`) |
| Codex | `<project>/.codex/skills/harness-coding/` (or `~/.codex/skills/`) |

> Permissions: the host project must allowlist `python scripts/artifact-check.py*` and `python scripts/derive-report.py*` (see this repo's `.claude/settings.json` / `opencode.json`).

## Verify

```bash
python scripts/artifact-check.py --fixtures fixtures/   # all 5 cases should match (broken expects errors)
python scripts/artifact-check.py specs/                 # validate the host project's task artifacts
python scripts/derive-report.py specs/<slug>            # generate the traceable view (stdout)
```

## Capability contract & adapters

Required (7): `read` / `write` / `edit` / `glob` / `grep` / `run_command` / `ask_user` (batch signature; single-question primitives degrade to serial asks within one round).
Optional (5, all with degradation): `spawn_agent` (inline execution) / `create_branch` (main workspace + not isolated) / `check_command` (run once to decide) / `find_skill` (fall back to the adapter §4 static conditional-skill table) / `web_search` (record `not verified online` in spec Assumptions).

Onboarding a new harness: copy `_adapter-template.md` and fill it section by section → run one 🟢 task (must create zero files) → run one 🔴 sample to verify artifacts + the validator. See `references/capability-contract.md` §6.

## Constraints

1. Ask before guessing: intent-unclear → "do we do it"; scope-fuzzy → clarification gate
2. Architecture decisions (new port / new event / table schema / aggregate behavior change) confirmed via `ask_user` before code
3. No skipped gates, no hidden failures; an open blocker/major blocks closing
4. The orchestrator never writes large implementations or tests itself (implementer role)
5. Web-search conclusions must cite source + time; AC must stay locally executable
