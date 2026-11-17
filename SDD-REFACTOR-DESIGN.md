---
name: harness-coding-sdd-refactor-design
status: implemented (v2.0.0–v2.2.4); design frozen 2026-10-23; DoD verified 2026-11-03 — acceptance record in §10
date: 2026-10-23
scope: v2.0.0 refactor proposal — protocol-driven → artifact-driven (SDD)
---

# SDD Refactor Design (v2 proposal)

> In one sentence: replace the reporting-protocol state machine that v1.0 invented and then had to maintain itself, with "plain markdown artifacts + git". Flow state no longer lives in the protocol; it lives in the artifacts. The three core assets — tiered channels, the capability contract, the adapter layer — are kept as-is.

## 1. Motivation (the disease, quantified)

| Symptom | Quantified |
|---------|-----------|
| Overweight skill body | SKILL.md at 23KB ≈ 8–10K tokens injected on every trigger, eating the working budget before work starts |
| Self-maintenance cost of the protocol | report_lib.py (297 lines) + smoke-report.py (587 lines) guard a self-invented protocol; six hardening rounds in the CHANGELOG all fixed bugs of that protocol itself (marker-reference misjudgment, trailing whitespace, path traversal) |
| Essence of the disease | Flow state (PHASE markers / per-task version counting / exclusive creation / concurrency guards) was implemented as a private state machine — capabilities git provides natively |
| Porting cost | `write_report` was the hardest of the 12 capabilities to port (the Claude Code adapter needed Read+Edit to simulate marker replacement) |

## 2. Goals / non-goals

**Goals**
- G1 SKILL.md 174 lines → ≤80 lines (including the §12 continuation protocol; completeness over the line-count number), token injection cut by half or more
- G2 The reporting-protocol state machine deleted wholesale; traceability carried by artifacts + git
- G3 The contract drops the heaviest `write_report` and the no-independent-value `run_quality_gate`, adds the thin-semantic optional capabilities `find_skill` / `web_search`; net 7 required + 5 optional (the point is not the count but that every capability is semantically trivial and every optional one has a degradation path)
- G4 Validation scripts 1221 lines → ~150 lines (a single artifact validator) <!-- estimate; actual landing: three scripts ~575 lines (validator ~246 incl. per-class fixture assertions, probe ~222 incl. short-query fix, view ~107) — scope grew with the probe and view added post-v2.0; annotated 2026-11-16, probe figure updated v2.2.9 -->
- G5 Tiered channels / capability contract / adapter layer kept as-is

**Non-goals**
- No Spec-Kit-style constitution / multi-file bundle (🟡 capped at one file, 🔴 capped at three)
- No backward-compatible migration of v1 report files (old `harness-reports/` stays archived, unmigrated)
- No changes to the methodology-related content of the three adapters (only the `write_report` mapping rows)

## 3. Core decision: protocol-driven → artifact-driven

| Original protocol mechanism | Carrier after SDD-ification |
|-----------------------------|------------------------------|
| Interrupted-run recovery (resume from a non-DONE marker) | Read the artifact files: the tasks.md checkboxes are the progress |
| Per-task version counting v\<N\> | git history / branches |
| Concurrency-collision guards (exclusive creation) | the git branch model |
| Five-section incremental report | the on-demand view `derive-report.py` + the closing chat reply (the report is demoted from a stored artifact to a derived view, see §5.1) |
| in-progress / abandoned state machine | the git working-tree state |
| Multi-turn report reuse within a task chain | the §12 continuation protocol: same-slug task chain, follow-up changes append tasks |

## 4. Channel × artifact matrix (the single truth of the new main flow)

| Channel | Artifacts | Flow | Close-out |
|---------|-----------|------|-----------|
| 🟢 light | **zero files** | implement directly → lint/format | inline summary (unchanged) |
| 🟡 standard | `intent.md` (one paragraph) | locate → implement → gates → review → close-out re-verify | close-out reply (incl. merge ask_user) + intent reference |
| 🔴 full | `spec.md` + `plan.md` + `tasks.md` | info-gathering (optional) → spec draft → clarification gate (ask_user) → plan → per-task implement+gates → review → close-out re-verify | close-out reply (incl. merge ask_user); on-demand view via `derive-report.py` |
| 📋 findings-only | spec / plan **IS the deliverable** | locate → review/validate | validation verdict |

