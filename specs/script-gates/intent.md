# script-gates intent

Intent: Close the static-check gap surfaced by the 2026-11-18 external review -- the four scripts/ tools were validated only by their fixture suites, with no lint or type gate on the Python code itself (scan-fixes' Gate Exemptions declared "no linter / no type checker configured"; true then, stale now). Added, not relaxed: ruff (E,F,W,UP,B,SIM,RUF; line-length 120 -- the E501 hits were long error-message strings whose detail is deliberate, and all lines are already under 120) and mypy --strict (every function annotated; the two real findings were the E741 ambiguous `l` loop variables in artifact-check/derive-report and derive-report's un-narrowed `CompletedProcess.stdout` Optional, fixed as `(stdout or "")` instead of silencing the checker). Both run locally and in release.yml as a new "Static checks" step shared by both lanes, with pinned versions (ruff==0.17.5 / mypy==2.4.1) matching the repo's supply-chain discipline. scan-fixes' chain-wide lint/format/type exemptions stay historically accurate for that chain; this chain declares none for lint/type.
Verify: ruff check scripts/ --isolated --select E,F,W,UP,B,SIM,RUF --line-length 120 && mypy --strict scripts/ && python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py

## Intent Additions
<!-- multi-turn continuation (§12): new requirements of the same task chain append here, each with a verify command -->

### 2026-11-18 documentation drift sweep (count-free wording)

Intent: De-digitize the two hardcoded fixture counts in README ("产物校验用例 9 个 ... 探针自检用例 4 个" in the tree comment, "9 个产物用例全部符合预期" in the verification block) -- the only finding in the 2026-11-18 review backed by an observed failure class rather than speculation: dod-closure's AC-8 (fixture-count comment matching the runner output) was superseded twice as the count drifted 5 -> 6 -> 7 -> 8 across v2.2.5/v2.2.7. Wording now states the category list and defers the count to the runner's actual output. CHANGELOG entries are immutable release history and keep their counts.
Verify: python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py && (grep -nE "用例 [0-9]+ 个|[0-9]+ 个产物用例" README.md || echo "no hardcoded counts remain")

### 2026-11-18 D1 discharge (requirements-dev.txt)

Intent: Discharge this chain's Deferred D1 -- add `requirements-dev.txt` as the single source of truth for the static-check tool pins (ruff==0.17.5 / mypy==2.4.1, unchanged from what CI already pinned inline); release.yml's Static checks step now installs via `pip install -r requirements-dev.txt` instead of repeating the versions inline, closing the local-vs-CI version-skew window by construction. README's verification section points at the file instead of hardcoding versions. The file is dev-only tooling: dist packaging's allowlist can never include it, and the runtime scripts stay pure stdlib.
Verify: ruff check scripts/ --isolated --select E,F,W,UP,B,SIM,RUF --line-length 120 && mypy --strict scripts/ && python scripts/artifact-check.py --fixtures fixtures/ && python scripts/find-skill.py --fixtures fixtures/skills/ && python scripts/artifact-check.py specs/ && python scripts/build-dist.py && pip install --quiet -r requirements-dev.txt && echo "requirements-dev.txt resolves"

## Gate Exemptions
<!-- a non-applicable gate must be declared here with a reason + scope, never skipped silently; artifact-check enforces the pairing -->
- GATE-NA(format): no formatter configured in this repo (ruff --fix not adopted; formatting stays hand-consistent and the checker is line-length neutral) -- scope: chain-wide
- GATE-NA(test): no pytest suite; the test slot is fulfilled by the fixture suites (9 artifact cases + 4 probe cases) plus specs validation plus the build's self-verification, run in full at close-out -- scope: chain-wide

## Deferred
<!-- remaining risks as open checkboxes: unchecked = not done -->
- [x] D1: local static-check runs use whatever ruff/mypy is installed in the session env, while CI pins exact versions (ruff==0.17.5 / mypy==2.4.1) -- a version-skew window between a local green and a CI red exists by construction; suggested follow-up: add a requirements-dev.txt (or equivalent) pinning both tools, referenced by README's verification section <!-- discharged 2026-11-18: requirements-dev.txt added as the single pin source; CI installs from it; see the "D1 discharge" Intent Addition -->

## Review
<!-- where review conclusions land (§5.2); an open blocker/major makes closing illegal -->
- R1 [resolved]: (minor) line-length was raised 100 -> 120 instead of wrapping six long error-message strings -- accepted deliberately: the strings are user-facing diagnostics whose detail is the point, and 120 covers every existing line; ruff still enforces E501 at the new bound
- R2 [resolved]: (minor) mypy --strict demanded annotations on all ~35 functions across 4 files -- a large mechanical diff, but chosen over a weaker mypy mode: relaxing the checker to fit unannotated code would be exactly the "loosen checks for a green light" behavior the repo's own gates forbid
- R3 [resolved]: (minor) find-skill.scan_roots reused the `root` loop variable as both str and Path (the mypy var-annotated/assignment finding) -- split into `root_dir` (str) and `root` (Path), no behavior change
