# harness-coding

> 把一句需求变成受控的代码变更流程：**会话分类 → 分级通道 → 角色派发 → 质量门禁 → 收尾回复**。
> 状态活在产物里，历史活在 git 里，证据活在门禁输出里——没有报告文件，没有自造的状态机。

| 项目属性 | 值 |
|---|---|
| 形态 | Agent Skill（方法论 `SKILL.md` + 纯标准库 Python 脚本），不是一个可运行的服务 |
| 当前版本 | `2.5.0`（以 `SKILL.md` frontmatter 为准） |
| 许可证 | MIT |
| 依赖 | 运行时零第三方依赖（Python 3.12）；静态检查用 `ruff==0.17.5` / `mypy==2.4.1` |
| 适配 Harness | Claude Code / Codex / opencode / WorkBuddy（+ 新增接入模板） |
| 规模 | `SKILL.md` 89 行（6.8 KB）· `references/` 16 文件 · 脚本 1056 行（4 个，纯标准库）· 55 次提交 · 6 条 dogfood 产物链 |
| 自测 | 9 个产物 fixture + 4 个迁移 fixture + 4 个探针 fixture + 6 条真实产物链，全部通过 |

---

## 1. 这是什么，不是什么

**是**：一套写给编码 Agent 的工程约束。你在 Claude Code / Codex / opencode / WorkBuddy 里装它之后，当你说"加个功能""修个 bug""重构一下"，它会先判断这件事该走多重流程，再按流程产出 markdown 产物、跑门禁、做评审，最后给一份有证据的收尾回复。

**不是**：

- 不是代码生成器——它不替你写业务代码，它规定"怎么写才算交付"
- 不是工作流引擎——没有服务、没有数据库、没有守护进程；唯一的运行面是几个可执行脚本和 markdown 文件
- 不是某个框架的绑定——方法论正文只出现**能力名**（`read` / `run_command`），不出现任何具体工具名，换 Harness 只需加一个适配器文件

---

## 2. 它要解决的四个真实病症

| 病症 | 常见表现 | 本项目的结构性对策 |
|---|---|---|
| **凭记忆声称通过** | "测试都过了"——其实没跑，或者只跑了一个文件 | 勾选任务必须粘贴 `Output:` 门禁输出；收尾前强制全量重跑；校验器机械检查证据与勾选的配对 |
| **跳门禁不留痕** | 这个项目没有类型检查，于是 type 门禁悄悄消失 | `GATE-NA(<gate>)` 必须先在 `## Gate Exemptions` 声明"原因 + 范围"，再在任务里引用；未声明的跳过是**校验错误** |
| **多轮上下文丢失** | 聊到第 40 轮，Agent 忘了前 3 个任务干了什么 | 上下文经产物流动，绝不经过父会话摘要；恢复 = 读 `specs/<slug>/tasks.md` |
| **一句话需求直接开写** | 需求模糊就先编码，返工三轮 | 澄清门：模糊点拆成 `Assumptions`（自决并记录）/ `Questions`（一轮批量问完）；架构决策永远问 |

这四个病症是同一件事的四个侧面：**把"请模型守纪律"换成"违反纪律会立刻暴露或物理不可能"**。

---

## 3. 核心设计：产物即状态

v1 用一套自造的报告协议来记录流程状态（`report_lib.py` 297 行 + `smoke-report.py` 587 行看守它自己），六轮 CHANGELOG 全在修这套协议自身的 bug。v2 直接把它删了，状态的载体换成三个平凡的 markdown 文件：

```
specs/<slug>/
├── spec.md     # Requirement / Background(file:line) / AC-n / Assumptions / Non-goals / Gate Exemptions
├── plan.md     # 技术方案、决策(AD-n)、风险
└── tasks.md    # - [ ] T1 (AC-1): 描述; verify: 命令
                # - [x] T2 (AC-1): 描述; verify: 命令; Output: <粘贴的门禁输出>
                # ## Deferred  (未勾选 = 未完成)
                # ## Review    (R1 [open|minor] / R2 [resolved])
```

