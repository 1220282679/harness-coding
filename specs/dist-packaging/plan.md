# dist-packaging plan

Approach: one self-verifying build script (scripts/build-dist.py, pure stdlib) implementing an ALLOWLIST copy — SKILL.md, LICENSE, references/**, scripts/*.py minus the packager itself — into dist/harness-coding/, then a byte-identical verification pass over every copied file plus a missing/extra tree check, then (by default) a reproducible zip named from the SKILL.md version. Allowlist instead of blocklist so dev-only files can never leak even when new ones appear in the repo; the only directory ever cleaned is dist/harness-coding/ itself, and --out must resolve inside the repo, so a misdirected --out cannot destroy source.

Architecture decisions:
- AD-1: allowlist copy, not blocklist — bundle membership is declared positively; adding runtime surface is a deliberate act
- AD-2: build-dist.py excludes itself from the bundle — the packager is not runtime surface; re-packaging happens from the repo
- AD-3: only the bundle subdir is cleaned; --out must resolve inside the repo — the blast radius of a wrong --out is a stray subdir, not lost source

Task breakdown: see tasks.md
