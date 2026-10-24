---
name: harness-coding-sdd-refactor-design
status: frozen (design complete, ready for implementation per §8)
date: 2026-10-23
scope: v2.0.0 重构提案 — 协议驱动 → 产物驱动（SDD）
---

# SDD 重构设计（v2 提案）

> 一句话：把 v1.0 自己发明并自我维护的报告协议状态机，替换为「平凡 markdown 产物 + git」。流程状态不再存在于协议里，而是存在于产物里。分级通道、能力契约、适配器分层三项核心资产原样保留。

## 1. 动机（量化病灶）

| 症状 | 量化 |
|------|------|
| 技能主体过重 | SKILL.md 23KB ≈ 每次触发注入 8–10K token，干活预算先被吃掉一截 |
| 协议自维护成本 | report_lib.py 297 行 + smoke-report.py 587 行，守护的是自己发明的协议；CHANGELOG 六轮加固修的全是自身协议 bug（标记引用误判、尾随空格、路径遍历） |
| 病灶本质 | 流程状态（PHASE 标记 / 按任务版本计数 / 排他创建 / 并发防护）被实现为一套私有状态机，而这些能力 git 原生就有 |
| 移植成本 | `write_report` 是 12 项能力中最难移植的一项（Claude Code 适配器需 Read+Edit 模拟标记替换） |

## 2. 目标 / 非目标

**目标**
- G1 SKILL.md 174 行 → ≤80 行（含 §12 续接协议；完整性优先于行数数字），token 注入减半以上
- G2 报告协议状态机整体删除；可追溯性由产物 + git 承载
- G3 契约删除最重的 `write_report` 与无独立价值的 `run_quality_gate`，新增薄语义可选能力 `find_skill` / `web_search`；净 7 必需 + 5 可选（重点不是数量，而是每项语义平凡、可选必有降级路径）
- G4 验证脚本 1221 行 → 约 150 行（单件产物校验器）
- G5 分级通道 / 能力契约 / 适配器分层原样保留

**非目标**
- 不引入 Spec Kit 式 constitution / 多文件全家桶（🟡 单文件封顶，🔴 三文件封顶）
- 不做 v1 报告文件的向后兼容迁移（旧 `harness-reports/` 归档不迁移）
- 不改动三份适配器中方法论相关内容（只删 `write_report` 映射行）

## 3. 核心决策：协议驱动 → 产物驱动

| 原协议机制 | SDD 化后承载者 |
|------------|----------------|
| 中断恢复（非 DONE 标记续跑） | 读产物文件：tasks.md 复选框即进度 |
| 按任务版本计数 v\<N\> | git 历史 / 分支 |
| 并发冲突防护（排他创建） | git 分支模型 |
| 五段式增量报告 | 按需视图 `derive-report.py` + 收尾对话回复（报告从存储产物降级为派生视图，见 §5.1） |
| in-progress / abandoned 状态机 | git 工作区状态 |
| 同任务链多轮复用报告 | §12 续接协议：同 slug 任务链，后续变更追加任务 |

## 4. 通道 × 产物矩阵（新主控流的唯一真相）

| 通道 | 产物文件 | 流程 | 收尾交付 |
|------|----------|------|----------|
| 🟢 轻量 | **零文件** | 直接实现 → lint/format | 内联摘要（不变） |
| 🟡 标准 | `intent.md`（一段话） | 定位 → 实现 → 门禁 → 评审 → 收尾重验 | 收尾回复（含合并 ask_user）+ intent 引用 |
| 🔴 完整 | `spec.md` + `plan.md` + `tasks.md` | 信息补给(可选) → spec 起草 → 澄清门(ask_user) → plan → 逐任务实现+门禁 → 评审 → 收尾重验 | 收尾回复（含合并 ask_user）；按需 `derive-report.py` 生成视图 |
| 📋 仅结论 | spec / plan **即交付物** | 定位 → 评审校验规格 | 校验结论 |

硬约束：🟢 通道不产生任何新文件——为 typo 写 spec 是荒谬的。SDD 只重组重通道的组织方式，不是全局流程。

