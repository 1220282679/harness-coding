# comment-ac tasks

- [x] T1 (AC-1): strip comments from the spec before AC extraction in validate_task_dir; verify: python scripts/artifact-check.py --fixtures fixtures/; Output: [PASS] fixture comment-ac (expect pass, got pass)

## Deferred
<!-- remaining risks as open checkboxes: unchecked = not done -->
- (none)

## Review
<!-- where review conclusions land (§5.2); an open blocker/major makes closing illegal -->
- R1 [resolved]: (minor) commented ACs also stop being referenceable targets -- a task citing a commented AC now errors "references unknown AC-<n>", which is the desired strictness (same shape as the v2.3.1 malformed-line guard)
