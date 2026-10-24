# gate-na tasks

- [x] T1 (AC-1): run the migration and verify the table exists; verify: psql -f migrations/001_init.sql; Output: CREATE TABLE / users | 1 row; GATE-NA(type): declared in spec Gate exemptions; GATE-NA(format): declared in spec Gate exemptions
- [x] T2 (AC-1): lint and test gates run as usual; verify: ruff check . && pytest tests/test_migrations.py; Output: ruff: All checks passed! / pytest: 3 passed

## Deferred
- [ ] D1: sqlfluff not adopted yet, SQL static checking owed; suggested follow-up: evaluate adopting sqlfluff

## Review
- R1 [resolved]: migration script lacked transaction wrapping → fixed in T1 (BEGIN/COMMIT added)