> **收尾重验**（🟡/🔴 必经，继承 v1 主流程第 8 步）：逐任务门禁绿 ≠ 全仓绿——后面任务的实现可能破坏前面任务已验证的行为。收尾前强制跑一次**全量门禁**，输出作为收尾回复的证据；全量门禁失败 → 回到逐任务循环定位根因。**合并决策**（PR / 直接合并 / 继续迭代）并入收尾时的 ask_user（继承 v1 第 10 步）。
>
> **前置链路**（🟡/🔴，协议见 §5.3）：意图识别（会话分类）→ 信息补给（`find_skill` 本地技能检索 / `web_search` 外部核实，均为可选能力、按需触发）→ 澄清门（模糊点拆假设/问题，批量反问一次）→ spec / intent 定稿。🟢 仅做会话分类，不经信息补给与澄清门（零文件约束优先）。

## 5. 产物规格（最小模板）

目录约定：`specs/<slug>/`，与仓库同生命周期、git 管理。**不设版本计数、不设归档机制。**slug 唯一性：目标目录已存在且不属于当前任务链（§12）→ 拒绝创建并要求换名，**不做自动后缀**（自动后缀会掩盖"撞名"这一语义信号）。

```markdown
<!-- spec.md -->
# <slug> spec
需求: <一句话>
背景: <两三行>
验收标准:            ← 每条 ID 唯一，尽量写成可执行命令
- AC-1: pytest tests/test_auth.py -k expired 通过
- AC-2: ...
假设:                ← 模糊点中低风险、自行决定的部分（§5.3 澄清门的产物）
- A1: <决定 + 依据；如经 web_search 核实须附来源与检索时间>
非目标: <明确排除项>

<!-- plan.md -->
# <slug> plan
方案要点: <架构与关键取舍>
架构决策:            ← 触发 ask_user 的四类: 新端口/新事件/表结构/聚合行为变更
- AD-1: <决策 + 确认结果>
任务拆分: 见 tasks.md

<!-- tasks.md -->
# <slug> tasks
- [ ] T1 (AC-1, AC-3): <描述>; 验证: <命令>
- [x] T2 (AC-2): <描述>; 验证: <命令>; 输出: <关键输出摘录>

## Deferred        ← 剩余风险的落地形态：未勾选即未完成
- [ ] D1: <已知缺口/待人工验证项>; 建议后续: <一句话>

## Review         ← 评审结论的归宿（见 §5.2）
- R1 [resolved]: <blocker 描述> → 修复于 T3
- R2 [open|minor]: <minor 描述，仅记录不阻断>

<!-- intent.md (🟡 专用，单文件) -->
意图: <一段话>; 验证: <命令>
```

不变量：勾选任务必须附最新命令输出（先有证据再有断言，继承 v1 原则）；AC 与 T 的引用关系是视图推导的追溯链。

### 5.1 报告降级为按需视图（取消持久终报）

五段终报的职责解绑后再取消：

| 终报段落 | 去向 |
|----------|------|
| 需求定位 | spec.md（本来就在） |
| 变更清单 | `git diff --stat` + commit message |
| 验证结果 | tasks.md 勾选 + 已粘贴的命令输出 |
| 剩余风险 | tasks.md「Deferred」节的未勾选任务（风险变成可执行后续，而非过期散文） |
| 技能使用日志 | 删除（harness 内部自省，无人类消费者） |

补救可读性：新增 `scripts/derive-report.py`（约 40 行）——想看时一条命令，从 tasks.md + 分支基点 diff 现场生成追溯视图到 stdout；**不落盘、不维护、永不腐化**。diff 基线用 `merge-base`（分支基点），**不用工作区 diff**——任务已提交后工作区 diff 为空，会丢变更清单。存储的只有状态（spec/tasks/git），展示的永远是投影。边界：📋 通道的 Findings/规格文档是**产品**（交付物本身），保留；🟢 的内联摘要是对话消息，不受影响。

### 5.2 角色产出的归宿

派发模板"读产物"之外，三个角色的**写**去向必须确定，否则角色结论只活在对话里、随会话蒸发：

| 角色 | 产出 | 归宿 |
|------|------|------|
| Explorer | 侦察结论（实现位置 / 调用链 / 可复用模式，带 file:line） | spec.md 背景节追加（侦察是写 spec 的输入） |
| Implementer | 实现 + 勾选 | tasks.md 任务行：勾选 + 验证命令输出 |
| Reviewer | 分级 Findings | tasks.md「Review」节：每条 `R<n>` 标注 `[resolved / open]` 与级别 |

