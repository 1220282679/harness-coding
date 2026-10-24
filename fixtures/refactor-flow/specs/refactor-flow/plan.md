# refactor-flow plan

Approach: extract RegistrationService; auth.py keeps only entry-point forwarding

Architecture decisions:
- AD-1: no new event (confirmed with the user, 2026-10-24)

Characterization baseline:
- tests/test_auth.py::test_register_flow pins current registration behavior; verified green before extraction

Task breakdown: see tasks.md
