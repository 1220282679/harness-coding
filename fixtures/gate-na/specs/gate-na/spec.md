# gate-na spec

需求: 演示合法的门禁豁免（Gate N/A protocol）——纯 SQL 迁移脚本改动
背景: 项目无静态类型检查适用面；test 门禁跑迁移脚本冒烟

验收标准:
- AC-1: psql -f migrations/001_init.sql && psql -c "\dt" 输出含 users 表

假设:
- A1: 迁移脚本幂等（IF NOT EXISTS），依据: 项目迁移规范约定

门禁豁免:
- GATE-NA(type): 纯 SQL 迁移脚本改动，项目无静态类型检查适用面
- GATE-NA(format): SQL 文件不在 ruff format 管辖范围，项目未配置 sqlfluff

非目标: 不改动任何 Python 代码
