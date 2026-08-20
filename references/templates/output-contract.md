---
name: harness-coding-template-output-contract
description: The final-report output contract template for harness-coding. Report structure (requirement positioning/change list/verification results/remaining risks/skill usage log), per-channel report depth, quality-gate evidence format, and the relationship to report closing. Read when the orchestrator delivers the final report.
---

# Output Contract

> The concrete template for the "output contract" in the methodology body. The orchestrator delivers the final report following this structure and ensures the report file is closed.
> Every completed harness session follows this contract, regardless of channel tier.

---

## Report structure (must be in this order)

```markdown
## Requirement Positioning
- Classification: <work task / non-work task — verb: <…>; noun: <…>; deliverable: <yes/no>> (per SKILL.md session classification)
- Ownership: <service / module / repo>; architecture decision: <none / yes — plan highlights and confirmation result>

## Change List
- <list of added / modified files, each with file:line and a one-line description>

## Verification Results
- Quality gates: <summary of lint / format / type / test>
- Review: <verdict, rejection count>
- Security review (if any): <verdict>

## Remaining Risks
- <uncovered edges, todos, items needing manual verification; write "none" if there are none>

## Skill Usage Log
- <conditional skills this skill loaded and their trigger stages, listed one by one>
```

## Per-channel report depth

| Channel | Report depth |
|---------|-------------|
| 🟢 Light | Simplified: change list + verification results (lint + format actually executed with pasted output; type/test on demand when the change touches type-relevant or logic/test-relevant code) |
| 🟡 Standard | Full five sections: positioning / changes / verification / remaining / skill usage log (write "none" when none) |
| 🔴 Full | Full five sections + review verdict + security review (if any) |
| 📋 Findings-only | Full five sections: the Change List reads "none — findings-only" (plan/design deliverables: "none — plan-only"); the Verification section carries the review verdict + the graded Findings (for a plan deliverable: the plan-validation verdict in place of code Findings; gate evidence only if the reviewer actually ran the gates) |

## Quality-gate evidence format (embedded in the report)

```text
lint:   <command> → <output summary, e.g. "All checks passed">
format: <command> → <output summary, e.g. "N files already formatted">
type:   <command> → <output summary, e.g. "Success: no issues found">
test:   <command> → <N passed, M failed; paste key errors on failure>
```

> Key principle: **evidence before assertion**. Every "passed/failed" must be backed by actual command output; never claim from memory.

## Relationship between reporting and report closing

1. summary stage: deliver the final report per this contract + close the report from `🔄 in progress` to `✅ passed` / `❌ rejected` (an in-progress report abandoned at init is marked `❌ abandoned` instead)
2. merge stage: record the merge method (PR / direct merge / keep iterating)
3. If `metadata.skills_log` is non-empty → append the "Skill Usage Log" table to the report (Skill / Trigger stage / Trigger condition, deduplicated)
