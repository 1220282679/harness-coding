# refactor-flow tasks

- [x] T1 (AC-1): 抽取 RegistrationService 并迁移过期处理逻辑; 验证: pytest tests/test_auth.py -k expired; 输出: 3 passed in 0.12s
- [ ] T2 (AC-2): 收尾全量门禁复跑; 验证: ruff check .

## Deferred
- [ ] D1: 性能基准未跑; 建议后续: 合并前补基准

## Review
- R1 [resolved]: 服务缺少构造注入 → 修复于 T1
- R2 [open|minor]: 日志措辞可统一
