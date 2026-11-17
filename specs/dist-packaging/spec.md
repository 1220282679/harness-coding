# dist-packaging spec

Requirement: Add a release mechanism that packages the repo into a slim, installable skill bundle under dist/ — one command, self-verifying, pure stdlib — so a harness install never drags dev-only files along.

Background: .gitignore has reserved dist/ since v2.2.9 ("slim install copy: SKILL.md + references/ + scripts/ + LICENSE") but the mechanism to produce it did not exist; installs today copy the whole repo (fixtures/specs/design docs included) or cherry-pick by hand. Install targets per README: Claude Code `.claude/skills/` (or `~/.claude/skills/`), opencode `.opencode/skills/` (or `~/.config/opencode/skills/`), Codex `.codex/skills/` (or `~/.codex/skills/`).

Acceptance criteria:
- AC-1: `python scripts/build-dist.py --no-zip` exits 0 and creates dist/harness-coding/ containing exactly the allowlisted runtime surface (SKILL.md, LICENSE, references/**, the three runtime scripts) with a printed manifest
- AC-2: the build self-verifies — every bundle file byte-identical to its source, no missing/extra files; verification output pasted in T2 <!-- superseded 2026-11-17 (v2.3.6): verification compares against the line-ending-normalized source (CRLF→LF, defensive) plus a no-CRLF assertion; re-pointed by AC-8 -->
- AC-3: the default run also produces dist/harness-coding-v<version>.zip with the version read from SKILL.md frontmatter; `--no-zip` skips it; zip entries use forward slashes and fixed timestamps (reproducible — two builds of the same tree produce the same sha256) <!-- superseded 2026-11-17 (v2.3.6): reproducibility scope widened from same-tree to cross-platform metadata (create_system pinned); re-pointed by AC-8 -->
- AC-4: dev-only files (README.md, CHANGELOG.md, SDD-REFACTOR-DESIGN.md, fixtures/, specs/, .claude/, opencode.json, build-dist.py itself) are all absent from the bundle
- AC-5: `python scripts/artifact-check.py --fixtures fixtures` PASS (7 artifact cases) and `python scripts/artifact-check.py specs/` PASS (now 3 chains) at close-out
- AC-6: SKILL.md `version: 2.3.0` + CHANGELOG entry; README documents the build command in the install section and the new script in the tree
- AC-7: `.github/workflows/release.yml` triggers on `v*` tag push and runs the same locally-verifiable commands — fixture gates + specs validation, `python scripts/build-dist.py`, then the zip is attached to the tag's GitHub Release; locally executable check: those gate + build commands pass on this tree (the live tag-push run verifies the wiring)
- AC-8: zip entry metadata is platform-independent — every entry in `dist/harness-coding-v<version>.zip` has `create_system == 3` (pinned; ZipInfo defaults to the running platform: 0 on Windows, 3 on Unix — this is the byte-level root cause of the v2.3.4 CI-vs-Windows sha256 mismatch, CI 2e8286a0… vs Windows 76ad4352…) — and no bundle file contains CRLF (defensive normalization, byte-level audit 2026-11-17: all current trees/blobs/zips are already LF-only). Locally executable check: a python one-liner over the built zip's infolist + bundle bytes
- AC-9: two release lanes in `release.yml`, identical gates on both (no skips): (a) v* tag push keeps the immutable versioned release with the default `harness-coding-v<version>.zip`; (b) push to main publishes a rolling prerelease tagged `latest` whose zip is named after the commit via `build-dist.py --zip-stem harness-coding-main-<short-sha>` — no version bump, no CHANGELOG entry (rolling builds are installs, not versions; the commit + zip sha256 are recorded in the release body and the previous rolling asset is deleted on replace). Locally executable check: `--zip-stem` builds a correctly named, self-verified zip and the default name is unchanged; workflow wiring verified by the live main-push run on the close-out push
- AC-10: release zips are byte-identical across machines by construction — every entry is STORED (compress_type 0; no deflate), so entry bytes are a pure function of file content plus pinned metadata (create_system 3, external_attr 0o644, fixed timestamps, forward-slash names). DEFLATED is dropped on empirical grounds: the cross-machine comparison pending since v2.3.6 came back negative for v2.3.7 — CI (ubuntu) build `bfa9986c…` vs same-content Windows build `e6f1a290…` had the SAME compressed size (45.4 KB) but different sha256; zlib's deflate output varies across platforms/zlib builds at any level, so it cannot be pinned. Cost: zip grows to the uncompressed bundle size (~100 KB). Locally executable check: double build → identical sha256, infolist compress_type all 0, testzip clean; the v2.3.8 tag push provides the final CI-vs-Windows confirmation

Assumptions:
- A1: the bundle copies scripts/*.py wholesale minus build-dist.py itself — new runtime scripts are picked up automatically; the packager is not runtime surface
- A2: README/CHANGELOG/design docs stay out of the bundle per the .gitignore comment's declared surface; repo browsing covers human-facing docs
- A3: dist/ remains gitignored build output — the release artifact is the zip, not a git object

Non-goals: no auto-install into harness skill directories (copy/link stays manual); no checksums manifest or GitHub release automation; no CI workflow (recorded as Deferred D1) <!-- superseded 2026-11-16: the CI follow-up landed as AC-7/T6 (append-only per §12) -->

## Gate Exemptions
- GATE-NA(lint): repo defines no linter; the project-defined gates are the fixture suites — scope: chain-wide
- GATE-NA(format): no formatter configured in this repo — scope: chain-wide
- GATE-NA(type): stdlib-only scripts, no type checker configured; build correctness is covered by its own verification pass plus the fixture suites — scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites plus the build's self-verification (AC-1/AC-2/AC-5), run in full at close-out — scope: chain-wide
