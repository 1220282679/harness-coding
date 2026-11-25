# harness-coding

**通用 Harness 编码编排技能（v2 · 产物驱动）**

把一句话需求变成受控的变更流程：会话分类 → 分级通道（🟢/🟡/🔴/📋）→ 角色派发 → 质量门禁 → 收尾回复。

核心转变：**状态活在产物里，历史活在 git 里，证据活在门禁输出里**——没有报告文件，没有私有协议状态机。

## 核心思想

1. **产物即状态**：任务状态活在 `specs/<slug>/` 的平凡 markdown（spec / plan / tasks；🟡 单文件 `intent.md`）——恢复 = 读文件，版本 = git
2. **能力名即契约**：方法论只引用能力名（7 必需 + 5 可选，可选项均带降级规则）；运行时对照对话上下文解析（context-first），适配器映射仅为提示
3. **纪律 → 结构**：勾选必须附输出、open blocker/major 拒绝收尾，`artifact-check.py` 机械执法——不靠 prompt 自觉
4. **单一事实源**：接入新 Harness 只需一份适配器文件

## 通道 × 产物矩阵

| 通道 | 产物 | 流程 | 收尾 |
|------|------|------|------|
| 🟢 轻量 | **零文件** | 实现 → lint/format | 内联摘要 |
| 🟡 标准 | `intent.md` | 定位 → 澄清 → 实现 → 门禁 → 评审 → 收尾重验 | 收尾回复 |
| 🔴 完整 | `spec.md` / `plan.md` / `tasks.md` | 信息补给 → 澄清门 → plan → 逐任务实现+门禁 → 评审 → 收尾重验 | 收尾回复 + 追溯视图 |
| 📋 仅结论 | spec/plan 即交付物 | 评审/校验 | 校验结论 |

- **多轮续接**：slug 由首个需求生成，后续消息默认追加任务；通道只升不降；AC 只增不改（修改用 supersede 标注）
- **收尾重验**（🟡/🔴）：逐任务绿 ≠ 全仓绿，收尾前强制全量门禁重跑
- **上下文经由产物流动**，绝不经由父会话摘要

## 角色与产物归宿

| 角色 | 职责 | 输出归宿 |
|------|------|---------|
| Explorer | 只读侦察（file:line） | `spec.md` Background |
| Implementer | 实现 + 测试 + 门禁 | `tasks.md` 勾选 + 粘贴 `Output:` |
| Reviewer | 分级评审结论 | `## Review` 节（`R<n> [open\|level]`） |

## 质量门禁

固定顺序 `lint → format → type → test`，命令由项目定义（适配器 §2）；证据必须粘贴，绝不凭记忆声称通过。

- **Gate N/A 豁免**：绝不静默跳过——在 spec/intent 的 `Gate Exemptions` 节声明 `GATE-NA(<gate>): <原因 + 范围>`，校验器机械校验配对
- **coverage 阈值**由项目声明，未声明 → 普通 pass/fail，绝不发明数字
- **重构**先建特征测试基线，一条 AC = "基线测试原样通过"

## 目录结构

```
harness-coding/
├── SKILL.md                    # 方法论主体
├── references/
│   ├── capability-contract.md  # 能力契约（7 必需 + 5 可选）
│   ├── flow.md                 # 通道流转细则（通道选择 / 澄清门 / 延续 / 收尾复验）
│   ├── conditional-skills.md   # 条件技能静态表（find_skill 未命中时的兜底）
│   ├── adapters/               # 适配器（claude-code / codex / opencode / workbuddy / _template）
│   └── templates/              # 产物模板 + 派发模板 + 收尾契约
├── scripts/
│   ├── artifact-check.py       # 产物校验器（AC↔T 闭合 / 评审收尾守卫 / Gate N/A 配对）
│   ├── derive-report.py        # 按需追溯视图（stdout，永不落盘）
│   ├── find-skill.py           # 技能库探针（find_skill 降级路径）
│   └── build-dist.py           # 发布打包（allowlist + 字节级自校验 + 可复现 zip）
├── specs/                      # dogfood 产物链（被 artifact-check.py 持续校验的真实样本）
└── fixtures/                   # 校验用例（含故意损坏样本，逐错误类断言）
```