| v1 的协议机制 | v2 的载体 |
|---|---|
| 中断后从 marker 恢复 | 读 `tasks.md` 的复选框就是进度 |
| 每任务版本号 `v<N>` | git 提交历史 |
| 并发写冲突保护（独占创建） | git 分支模型 |
| 五段式增量报告 | 收尾聊天回复 + 按需追溯视图（`derive-report.py`，只打 stdout，永不落盘） |
| in-progress / abandoned 状态机 | 工作区状态 + 未勾选的 Deferred |

一条硬约束贯穿全部：**AC 只增不改**。需求变了就新增 AC；旧 AC 确实要改，标注 `supersede` 指向新 AC，追溯链不断。

---

## 4. 四条通道（这是全项目的骨架）

| 通道 | 触发条件 | 产物 | 流程 | 收尾 |
|---|---|---|---|---|
| 🟢 轻量 | 单文件、显而易见、无设计决策 | **零文件** | 实现 → lint / format | 内联摘要 |
| 🟡 标准 | 一段话能说清的意图、跨几个文件 | `intent.md` | 定位 → 澄清 → 实现 → 门禁 → 评审 → 收尾重验 | 收尾回复 |
| 🔴 完整 | 新功能 / 表结构 / API / 重构，或需要 plan 与 reviewer | `spec.md` + `plan.md` + `tasks.md` | 信息补给 → spec → 澄清门 → plan → 逐任务实现+门禁 → 评审 → 收尾重验 | 收尾回复 + 追溯视图 |
| 📋 仅结论 | 结论本身就是交付物（评审、方案校验） | spec / plan **就是**交付物 | 定位 → 评审 → 结论 | 校验结论 |

**硬约束**：🟢 绝不创建任何文件（"为改一个错别字写 spec"是荒谬的）；🔴 三件套齐全；🧭 通道只升不降。

`references/flow.md` 补的是**判据互相打架时**的边界情况，这是最容易误判的部分：

| 情况 | 应选 | 默认判据为什么会误导 |
|---|---|---|
| 只改一个文件，但它动了 schema / 公开签名 / 配置契约 | 🔴 | "单文件"不是标准，爆炸半径才是 |
| 纯文档、注释、格式化——哪怕十个文件 | 🟢 | 没有设计决策、没有 AC 集合、没什么可验证 |
| 依赖、构建、CI 配置变更 | 🟡 | 跨文件，且受影响的测试无法枚举 |
| 跨模块机械重命名 / 移动 | 🟡 | 面广但无设计：需要受影响子集，不需要 plan |
| 需要测试钉住现有行为的 bug 修复 | 🟡 | 回归钉住本身是设计工作，不是守卫动作 |
| 只读审计，但用户期待同一轮里修掉 | 🟡 | 结论不再是交付物 |
| AC 集合一段话写不完 | 🔴 | 说明范围还没被理解 → 先 plan |
| 🟡 与 🔴 之间犹豫 | 🔴 | 升级可以补产物，降级只会丢掉产物 |

---

## 5. 一次 🔴 任务的完整时序

```
用户: "给订单服务加一个超时取消的定时任务"
  │
  ├─ ① 分类        记录 `<verdict> — verb: add; noun: scheduler; deliverable: yes`
  │                 拿不准会不会动文件 → 直接问"要不要做"，绝不猜
  │
  ├─ ② 选通道      动表结构 + 新事件 → 🔴；建 specs/order-timeout-cancel/
  │
  ├─ ③ 信息补给    find_skill 找本地技法 / web_search 查外部事实
  │                 （能查仓库就不上网；网搜结论必须带来源+时间，且不能变成 AC）
  │
  ├─ ④ 澄清门      拆成 Assumptions(A1..An 自决并记录) 与 Questions
  │                 Questions 一轮 ask_user 批量问完，绝不逐轮挤牙膏
  │                 答案落地为 AC 或 AD，架构决策（新端口/新事件/表结构）必须问
  │
  ├─ ⑤ spec        Requirement / Background 占位 / AC-n（尽量可执行）/ Non-goals
  │
  ├─ ⑥ explorer    只读侦察，产出 file:line，**替换**（不是追加）spec.md 的 Background 占位
  │
  ├─ ⑦ plan ⑧ 逐任务实现
  │                 每完成一个任务：lint/format/type 全量 + 受影响测试子集
  │                 勾选 T<n> 并粘贴 Output:；失败 → 定位根因 → 修复 → 从失败那道重跑
  │
  ├─ ⑨ reviewer    分级 Findings → tasks.md 的 ## Review
  │                 blocker/major 仍 open → 禁止收尾（机械拦截，不是建议）
  │
  └─ ⑩ 收尾       全量门禁重跑（逐任务绿 ≠ 全仓绿）
                   artifact-check.py specs/ 校验
                   derive-report.py 出追溯视图（stdout）
                   按 output-contract.md 出回复，ask_user 问合并方式
```

