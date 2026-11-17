# comment-ac spec

Requirement: a commented-out AC block must not count as a declared acceptance criterion (comment-stripping on AC extraction, symmetric with the v2.2.8 GATE-NA fix)
Background: AC extraction ran AC_RE over the raw spec text -- AC lines inside a multi-line HTML comment were collected as declared ACs and then flagged "is not covered by any task"; a comment is not a requirement

Acceptance criteria:
- AC-1: python scripts/artifact-check.py --fixtures fixtures/ reports comment-ac as matched (expect pass)
<!-- scope dropped while the spec was still a draft (append-only discipline applies to
committed ACs; a draft block commented out before first commit is not a requirement)
- AC-2: this commented-out AC must not be collected as declared
- AC-3: nor must this one -- under the pre-fix code both raise "is not covered by any task"
-->

Assumptions:
- A1: single-line comments (<!-- - AC-4: ... -->) were never collected (the line starts with '<', so AC_RE cannot match); only the multi-line block shape is the blind spot

Non-goals: no changes to gate-exemption scanning (already comment-stripped since v2.2.8)
