# comment-ac plan

Approach: strip HTML comments from the spec text before AC_RE extraction in validate_task_dir (the same without_comments helper the v2.2.8 GATE-NA fix introduced); pinned by this fixture -- under the old code the commented AC-2/AC-3 lines raised "is not covered by any task" and the case failed
