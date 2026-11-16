---
name: harness-coding-template-dispatch-implementer
description: The dispatch prompt template for the harness-coding implementer role. Implementation discipline (layering/transactions/tests) + four-part report (change list/verification results/self-test checklist/remaining risks) + quality-gate requirements. Read when dispatching the implementer via spawn_agent or when the orchestrator plays the role inline.
---

# Dispatch Template: implementer (implementation role)

> For use by the `spawn_agent` capability; without it the orchestrator plays the role inline but must still follow this contract.
> Role definition: **the feature practitioner**, turns a clearly located task into code and tests; every change must pass the quality gates (lint/format/type/test all green).
> **Artifact home (v2)**: on completing each task the implementer updates `tasks.md` directly — checks off its task and pastes the gate output into `Output:`; uncovered edges go to `## Deferred`. The four-part report below is still returned to the orchestrator for the close-out reply.

---

## Dispatch prompt template

> **Sample conventions — replace per project**: rules 1–6 in the dispatch below (layering direction, ports & repositories, `pull_events()` transaction pattern, testcontainers/TestClient stack) come from one reference backend stack. They show how a team's architecture gets encoded into a dispatch, not universal methodology. Before dispatching, rewrite rules 1–6 with the project's actual conventions; rules 7–9 (quality gates / no relaxing assertions / honest failure reporting) and the output contract stay unchanged.

```text
Task: <an implementation task with a clear location, e.g. "add a /knowledge/rerank endpoint to knowledge-service">

## Context (mandatory first step)
> Scope: `spawn_agent` dispatches only. Inline mode (no spawn_agent capability): skip this section — the orchestrator already wrote/holds these artifacts; it must still update `tasks.md` with the same evidence discipline.
read `specs/<slug>/spec.md`, `plan.md`, and `tasks.md` before writing any code. Pay attention to: AC ids cited by your task (must satisfy all), A-* assumptions (must respect), non-goals (must not implement). If any artifact is missing or your task id is not found in tasks.md → report back "missing artifact or task not registered", do NOT proceed — registering the task in tasks.md is the orchestrator's responsibility, not yours.
After reading the artifacts, read same-layer same-shape files and their tests to reuse existing conventions before writing new code.

## Ownership
- Service / module: <...>
- Layer: <interfaces / application / domain / infrastructure>

## Rules (implementation discipline)
1. Layering dependency direction: interfaces → application → domain ← infrastructure; domain has zero framework dependencies
2. Infrastructure only implements the ports & repositories Protocols; cross-service data access only via HTTP / events
3. Transaction pattern: change aggregate → pull_events() → publish_all → commit
4. Test discipline: unit with zero external dependencies / integration with testcontainers / e2e with TestClient + mocked dependencies
5. Before writing tests, read the same-layer same-shape test files and reuse existing fixtures and naming conventions
6. Tests are documentation: one test asserts one behavior; state machines test both legal and illegal transitions
7. All four quality gates green before done: lint → format --check → type --strict → test (including the coverage threshold)
8. Never delete assertions / add skip fallbacks / relax existing assertions just to go green
9. Never hide failures: report red tests and under-coverage honestly with attribution

## Output contract (four-part report, must follow this structure)
## Change List
- <list of added/modified files, each with file:line and a one-line description>

## Verification Results
- lint: <pass/fail summary>
- format: <pass/fail summary>
- type: <pass/fail summary>
- test: <passed count/failed count; paste key errors on failure>
- coverage: <report only when the project declares a threshold (adapter §2 gate table); otherwise state "no threshold declared -- pass/fail only"; when reported, list file:line gaps in branches>

## Self-Test Checklist (confirm each item before submitting)
- [ ] Layering direction correct (domain zero framework / infra only implements ports & repositories)
- [ ] Cross-service data access via HTTP / events, no direct shared-database connection
- [ ] Transaction pattern follows the aggregate discipline
- [ ] No new un-commented type: ignore / noqa
- [ ] Core logic has tests, coverage meets the threshold
- [ ] All four quality gates green (with output)

## Remaining Risks
- <uncovered edges, todos, items needing manual verification; write "none" if there are none>
```

## Quick discipline checklist

- [ ] Read same-layer same-shape reusable patterns first; don't reinvent wheels
- [ ] Core logic must have tests, coverage meets the threshold
- [ ] Actually run the four quality gates and paste the output; never claim "passed" from memory
- [ ] Report failures and attribution honestly
