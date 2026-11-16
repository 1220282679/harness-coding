# gate-na spec

Requirement: demonstrate a legal gate exemption (Gate N/A protocol) — SQL-only migration-script change
Background: the project has no applicable static type checking; the test gate runs migration-script smoke tests

Acceptance criteria:
- AC-1: psql -f migrations/001_init.sql && psql -c "\dt" output contains the users table

Assumptions:
- A1: the migration script is idempotent (IF NOT EXISTS), rationale: project migration convention

Non-goals: do not touch any Python code

## Gate Exemptions
- GATE-NA(type): SQL-only migration change; the project has no applicable static type checking (chain-wide for this task chain)
- GATE-NA(format): SQL files are out of ruff format's scope; the project has no sqlfluff configured (chain-wide for this task chain)
