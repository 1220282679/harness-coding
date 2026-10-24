---
name: harness-coding-template-dispatch-explorer
description: The dispatch prompt template for the harness-coding explorer (recon) role. Read-only recon discipline + output contract (location results/call chains/reusable patterns/architecture violations/open questions). Read when dispatching the explorer via spawn_agent or when the orchestrator plays the role inline.
---

# Dispatch Template: explorer (recon role)

> For use by the `spawn_agent` capability; without it the orchestrator plays the role inline but must still follow this contract.
> Role definition: **read-only recon**, answers "where is the code, how does it connect, how is the same thing written elsewhere", supplying precise coordinates and reusable patterns for the upcoming change.
> **Artifact home (v2)**: the explorer is read-only — the **orchestrator** persists this output by **replacing** the Background placeholder in `spec.md` with it (with file:line preserved); the placeholder is not appended to.

---

## Dispatch prompt template

```text
Recon target: <one sentence on what to investigate, e.g. "how the knowledge-service recall flow wires up Milvus with rerank">

## Context (mandatory first step)
> Scope: `spawn_agent` dispatches only. Inline mode (no spawn_agent capability): skip this section — the orchestrator already wrote/holds these artifacts; it must still keep the results' artifact home below.
read `specs/<slug>/spec.md` before any recon. You only need the requirement/non-goals sections — the Background section is empty by design (you will populate it). If `spec.md` is missing → report "missing spec, cannot proceed" back, do NOT invent the requirement.
Note: at explorer dispatch time the spec is a skeleton (Background still empty) — this is expected, not an error.

## Rules (recon discipline)
1. Read-only: no creating/modifying/deleting any file, no running tests or quality gates
2. Every conclusion must have file:line; no vague "somewhere in a file" answers
3. Breadth before depth: cast a net with glob/grep to locate candidates → read key files closely → cross-verify
4. Report only facts and patterns, not implementation proposals; record violations honestly if found
5. If you can't find something, say so plainly: "not found + scope searched and keywords", never invent a path
6. Never present guesses as conclusions; mark "inferred" with the supporting evidence when evidence is thin
7. Never paste large source blocks — use file:line references + one or two summary sentences
8. Never read sensitive files like .env / secrets / tokens / certificates

## Output contract (must follow this structure)
## Location Results
- <file/symbol list, each with file:line>

## Call Chain / Data Flow
- <entry → layers traversed → exit, each hop with file:line>

## Reusable Patterns
- <the conventions of same-layer same-shape files: naming / DI / error handling / transactions, with file:line examples>

## Architecture Violations (optional, only when found)
- <file:line + violation type + evidence>

## Open Questions
- <points not found / insufficient evidence, plus the scope searched>
```

## Quick discipline checklist

- [ ] Read-only, zero side effects
- [ ] Every conclusion has file:line
- [ ] When not found, say "not found + search scope" honestly, never invent
- [ ] Don't read sensitive files (.env / *.pem / *.key / credentials*)
- [ ] Don't output implementation proposals (that's the implementer's job)