Hard constraint: the 🟢 channel creates no new files — writing a spec for a typo fix is absurd. SDD reorganizes the heavy channels' organization, not the global flow.

> **Close-out re-verification** (🟡/🔴 mandatory, inherited from v1 main-flow step 8): per-task green ≠ repo green — later tasks may break behavior verified by earlier ones. Before closing, a **full gate run** is mandatory and its output is the closing reply's evidence; a full-run failure → back to the per-task loop to locate the root cause. The **merge decision** (PR / direct merge / keep iterating) rides the close-out ask_user (inherited from v1 step 10).
>
> **Front pipeline** (🟡/🔴, protocol in §5.3): intent recognition (session classification) → info-gathering (`find_skill` local skill search / `web_search` external verification, both optional, triggered on demand) → clarification gate (fuzzy points split into assumptions/questions, batch-asked in one round) → spec / intent finalized. 🟢 performs session classification only and skips info-gathering and the clarification gate (zero-file constraint first).

## 5. Artifact spec (minimal templates)

Directory convention: `specs/<slug>/`, same lifecycle as the repo, git-managed. **No version counting, no archival mechanism.** Slug uniqueness: if the target directory exists and does not belong to the current task chain (§12) → refuse creation and require a rename, **no automatic suffixes** (an auto-suffix masks the semantic signal of a name collision).

```markdown
<!-- spec.md -->
# <slug> spec
Requirement: <one sentence>
Background: <two or three lines>
Acceptance criteria:            ← each ID unique, executable commands where possible
- AC-1: pytest tests/test_auth.py -k expired passes
- AC-2: ...
Assumptions:                ← low-risk self-decided parts of fuzzy scope (§5.3 clarification-gate output)
- A1: <decision + rationale; if verified via web_search, cite source + retrieval time>
Non-goals: <explicit exclusions>

<!-- plan.md -->
# <slug> plan
Approach: <architecture and key trade-offs>
Architecture decisions:            ← the four ask_user triggers: new port / new event / table schema / aggregate behavior change
- AD-1: <decision + confirmation result>
Task breakdown: see tasks.md

<!-- tasks.md -->
# <slug> tasks
- [ ] T1 (AC-1, AC-3): <description>; verify: <command>
- [x] T2 (AC-2): <description>; verify: <command>; Output: <key output excerpt>

## Deferred        ← remaining risks as open checkboxes: unchecked = not done
- [ ] D1: <known gap / item needing manual verification>; suggested follow-up: <one sentence>

## Review         ← where review conclusions land (see §5.2)
- R1 [resolved]: <blocker description> → fixed in T3
- R2 [open|minor]: <minor description, recorded only, non-blocking>

<!-- intent.md (🟡 only, single file) -->
Intent: <one paragraph>; verify: <command>
```

Invariant: a checked task must carry fresh command output (evidence before assertion, inherited from v1); the AC↔T reference relation is the traceability chain the view derives from.

### 5.1 Reports demoted to an on-demand view (no persistent final report)

The five report sections are unbound before cancellation:

| Report section | Destination |
|----------------|-------------|
| Requirement positioning | spec.md (already there) |
| Change list | `git diff --stat` + commit messages |
| Verification results | tasks.md checks + pasted command output |
| Remaining risks | unchecked tasks in tasks.md's "Deferred" section (risk becomes an actionable follow-up, not stale prose) |
| Skill-usage log | deleted (harness-internal self-audit, no human consumer) |

Readability remedy: the new `scripts/derive-report.py` (~95 lines as shipped) — one command when you want to see it, generating a traceable view to stdout from tasks.md + a branch-baseline diff on the fly; **never persisted, never maintained, never rots**. The diff baseline is `merge-base`, **not** the working-tree diff — after tasks are committed the working-tree diff is empty and the change list would be lost. Only state is stored (spec/tasks/git); display is always a projection. Boundaries: the 📋 channel's Findings/spec documents are the **product** (the deliverable itself) and stay; 🟢's inline summary is a chat message and is unaffected.

### 5.2 Where role outputs land