## 安装

```bash
python scripts/build-dist.py     # → dist/harness-coding/ + dist/harness-coding-v<version>.zip
```

或从 GitHub Releases 下载：`v*` tag → 不可变版本 Release；main push → `latest` 滚动 prerelease。两车道门禁完全相同；滚动构建仅用于安装，不计入 CHANGELOG。

复制（或软链）`dist/harness-coding/` 到技能目录：

| Harness | 路径 |
|---------|------|
| Claude Code | `<project>/.claude/skills/harness-coding/`（或 `~/.claude/skills/`） |
| opencode | `<project>/.opencode/skills/harness-coding/`（或 `~/.config/opencode/skills/`） |
| Codex | `<project>/.codex/skills/harness-coding/`（或 `~/.codex/skills/`） |

> 权限：宿主项目放行 `python scripts/artifact-check.py*`、`python scripts/derive-report.py*`、`python scripts/find-skill.py*`。

打包为 **allowlist 白名单制**，只含运行面，dev 文件不混入；zip 条目 STORED + 固定元数据，跨机器字节可复现是构造性保证。

## 验证

```bash
ruff check scripts/ --isolated --select E,F,W,UP,B,SIM,RUF --line-length 120  # lint（版本钉死在 requirements-dev.txt）
ruff format --check scripts/ --line-length 120                                # format
mypy --strict scripts/                                                        # type
python scripts/artifact-check.py --fixtures fixtures/   # 产物校验自测（含故意损坏样本）
python scripts/find-skill.py --fixtures fixtures/skills # 探针自测
python scripts/artifact-check.py specs/                 # 校验宿主项目的任务产物
python scripts/artifact-check.py --migrate specs/ --dry-run  # 预览遗留 GATE-NA 迁移（执法强化前合法关闭的链）
python scripts/artifact-check.py --migrate specs/            # 执行迁移：内联用法归并进 ## Gate Exemptions 节（幂等）
python scripts/artifact-check.py --migrate-fixtures fixtures/migrate/  # 迁移自测（门集合 + 迁移后 PASS + 幂等）
python scripts/derive-report.py specs/<slug>            # 生成追溯视图（stdout）
```

## 能力契约与适配器

- **必需（7）**：`read` / `write` / `edit` / `glob` / `grep` / `run_command` / `ask_user`
- **可选（5，均带降级）**：`spawn_agent`（内联执行）/ `create_branch`（主工作区+标注）/ `check_command`（先跑再决定）/ `find_skill`（探针→静态表）/ `web_search`（记录 `not verified online`）

接入新 Harness：复制 `_adapter-template.md` 逐节填写 → 跑一个 🟢 任务（必须零新文件）→ 跑一个 🔴 示例验证产物。详见 `references/capability-contract.md` §6。

## 硬约束

1. 先问再猜：意图不明 → 问"做不做"；scope 模糊 → 澄清门
2. 架构决策（新端口 / 新事件 / 表结构 / 聚合行为变更）写代码前经 `ask_user` 确认
3. 不跳门禁、不藏失败；open 的 blocker/major 拒绝收尾
4. 编排器绝不亲自写大型实现或测试
5. 网搜结论必须附来源与时间；AC 必须保持本地可执行

## 版本与发布约定

**批量发布制**：版本 = 发布动作（1 version = N chains）。

- **变更期**：commit + 全量门禁 → 推 main；不动版本号、不写 CHANGELOG（`latest` 滚动 Release 由 CI 自动更新）
- **发布期**：一次性 bump 版本 + CHANGELOG 汇总 + 推 `v*` tag
- **不变底线**：产物链纪律、全量门禁、open blocker/major 拒绝收尾
