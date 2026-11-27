# harness-coding

harness-coding 是一套供编码 Agent 加载的技能。你可以从一句「修复这个 bug」或「给接口加校验」开始，Agent 会按改动范围选择流程，记录需要确认的决定，并在交付时说明改了什么、跑了哪些检查、还有哪些问题待解决。

任务状态保存在项目的 Markdown 产物里。大型任务可以从 `specs/<slug>/tasks.md` 恢复，评审可以沿验收条件追到实现任务和验证输出。

## 快速开始

1. 从 [GitHub Releases](https://github.com/1220282679/harness-coding/releases) 下载版本 ZIP，或在仓库根目录执行 `python scripts/build-dist.py`，生成 `dist/harness-coding/` 和 `dist/harness-coding-v<version>.zip`。
2. 将解压后的 `harness-coding/` 放进宿主的技能目录，确认 `SKILL.md` 位于 `harness-coding/` 根目录。
3. 在宿主中加载技能，用一句真实需求试跑，例如「用 harness-coding 给订单查询接口加分页，先确认兼容性和验收条件」。

| 宿主 | 项目级技能安装位置 |
| --- | --- |
| Claude Code | `.claude/skills/harness-coding/` |
| Codex | `.codex/skills/harness-coding/` |
| opencode | `.opencode/skills/harness-coding/` |

脚本使用 Python 3.12 标准库。宿主的工具映射、命令审批与降级路径见各自的适配器。 [Claude Code](references/adapters/claude-code.md) · [Codex](references/adapters/codex.md) · [opencode](references/adapters/opencode.md) · [WorkBuddy](references/adapters/workbuddy.md)

## 一次任务怎么进行

| 通道 | 适用场景 | 过程产物 |
| --- | --- | --- |
| 🟢 轻量 | 单文件、改法明确的小改动 | 不创建流程文档 |
| 🟡 标准 | 目标清楚、涉及多个文件的改动 | `specs/<slug>/intent.md` |
| 🔴 完整 | 功能、架构、接口或需要分步评审的改动 | `specs/<slug>/` 下的 `spec.md`、`plan.md`、`tasks.md` |
| 📋 仅结论 | 需求是审查方案或给出判断 | 被审查的 spec 或 plan、评审结论 |

以接口分页为例，先确认默认页大小、排序和旧调用的兼容性，再把决定写进验收条件。实现任务逐项关联这些条件，并记录验证命令和输出。评审问题保留在产物里，未解决的阻断或重大问题会阻止收尾。

质量门禁按 `lint → format → type → test` 执行，命令由宿主项目定义。标准和完整通道在交付前重新跑全量门禁。某项门禁不适用时，用 `GATE-NA(<gate>)` 在产物中说明原因和范围，并在任务证据中引用。 [流程细则](references/flow.md) · [能力契约](references/capability-contract.md)

## 仓库导航

| 路径 | 内容 |
| --- | --- |
| [`SKILL.md`](SKILL.md) | 技能入口，包括任务分类、按需加载规则和收尾要求 |
| [`references/adapters/`](references/adapters/) | 各宿主的能力映射、审批规则与适配器模板 |
| [`references/templates/`](references/templates/) | 意图、规格、计划、任务、角色派发与交付模板 |
| [`scripts/`](scripts/) | 产物校验、追溯视图、技能探测与发布打包 |
| [`specs/`](specs/) · [`fixtures/`](fixtures/) | 项目自身的任务产物和脚本验证用例 |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本发布记录 |

## 验证和打包

由仓库根目录运行以下命令，与发布工作流使用相同的静态检查和用例。

```bash
python -m pip install -r requirements-dev.txt
ruff check scripts/ --isolated --select E,F,W,UP,B,SIM,RUF --line-length 120
ruff format --check scripts/ --line-length 120
mypy --strict scripts/
python scripts/artifact-check.py --fixtures fixtures/
python scripts/artifact-check.py --migrate-fixtures fixtures/migrate/
python scripts/find-skill.py --fixtures fixtures/skills/
python scripts/artifact-check.py specs/
python scripts/build-dist.py
```

校验器会检查验收条件与任务是否闭合、勾选是否有可核查的证据、评审是否允许收尾，以及门禁豁免是否已声明。`python scripts/derive-report.py specs/<slug>` 可把单条任务链的追溯视图输出到终端。遗留门禁豁免可用 `python scripts/artifact-check.py --migrate specs/ --dry-run` 先预览。

打包器按白名单生成安装目录和可复现的 ZIP。推送 `main` 后，GitHub Actions 验证并上传 `harness-coding-main-<sha>.zip` 到 `latest` 预发布。正式版本在更新 `SKILL.md` 版本号和 `CHANGELOG.md` 后推送 `v*` 标签，由同一工作流上传 `harness-coding-v<version>.zip`。 [发布工作流](.github/workflows/release.yml)
