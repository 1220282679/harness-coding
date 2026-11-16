# review-hardening plan

Approach: four tracks in dependency order — (1) section-shape normalization (template + gate-na fixture + dod-closure spec), (2) validator upgrade: `.expect` gains per-error-class `err=<substring>` assertions checked by `run_fixtures`, (3) 🟡 pairing coverage: two symmetric fixtures — the first run of broken-intent-na exposed a real bug (the 🟡 pairing check was vacuous: usage self-declared from the same full text), fixed by scoping intent declarations to the `## Gate Exemptions` section, (4) debt hygiene (D1 check-off) + docs sync (README count, design §11.3) + release (CHANGELOG, version bump) + this dogfood chain.

Architecture decisions:
- AD-1: `.expect` stays line-based and backward compatible — first line pass|fail, optional `err=<substring>` lines each required to appear in one of the reported error lines (key=value style, mirroring the probe's `.expect` format)
- AD-2: the 🟡 pairing fix scopes declarations to the intent's `## Gate Exemptions` section rather than accepting inline labels — the normalized shape is the documented contract; a full-intent declaration scan is structurally vacuous and must not be restored

Task breakdown: see tasks.md
