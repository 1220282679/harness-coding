# malformed-task tasks

- [x] T1 (AC-1): add the TASK_LIKE_RE guard to check_task_file and land this fixture (spec/plan/tasks + .expect with the err= substring); verify: python scripts/artifact-check.py --fixtures fixtures/; Output: [FAIL] fixture malformed-task (expect fail, got fail) -- "malformed task line ... silently skipped otherwise: - [x] T2: this line is deliberately missing the (AC-x) reference block" reported; run exits 0 ("PASS fixtures: 8 artifact cases matched expectations")
- [x] T2: this line is deliberately missing the (AC-x) reference block

## Deferred
<!-- remaining risks as open checkboxes: unchecked = not done -->
- (none -- the guard's scope decision is recorded as spec A1)

## Review
<!-- where review conclusions land (§5.2); an open blocker/major makes closing illegal -->
- R1 [resolved]: (minor) T2 must stay malformed forever or the fixture stops testing the guard -- enforced by the .expect err= assertion, which fails the fixture run if the error ever disappears
