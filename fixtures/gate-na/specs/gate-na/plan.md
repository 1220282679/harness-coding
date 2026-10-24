# gate-na plan

1. 审阅 migrations/001_init.sql 的幂等性（IF NOT EXISTS 全覆盖）
2. 在本地 psql 执行迁移并验证 \dt 输出
3. lint + test 门禁照常；type/format 按 spec 门禁豁免跳过
