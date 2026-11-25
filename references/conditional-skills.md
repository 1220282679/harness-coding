---
name: harness-coding-conditional-skills
description: Static conditional-skill fallback table for the harness-coding skill (L3, read only when find_skill misses). Lists the eight technique slots the methodology may pull in — question technique, isolation, decision record, debugging, simplify, security review, verification, branch finishing — each tied to the point in the flow where it applies. Read after find-skill.py exits 2 or reports no match.
---

# Conditional Skills (static fallback)

> SKILL.md §7 resolves `find_skill` context-first. This table is what remains when no library answers: eight technique slots, each bound to a moment in the flow. Installing one into a host skill library turns it from a static hint into a loadable skill; until then, apply it as a discipline inline.

| Slot | Applies at | What it buys |
|------|-----------|--------------|
| question technique (`grill-me`-class) | clarification gate, 🟡/🔴 fuzzy scope | decision-forcing questions with declared landing spots; ≤7 per batch |
| isolation | after the plan, before implementation | the change lands on its own branch/worktree, not the shared tree |
| decision record | after the plan, at any architecture call | one paragraph per decision: context, options, choice, reversal cost |
| debugging | after any gate failure | root-cause order — reproduce → bisect → read the diff, never "fix and re-run" |
| simplify | after gates pass, before review | remove what the change made redundant; add no behavior |
| security review | 🔴, before close-out re-verification | trust boundaries, injection surface, secrets, authz on the new path |
| verification | before close-out | does the evidence cover the ACs, or only the tests that were convenient |
| branch finishing | after close-out | commit shape, PR body, cleanup of scratch artifacts |

A slot that does not apply is skipped silently — it is not a gate and needs no `GATE-NA` declaration.
