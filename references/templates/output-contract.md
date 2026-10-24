---
name: harness-coding-template-output-contract
description: The close-out reply contract for harness-coding (v2). Structure of the closing chat reply (requirement positioning / verification results / remaining risks), per-channel depth, and quality-gate evidence format. The reply is derived from artifacts + diff — never from memory; no report file is written. Read when the orchestrator delivers the close-out.
---

# Output Contract (close-out reply, v2)

> The concrete template for close-out. The closing reply is a **chat message derived from artifacts + diff** — there is no report file. Durable traceability lives in `specs/<slug>/` + git; an on-demand full view is available via `python scripts/derive-report.py specs/<slug>`.

---

## Reply structure (must be in this order)

```markdown
## Requirement Positioning
- Classification: <work task / non-work task — verb: <…>; noun: <…>; deliverable: <yes/no>>
- Ownership: <service / module / repo>; architecture decisions: <none / yes → point to spec.md AD-ids>

## Verification Results
- Quality gates: <summary of lint / format / type / test — per-task and close-out re-verification>
- Review: <verdict; open findings count by level>
- Security review (if any): <verdict>

## Remaining Risks
- <open `## Deferred` entries verbatim; write "none" when the section is empty>

## Next Step
- <merge decision from ask_user: PR / direct merge / keep iterating>
```

> The old "Skill Usage Log" section is dropped (harness-internal self-audit, no consumer). Conditional-skill usage is visible in the artifacts/repo history where it matters.

## Per-channel depth

| Channel | Close-out depth |
|---------|-----------------|
| 🟢 Light | Inline summary: classification line + change list + verification results (lint + format executed with pasted output; type/test on demand with reason). **Zero files created.** |
| 🟡 Standard | Full structure above, derived from `intent.md` (Review/Deferred sections) + diff |
| 🔴 Full | Full structure above, derived from spec/plan/tasks + diff; review verdict from the `## Review` section |
| 📋 Findings-only | Full structure above; Change List reads "none — findings-only" (plan deliverables: "none — plan-only"); Verification carries the graded Findings / plan-validation verdict |

## Quality-gate evidence format (embedded in the reply)

```text
lint:   <command> → <output summary, e.g. "All checks passed">
format: <command> → <output summary, e.g. "N files already formatted">
type:   <command> → <output summary, e.g. "Success: no issues found">
test:   <command> → <N passed, M failed; paste key errors on failure>
```

> Key principle: **evidence before assertion**. Every "passed/failed" must be backed by actual command output; never claim from memory. The close-out re-verification (🟡/🔴) output is the authoritative evidence for the reply.
