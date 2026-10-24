# refactor-flow spec

需求: 将注册逻辑拆分为独立服务并补充过期处理测试
背景: register() 过长；调用链见 src/auth.py:12（explorer 侦察）

验收标准:
- AC-1: pytest tests/test_auth.py -k expired 通过
- AC-2: ruff check . 通过

假设:
- A1: 沿用既有 AuthService 命名约定（依据: 仓库内既有模式）

非目标: 不改动登录流程
