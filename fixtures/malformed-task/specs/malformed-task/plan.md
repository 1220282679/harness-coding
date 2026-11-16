# malformed-task plan

Approach: add a task-like-line guard to check_task_file -- lines matching the `- [<x>] T<n>` prefix but failing TASK_RE report a "malformed task line" error instead of being skipped; prove the regression with a new fixture whose tasks.md carries one valid T-line and one deliberately malformed T-line

Architecture decisions:
<!-- the four ask_user triggers: new port / new event / table schema / aggregate behavior change; the confirmation result must be recorded -->
- AD-1: guard scope = the `- [<x>] T<n>` prefix only (A1 in spec); no new error class beyond the one message -- keeps the .expect err= assertion surface minimal (confirmed by the user's "修复掉吧" on the 2026-11-16 scan reply)

Characterization baseline:
<!-- required only for behavior-preserving refactors; delete this section for non-refactor tasks -->
(not a behavior-preserving refactor: this adds a new error path where the old behavior was a silent skip)

Task breakdown: see tasks.md
