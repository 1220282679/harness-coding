# intent-gate-na intent

Intent: tweak the register endpoint's SQL migration script (index-only change)
Verify: python -m pytest tests/test_register.py -q

- patch migrations/002_add_index.sql; verify: psql -f migrations/002_add_index.sql; Output: migration applied; GATE-NA(type): declared in intent Gate Exemptions

## Gate Exemptions
- GATE-NA(type): SQL-only migration change; the project has no applicable static type checking (chain-wide for this task chain)