---

## 6. 角色与上下文流动

| 角色 | 职责 | 产物归宿 |
|---|---|---|
| explorer | 只读侦察（定位、调用链、可复用模式、开放问题，全部带 `file:line`） | `spec.md` 的 Background（**替换**占位） |
| implementer | 落地代码 + 测试 + 门禁 | `tasks.md` 勾选 + 粘贴 `Output:` |
| reviewer | 分级评审（blocker / major / minor / suggestion），只报告不修改 | `tasks.md` 的 `## Review`（`R<n> [open\|level]`） |

关键纪律：**上下文经由产物流动，绝不经过父会话摘要**。派发子 Agent 时只传"任务指针 + 角色纪律"，子 Agent 自己去读产物——这样即使编排器上下文被压缩，实现者的输入也不失真。

没有 `spawn_agent` 能力的 Harness 就由编排器内联扮演同一角色，**输入输出契约不变**；但编排器绝不亲自写大型实现或测试。

---

## 7. 质量门禁协议

固定顺序，命令由**宿主项目**定义（适配器 §2 的 `<entrypoint>` 四动词）：

```
lint → format --check → type --check --strict → test（含覆盖率阈值）
```

| 规则 | 说明 |
|---|---|
| 逐任务模式 | lint / format / type **全量**（它们很快）+ **受影响的测试子集**；全量测试属于收尾 |
| 收尾重验 | 逐任务绿 ≠ 全仓绿——后面的任务可能破坏前面验证过的行为，收尾必须全量重跑 |
| 证据 | 每句"通过"都要有命令输出；失败要贴关键错误，绝不隐藏 |
| Gate N/A | 不适用 ≠ 悄悄跳过。必须 `- GATE-NA(<gate>): <原因 + 范围>` 声明（chain-wide 或 task-scoped），并在使用处引用；校验器校验配对 |
| 范围语义 | chain-wide 豁免在收尾重验时依然有效；task-scoped **不**延续——收尾照样跑这道门禁。存疑时按 task-scoped 处理（更安全） |
| 覆盖率 | 阈值由项目声明（如 `fail_under`）；项目没声明 → 就是普通 pass/fail，**绝不发明数字**，也不拿够不到的全仓阈值卡老代码库 |
| 行为保持型重构 | plan 必须先建**特征测试基线**，且至少一条 AC 是"基线测试原样通过" |
| 失败处理 | 定位根因 → 修复 → 从失败那道重跑；绝不为了让灯变绿而删断言或放宽断言 |

---

## 8. 能力契约与适配器

方法论只引用**能力名**，`references/capability-contract.md` 是每个能力签名与降级规则的唯一事实源。

**必需 7 个**（缺一个则技能不可用）：`read` / `write` / `edit` / `glob` / `grep` / `run_command` / `ask_user`

**可选 5 个**（每个都带降级路径，绝不因缺失而阻塞）：

| 能力 | 缺失时 |
|---|---|
| `spawn_agent` | 编排器内联串行扮演角色，职责不变 |
| `create_branch` | 直接在主工作区改，标注 `not isolated (no branch capability)` |
| `check_command` | 用 `run_command` 跑一次看结果 |
| `find_skill` | 先跑 `find-skill.py` 探针；无库则查静态表 `conditional-skills.md`，并记录 `skill library unavailable` |
| `web_search` | 在 spec 的 Assumptions 记 `not verified online`，流程不阻塞 |

两个容易被忽略的语义：

