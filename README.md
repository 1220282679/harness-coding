# harness-coding

**通用 Harness 编码编排技能（v2 · 产物驱动）**

把一行需求变成一次受控的代码变更流程。v2 的核心转变：**状态在产物里，历史在 git 里，证据在门禁输出里，报告只是按需视图**——没有报告文件，没有私有协议状态机。

> 会话分类判定意图 → 分级通道（🟢 轻量 / 🟡 标准 / 🔴 完整 / 📋 仅结论）选择流程深度 → 前置链路（信息补给 + 澄清门）→ 角色派发（探索 / 实现 / 评审）→ 质量门禁 → 收尾回复 + 按需追溯视图。

## 核心思想

1. **产物即状态**：任务状态存在于平凡 markdown 产物（`specs/<slug>/` 的 `spec.md` / `plan.md` / `tasks.md`；🟡 单文件 `intent.md`）——恢复 = 读文件，版本 = git，并发 = git 分支
2. **能力名称即契约**：方法论主体只引用能力名（7 必需 + 5 可选，每项可选能力带降级规则），具体工具由适配器层决定
3. **纪律 → 结构**：v1 靠 prompt 条款求纪律（"绝不凭记忆声称通过"），v2 靠结构保证（勾选必须附输出、open blocker/major 不得收尾、`artifact-check.py` 机械校验）
4. **单一事实来源**：接入新 Harness 只需一份适配器文件

## 通道 × 产物矩阵（主控流唯一真相）

| 通道 | 产物文件 | 流程 | 收尾交付 |
|------|----------|------|----------|
| 🟢 轻量 | **零文件** | 实现 → lint/format | 内联摘要 |
| 🟡 标准 | `intent.md` | 定位 → 澄清 → 实现 → 门禁 → 评审 → 收尾重验 | 收尾回复（合并 ask_user） |
| 🔴 完整 | `specs/<slug>/{spec,plan,tasks}.md` | 信息补给 → spec 起草 → 澄清门 → plan → 逐任务实现+门禁 → 评审 → 收尾重验 | 收尾回复 + 按需追溯视图 |
| 📋 仅结论 | spec/plan **即交付物** | 定位 → 评审校验规格 | 校验结论 |

- **前置链路**（🟡/🔴，需求模糊时）：信息补给（`find_skill` 本地技能检索 / `web_search` 外部核实）→ 澄清门（模糊点拆**假设**/A-ID 与**问题**/批量一次反问）→ 产物定稿
- **收尾重验**（🟡/🔴）：逐任务门禁绿 ≠ 全仓绿，收尾前强制全量重跑；合并决策（PR / 直接合并 / 迭代）并入收尾 ask_user
- **续接协议**：slug 由首个需求生成；后续消息默认追加任务（🟡 = intent.md 加意图段）；通道升级补齐产物、不降级；**AC 只增不改**（修改用 supersede 标注）

## 角色与产物归宿

| 角色 | 职责 | 产出归宿 |
|------|------|----------|
| Explorer | 只读侦察（file:line） | `spec.md` 背景节（编排器**替换占位符**，非追加） |
| Implementer | 实现 + 测试 + 门禁 | `tasks.md` 勾选 + 粘贴 `输出:` |
| Reviewer | 分级 Findings | `## Review` 节（`R<n> [open\|级别]` / `[resolved]`） |

**收尾规则：open 状态的 blocker/major 使收尾不合法**——评审拒绝机械地回到实现循环。

## 质量门禁

```text
lint → format → type → test
```

固定顺序、项目自定义命令（适配器 §2）；证据必须粘贴，绝不凭记忆声称通过；失败先定位根因再修复。🟢 仅强制 lint + format，type/test 按需并记录原因。

- **Gate N/A 豁免协议**：不适用的门禁禁止静默跳过——在 spec/intent `门禁豁免` 节声明 `GATE-NA(<gate>): <原因+范围>`，任务输出以同名标记引用，`artifact-check.py` 校验配对（🟡/🔴 全文扫描）；全链豁免收尾同免，任务级豁免收尾全量照常跑
- **增量 per-task 门禁**：lint/format/type 全跑 + test 受影响子集；全量 test 在收尾重验强制
- **coverage 阈值项目级声明**（适配器 §2 引用来源）：无声明不强制，绝不发明数字
- **重构基线**：行为保持型重构先在 plan 建特征测试基线，AC 必含"基线测试全部通过"

## 目录结构

```
harness-coding/
├── SKILL.md                        # 方法论主体（v2：68 行）
├── SDD-REFACTOR-DESIGN.md          # v2 重构设计文档（冻结）
├── references/
│   ├── capability-contract.md      # 能力契约（7 必需 + 5 可选）
│   ├── adapters/                   # 适配器层（claude-code / codex / opencode / _template）
│   └── templates/                  # spec / plan / tasks / intent 产物模板 + 三个角色派发模板 + 收尾契约
├── scripts/
│   ├── artifact-check.py           # 产物校验器（schema / AC↔T 闭合 / 评审收尾守卫）
│   └── derive-report.py            # 按需追溯视图（merge-base 基线，stdout，不落盘）
└── fixtures/                       # 5 个校验用例（含故意损坏的 broken、合法豁免的 gate-na）
```

## 安装

| Harness | 安装路径 |
|---------|----------|
| Claude Code | `<project>/.claude/skills/harness-coding/`（或 `~/.claude/skills/`） |
| opencode | `<project>/.opencode/skills/harness-coding/`（或 `~/.config/opencode/skills/`） |
| Codex | `<project>/.codex/skills/harness-coding/`（或 `~/.codex/skills/`） |

> 权限放行：宿主项目需在自己的配置中放行 `python scripts/artifact-check.py*` 与 `python scripts/derive-report.py*`（参考本仓库 `.claude/settings.json` / `opencode.json`）。

## 验证

```bash
python scripts/artifact-check.py --fixtures fixtures/   # 5 用例应全过（broken 预期报错）
python scripts/artifact-check.py specs/                 # 校验宿主项目的任务产物
python scripts/derive-report.py specs/<slug>            # 生成追溯视图（stdout）
```

## 能力契约与适配器

必需（7）：`read` / `write` / `edit` / `glob` / `grep` / `run_command` / `ask_user`（批量签名，单问原语降级为同轮连续单问）。
可选（5，均带降级）：`spawn_agent`（内联执行）/ `create_branch`（主线修改 + not isolated）/ `check_command`（跑一次决定）/ `find_skill`（回落适配器 §4 静态条件技能表）/ `web_search`（spec 假设区记 `not verified online`）。

接入新 Harness：复制 `_adapter-template.md` 逐节填写 → 跑一个 🟢 任务（必须零新文件）→ 跑一个 🔴 样例验证产物与校验器。详见 `references/capability-contract.md` §6。

## 约束

1. 先问后猜：意图不明问"做不做"，需求模糊走澄清门
2. 架构决策（新端口 / 新事件 / 表结构 / 聚合行为变更）动代码前必须 `ask_user` 确认
3. 不跳门禁、不藏失败；open blocker/major 不得收尾
4. 编排器不亲自写大型实现与测试（归实现角色）
5. 网搜结论须附来源与时间；AC 必须本地可执行
