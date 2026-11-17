# workbuddy-adapter intent

Intent: Add the WorkBuddy adapter (`references/adapters/workbuddy.md`) -- the capability contract's `find_skill` probe already scans `~/.workbuddy/skills` (DEFAULT_ROOTS), but `references/adapters/` shipped no workbuddy.md, so the skill was designed for WorkBuddy yet not onboarded onto it (onboarding checklist §6). The adapter maps the 7 required capabilities (Read / Write / Edit / Glob / Grep / Bash+PowerShell / AskUserQuestion) and the 4 mapped optional ones (Agent / git-branch / command probe / WebSearch+WebFetch) per `_adapter-template.md`, structured like the claude-code and opencode siblings. Uniquely, the tool names are verified against the live WorkBuddy session authoring the adapter (2026-11-17) rather than external docs. Doc sync: README directory-tree adapters comment. Doc sync deliberate non-change: SKILL.md and capability-contract.md name no adapter files, so they need no edit.
Verify: python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py

## Gate Exemptions
<!-- a non-applicable gate must be declared here with a reason + scope, never skipped silently; artifact-check enforces the pairing -->
- GATE-NA(lint): repo defines no linter; the project-defined gates are the fixture suites -- scope: chain-wide
- GATE-NA(format): no formatter configured in this repo -- scope: chain-wide
- GATE-NA(type): stdlib-only scripts, no type checker configured; the adapter is markdown -- scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites (9 artifact cases + 4 probe cases) plus specs validation plus the build's self-verification (the new adapter must appear in the bundle listing), run in full at close-out -- scope: chain-wide

## Deferred
<!-- remaining risks as open checkboxes: unchecked = not done -->
- [ ] D1: the adapter has not been exercised end-to-end under WorkBuddy yet (onboarding §6: one 🟢 zero-file task + one 🔴 sample in a host project); suggested follow-up: install `dist/harness-coding-v<version>.zip` into a real project and run the drill -- this is the standing "host-project validation" next step, independent of any adapter bug

## Review
<!-- where review conclusions land (§5.2); an open blocker/major makes closing illegal -->
- R1 [resolved]: (minor) tool-name verification claim is unusually strong (live session) but must stay falsifiable -- the version note still defers to "the live tool catalogue of the current session" as authoritative, matching the other adapters' stance
- R2 [resolved]: (minor) WorkBuddy has no repo-shipped permission-config file documented (unlike opencode.json / .claude/settings.json) -- §5 states honest first-use guidance instead of inventing a config path; if a WorkBuddy permission surface is confirmed later, add the file and point §5 at it
- R3 [resolved]: (minor) sandbox-escalation semantics added as a §7 deviation: escalation is an ask_user decision, never a silent way past a failed gate -- a mapping decision, recorded to prevent the orchestrator from discovering it the hard way