- **`ask_user` 是批量原语**：澄清门的所有问题必须一轮问完。宿主只支持单问时，降级为"同一澄清轮内的连续追问"，不能摊到多轮。无头环境选**最保守选项**并记录 `⚠️ unable to ask the user...`，绝不假装用户确认过。
- **能力名是锚点不是实现**（context-first）：运行时对着**当前对话里实际存在的工具**解析；适配器的映射行只是提示，冲突时以现场为准，并把偏差记录下来。

**适配器层**只回答一个问题：这个 Harness 用什么具体机制实现每个能力。现有 5 个文件：`claude-code.md` / `codex.md` / `opencode.md` / `workbuddy.md` / `_adapter-template.md`。它们是"探针顺序 → 回退方案"，不是"已验证支持版本 X"的声明——这个区别是踩坑换来的：codex 适配器曾断言有 `read_file` / `apply_patch`，而实际会话只暴露 `exec_command`，导致 172 次整文件 shell 倾倒。

WorkBuddy 适配器还额外规定**审批纪律**：它同时有 Bash 与 PowerShell 两个命令工具，同一个门禁的两种拼法就是两个命令前缀、两次审批；没有仓库级权限文件，所以要求"一个项目一个入口、预先批准一次、单会话 ≤3 次审批、禁止 `bash -c "..."` 嵌套"。

---

## 9. 四个脚本（纯标准库，零依赖）

### `scripts/artifact-check.py`（473 行）— 产物校验器，项目的"编译器"

```bash
python scripts/artifact-check.py specs/            # 校验产物链
python scripts/artifact-check.py --fixtures fixtures/          # 校验器自测
python scripts/artifact-check.py --migrate specs/ --dry-run    # 预览历史豁免迁移
python scripts/artifact-check.py --migrate-fixtures fixtures/migrate/
```

它机械执行的规则（每条都对应一次真实事故）：

| 检查 | 触发条件 |
|---|---|
| 目录名必须是 lowercase kebab-case | slug 规范 |
| `spec.md` 必须有 `Requirement:` 行、必须有 `AC-n` | 注释块里的 AC 不算（注释不是需求） |
| 有 `spec.md` → 必须有 `plan.md` + `tasks.md` | 🔴 通道三件套 |
| 任务行必须是 `- [x] T<n> (AC-x): 描述` | 形状像任务但格式不全的行**必须报错**，否则它会静默逃过所有检查 |
| 每个任务必须引用 AC；引用的 AC 必须存在 | AC ↔ T 闭包 |
| 已勾选必须带 `Output:` | 证据与勾选配对 |
| 每条 AC 至少被一个任务覆盖 | 闭包反向检查 |
| `## Review` 的 `R<n>` 状态合法、open 必须带等级 | 分级评审 |
| **open 的 blocker/major → 直接报错** | 评审网关，禁止带病收尾 |
| `GATE-NA(gate)` 必须有配对声明；gate 名必须在 lint/format/type/test 内 | 门禁豁免协议 |

`--migrate` 是**诚实的历史补偿**：执法规则逐版加固（v2.0.2 引入协议、v2.2.7 收窄到章节、v2.3.3 剥离注释），早期合法关闭的链会被追溯判失败（真实案例：42 条链里 7 条）。迁移只按"实际用法"声明门禁，**不发明理由**，未知门禁只报告不改写，且幂等。

### `scripts/derive-report.py`（108 行）— 按需追溯视图

读产物 + `merge-base` diff，向 stdout 打印 Requirement / Change List / Verification Results / Remaining Risks。**只读，永不落盘**——报告从"存储的产物"降级为"派生的视图"。🟡 链没有 T 行时，改打 intent 的 `Verify:` 与 `Intent Additions`。

### `scripts/find-skill.py`（230 行）— 技能库探针

探 5 个全局根（`~/.agents`、`~/.claude`、`~/.codex`、`~/.config/opencode`、`~/.workbuddy`）+ 4 个项目根，解析 `SKILL.md` frontmatter，按"名称命中 2 分 / 描述命中 1 分"打分排序。还做**漂移检测**：同名技能在多处版本不一致 → 打 `DRIFT` 警告"在解决前不要信任任何一份"（真实故障类：旧 v1.0.0 影子覆盖了 v2.x）。

