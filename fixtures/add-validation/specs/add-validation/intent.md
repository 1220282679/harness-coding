# add-validation intent

意图: 为注册接口补充参数校验（邮箱格式 / 密码长度）
验证: python -m pytest tests/test_register.py -q

## 意图追加
- 密码强度提示信息补全; 验证: python -m pytest tests/test_register.py -q -k hint

## Deferred
- [ ] D1: 密码长度上限待产品确认; 建议后续: 确认后补充规格

## Review
- R1 [resolved]: 缺少邮箱格式校验用例 → 修复于实现
- R2 [open|minor]: 提示文案可再统一
