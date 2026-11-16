# broken-intent-na intent

Intent: tweak the register endpoint's SQL migration script; the type gate is skipped without declaring an exemption (deliberately broken -- proves the intent-channel pairing check has teeth)
Verify: python -m pytest tests/test_register.py -q

- patch migrations/002_add_index.sql; verify: psql -f migrations/002_add_index.sql; Output: migration applied; GATE-NA(type): skipped silently