退出码是契约：`0` 命中 / `1` 有库无匹配（转静态表）/ `2` 完全没有库（记 `skill library unavailable`）/ `3` 仅自测失败。

### `scripts/build-dist.py`（245 行）— 可复现打包

- **allowlist 白名单制**：只装 `SKILL.md` + `LICENSE` + `references/**` + 三个运行时脚本；dev 文件（README、CHANGELOG、`fixtures/`、`specs/`、`.claude/`）**即使新增也不会泄漏**到产物里；打包器排除自己（它不是运行面）
- **自校验**：逐个文件与归一化后的源比对、检查树里缺件/多件、检查是否残留 CRLF
- **字节级可复现**：zip 条目 `STORED`（不压缩）+ 固定时间戳 `1980-01-01` + `create_system=3` + `0o644`。这不是保守，是实证结论——v2.3.7 的对照显示 CI(ubuntu) 与 Windows 构建**压缩后大小相同（45.4 KB）但 sha256 不同**，zlib 的 deflate 输出在任何级别都跨平台不稳定；`STORED` 是原始字节 + CRC32，两边都确定性，因此"同内容必同字节"成为构造性保证，代价只是 zip 涨到约 100–120 KB

---

## 10. 目录结构

```
harness-coding/
├── SKILL.md                        # 方法论主体（L1，加载时只读这一个）
├── references/
│   ├── capability-contract.md      # 能力契约：7 必需 + 5 可选 + 门禁/角色/降级（L2，按需）
│   ├── flow.md                     # 通道边界情况、澄清门、slug/延续/升级、收尾重验（L3，按需）
│   ├── conditional-skills.md       # 8 个技法槽位静态表（find_skill 未命中时兜底）
│   ├── adapters/                   # claude-code / codex / opencode / workbuddy / _template
│   └── templates/                  # spec/plan/tasks/intent + 3 个派发模板 + 收尾契约
├── scripts/
│   ├── artifact-check.py           # 产物校验器（含 fixture 自测与历史迁移）
│   ├── derive-report.py            # 按需追溯视图（stdout only）
│   ├── find-skill.py               # 技能库探针（含漂移检测）
│   └── build-dist.py               # 发布打包（白名单 + 自校验 + 可复现 zip）
├── specs/                          # dogfood：6 条被持续校验的真实产物链
├── fixtures/                       # 自测用例（含故意损坏样本 + 迁移用例 + 探针库）
├── SDD-REFACTOR-DESIGN.md          # v2 重构设计文档（含量化动机与设计公理）
├── CHANGELOG.md                    # 逐版本发布记录（根因长叙述在 specs/ 各链）
├── .github/workflows/release.yml   # 双车道 CI（tag 不可变 Release / main 滚动构建）
├── .claude/settings.json           # Claude Code 预授权
├── opencode.json                   # opencode 预授权
└── requirements-dev.txt            # 静态检查版本单源（ruff / mypy）
```

---

## 11. 安装与接入

```bash
python scripts/build-dist.py
# → dist/harness-coding/                         （可安装的技能目录）
# → dist/harness-coding-v<version>.zip            （可复现发布包）
```

把 `dist/harness-coding/` 复制或软链到目标 Harness 的技能目录：

| Harness | 路径 |
|---|---|
| Claude Code | `<project>/.claude/skills/` 或 `~/.claude/skills/` |
| Codex | `<project>/.codex/skills/` 或 `~/.codex/skills/` |
| opencode | `<project>/.opencode/skills/` 或 `~/.config/opencode/skills/` |
| WorkBuddy | `~/.workbuddy/skills/`（探针默认根之一） |

在**宿主项目**里放行三个脚本，避免每次门禁都弹审批（仓库自带两份示例）：

```json
// opencode.json
{ "permission": { "bash": {
  "python scripts/artifact-check.py*": "allow",
  "python scripts/derive-report.py*": "allow",
  "python scripts/find-skill.py*": "allow" } } }
```

```json
// .claude/settings.json
{ "permissions": { "allow": [
  "Bash(python scripts/artifact-check.py*)",
  "Bash(python scripts/derive-report.py*)",
  "Bash(python scripts/find-skill.py*)" ] } }
```