结构保证（纪律→结构的又一落地）：**blocker / major 级 finding 处于 open 状态时收尾不合法**——评审拒绝自动回到实现循环，因为"未解决的 major"在 tasks.md 里是可见的未闭合状态，artifact-check 可机械校验；minor 允许 open（仅记录，转 Deferred 与否由用户定）。

🟡 通道没有 tasks.md：评审结论与 Deferred 以**同名小节附在 intent.md 末尾**（`## Review` / `## Deferred`，格式与校验规则同 🔴），保证"open blocker/major 不得收尾"在 🟡 同样成立。

### 5.3 澄清与反问协议（意图识别的两层）

意图识别分两层，反问的对象不同：**意图不明**问"做不做"（会话分类层，v1 已有：verb/noun/deliverable 判定 + 拿不准先问）；**需求模糊**问"怎么做、做到哪"（本节，分类已定但 scope 不清）。

起草 spec / intent 时，把每个模糊点强制拆成两类：

| 类别 | 判据 | 处理 |
|------|------|------|
| **假设** | 低风险、可逆、错了代价小 | 自行决定，写入 spec「假设」节显式标注（A-ID） |
| **问题** | 高风险、不可逆、架构决策四类（新端口/新事件/表结构/聚合行为变更） | 必须 `ask_user` 反问 |

规则：
1. **批量一次问**——所有问题合并为一轮反问，禁止连环单问。契约侧 `ask_user` 签名扩展为支持批量（`ask_user(questions[]) -> answers[]`，见 §6）；原语不支持批量时降级为**同一澄清轮内连续单问**，不得分散到多轮会话
2. **答案落档**——Q&A 结论转成 spec 的 AC / AD / 假设条目，不留在聊天记录里蒸发
3. **信息补给先行**——反问之前先用 `find_skill` / `web_search`（可选能力）把"能自己查清的"查清，只把真正需要用户决断的留给反问

### 5.4 信息补给层（两个新增可选能力）

| 能力 | 签名 | 用途 | 降级规则 |
|------|------|------|----------|
| `find_skill` | `find_skill(query) -> list[skill]` | 分类后、起草前检索本地技能库，命中则加载为条件技能 | 能力缺失或无命中 → 回落内置静态条件技能表（继承 v1 条件技能映射） |
| `web_search` | `web_search(query) -> results` | spec 的不确定性无法从仓库内部解决时核实外部知识（依赖版本 / 兼容性 / API 行为） | 能力缺失 → spec 假设区记录「未联网核实」，流程不阻断 |

`web_search` 三条纪律：结果进 spec 必须附**来源与检索时间**；**AC 必须本地可执行**（网搜结论不得直接充当验收标准）；触发克制——仓库内部能解决的绝不外搜。两个能力都属 harness 工具层，编排器只引用能力名，具体原语由适配器映射。

## 6. 能力契约变更

- **删除** `write_report`（必需 8 → 7）
- **保留** 可选 `spawn_agent` / `create_branch` / `check_command`；`run_quality_gate` 删除（无独立价值）
- **新增** 可选 `find_skill` / `web_search`（§5.4）。可选区变动：4 项 → 删 1 → 加 2 = **5 项**（spawn_agent / create_branch / check_command / find_skill / web_search），每项均带降级规则
- **签名调整**：`ask_user` 扩展为 `ask_user(questions[]) -> answers[]` 支持批量反问（§5.3）；原语仅支持单问题时按同一澄清轮连续单问降级
- 适配器各删 `write_report` 映射行、各增 `find_skill` / `web_search` 映射行；`references/templates/write-report.md` 删除
- 契约新增一条声明：**产物即状态**——无报告写入能力；报告是收尾回复 + 按需视图（§5.1），不是持久产物

## 7. 模块级变更清单

