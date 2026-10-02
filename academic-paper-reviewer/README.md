# Academic Paper Reviewer — Codex Plugin

证据驱动的中英文学术审稿插件。读取 PDF、Markdown、LaTeX 或 TXT，完成核心主张、
方法、统计、AI/ML 实验、写作、可复现性及内部一致性审查，并生成有原文证据的
peer review 和 meta-review。

## 安装

在支持插件的 Codex CLI 中执行：

```powershell
codex plugin marketplace add sunan404/Sunzus --ref main --sparse .agents/plugins --sparse academic-paper-reviewer
codex plugin add academic-paper-reviewer@sunzus
```

在 Codex 桌面端也可以添加 marketplace `sunan404/Sunzus`，选择 **Sunzus Plugins**，
安装 **Academic Paper Reviewer**。安装后开启新聊天；如果列表尚未刷新，重新打开应用。
GitHub marketplace 分发不代表插件已进入 OpenAI 官方公共插件目录。

首次使用需要 Python >=3.10 和内置 Skill 的 Python 依赖。插件提供所有脚本和
requirements 文件；安装插件不会自动执行 pip 或 hook。依赖准备好后无需 API key：

```powershell
# 从源码准备依赖：
python -m pip install -r academic-paper-reviewer/skills/academic-paper-reviewer/requirements-pdf.txt
```

可使用 [插件 ZIP](https://github.com/sunan404/Sunzus/releases/tag/academic-paper-reviewer-v0.2.0)
归档源码。插件包包含 `plugin.json`、Codex compatibility manifest 和完整 Skill。

## 使用

安装后直接在 Codex 中发送以下提示，并附上论文或填写完整文件路径：

```text
使用 Academic Paper Reviewer 插件审查 E:\审查\我的论文.pdf，用中文输出。
重点检查核心 claim、实验设计、统计单位、数字一致性和可复现性。
重要意见必须关联原文位置，区分论文事实、审稿人推断和修改建议。
将 paper_representation.json、review.json 和 review.md 保存到 E:\审查\我的论文-review。
```

插件提供 `academic-paper-reviewer` Skill，可从 Skill 选择器选择；新会话通常显示
插件命名空间 `academic-paper-reviewer:academic-paper-reviewer`。也可直接用上面的
自然语言请求，不需要手动运行解析和校验脚本。

最终主要阅读 `review.md`；JSON 文件保留证据台账、核心主张、模块意见和图关系。
补充材料应与正文一起提供，避免把材料未提供误认为作者未报告。

## 插件结构

```text
academic-paper-reviewer/
├── plugin.json                         Portable Agent Plugins manifest
├── .codex-plugin/plugin.json           Codex compatibility manifest
├── README.md / CHANGELOG.md
├── scripts/build_plugin.py             Offline bundle validator and ZIP packager
├── tests/test_plugin_package.py
└── skills/academic-paper-reviewer/
    ├── SKILL.md / README.md / agents/openai.yaml
    ├── requirements.txt / requirements-pdf.txt
    ├── references/                     Evidence rules and seven review modules
    ├── schemas/                        Paper, concern and review schemas
    ├── scripts/                        Intake, calculations, validation, renderer
    ├── tests/                          41 review pipeline tests and fixtures
    └── examples/                       Evidence-linked example review and JSON

Sunzus repository:
└── .agents/plugins/marketplace.json     Plugin catalog for GitHub/local installs
```

Portable manifest 使用 Agent Plugins 1.0.0 schema；OpenAI 展示信息位于
`extensions.com.openai`。compatibility manifest 保持相同名称、版本和展示信息，
并显式声明 `./skills/`。本插件由 Skill 和离线工具组成，不需要额外 MCP server、
远程服务账号或 hooks。[官方打包规范](https://developers.openai.com/plugins/build/plugins)。

完整工作流和算法边界见 [Skill README](skills/academic-paper-reviewer/README.md)。
可阅读 [完整示例审稿](skills/academic-paper-reviewer/examples/example_review.md)、
[结构化 Review](skills/academic-paper-reviewer/examples/example_review.json) 和
[测试结果](skills/academic-paper-reviewer/examples/test-results.md)。
插件打包与真实安装记录见 [TESTING.md](TESTING.md)。

## 验证和打包

```powershell
# 在插件根目录运行：
python -m unittest discover -s skills/academic-paper-reviewer/tests -v
python -m unittest discover -s tests -v
python scripts/build_plugin.py --marketplace ../.agents/plugins/marketplace.json --marketplace-root ..
python scripts/build_plugin.py --out dist/academic-paper-reviewer-plugin-0.2.0.zip
```

review tests 检查确定性约束和已保存的 Codex-authored fixture judgments；package
tests 检查完整组件、manifest 一致性、路径范围和归档内容。Codex CLI 安装与列表
检查作为真实 host 集成验证。未进行未见论文上的独立模型采样。

## 当前范围

保留现有七模块、claim–evidence graph、证据型 strengths、deduplicated meta-review
及全部确定性检查。没有证据时明确标记未建立；不输出论文质量分数或录用概率。
扫描 PDF 无 OCR；复杂表格/公式需视觉核对；LaTeX 不执行宏或 includes。
外部文献 novelty verification 和 citation semantic audit 仍是后续接口。
