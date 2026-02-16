# LLM 时代的文本智能与商务应用

一本面向"有 Python 基础的研究生"的现代文本应用教材，用 AI agent 团队协作的方式生产每一周的章包交付物。

## 这个项目是什么

8 周课程，分四个阶段，紧跟 2024-2025 顶级高校 NLP 课程演进：

| 阶段 | 周次 | 能力目标 |
|------|------|---------|
| LLM 基础 | 01–02 | LLM API 使用、Prompt Engineering、效果评估 |
| 知识增强 | 03–04 | RAG 原理、向量检索、混合检索、重排序 |
| 智能体 | 05–06 | Agent 设计、Function Calling、多智能体协作 |
| 应用落地 | 07–08 | 评估框架、成本优化、端到端系统部署 |

**核心理念**：从"训练模型"到"设计系统"的范式转变。

每周交付一个**章包**（正文 + 示例 + 作业 + 测试 + QA），由 9 个 AI agent 协作产出，经校验脚本和 hooks 自动把关。

详细大纲见 [`chapters/SYLLABUS.md`](chapters/SYLLABUS.md)，目录见 [`chapters/TOC.md`](chapters/TOC.md)。

## 与传统 NLP 课程的对比

| 维度 | 传统 NLP (2015-2022) | 本课程 (2024+) |
|------|---------------------|------------------|
| 核心 | Word2Vec、LSTM、主题模型 | Prompt Engineering、RAG、Agents |
| 方法 | 从头训练或微调 | API 调用 + LoRA/PEFT |
| 知识 | 训练数据中固化 | RAG 动态检索 |
| 任务 | 单一模型解决 | Agent 规划 + 工具调用 |
| 评估 | 准确率、F1 | 效果 + 成本 + 延迟 |

## 快速开始

```bash
# 1. 克隆并进入项目
git clone <repo-url> && cd text-agent-nlp

# 2. 一键环境搭建
make setup            # 创建 .venv 并安装依赖

# 3. 批量创建 8 周目录
make scaffold         # 从 TOC.md 读取标题，生成所有周的模板

# 4. 校验
make validate W=01    # 校验第 1 周（默认 release 模式）
make test W=01        # 跑第 1 周测试
make book-check       # 全书一致性检查
```

所有命令见 `make help`。

## 一周写作流程

在 Claude Code / Cursor 中打开本项目，使用 skill 命令：

```
/new-week 01 从文本处理到 LLM 时代   # 1. 创建新周
/draft-chapter week_01               # 2. 完整写作流水线
                                     #    规划 → 写正文 → 润色 → QA → 修订回路
/polish-week week_01                 # 3. 再次深度润色
/make-assignment week_01             # 4. 生成作业 + 评分标准
/qa-week week_01                     # 5. 质量检查
/release-week week_01                # 6. 发布
/qa-book --mode fast                 # 7. 跨周一致性检查
```

或者用 agent team 并行产出：`/team-week week_01`

## 目录结构

```
chapters/
  SYLLABUS.md              # 8 周教学大纲（含贯穿项目与 AI 协作框架）
  TOC.md                   # 目录
  week_XX/                 # 每周一个章包
    CHAPTER.md             #   正文
    ASSIGNMENT.md          #   作业
    RUBRIC.md              #   评分标准
    QA_REPORT.md           #   质量报告（阻塞项/建议项/评分）
    ANCHORS.yml            #   可验证断言
    TERMS.yml              #   本周新术语
    examples/              #   示例代码
    starter_code/          #   作业起始代码 + solution.py
    tests/                 #   pytest 用例

shared/
  style_guide.md           # 行文风格规范
  writing_exemplars.md     # 写作范例库
  glossary.yml             # 全书术语表
  concept_map.yml          # 概念图谱
  book_project.md          # 贯穿项目 TextAgent 设计

.claude/
  agents/                  # 9 个专职 Agent
  skills/                  # 10 个 Skill 命令
  hooks/                   # 自动校验
  settings.json            # Claude Code 项目配置

scripts/                   # 校验/构建脚本
Makefile                   # 快捷命令入口
```

## 课程特色

- **紧跟前沿**：参考 Stanford CS224N、Berkeley LLM Agents、CMU 11-766 等顶级课程
- **范式转变**：从传统 NLP 到 LLM-native 的完整路径
- **实用导向**：每个知识点都有可运行的代码和评估
- **贯穿项目**：8 周构建一个完整的 Agentic 文本分析系统
- **AI 协作**：教授如何在 AI 时代负责任地使用 AI

## 参考课程

- [Stanford CS224N](https://web.stanford.edu/class/cs224n/) - NLP with Deep Learning
- [Berkeley CS294/194-196](http://rdi.berkeley.edu/llm-agents/f24) - LLM Agents
- [CMU 11-766](http://cmu-llms.org/) - LLM Methods and Applications
- [Stanford CS329A](https://cs329a.stanford.edu/) - Self-Improving AI Agents
- [Johns Hopkins Agentic AI Certificate](https://online.lifelonglearning.jhu.edu/jhu-certificate-program-agentic-ai)