| 文件 | 处置 |
|------|------|
| `SKILL.md` | 重写：≤80 行，内容 = 会话分类 + 通道×产物矩阵 + 契约引用 + §12 续接协议摘要 |
| `references/capability-contract.md` | 删 `write_report` 语义节与报告协议不变量；新增 `find_skill` / `web_search` 可选能力定义与降级规则 |
| `references/adapters/{claude-code,codex,opencode}.md` | 删 `write_report` 行与报告路径配置；各增 `find_skill` / `web_search` 映射行（映射到各自的条件技能检索与搜索原语） |
| `references/templates/write-report.md` | 删除 |
| `references/templates/report-template.md` | 删除（终报不再落盘；视图格式内化到 `derive-report.py`） |
| `references/templates/` | 新增 `spec.md` / `plan.md` / `tasks.md` / `intent.md` 四个微型模板 |
| `scripts/report_lib.py` / `smoke-report.py` / `consistency-check.py` | 删除 |
| `scripts/workflow-check.py` | 重写为 `artifact-check.py`（约 150 行：产物 schema + tasks 勾选 vs git 状态 + AC 引用完整性 + Deferred 节校验 + Review 节 open blocker/major 拒绝收尾） |
| `scripts/derive-report.py` | 新增（约 40 行：tasks.md + 分支基点 diff（merge-base）→ 追溯视图到 stdout，不落盘） |
| `.claude/settings.json` / `opencode.json` | 更新放行清单：`artifact-check.py` / `derive-report.py`（替换原三件套的放行条目） |
| `README.md` / `CHANGELOG.md` | 同步更新 |

## 8. 迁移步骤（每步独立提交、可回退）

1. **契约瘦身**：删 `write_report`（契约 + 三适配器 + write-report.md），跑现有 consistency-check 确认无残留引用
2. **产物引入**：四模板 + `artifact-check.py` + `derive-report.py` + `fixtures/` 三个示例任务（见 §11.3）
3. **主体重写**：SKILL.md 按通道×产物矩阵 + §12 续接协议重写至 ≤80 行；角色派发模板改为读写产物文件（§5.2）
4. **收尾**：删旧脚本三件套、更新 README / CHANGELOG、发 v2.0.0

## 9. 风险与对策

| 风险 | 对策 |
|------|------|
| spec 腐化（代码改了 spec 没改） | 验收标准强制可执行化并挂质量门禁；勾选必须附最新输出 |
| SDD 滥用到轻通道 | 矩阵硬约束 🟢 零文件；artifact-check 校验 |
| 产物目录污染宿主仓库 | `specs/` 默认纳入 git；**inline 仅限 🟢（对话即交付），🟡/🔴 恒写盘——中断恢复优先于目录洁癖** |
| 收尾信息丢失 | 剩余风险落 Deferred 节（未勾选即显式欠账）；`derive-report.py` 按需生成完整追溯视图 |
| 证据新鲜度（勾选附的输出可能是陈旧的） | 收尾重验兜底（§4）：全量门禁在收尾前强制重跑，输出直接进收尾回复 |
| 多轮归属误判（追加错任务链 / 撞 slug） | §12 续接协议 + slug 拒绝创建规则 |
| 网搜内容污染 spec（过时/错误的外部结论） | 三条纪律：附来源与检索时间；AC 必须本地可执行；仓库内能解决不外搜 |

## 10. 验收判据（Definition of Done）

**机器断言**（`artifact-check.py` / fixture 自动化）：
- [ ] `artifact-check.py` 在 fixture 任务上通过；`broken` 用例必须报错（含 Review 节 open blocker/major 拒绝收尾的用例）
- [ ] §11.3 三个 fixture 的机器断言全部通过/报错
- [ ] L0–L3 分层加载协议成立：SKILL.md 不内联复制任何下层内容

**人工演练判据**（端到端走一遍，机器无法全代）：
- [ ] SKILL.md ≤80 行，且四通道行为可从文档唯一推导
- [ ] 三份适配器均无 `write_report` 依赖；按 `_adapter-template.md` 演练接入新 Harness 一次通过
- [ ] 一个 typo 任务端到端不产生任何新文件（🟢 零文件约束，含 lint/format 实际执行）
- [ ] 一个 🔴 示例任务：收尾重验跑全量门禁、合并决策走 ask_user、`derive-report.py` 可由产物 + diff 完整推导追溯视图，且全程无终报文件落盘
- [ ] 一个多轮任务链演练：同 slug 追加任务、通道升级补齐产物（§12）
- [ ] 一个模糊需求演练：澄清门批量反问一次（无连环追问）、答案转 AC/AD/假设落档 spec（§5.3）

## 11. Harness 工程原则（v2 的设计公理）

> 唯一公理：**模型是常量，脚手架是变量**——改不了模型权重，但上下文、工具面、反馈回路、状态存储全在工程手里，预算全部投向脚手架。执行原则：**判断归模型，状态归机械层**。

### 11.1 分层加载协议（上下文即稀缺资源）