**接入新的 Harness**：复制 `_adapter-template.md` 逐节填写 → 跑一个 🟢 任务（必须零新文件）→ 跑一个 🔴 示例验证产物与校验。必需能力无法满足时，在适配器顶部标注"unsupported capabilities"，靠降级规则继续。

---

## 12. 验证（本文档写作时全部实跑通过）

```bash
# 静态检查（版本钉死在 requirements-dev.txt，CI 与本机同源）
ruff check scripts/ --isolated --select E,F,W,UP,B,SIM,RUF --line-length 120
ruff format --check scripts/ --line-length 120
mypy --strict scripts/

# 脚本自测
python scripts/artifact-check.py --fixtures fixtures/            # 9 个产物用例
python scripts/artifact-check.py --migrate-fixtures fixtures/migrate/   # 4 个迁移用例
python scripts/find-skill.py --fixtures fixtures/skills/         # 4 个探针用例

# 校验本仓库自己的产物链
python scripts/artifact-check.py specs/                          # 6 条链全 PASS
```

`fixtures/` 的设计要点：**故意损坏的样本必须在**。只验证"合法输入能过"的校验器无法证明自己有牙齿；这里每个错误类别都用 `.expect` 的 `err=<substring>` 单独断言，一个静默的检查回归没法藏到别的错误后面。

| fixture | 通道 | 断言 |
|---|---|---|
| `fix-typo` | 🟢 | 端到端零新文件 |
| `add-validation` | 🟡 | intent 存在、带 verify 命令、门禁输出随勾选粘贴 |
| `refactor-flow` | 🔴 | 三件套 schema、AC↔T 闭包、追溯视图可完整派生 |
| `broken` | 🔴 | **必须报错**（缺 AC 引用 / 勾选无输出 / Review open blocker / 未声明豁免），逐错误类断言 |
| `gate-na` / `intent-gate-na` | 🔴 / 🟡 | 合法的链级豁免：用法与声明配对成立 |
| `broken-intent-na` | 🟡 | 故意违反：🟡 用了 `GATE-NA(type)` 却没声明（这个用例第一次跑就暴露了真实的空转 bug） |
| `malformed-task` | 🔴 | 故意违反：`- [x] T2: ...` 缺 `(AC-x)` 块，曾经静默逃过所有任务检查 |
| `comment-ac` | 🔴 | 合法：HTML 注释里的 AC 行不得被当成需求 |

---

## 13. CI 与发布（双车道）

| 车道 | 触发 | 产物 | 语义 |
|---|---|---|---|
| 版本车道 | 推 `v*` tag | `harness-coding-v<version>.zip` → 不可变 GitHub Release | 里程碑，必须以 CHANGELOG 条目为门槛 |
| 滚动车道 | push `main` | `harness-coding-main-<sha>.zip` → 覆盖 `latest` prerelease | 只用于安装，**不计入 CHANGELOG**，永不作为版本号被引用 |

两条车道跑**完全相同**的步骤：静态检查 → 三个 fixture 套件 + `specs/` 校验 → 自校验构建。所有 GitHub Actions 都钉在 commit SHA 上（注释里记录了 `git ls-remote` 的核验日期与 SHA 来源）。

**批量发布制**（v2.4.0 起）：版本 = 发布动作，不是变更动作（1 version = N chains）。

- 变更期：commit + 全量门禁 → 推 main；不动版本号、不写 CHANGELOG
- 发布期：一次性 bump 版本 + CHANGELOG 汇总 + 推 tag

---

## 14. 版本演进（读 CHANGELOG 的正确姿势）

| 版本 | 主题 |
|---|---|
| **v2.0.0** | SDD 重写：删掉报告协议状态机（`report_lib` + `smoke-report` 共 884 行），改为产物驱动；`SKILL.md` 从 23 KB 压到个位数 KB |
| v2.2.x | 校验器加固：GATE-NA 配对、🟡 声明收窄到章节、HTML 注释剥离、malformed task 拦截、短查询匹配、纠结点诊断 |
| v2.3.x | 工程化：脚本静态门禁进 CI、可复现构建（`STORED` 决策）、版本单源、适配器示例去技术栈绑定 |
| v2.4.x | 流程化：批量发布制、历史链迁移通道（`--migrate`）、迁移用例并入 CI |
| **v2.5.0** | 会话纪律：回放 235 个真实 Codex 会话 → 单条 371 轮链 41.7M input / 90.95% 缓存命中，但 **58% 的未命中 token 集中在 25 轮**，且每轮都紧跟一次审批；据此加"惰性加载协议"（加载成本 28.4 KB → 7.0 KB，-75%）与 §8 会话纪律（≤3 次审批、禁嵌套 shell、禁重复读已注入文件、单轮 ≤12 次工具调用） |

