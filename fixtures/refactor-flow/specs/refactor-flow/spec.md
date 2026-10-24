# refactor-flow spec

Requirement: split registration logic into a standalone service and add expiry-handling tests
Background: register() too long; call chain at src/auth.py:12 (explorer recon)

Acceptance criteria:
- AC-1: pytest tests/test_auth.py -k expired passes
- AC-2: ruff check . passes
- AC-3: pytest tests/test_auth.py (full baseline suite) passes unchanged

Assumptions:
- A1: keep the existing AuthService naming convention (rationale: existing repo pattern)

Non-goals: do not touch the login flow
