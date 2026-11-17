# harness-coding

**通用 Harness 编码编排技能（v2 · 产物驱动）**

把一句话需求变成受控的变更流程。v2 的核心转变：**状态活在产物里，历史活在 git 里，证据活在门禁输出里，报告只是一个按需视图**——没有报告文件，没有私有协议状态机。

> 会话分类判定意图 → 分级通道（🟢 轻量 / 🟡 标准 / 🔴 完整 / 📋 仅结论）选定流程深度 → 前置链路（信息补给 + 澄清门）→ 角色派发（explorer / implementer / reviewer）→ 质量门禁 → 收尾回复 + 按需追溯视图。

## 核心思想

1. **产物即状态**：任务状态活在平凡 markdown 产物里（`specs/<slug>/` 下的 `spec.md` / `plan.md` / `tasks.md`；🟡 单文件 `intent.md`）——恢复 = 读文件，版本 = git，并发 = git 分支
2. **能力名即契约**：方法论主体只引用能力名（7 必需 + 5 可选，每个可选项都带降级规则）；可选能力**运行时对照对话上下文解析**（context-first），适配器映射仅为提示
3. **纪律 → 结构**：v1 用 prompt 条款求纪律（"绝不凭记忆声称通过"）；v2 用结构保证它（勾选必须附输出、open blocker/major 拒绝收尾、`artifact-check.py` 机械执法）
4. **单一事实源**：接入新 Harness 只需一份适配器文件

## 通道 × 产物矩阵（流程的唯一真相）

| 通道 | 产物 | 流程 | 收尾 |
|------|------|------|------|
| 🟢 轻量 | **零文件** | 实现 → lint/format | 内联摘要 |
| 🟡 标准 | `intent.md` | 定位 → 澄清 → 实现 → 门禁 → 评审 → 收尾重验 | 收尾回复（含合并 ask_user） |
| 🔴 完整 | `specs/<slug>/` 下的 `spec.md` / `plan.md` / `tasks.md` | 信息补给 → spec 草稿 → 澄清门 → plan → 逐任务实现+门禁 → 评审 → 收尾重验 | 收尾回复 + 按需追溯视图 |
| 📋 仅结论 | spec/plan **即交付物** | 定位 → 评审/校验 | 校验结论 |

- **前置链路**（🟡/🔴，需求模糊时）：信息补给（`find_skill` 本地技能检索 / `web_search` 外部核实）→ 澄清门（模糊点拆成**假设**/A-id 与**问题**/批量一轮反问，问题清单技法可委托 `grill-me` 条件技能——门只管筛和收，技能管怎么问得狠）→ 产物定稿
- **收尾重验**（🟡/🔴）：逐任务绿 ≠ 全仓绿；收尾前强制全量门禁重跑；合并决策（PR / 直接合并 / 继续迭代）并入收尾 ask_user
- **多轮续接**：slug 由首个需求生成；后续消息默认追加任务（🟡 = 追加意图段）；通道升级补齐产物、绝不降级；**AC 只增不改**（确需修改用 supersede 标注重指向）

## 角色与产物归宿

| 角色 | 职责 | 输出归宿 |
|------|------|---------|
| Explorer | 只读侦察（file:line） | `spec.md` Background（编排器**整体替换占位符**，不是追加） |
| Implementer | 实现 + 测试 + 门禁 | `tasks.md` 勾选 + 粘贴 `Output:` |
| Reviewer | 分级评审结论 | `## Review` 节（`R<n> [open\|level]` / `[resolved]`） |

**收尾规则：open 状态的 blocker/major 使收尾不合法**——评审拒绝机械地回到实现循环。

每个角色的 `spawn_agent` 派发以强制的 Context 步骤开头（先读产物再干活）；内联模式跳过。**上下文经由产物流动，绝不经由父会话摘要。**

## 质量门禁

```text
lint → format → type → test
```

固定顺序、命令由项目定义（适配器 §2）；证据必须粘贴，绝不凭记忆声称通过；失败先定位根因再修复。🟢 仅强制 lint + format；type/test 按需并记录原因。

- **Gate N/A 豁免协议**：不适用的门禁绝不静默跳过——在 spec/intent 的 `Gate Exemptions` 节声明 `GATE-NA(<gate>): <原因 + 范围>`，任务输出引用同一标记；`artifact-check.py` 机械校验配对（🟡/🔴 全文扫描）。全链豁免在收尾重验时同免；任务级豁免不免责
- **增量 per-task 门禁**：lint/format/type 全跑 + 受影响的测试子集；全量测试套件在收尾重验时强制
- **coverage 阈值由项目声明**（来源在适配器 §2 引用）：未声明 → 普通 pass/fail，绝不发明数字
- **重构基线**：保持行为不变的重构先在 plan 阶段建特征测试基线；一条 AC = "基线测试全部原样通过"

## 目录结构