v2.5.0 里最值得抄的一段工程态度：目标是 3 KB，两次尝试都被否决并**公开写明"目标未达成且不延期，直接放弃"**——理由是剩下的每一 KB 都是决策规则（通道判据、`GATE-NA` 语法、四条硬约束），砍掉就是用一个静默误判换约 $0.03 的缓存前缀。

---

## 15. 设计原则（为什么长这样）

单条公理：**模型是常量，脚手架是变量**——你改不了模型权重，但上下文、工具面、反馈回路、状态存储全在工程手里，预算该全花在脚手架上。执行原则：**判断归模型，状态归机械层**。

1. **分层加载**：L0 描述（常驻）→ L1 `SKILL.md` → L2 契约 + 适配器 → L3 模板。硬约束是"任何层不得内联复制下层内容，只能引用路径"。v1 的 23 KB 常驻注入就是这条规则的反面教材。
2. **纪律 → 结构**：v1 用大段散文恳求模型守规矩；v2 把每条规矩换成结构保证——违规要么物理不可能（git 分支即状态），要么被校验器立刻抓出。
3. **单一事实源**：流程真相在 `SKILL.md` §2，能力语义在契约 §2，通道边界在 `flow.md`——三者有重叠时以 `SKILL.md` 为准，且不允许"两张互补的表"这种自我安慰（v2.5 发现所谓互补的两张表 95% 逐行重复，最后是拆分职责而非保留双份）。
4. **校验器自己也要被测**：`fixtures/` 是这套 harness 的 eval，不是可选项。
5. **诚实优先于好看**：迁移不发明理由；无法联网就写 `not verified online`；无头环境选了保守选项就明说没问过用户；版本发布缺 gate 就直接记一笔。

---

## 16. 已知限制与使用注意

- **它不产生业务价值，只降低返工率**。如果你只写三行脚本，🟢 通道才是正确选择——本项目自己就坚持"为错别字写 spec 是荒谬的"。
- **门禁命令必须由宿主项目提供**。仓库本身没有 pytest：它的 test 槽位由三个 fixture 套件满足，并在 spec 里以 chain-wide 豁免声明（这是一个合法豁免的活样本，不是遗漏）。
- **脚本按相对路径 `python scripts/...` 调用**，需在产物所在项目根目录执行；跨目录调用会让适配器的预授权前缀失配，进而退化成每次都弹审批。
- **`--migrate` 是补偿工具，不是日常命令**。它会写文件（`--dry-run` 除外）；迁移只能把"用法"提升为"声明"，理由列写的是一条诚实的说明，不是编造的根因。
- **`dist/` 被 `.gitignore` 忽略**。本地 ZIP 由打包脚本生成，正式发布包通过 GitHub Releases 分发。
- **`README.md` 提供中文速查**，本文补充流程、门禁和发布细节。

---

## 17. 参考索引

| 想了解 | 打开 |
|---|---|
| 方法论全文（89 行） | `SKILL.md` |
| 能力签名 / 降级 / 门禁协议 / 角色契约 | `references/capability-contract.md` |
| 通道边界、澄清门、多轮延续、收尾重验 | `references/flow.md` |
| 我这个 Harness 该映射到哪些工具 | `references/adapters/<harness>.md` |
| 产物长什么样 | `references/templates/{spec,plan,tasks,intent}.md` |
| 收尾回复的结构 | `references/templates/output-contract.md` |
| 为什么这样设计（含量化动机与公理） | `SDD-REFACTOR-DESIGN.md` |
| 每个版本的根因与证据 | `CHANGELOG.md` + `specs/<slug>/tasks.md` |
