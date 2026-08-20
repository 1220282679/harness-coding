# harness-coding

**通用 Harness 编码编排技能（Universal Harness Coding Orchestrator）**

一个与执行环境（Harness）解耦的通用编码编排技能。它将一行需求转化为一次受控的代码变更流程：通过**会话分类**判定意图，经由**分级通道**（🟢 轻量 / 🟡 标准 / 🔴 完整 / 📋 仅结论）选择流程深度，通过**角色派发**（探索 / 实现 / 评审）分工执行，经过**质量门禁**把关，最终交付一份**五段式可追溯报告**。

> **核心思想**：方法论与执行环境彻底解耦。技能主体只使用"能力"表述（读取文件 / 运行命令 / 派发 / 提问 / 写报告），具体的工具由**适配器层**决定。它只依赖一份能力契约，并通过任意执行 Harness 的适配器层运行。

---

## 目录

- [项目简介](#项目简介)
- [核心思想](#核心思想)
- [目录结构](#目录结构)
- [工作原理](#工作原理)
- [会话分类](#会话分类)
- [分级通道](#分级通道)
- [主流程（🔴 完整通道）](#主流程完整通道)
- [角色](#角色)
- [质量门禁](#质量门禁)
- [报告协议](#报告协议)
- [能力契约](#能力契约)
- [适配器层](#适配器层)
- [条件触发技能](#条件触发技能)
- [输出契约](#输出契约)
- [运行时配置](#运行时配置)
- [验证脚本](#验证脚本)
- [使用前置条件](#使用前置条件)
- [约束](#约束)

## 项目简介

`harness-coding` 是一个 **SKILL.md 技能包**（带 frontmatter 的标准技能格式），能够运行在任意实现了能力契约的执行 Harness 上。它自身并不直接编写大型实现，而是按阶段派发给对应角色，并强制执行架构决策确认点与质量门禁。

当前已内置以下执行环境的适配器层：

| 适配器 | 对应文件 | 说明 |
|--------|----------|------|
| Claude Code | [references/adapters/claude-code.md](references/adapters/claude-code.md) | Read / Write / Edit / Glob / Grep / Bash / AskUserQuestion / Agent / EnterWorktree |
| OpenAI Codex CLI | [references/adapters/codex.md](references/adapters/codex.md) | read_file / apply_patch / shell / rg / glob_file_search / list_dir / spawn_agent |
| opencode | [references/adapters/opencode.md](references/adapters/opencode.md) | tool.read / tool.write / tool.edit / tool.apply_patch / tool.bash / tool.grep / tool.glob / tool.question / tool.task |
| 新 Harness | [_adapter-template.md](references/adapters/_adapter-template.md) | 按模板逐节填写即可接入 |

## 核心思想

1. **能力名称即契约**：技能主体只使用能力名称（`read` / `run_command` 等），从不引用具体工具名词（如 Read 工具、Bash、Agent）。
2. **必需 vs 可选**：必需能力缺失则技能无法工作；可选能力缺失则按降级规则退化为串行/手动执行。
3. **单一事实来源**：接入新 Harness 只需新增一个适配器文件，方法论保持不变。

## 目录结构

```
harness-coding/
├── SKILL.md                           # 技能主体（方法论与主控制流）
├── README.md                          # 本文档（中文）
├── opencode.json                      # opencode 权限配置（放行验证脚本）
├── .gitignore                         # 忽略运行时报告、字节码缓存等
├── .claude/settings.json              # Claude Code 本地权限配置
├── references/
│   ├── capability-contract.md         # 能力契约（8 必需 + 4 可选能力）
│   ├── adapters/                      # 适配器层（每个 Harness 一份）
│   │   ├── _adapter-template.md       # 接入新 Harness 的填写模板
│   │   ├── claude-code.md             # Claude Code 适配器
│   │   ├── codex.md                   # OpenAI Codex CLI 适配器
│   │   └── opencode.md                # opencode 适配器
│   └── templates/                     # 模板
│       ├── dispatch-explorer.md       # 探索角色派发提示模板
│       ├── dispatch-implementer.md    # 实现角色派发提示模板
│       ├── dispatch-reviewer.md       # 评审角色派发提示模板
│       ├── output-contract.md         # 最终报告输出契约
│       ├── report-template.md         # 阶段报告骨架模板
│       └── write-report.md            # write_report 能力的自包含实现
└── scripts/                           # 验证脚本（纯标准库，零第三方依赖）
    ├── report_lib.py                  # 报告协议的单一实现源
    ├── smoke-report.py                # 报告协议冒烟验证（单元断言）
    ├── workflow-check.py              # 分级通道端到端生命周期验证
    └── consistency-check.py           # 技能文档跨文档一致性验证
```

## 工作原理

一次会话从需求到交付的完整路径：

```
一行需求
   │  ① 会话分类（必须最先执行）
   ▼
工作任务/非工作任务/意图不明（→ 先问，绝不猜测）
   │  ② 选择分级通道（🟢 / 🟡 / 🔴 / 📋）
   ▼
按通道执行阶段流程
   │  ③ 派发角色（探索 / 实现 / 评审）
   │  ④ 质量门禁（lint → format → type → test）
   │  ⑤ 逐步追加可追溯报告
   ▼
按输出契约交付五段式最终报告
```

## 会话分类

> 必须在任何会话首次响应之前执行，不可跳过。

| 条件 | 判定 | 后续 |
|------|------|------|
| 改代码 / 修 bug / 加功能 / 重构 / 写测试 / 改表结构 / 代码评审（产出 Findings）/ 产生正式 Findings 交付物的只读评估（即使不改文件）/ 任何磁盘写入动作 | **工作任务** | 初始化报告，走分级通道 |
| 问答 / 解释 / 咨询 / 闲聊 / 非正式只读查看（无正式评审交付物，无文件改动） | **非工作任务** | 正常交互，跳过技能 |
| 无法判断是否会改代码 | **意图不明** | **先问，绝不猜测** |

**快速启发式**：先看动词，再看名词。"新增/重构/修复/更改/替换/实现" → 工作任务；"设计/规划/评估"后接仓库特性/模块 → 当结果是正式交付物（计划 / Findings / 实现）时算工作任务；只有纯粹咨询式的只读查看且无正式交付物才算非工作任务。拿不准 → 问。

**分类记录（可审计）**：每次分类产出一行记录 `<判定> — verb: <动词>; noun: <名词>; deliverable: <yes/no>`。工作判定必须在定位阶段被记录在报告中，否则视为协议违规。

**`ask_user` 降级**：当当前 Harness/上下文无法交互式提问时，自行选择最保守的选项并在报告中记录"⚠️ 无法询问用户；已按保守选项决定"，绝不假装用户已确认。

## 分级通道

> **先分类，再派发**——按变更规模选择通道，避免小改动走重型流程。

| 级别 | 适用场景 |
|------|----------|
| 🟢 **轻量** | 拼写错误 / import 修复 / 单行配置 / 格式化 / docstring 微调 |
| 🟡 **标准** | 实质性单文件 / 单函数变更，或小型双文件变更；不涉及新端口 / 事件 / 表结构 |
| 🔴 **完整** | 跨文件重构 / 新功能 / 架构变更 / 涉及端口、事件或表结构 |
| 📋 **仅结论** | 代码评审 / 只读评估，交付物是分级的 Findings 文档，或计划/设计交付物（不改代码） |

**判定规则**：符合 🟢 类别列表（≤1 文件、无架构影响）→ 🟢；其他单文件或小型双文件变更 → 🟡；3 个及以上文件或涉及架构决策 → 🔴（例外：符合 🟢 类别且无架构影响的微改，无论文件数只升级到 🟡——跨多文件的 typo/import 修复不属于完整流程级变更）；交付物为 Findings 文档的评审/评估任务 → 📋，无代码变更的计划/设计交付物也归 📋（计划即为交付物，在探索阶段产出、评审阶段校验，评审角色保持"只报告、不修改"纪律）。

**升级条款**：单文件变更超过 50 行业务逻辑 → 自动升级为 🟡（即使形似 🟢 类别）；若同时涉及架构决策 → 升级为 🔴。

| 通道 | 步骤数 | 执行步骤 | 跳过步骤 |
|------|--------|----------|----------|
| 🟢 轻量 | 3 步 | 实现 → 质量门禁 → 报告 | 探索、计划、隔离、评审、验证、合并 |
| 🟡 标准 | 6 步 | 定位+探索 → 实现 → 质量门禁 → 评审 → 报告 → 合并 | 计划、隔离、验证 |
| 🔴 完整 | 10 步 | 见[主流程](#主流程完整通道) | 无 |
| 📋 仅结论 | 3 步 | 定位 → 评审 → 总结 | 计划、隔离、实现、质量门禁、验证、合并（探索可选） |

> **跳过阶段留痕**：被 🟢/🟡/📋 通道跳过的阶段，在报告中写作"(🟢/🟡/📋 skipped)"并标记 `DONE`，不展开内容。唯一例外是 🟢 下的**定位**：级别判定内联记录在定位阶段标记中，这是每个通道都会记录的一个阶段。
>
> **成本提示**：派发子代理 + 四道质量门禁有 token 与延迟成本。🟢/🟡 通道避免重复全量运行与重复派发；同轮可复用的质量门禁输出要复用；无理由不升级通道。

## 主流程（🔴 完整通道）

| 步骤 | 动作 | 派发 / 条件 |
|------|------|-------------|
| 1 定位 | 解析需求、判定级别、确认归属与架构决策 | — |
| 2 探索 | 派发探索角色定位变更点 + 可复用模式 | 探索角色 |
| 3 计划 | 涉及架构决策时，将计划写入报告并用 `ask_user` 确认 | — |
| 4 隔离 | 涉及代码变更 → 分支 / worktree / 目录快照 | 隔离能力 |
| 5 实现 | 派发实现角色；核心逻辑缺测试则补齐 | 实现角色 |
| 6 质量门禁 | lint + format + type + test。失败 → 定位根因 → 回到步骤 5 | 质量门禁 |
| 7 评审 | 派发评审角色；blocker/major 被拒 → 循环 5→6→7；涉及安全则做安全评审 | 评审角色 |
| 8 验证 | 重跑质量门禁获得新鲜证据；绝不凭记忆声称"通过" | 验证 |
| 9 总结 | 按输出契约交付最终报告，关闭报告 | — |
| 10 合并 | 询问用户：PR / 直接合并 / 继续迭代 | — |

> 质量门禁失败循环：先定位根因再修复（禁止盲目尝试）→ 回到实现 → 重跑。不跳过任何步骤，不隐藏任何失败。
>
> **隔离降级**：worktree/分支创建失败（如 Windows+uv 下的 venv 损坏、无 git 权限）→ 降级为主仓库的功能分支，或直接在主线工作区修改；报告标注 `not isolated (<原因>)`（如 `not isolated (venv corruption)`），与契约的 `not isolated (no branch capability)` 形式一致；环境障碍不阻断流程。

## 角色

| 角色 | 职责 | 派发时机 |
|------|------|----------|
| **Explorer（探索）** | 只读侦察：定位实现 / 调用链 / 可复用模式，输出带 file:line | 定位不明 / 跨文件变更前 |
| **Implementer（实现）** | 落地实现 + 补测试 + 通过质量门禁，输出四段式报告 | 定位清晰之后 |
| **Reviewer（评审）** | 合规性 / 正确性 / 质量门禁复查，输出分级 Findings | 实现之后（有代码变更时）；📋 仅结论任务中直接作用于评审对象 |

派发提示模板见 [references/templates/](references/templates/)。不具备 `spawn_agent` 能力的 Harness 由编排器内联执行；角色职责与输出契约不变。

## 质量门禁

全部四项通过才算完成，顺序固定：

```text
lint   → format   → type check   → test
```

- 具体命令由项目定义（如 ruff / ruff format --check / mypy --strict / pytest），本技能不绑定任何具体工具
- **必须实际执行并将输出粘贴为证据**，绝不凭记忆声称"通过"
- 覆盖率阈值（如有）归属测试门禁（如 ≥70%）
- 失败 → 先定位根因再修复；绝不删除断言 / 放宽既有断言来换取绿灯
- **🟢 例外**：轻量通道只强制 lint + format（见分级通道）；type + test 在变更触及类型相关或逻辑/测试相关代码时按需运行，并记录原因

## 报告协议

> 一份逐阶段、完全可追溯的报告。与 `harness-reporting` 类似，但绑定的是能力契约而非具体工具。

1. **命名**：`<report.prefix>-<slug>-v<N>.md`，默认 `harness-task-<slug>-v<N>.md`（无 slug 时 `harness-task-v<N>.md`）。`v<N>` 中的 `N` 必须是纯整数且**按任务解析**——glob 该任务自己的报告取最大值 +1（新任务为 0）
2. **初始化**：glob 该任务历史报告 → 取最大版本 N；若该任务最高版本报告（v<N> 那份）仍是"🔄 in progress"，**先询问用户继续还是放弃**，绝不静默覆盖；放弃 → 将 in-progress 报告标记为 `❌ abandoned`（仅改头部状态行，阶段内容原样保留，不再重复触发询问）后新建 `v<N+1>`；新建文件**排他创建**，遇并发冲突重 glob 后以**下一个版本号**重试，绝不覆盖并发报告
3. **增量追加**：每阶段完成后，用阶段内容 + 尾部 `DONE` 标记替换对应阶段标记
4. **故障优先**：静默写失败不阻断主流程，但必须显式打印"⚠️ report not persisted — write anomaly"警告
5. **恢复**：会话中断后从第一个非 `DONE` 标记（最早未完成阶段）继续；乱序缺口记录为恢复异常，绝不静默跳过
6. **关闭**：总结阶段将"🔄 in progress"改为"✅ passed / ❌ rejected"（init 阶段放弃的 in-progress 报告改为标记 `❌ abandoned`，见第 2 步）；合并阶段记录合并方式
7. **模板**：[references/templates/report-template.md](references/templates/report-template.md)

> 报告仅供追溯，不影响任务执行。归档：报告超过 20 份时提醒移入 `<report.dir>archive/`（默认 `harness-reports/archive/`，保留最近修改的 2 份）。
>
> **磁盘开关**：能力契约配置 `report.on_disk=false` 时，报告仅内联输出、不写盘（适用于 🟢 轻量通道或临时会话）；内联输出必须携带显式"⚠️ report not persisted (inline-only)"标记。

`write_report` 的自包含最小实现（read/write/edit 组合）见 [references/templates/write-report.md](references/templates/write-report.md)。

## 能力契约

**技能与任意执行 Harness 之间的唯一接口。** 方法论主体只引用契约中的能力名称，从不引用具体工具、CLI 或框架。每个 Harness 通过一份适配器文件（`adapters/<harness>.md`）将能力名称映射到自己的实现。

详细定义见 [references/capability-contract.md](references/capability-contract.md)。

### 必需能力（缺失 → 技能不可用）

| # | 能力 | 签名 | 语义 |
|---|------|------|------|
| 1 | `read` | `read(path) -> str` | 读取文件 / 目录内容 |
| 2 | `write` | `write(path, content) -> void` | 写入 / 覆盖文件 |
| 3 | `edit` | `edit(path, old, new) -> void` | 文件片段的精确替换（old 必须唯一匹配） |
| 4 | `glob` | `glob(pattern) -> list[str]` | 按模式列出文件路径 |
| 5 | `grep` | `grep(pattern, path?) -> list[Match]` | 内容搜索，返回带 file:line 的匹配 |
| 6 | `run_command` | `run_command(cmd) -> Output` | 运行 shell 命令，返回 stdout/stderr/exit_code |
| 7 | `ask_user` | `ask_user(question, options) -> Answer` | 向用户提问并附选项确认 |
| 8 | `write_report` | `write_report(report_path, phase, ...) -> void` | 向报告文件追加阶段内容 |

### 可选能力（缺失 → 按降级规则处理）

| # | 能力 | 签名 | 语义 | 降级规则 |
|---|------|------|------|----------|
| 9 | `spawn_agent` | `spawn_agent(role, prompt) -> AgentReport` | 派发子代理并收集结构化报告 | 编排器内联执行该角色（串行），职责不变 |
| 10 | `create_branch` | `create_branch(name) -> void` | 创建隔离分支/worktree | 直接在主工作区修改，报告标注"not isolated" |
| 11 | `check_command` | `check_command(cmd) -> bool` | 仅验证命令可用 | 运行一次决定 |
| 12 | `run_quality_gate` | `run_quality_gate(commands) -> GateResult` | 一次跑完四道质量门禁 | 逐一通过 run_command 运行 |

> **降级规则汇总**：`spawn_agent` 缺失 → 内联执行（标注 `no sub-agent, inline execution`）；`create_branch` 缺失 → 主线修改（标注 `not isolated (no branch capability)`）；`check_command` / `run_quality_gate` 缺失 → 无标注。

## 适配器层

每个适配器文件回答一个问题：**当前 Harness 用何种具体机制实现契约中的每一项能力**。接入新 Harness 的步骤（见能力契约 §7）：

1. 逐项检查 8 个必需能力，映射到该 Harness 的工具/原语
2. 按 [_adapter-template.md](references/adapters/_adapter-template.md) 复制生成 `adapters/<harness>.md`：能力映射表 + 质量门禁命令 + 角色映射 + 条件技能映射 + 降级规则声明
3. 若必需能力无法满足 → 在适配器顶部标注"unsupported capabilities"，技能加载时按降级规则继续
4. 跑一个轻量需求端到端（如修一个拼写错误）验证最低通道可用

## 条件触发技能

| 条件技能 | 触发阶段 | 条件 |
|----------|----------|------|
| 隔离技能 | 计划确认后 → 实现前 | 涉及代码变更 |
| 决策记录技能 | 计划确认后 | 确认了架构决策 |
| 调试技能 | 质量门禁失败后 | 标准/完整通道 |
| 简化技能 | 质量门禁通过后 → 评审前 | 标准/完整通道 |
| 安全评审 | 评审通过后 → 验证前（完整）/ 报告前（标准） | 涉及令牌 / 认证 / 权限 / 加密 / 外部集成 |
| 验证技能 | 评审通过后 → 总结前 | 完整通道 |
| 分支收尾技能 | 总结通过后 | 标准/完整通道 |

抽象条件技能到具体可加载技能的映射，定义在对应适配器的"条件技能映射"表中（详见 [_adapter-template.md](references/adapters/_adapter-template.md) §4）。

## 输出契约

```markdown
## 需求定位
- 分类: <工作任务 / 非工作任务 — verb: <…>; noun: <…>; deliverable: <yes/no>>
- 归属: <…>; 架构决策: <无 / 有 — 计划要点与确认结果>

## 变更清单
- <新增 / 修改文件列表，每项带 file:line 与一句话说明>

## 验证结果
- 质量门禁: <lint / format / type / test 汇总>; 评审: <结论，拒绝数>

## 剩余风险
- <未覆盖边界、待办、需人工验证项; 无则写 "无">

## 技能使用日志
- <本技能加载的条件技能及其触发阶段>
```

> 模板见 [references/templates/output-contract.md](references/templates/output-contract.md)。核心原则：**先有证据，再有断言**。每项"通过/失败"都必须有实际命令输出背书，绝不凭记忆声称。

### 各通道报告深度

| 通道 | 报告深度 |
|------|----------|
| 🟢 轻量 | 简化版：变更清单 + 验证结果（lint + format 实际执行并粘贴输出；type/test 按需） |
| 🟡 标准 | 完整五段：定位 / 变更 / 验证 / 剩余 / 技能日志 |
| 🔴 完整 | 完整五段 + 评审结论 + 安全评审（如有） |
| 📋 仅结论 | 完整五段：变更清单写"无 — 仅结论"；验证段承载评审结论 + 分级 Findings |

## 运行时配置

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `report.dir` | `harness-reports/` | 报告目录——**相对项目根路径**（解析到 Harness 工作目录，绝不指向技能自身目录） |
| `report.prefix` | `harness-task` | 报告文件名基；版本后缀 `-v<N>` 始终追加在末尾 |
| `report.on_disk` | `true` | 是否写盘；`false` → 仅内联输出（适合 🟢 轻量通道或临时会话） |

> **路径约束**：`report.dir` 必须以 `/` 结尾（默认即如此）；归档路径以 `<report.dir>archive/` 拼接，不带尾部斜杠的覆盖项会被静默拼成 `reportsarchive/`。
>
> **版本解析（按任务）**：`v<N>` 指"该任务的第 N 份报告"，不同任务使用相互独立的计数器。文件名混合后缀（如 `v-test1`）与前置零版本（如 `v010`）不参与最大值解析。

## 验证脚本

全部为纯 Python 标准库实现，零第三方依赖：

| 脚本 | 作用 | 运行方式 |
|------|------|----------|
| [scripts/smoke-report.py](scripts/smoke-report.py) | 报告协议冒烟验证：版本解析 / 标记追加与 DONE 替换 / 相邻标记不复制 / 截断 / 恢复 / 关闭 / 写保护 / 目录创建 / 内联模式 / 归档 / 并发冲突防护 | `python scripts/smoke-report.py` |
| [scripts/workflow-check.py](scripts/workflow-check.py) | 分级通道端到端生命周期验证：🟢/🟡/🔴/📋 各通道报告形态 + 与 SKILL.md "Skips:" 声明的交叉校验 | `python scripts/workflow-check.py` |
| [scripts/consistency-check.py](scripts/consistency-check.py) | 跨文档一致性验证：frontmatter / 内部引用 / 能力用法 / 角色模板 / 阶段集 / 适配器映射 / 报告协议不变量 | `python scripts/consistency-check.py` |
| [scripts/report_lib.py](scripts/report_lib.py) | 报告协议机械规则的**单一实现源**，被 smoke 与 workflow 两个脚本共同引用，防止文档与验证器漂移 | 库模块，被 smoke-report 与 workflow-check 导入 |

> 任何 PASS 打印后退出码为 0；任何 FAIL 退出码为 1。Windows 控制台在 GBK 下会乱码，可先设置 `PYTHONIOENCODING=utf-8`（脚本自身已尝试强制 UTF-8）。
>
> **配置边界**：验证器针对**默认运行时配置**（`report.prefix=harness-task` / `report.dir=harness-reports/`）校验报告协议；若某项目在适配器层覆盖了这两项，验证器不再覆盖新的命名约定（属预期——覆盖配置由该适配器自行验证，见[能力契约](references/capability-contract.md)运行时配置一节）。
>
> **权限配置**：仓库自带的 `opencode.json` 与 `.claude/settings.json` 放行验证脚本（`python scripts/smoke-report.py` / `workflow-check.py` / `consistency-check.py`）及退出码回读（`echo exit=$?`），可在对应 Harness 中非交互运行验证器。

## 使用前置条件

1. 当前 Harness 满足能力契约的**必需能力**（见 [references/capability-contract.md](references/capability-contract.md)）
2. 从 [references/adapters/](references/adapters/) 加载当前 Harness 的适配器层（缺失时按 [_adapter-template.md](references/adapters/_adapter-template.md) 生成），并确认每项能力对应的具体工具
3. 确认项目的质量门禁命令（lint / format / type / test，通过 `run_command` 能力执行）
4. 确认角色代理类型（explorer / implementer / reviewer）已在 Harness 注册；未注册则降级为通用子代理或由编排器内联执行（职责与输出契约不变）

## 约束

1. 收到需求先判定级别与归属；信息不足先问，绝不猜测
2. 架构决策必须在动代码前用 `ask_user` 确认
3. 评审前全部质量门禁必须绿灯；被拒评审走完整循环，不跳过步骤
4. 编排器自身不得编写大型实现与测试（实现与测试归实现角色）
5. 绝不隐藏质量门禁 / 测试失败；输出契约按通道的报告深度交付（🟢 简化 / 🟡 完整五段 / 🔴 完整五段 + 评审结论 + 安全评审 / 📋 完整五段且变更清单写"无 — 仅结论"）