| 层级 | 内容 | 加载时机 | 预算 |
|------|------|----------|------|
| L0 | frontmatter description | 常驻（所有会话可见） | ≤80 词 |
| L1 | SKILL.md 主体（分类 + 通道×产物矩阵 + 契约引用 + §12 摘要） | 技能触发时一次 | ≤80 行 |
| L2 | capability-contract.md + 当前 Harness 适配器 | 按需：触及契约或降级时 | — |
| L3 | 四个产物模板 | 用到对应通道时 | — |

硬约束：**任一层不得内联复制下层内容，只允许引用路径**（v1 的 23KB 常驻注入正是本条的反例）。这是把"SKILL.md 压到 ≤80 行"从口号变成可校验规则的方式。

### 11.2 纪律 → 结构（v1 → v2 的进化本质）

v1 的大量条款本质是**用散文向模型求纪律**；v2 把它们转化为**结构保证**——违反要么物理上不可能，要么立刻被校验器暴露。这解释了为什么 SKILL.md 能砍掉 2/3：砍掉的不是规则，是规则的执行方式。

| v1 的 prompt 纪律 | v2 的结构保证 |
|------------------|---------------|
| "绝不凭记忆声称通过" | 收尾回复与按需视图必须由产物 + diff 推导；勾选必须附命令输出；artifact-check 校验 |
| "绝不静默覆盖 in-progress 报告" | git 分支/提交即状态，覆盖在物理上不可发生 |
| "先有证据再有断言" | AC 可执行化并挂门禁，证据与产物同址存放 |
| "跳过阶段必须留痕" | 通道×产物矩阵硬约束；🟢 零文件由 fixture 校验兜底 |

### 11.3 微型 eval：fixture 任务集

> 校验器本身也要有测试——eval 不是可选项，是 harness 的一部分。

| fixture | 通道 | 断言 |
|---------|------|------|
| `fix-typo` | 🟢 | 端到端不产生任何新文件；lint/format 实际执行 |
| `add-validation` | 🟡 | `intent.md` 存在且含验证命令；门禁输出已随勾选粘贴 |
| `refactor-flow` | 🔴 | spec/plan/tasks 三产物 schema 合法；AC↔T 引用闭合；`derive-report.py` 视图可完整推导 |
| `broken`（故意损坏） | 🔴 | artifact-check **必须报错**（缺 AC 引用 / 勾选无输出 / Review 节 open blocker）——验证校验器有牙齿 |

运行方式：`python scripts/artifact-check.py --fixtures fixtures/`，并入 §8 迁移第 2 步交付。断言分两类：**机器断言**（产物形态，artifact-check 自动校验）与**人工演练判据**（如"lint/format 实际执行"，属 §10 人工项）——`fix-typo` 的执行性断言归后者。

## 12. 多轮与续接协议（任务归属规则）

> git 管状态，不管语义归属——"这条新需求属于哪个任务链"必须显式定义。本节替代 v1 的多轮会话规则（复用 in-progress 报告 / 通道升级 abandoned / 重开 v\<N+1\>）。

1. **每条用户消息后重跑会话分类**（继承 v1，不变）
2. **归属判定**：slug 由任务链的**首个需求**生成；后续消息**默认追加为当前任务链的新任务**（写入 tasks.md，含 Review/Deferred 归属判断）。🟡 通道没有 tasks.md，追加 = **intent.md 扩展为多段意图列表**（每段一个意图 + 验证命令，追加即加段）。仅两种情况开新链：用户显式说"新任务 / 另外一件事"，或需求主题与当前链明显无关（拿不准 → ask_user）
3. **通道升级**：后续需求把通道抬高（🟢→🟡/🔴）时，**补齐缺失产物**（补 intent.md / spec.md + plan.md），不新建目录、不弃任务链——升级前的已验证勾选仍然有效；通道**不降级**（继承 v1）
4. **收尾与续开**：收尾回复交付后任务链关闭；同 slug 再来新需求 = 重开同链（产物已在，追加任务即可）。重开时 spec 的演化规则：**AC 只增不改**——新需求新增 AC 条目，确需修改旧 AC 时用 `supersede` 标注指向新 AC，保证追溯链不断
5. **中途放弃**：不设 abandoned 状态机——未勾选任务 + Deferred 条目本身就是显式欠账，留档还是丢弃由用户在收尾时决定
