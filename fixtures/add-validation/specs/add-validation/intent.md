# add-validation intent

Intent: add parameter validation to the register endpoint (email format / password length)
Verify: python -m pytest tests/test_register.py -q

## Intent Additions
- password-strength hint copy completion; verify: python -m pytest tests/test_register.py -q -k hint

## Deferred
- [ ] D1: password length upper bound pending product confirmation; suggested follow-up: spec it once confirmed

## Review
- R1 [resolved]: missing email-format test case → fixed during implementation
- R2 [open|minor]: hint copy could be unified
