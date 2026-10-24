# gate-na tasks

- [x] T1 (AC-1): 执行迁移并验证表存在; 验证: psql -f migrations/001_init.sql; 输出: CREATE TABLE / users | 1 row; GATE-NA(type): declared in spec 门禁豁免; GATE-NA(format): declared in spec 门禁豁免
- [x] T2 (AC-1): lint 与 test 门禁照常执行; 验证: ruff check . && pytest tests/test_migrations.py; 输出: ruff: All checks passed! / pytest: 3 passed

## Deferred
- [ ] D1: sqlfluff 未接入，SQL 静态检查欠账; 建议后续: 评估接入 sqlfluff

## Review
- R1 [resolved]: 迁移脚本缺少事务包裹 → 修复于 T1（BEGIN/COMMIT 已补）
