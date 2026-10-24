# refactor-flow tasks

- [x] T1 (AC-1): extract RegistrationService and migrate expiry-handling logic; verify: pytest tests/test_auth.py -k expired; Output: 3 passed in 0.12s
- [x] T3 (AC-3): characterization baseline re-run after extraction; verify: pytest tests/test_auth.py; Output: 5 passed in 0.31s
- [ ] T2 (AC-2): close-out full gate re-run; verify: ruff check .

## Deferred
- [ ] D1: performance benchmark not run; suggested follow-up: benchmark before merge

## Review
- R1 [resolved]: service missing constructor injection → fixed in T1
- R2 [open|minor]: log wording could be unified