```
harness-coding/
├── SKILL.md                        # 方法论主体（v2）
├── SDD-REFACTOR-DESIGN.md          # v2 重构设计文档（已冻结）
├── .github/
│   └── workflows/release.yml       # 双车道发布 CI（main→latest 滚动 prerelease；v*→不可变版本 Release；门禁相同）
├── references/
│   ├── capability-contract.md      # 能力契约（7 必需 + 5 可选）
│   ├── adapters/                   # 适配器层（claude-code / codex / opencode / workbuddy / _template）
│   └── templates/                  # spec / plan / tasks / intent 产物模板 + 3 份派发模板 + 收尾契约
├── scripts/
│   ├── artifact-check.py           # 产物校验器（schema / AC↔T 闭合 / 评审收尾守卫 / Gate N/A 配对）
│   ├── derive-report.py            # 按需追溯视图（merge-base 基线，stdout，永不落盘）
│   ├── find-skill.py               # 技能库探针（find_skill 降级路径：标准位置扫描 + 同名多版本漂移告警 + junction 同源去重）
│   └── build-dist.py               # 发布打包（allowlist 精简副本 + 字节级自校验 + 可复现 zip → dist/；--zip-stem 支持滚动车道按提交命名）
├── specs/                          # dogfood 产物链（dod-closure / review-hardening / dist-packaging / scan-fixes🟡）——artifact-check.py specs/ 持续校验的真实样本
└── fixtures/                       # 产物校验用例 9 个（含故意损坏的 broken / broken-intent-na / malformed-task、合法豁免的 gate-na / intent-gate-na、注释 AC 的 comment-ac；.expect 支持逐错误类断言）+ 探针自检用例 4 个（short-query 回归 2 字符词过滤修复）
```

## 安装

从本仓库构建精简安装包（推荐）：

```bash
python scripts/build-dist.py     # → dist/harness-coding/ + dist/harness-coding-v<version>.zip
```

不想本地构建也可以直接从 GitHub Releases 下载 zip，两条车道门禁完全相同（`.github/workflows/release.yml`）：**正式版**——推送 `v*` tag，CI 构建不可变的版本 Release（对应 CHANGELOG）；**滚动版**——每次 main push 自动更新 `latest` prerelease，zip 按提交命名（`harness-coding-main-<sha>.zip`），无需版本号，随时可取最新构建。滚动构建仅用于安装，不是版本，不计入 CHANGELOG。

把 `dist/harness-coding/` 整体复制（或软链）到下表任一技能目录即可。打包为 **allowlist 白名单制**：只含运行面（SKILL.md / references/ / 三个运行脚本 / LICENSE），dev 文件（README / CHANGELOG / fixtures / specs / 设计文档）不会混入；构建自带自校验（含零 CRLF 断言），zip 条目元数据平台无关（`create_system` 固定）——同内容的跨机器构建可复现（首次跨机器实证：对比下一次 tag-push 的 CI 产物与本地构建的 sha256）。

| Harness | 路径 |
|---------|------|
| Claude Code | `<project>/.claude/skills/harness-coding/`（或 `~/.claude/skills/`） |
| opencode | `<project>/.opencode/skills/harness-coding/`（或 `~/.config/opencode/skills/`） |
| Codex | `<project>/.codex/skills/harness-coding/`（或 `~/.codex/skills/`） |

> 权限：宿主项目需放行 `python scripts/artifact-check.py*`、`python scripts/derive-report.py*` 与 `python scripts/find-skill.py*`（参见本仓库的 `.claude/settings.json` / `opencode.json`——三者的放行清单一致）。

## 验证

```bash
python scripts/artifact-check.py --fixtures fixtures/   # 9 个产物用例全部符合预期（broken / broken-intent-na / malformed-task 预期报错；另有 1 个非产物探针目录跳过）
python scripts/find-skill.py --fixtures fixtures/skills # 探针自测（drift / no-drift / empty / short-query；.expect 支持 query= 覆盖）
python scripts/artifact-check.py specs/                 # 校验宿主项目的任务产物
python scripts/derive-report.py specs/<slug>            # 生成追溯视图（stdout）
```

## 能力契约与适配器

必需（7）：`read` / `write` / `edit` / `glob` / `grep` / `run_command` / `ask_user`（批量签名；仅支持单问的原语在同一轮内降级为连续逐问）。
可选（5，均带降级）：`spawn_agent`（内联执行）/ `create_branch`（主工作区 + 标注 not isolated）/ `check_command`（先跑一次再决定）/ `find_skill`（**context-first**：宿主原生技能机制优先 → `scripts/find-skill.py` 探针 → SKILL.md §7 静态表；库不存在显式记录 `skill library unavailable`）/ `web_search`（在 spec Assumptions 记录 `not verified online`）。适配器不含任何技能加载逻辑——机械层归属宿主，harness-coding 只承载纪律。

接入新 Harness：复制 `_adapter-template.md` 逐节填写 → 跑一个 🟢 任务（必须零新文件）→ 跑一个 🔴 示例验证产物 + 校验器。见 `references/capability-contract.md` §6。

## 硬约束

1. 先问再猜：意图不明 → 问"做不做"；scope 模糊 → 澄清门
2. 架构决策（新端口 / 新事件 / 表结构 / 聚合行为变更）写代码前经 `ask_user` 确认
3. 不跳门禁、不藏失败；open 的 blocker/major 拒绝收尾
4. 编排器绝不亲自写大型实现或测试（implementer 职责）
5. 网搜结论必须附来源与时间；AC 必须保持本地可执行
