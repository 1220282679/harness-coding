---
name: harness-coding-flow
description: Channel flow detail for the harness-coding skill (L3, read on demand). Covers the channel edge cases where SKILL.md §2's criteria disagree, plus the clarification-gate protocol (Assumptions vs Questions, one round), info-gathering order, slug/continuation/upgrade rules, and close-out re-verification with the merge decision. Read for 🟡/🔴 work only — 🟢 light and 📋 findings-only never need it.
---

# Flow Detail

> L3 of the loading tiers. SKILL.md §2 carries the routing table and the hard constraints; this file carries the protocol behind them. On conflict SKILL.md wins — it is the single source of flow truth.

## Choosing the channel — edge cases only

§2 carries the criteria; do not re-derive them here. This table is for the rows where the criteria disagree with each other — check it only when the default pick feels off.

| Situation | Pick | Why the default misleads |
|-----------|------|--------------------------|
| One file, but it touches a schema, a public signature, or a config contract | 🔴 | "one file" is not the test; blast radius is |
| Pure docs, comments, or formatting — even across ten files | 🟢 | No design call, no AC set, nothing to verify |
| Dependency, build, or CI config change | 🟡 | Cross-file, and affected tests are not enumerable |
| Mechanical rename or move across modules | 🟡 | Wide but design-free: needs the affected subset, not a plan |
| A bug fix that needs tests pinning existing behavior | 🟡 | Regression pinning is design work, not a guard |
| Read-only audit where the user expects a fix in the same turn | 🟡 | The verdict stops being the deliverable |
| An AC set you cannot write in one paragraph | 🔴 | Scope is not understood yet → plan first |

Unsure between 🟡 and 🔴 → pick 🔴. Upgrading backfills the missing artifacts; downgrading throws them away.

## Clarification gate

Runs at 🟡/🔴 when scope is fuzzy, after classification, before drafting.

1. **Split every unknown**:
   - **Assumption** — low-risk, reversible, answerable from the repo or convention. Decide it, log `A-<n>` in the spec/intent Assumptions section, proceed.
   - **Question** — the answer changes the shape of the work (scope boundary, data model, exposed API, edge-case behavior). Batch these.
2. **Ask once.** One `ask_user` round carrying every question, never serial across turns — each extra round costs a full context re-read. Drafting may delegate to a question-technique skill (`grill-me`) found via `find_skill`; filtering and the one-round discipline stay here.
3. **Land the answers.** A question's answer becomes an AC (🔴) or a decision entry (🟡). An assumption the user later vetoes becomes an AC too — ACs are only added, never rewritten.

Architecture calls (new port, event, table schema, aggregate behavior) are always Questions — never self-decided, even under schedule pressure.

## Info-gathering

Before drafting: `find_skill` for a local technique that fits the task; `web_search` for external facts the repo cannot answer (cite source + retrieval time; the AC stays locally executable). If the repo can answer it, do not search.

## Slug, continuation, upgrade

- **Slug** from the first requirement, kebab-case, one dir `specs/<slug>/`.
- **Same topic continues the chain**: follow-ups append tasks (🟡: append intent paragraphs). The chain ends only at an explicit "new task" or an unrelated topic.
- **Checkpoint** at each phase boundary — artifacts updated, gates recorded — so a fresh session can resume from `tasks.md` alone. Past ~60 turns do this unconditionally: every turn after a compaction re-pays the whole prefix.
- **Upgrade** (🟢→🟡→🔴) backfills the missing artifacts from what already happened; never downgrade to save work.
- A dir that exists but belongs to another chain → reject the name and rename; never append into someone else's artifacts.

## Close-out

1. Re-run the **full** gate sequence — per-task green is not repo green, and an affected-subset run proves nothing about the repo.
2. Validate: `python scripts/artifact-check.py specs/`.
3. Confirm no open blocker/major in `## Review`; `## Deferred` carries the remaining risks.
4. Derive the reply from artifacts + diff, then ask the merge decision (PR / merge / iterate) via `ask_user`.