Beyond dispatch templates "reading artifacts", the three roles' **write** destinations must be fixed, or role conclusions live only in the conversation and evaporate with the session:

| Role | Output | Home |
|------|--------|------|
| Explorer | recon conclusions (implementation locations / call chains / reusable patterns, with file:line) | spec.md Background section, appended (recon is the input to writing the spec) |
| Implementer | implementation + check-offs | tasks.md task lines: check + verification command output |
| Reviewer | graded findings | tasks.md "Review" section: each `R<n>` tagged `[resolved / open]` with a level |

Structural guarantee (another discipline→structure landing): **a blocker/major finding left open makes closing illegal** — review rejection automatically returns to the implementation loop, because "an unresolved major" is a visible, unclosed state in tasks.md that artifact-check can verify mechanically; minor may stay open (recorded only; whether it converts to Deferred is the user's call).

The 🟡 channel has no tasks.md: review conclusions and Deferred attach as **same-named sections at the end of intent.md** (`## Review` / `## Deferred`, same format and validation rules as 🔴), so "an open blocker/major blocks closing" holds on 🟡 too.

### 5.3 Clarification & ask-back protocol (the two layers of intent recognition)

Intent recognition has two layers, asking about different things: **intent unclear** asks "do we do it" (session-classification layer, already in v1: verb/noun/deliverable verdict + ask first when unsure); **scope fuzzy** asks "how, and how far" (this section — classification settled but scope unclear).

When drafting spec / intent, every fuzzy point is forcibly split into two classes:

| Class | Criterion | Handling |
|-------|-----------|----------|
| **Assumption** | low-risk, reversible, cheap when wrong | decide autonomously, record it explicitly in spec's Assumptions section (A-ID) |
| **Question** | high-risk, irreversible, or one of the four architecture-decision classes (new port / new event / table schema / aggregate behavior change) | must ask back via `ask_user` |

Rules:
1. **Batch into one round** — all questions merge into a single ask-back round; serial single questions across turns are forbidden. On the contract side the `ask_user` signature extends to batch (`ask_user(questions[]) -> answers[]`, see §6); when the primitive supports only one question, degrade to **serial asks within the same clarification round**, never spread across multiple turns
2. **Answers land in artifacts** — Q&A conclusions convert into spec AC / AD / assumption entries; they never evaporate in the chat log
3. **Info-gathering first** — before asking back, use `find_skill` / `web_search` (optional capabilities) to resolve everything self-resolvable; leave only what genuinely needs the user's judgment for the ask-back

### 5.4 Info-gathering layer (two new optional capabilities)

| Capability | Signature | Use | Degradation |
|------------|-----------|-----|-------------|
| `find_skill` | `find_skill(query) -> list[skill]` | after classification, before drafting, search the local skill library; a hit loads as a conditional skill | capability missing or no hit → fall back to the built-in static conditional-skill table (inherited from v1's conditional-skill mapping) |
| `web_search` | `web_search(query) -> results` | verify external knowledge the repo cannot resolve (dependency versions / compatibility / API behavior) | capability missing → record "not verified online" in spec Assumptions; the flow is not blocked |

The three `web_search` disciplines: results entering the spec must carry **source + retrieval time**; **AC must stay locally executable** (a web-search conclusion never becomes an acceptance criterion directly); restraint — if the repo can answer it, never search externally. Both capabilities belong to the harness tool layer; the orchestrator references only capability names, with concrete primitives mapped by adapters.

## 6. Capability-contract changes

- **Delete** `write_report` (required 8 → 7)
- **Keep** optional `spawn_agent` / `create_branch` / `check_command`; `run_quality_gate` deleted (no independent value)
- **Add** optional `find_skill` / `web_search` (§5.4). Optional set: 4 → delete 1 → add 2 = **5** (spawn_agent / create_branch / check_command / find_skill / web_search), each with a degradation rule
- **Signature change**: `ask_user` extends to `ask_user(questions[]) -> answers[]` for batch ask-back (§5.3); when the primitive supports only a single question, degrade to serial asks within one clarification round
- Each adapter deletes its `write_report` mapping row and adds `find_skill` / `web_search` rows; `references/templates/write-report.md` deleted
- The contract gains one declaration: **artifacts as state** — no report-writing capability; the report is a close-out reply + an on-demand view (§5.1), never a persisted artifact

## 7. Module-level change list

| File | Disposition |
|------|-------------|
| `SKILL.md` | rewrite: ≤80 lines, content = session classification + channel×artifact matrix + contract references + §12 continuation summary |
| `references/capability-contract.md` | delete the `write_report` semantics section and reporting-protocol invariants; add `find_skill` / `web_search` optional definitions with degradation rules |
| `references/adapters/{claude-code,codex,opencode}.md` | delete `write_report` rows and report-path config; add `find_skill` / `web_search` rows (mapped to each harness's skill-search and search primitives) |
| `references/templates/write-report.md` | delete |
| `references/templates/report-template.md` | delete (no persisted final report; the view format is internalized into `derive-report.py`) |
| `references/templates/` | add four micro-templates: `spec.md` / `plan.md` / `tasks.md` / `intent.md` |
| `scripts/report_lib.py` / `smoke-report.py` / `consistency-check.py` | delete |
| `scripts/workflow-check.py` | rewrite as `artifact-check.py` (~150 lines: artifact schema + tasks checks vs git state + AC reference integrity + Deferred section validation + Review open-blocker/major closing guard) |
| `scripts/derive-report.py` | add (~95 lines as shipped: tasks.md + merge-base diff → traceable view to stdout, never persisted) |
| `.claude/settings.json` / `opencode.json` | update allowlists: `artifact-check.py` / `derive-report.py` (replacing the old trio's entries) |
| `README.md` / `CHANGELOG.md` | update in sync |

## 8. Migration steps (each an independent, revertible commit)

1. **Contract slimming**: delete `write_report` (contract + three adapters + write-report.md); run the existing consistency-check to confirm no residue
2. **Artifact introduction**: four templates + `artifact-check.py` + `derive-report.py` + `fixtures/` sample tasks (see §11.3)
3. **Body rewrite**: SKILL.md rewritten to ≤80 lines from the channel×artifact matrix + §12 continuation protocol; dispatch templates changed to read/write artifacts (§5.2)
4. **Wrap-up**: delete the old script trio, update README / CHANGELOG, release v2.0.0

## 9. Risks & countermeasures

| Risk | Countermeasure |
|------|----------------|
| Spec rot (code changed, spec not) | acceptance criteria forced executable and wired to quality gates; checks must carry fresh output |
| SDD misapplied to the light channel | the matrix hard-constrains 🟢 to zero files; artifact-check validates |
| Artifact dirs polluting the host repo | `specs/` git-tracked by default; **inline is 🟢-only (the conversation is the deliverable), 🟡/🔴 always write to disk — interrupt recovery beats directory tidiness** |
| Close-out information loss | remaining risks land in Deferred (unchecked = an explicit debt); `derive-report.py` generates the full traceable view on demand |
| Evidence staleness (pasted outputs may be old) | close-out re-verification backs it up (§4): full gates force re-run before closing, output goes straight into the reply |
| Multi-turn misattribution (appending to the wrong chain / slug collision) | §12 continuation protocol + the slug rejection rule |
| Web content polluting the spec (stale/wrong external conclusions) | the three disciplines: cite source + retrieval time; AC stays locally executable; never search externally when the repo can answer |

## 10. Acceptance criteria (Definition of Done)

**Machine assertions** (`artifact-check.py` / fixture automation):
- [x] `artifact-check.py` passes on the fixture tasks; the `broken` case must error (including the Review open-blocker/major closing guard) — verified 2026-11-03: `--fixtures fixtures` → 6/6 cases matched; `broken` errors include the R1 open-blocker guard and the GATE-NA pairing check
- [x] All machine assertions of the §11.3 fixtures pass/error as expected — same run 2026-11-03; probe fixtures added in v2.2.x also pass (`find-skill.py --fixtures fixtures/skills` → 3/3: drift warns, empty exits 2, no-drift clean)
- [x] The L0–L3 layered-loading protocol holds: SKILL.md inlines no lower-layer content — audit 2026-11-03: SKILL.md at 72 lines, references lower layers by path only (`references/capability-contract.md`, `references/adapters/`, `references/templates/`); adapters point to SKILL.md §7 instead of inlining the conditional-skill table (enforced since v2.2.0); L0 description budget re-checked 2026-11-03 — found at 105 words (>80), trimmed to 76 in v2.2.6

**Manual drill criteria** (walk end-to-end; machines cannot fully substitute):
- [x] SKILL.md ≤80 lines, and all four channels' behavior uniquely derivable from the docs — 72 lines (2026-11-03); the v2.0.3–v2.2.3 consistency sweeps plus the 2026-11-03 full-doc audit surfaced no channel ambiguity, only stale cross-references (fixed in v2.2.3)
- [x] None of the three adapters depends on `write_report`; onboarding a new harness per `_adapter-template.md` passes first try — grep 0 hits across SKILL.md / references/ / scripts/ / fixtures/ (2026-11-03); template audited complete against the contract (7 required + 4 mapped optional rows, §1–§5); the literal first-try onboarding executes at the first real new-harness adoption
- [x] A typo task creates zero new files end-to-end (🟢 zero-file constraint, with lint/format actually executed) — drill 2026-11-03: the README probe-line addition (T3 of `specs/dod-closure`) modified 1 file and created 0; this repo's project-defined gates (both fixture suites) were executed with output pasted in the tasks; markdown-only change → lint/format declared GATE-NA chain-wide in the spec
- [x] A 🔴 sample: close-out re-verification runs full gates, the merge decision rides ask_user, `derive-report.py` derives the full traceable view from artifacts + diff, and no report file is ever written — this chain (`specs/dod-closure`, 2026-11-03): both fixture suites re-run green at close-out; the merge decision (commit+push) was confirmed in one batch ask round; the traceable view was derived to stdout; `git status` confirmed no report file
- [x] A multi-turn chain drill: same-slug task append, channel upgrade backfills artifacts (§12) — real drill 2026-11-03: the follow-up "check the skill again" requirement landed on the existing `specs/dod-closure` chain and was appended as tasks T7–T9 with new AC-7–AC-10 (append-only, one supersede annotation), no new slug, no channel downgrade; the appended release (v2.2.5) re-ran full gates at close-out
- [x] A fuzzy-requirement drill: clarification gate batch-asks once (no serial questioning), answers land in spec as AC/AD/assumptions (§5.3) — 2026-11-03: 3 fuzzy points (artifact destination / open-item handling / merge decision) batch-asked in a single round; answers landed as spec A1–A3 and plan AD-1/AD-2

## 11. Harness-engineering principles (v2's design axioms)

> The single axiom: **the model is a constant, the scaffold is the variable** — you cannot change model weights, but context, tool surface, feedback loops, and state storage are all in engineering's hands; spend the whole budget on the scaffold. Execution principle: **judgment belongs to the model, state belongs to the mechanical layer**.

### 11.1 Layered-loading protocol (context is the scarce resource)

| Layer | Content | Loaded when | Budget |
|-------|---------|-------------|--------|
| L0 | frontmatter description | resident (visible to all sessions) | ≤80 words |
| L1 | SKILL.md body (classification + channel×artifact matrix + contract references + §12 summary) | once at skill trigger | ≤80 lines |
| L2 | capability-contract.md + the current harness's adapter | on demand: when touching the contract or degrading | — |
| L3 | the four artifact templates | when the channel is used | — |

Hard constraint: **no layer may inline-copy lower-layer content; only reference paths** (v1's 23KB resident injection is the counterexample for exactly this rule). This is how "keep SKILL.md ≤80 lines" turns from a slogan into a verifiable rule.

### 11.2 Discipline → structure (the essence of the v1 → v2 evolution)

v1's many clauses were essentially **begging the model for discipline in prose**; v2 converts them into **structural guarantees** — violations become either physically impossible or immediately exposed by the validator. This explains why SKILL.md could shed 2/3: what was cut is not the rules but the way rules were enforced.

| v1 prompt discipline | v2 structural guarantee |
|----------------------|--------------------------|
| "never claim pass from memory" | the close-out reply and the on-demand view must derive from artifacts + diff; checks must carry command output; artifact-check validates |
| "never silently overwrite an in-progress report" | git branches/commits are the state — overwriting is physically impossible |
| "evidence before assertion" | AC made executable and wired to gates; evidence stored co-located with artifacts |
| "skipping a stage must leave a mark" | the channel×artifact matrix hard constraint; 🟢 zero files backed by fixture validation |

### 11.3 Micro eval: the fixture task set

> The validator itself needs tests — eval is not optional; it is part of the harness.

| fixture | Channel | Assertions |
|---------|---------|------------|
| `fix-typo` | 🟢 | zero new files end-to-end; lint/format actually executed |
| `add-validation` | 🟡 | `intent.md` exists and carries a verify command; gate output pasted with the check |
| `refactor-flow` | 🔴 | spec/plan/tasks schemas valid; AC↔T references closed; the `derive-report.py` view fully derivable |
| `broken` (deliberately broken) | 🔴 | artifact-check **must error** (missing AC reference / check without output / Review open blocker / undeclared exemption) — per-error-class assertions via `.expect` `err=` substrings since v2.2.7; proves the validator has teeth |
| `gate-na` (added v2.0.2) | 🔴 | legal chain-wide exemption: every GATE-NA usage is paired with a `## Gate Exemptions` declaration |
| `broken-intent-na` (added v2.2.7) | 🟡 | deliberately broken: a 🟡 intent uses GATE-NA(type) with no declaration — exposed the vacuous 🟡 pairing check (usage self-declared from the same full text); declarations now scoped to the intent's `## Gate Exemptions` section |
| `intent-gate-na` (added v2.2.7) | 🟡 | legal 🟡 exemption: usage declared in the intent's `## Gate Exemptions` section — the pass side of the pairing matrix |
| `malformed-task` (added v2.3.1) | 🔴 | deliberately broken: a task-shaped line `- [x] T2: ...` without the `(AC-x)` reference block used to escape every task check (silent skip); check_task_file now reports "malformed task line" for `- [<x>] T<n>`-prefixed lines failing the full format |
| `comment-ac` (added v2.3.3) | 🔴 | legal: AC lines inside a multi-line HTML comment block must not be collected as declared ACs (a comment is not a requirement) — under the pre-v2.3.3 code they raised "is not covered by any task"; closes the comment-stripping asymmetry with the v2.2.8 GATE-NA fix |

Run: `python scripts/artifact-check.py --fixtures fixtures/`, delivered as part of §8 migration step 2. Probe fixtures (`fixtures/skills/`, added v2.2.0: drift / no-drift / empty; short-query added v2.2.9) self-test `find-skill.py` separately. Assertions split into two classes: **machine assertions** (artifact shape, auto-validated by artifact-check) and **manual drill criteria** (e.g. "lint/format actually executed", a §10 manual item) — fix-typo's executability assertion belongs to the latter.

## 12. Multi-turn & continuation protocol (task-ownership rules)

> git manages state, not semantic ownership — "which task chain does this new requirement belong to" must be defined explicitly. This section replaces v1's multi-turn session rules (reuse in-progress reports / channel upgrade marks abandoned / reopen v\<N+1\>).

1. **Re-run session classification after every user message** (inherited from v1, unchanged)
2. **Ownership**: the slug is generated from the task chain's **first requirement**; follow-up messages **default to appending as new tasks of the current chain** (written to tasks.md, including Review/Deferred placement). The 🟡 channel has no tasks.md — appending = **extending intent.md into a multi-paragraph intent list** (each paragraph one intent + verify command). Only two cases open a new chain: the user explicitly says "new task / a different thing", or the topic is clearly unrelated to the current chain (unsure → ask_user)
3. **Channel upgrade**: when a follow-up raises the channel (🟢→🟡/🔴), **backfill the missing artifacts** (add intent.md / spec.md + plan.md), never a new directory, never abandoning the chain — checks verified before the upgrade remain valid; channels **never downgrade** (inherited from v1)
4. **Close-out and reopen**: the chain closes when the close-out reply is delivered; a new requirement under the same slug = reopening the chain (artifacts exist; just append tasks). Spec evolution on reopen: **AC are append-only** — new requirements add AC entries; when an old AC genuinely must change, mark it `supersede` pointing to the new AC, keeping the traceability chain intact
5. **Mid-flight abandonment**: no abandoned state machine — unchecked tasks + Deferred entries are themselves explicit debts; keeping or discarding them is the user's decision at close-out
