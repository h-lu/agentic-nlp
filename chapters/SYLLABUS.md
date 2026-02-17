# LLM 时代的文本智能与商务应用 — 8周教学大纲

> **核心理念**：在 LLM 时代，文本分析不再是"训练模型"，而是"设计系统"——用 Prompt、RAG 和 Agent 构建智能文本应用。
>
> **设计参考**：
> - 课程结构参考：
>   - [Stanford CS224N](https://web.stanford.edu/class/cs224n/)：NLP with Deep Learning（2024+ 重心转向 Transformer 和 LLM）
>   - [Berkeley CS294/194-196](http://rdi.berkeley.edu/llm-agents/f24)：Large Language Model Agents
>   - [CMU 11-766](http://cmu-llms.org/)：LLM Methods and Applications
>   - [Stanford CS329A](https://cs329a.stanford.edu/)：Self-Improving AI Agents
> - 行业参考：
>   - OpenAI API 最佳实践
>   - LangChain / LlamaIndex 应用框架
>   - 企业级 RAG 系统架构

---

## 课程定位

- **目标学生**：研究生，已具备基础 Python 能力，了解基本机器学习概念
- **课程时长**：8 周，每周 4 课时（每课时 45 分钟）
- **技术栈**：Python + OpenAI/本地 LLM API + LangChain/LlamaIndex + ChromaDB/FAISS + Pydantic
- **项目形式**：个人/小组 Agentic 文本分析系统 + 期末商业应用展示
- **核心理念**：从"训练模型"到"设计系统"的范式转变

---

## 设计理念：从传统 NLP 到 Agentic AI

### 范式转变

| 维度 | 传统 NLP (2015-2022) | LLM 时代 (2023+) |
|------|---------------------|------------------|
| **核心任务** | 训练分类器、NER、主题模型 | 设计 Prompt、构建 RAG、编排 Agent |
| **数据处理** | 分词、向量化、特征工程 | 文本切分、Embedding、检索优化 |
| **模型使用** | 从头训练或微调 | API 调用 + 少量微调（LoRA/PEFT） |
| **知识管理** | 训练数据中固化 | RAG 动态检索 + 知识库更新 |
| **复杂任务** | Pipeline 级联多个模型 | Agent 规划、工具调用、多步推理 |
| **评估方式** | 准确率、F1 等指标 | 端到端效果、成本、延迟、用户满意度 |

### 本课程的四个核心能力

1. **Prompt Engineering** — 让 LLM 准确理解需求
2. **RAG 构建** — 给 LLM 装上可更新的"外部记忆"
3. **Agent 设计** — 让 LLM 会规划、会调用工具
4. **系统化思维** — 评估、优化、部署企业级应用

---

## 8 周课程结构

| 阶段 | 周次 | 主题 | 能力目标 |
|------|------|------|----------|
| **阶段一：LLM 基础** | 01-02 | Prompt Engineering | LLM API 使用、提示设计、效果评估 |
| **阶段二：知识增强** | 03-04 | RAG 系统 | 向量检索、知识库构建、检索优化 |
| **阶段三：智能体** | 05-06 | LLM Agents | 工具调用、规划推理、多智能体 |
| **阶段四：应用落地** | 07-08 | 企业应用 | 评估框架、成本优化、端到端系统 |

---

## 阶段一：LLM 基础与 Prompt Engineering（Week 01-02）

### Week 01：从文本处理到 LLM 时代 —— 范式转变与 API 实践

**核心理念**：理解从"训练模型"到"调用 API"的范式转变，建立 LLM 时代的新思维

**核心内容**：
- **范式转变：传统 NLP vs LLM 时代**
  - 传统方法回顾：分词 → 向量化 → 训练 → 评估
  - LLM 方法：理解需求 → 设计 Prompt → 调用 API → 迭代优化
  - 何时用传统方法，何时用 LLM（成本、延迟、效果权衡）
- **LLM API 基础**
  - OpenAI API：Chat Completions、Embeddings
  - 国产 LLM API：智谱、通义、文心等
  - API 封装与错误处理（重试、限流、超时）
  - 成本计算：Token 计费与优化策略
- **文本处理的新方式**
  - 用 LLM 做文本分类、摘要、实体抽取
  - 结构化输出：JSON Mode、Function Calling
  - Pydantic 模型定义与验证
- **开发环境搭建**
  - Python 环境与依赖管理
  - API Key 安全管理
  - 日志与调试技巧

**实践**：
- 封装一个统一的 LLM Client 类
- 用 LLM 完成三种文本任务（分类、摘要、抽取）
- 比较不同 LLM 的效果和成本

**贯穿项目**：TextAgent 系统初始化 —— 搭建项目框架和 LLM 调用层

---

### Week 02：Prompt Engineering 实战 —— 让 LLM 听懂你的需求

**核心理念**：Prompt 是 LLM 时代的第一编程语言，好的 Prompt = 好的系统一半

**核心内容**：
- **Prompt 设计原则**
  - 清晰性：任务描述、输出格式、约束条件
  - 一致性：用词统一、格式统一
  - 鲁棒性：处理边界情况、异常输入
- **核心技巧**
  - Zero-shot vs Few-shot：什么时候需要示例
  - Chain-of-Thought（CoT）：让模型"思考"
  - Self-Consistency：多次采样取共识
  - 角色扮演：给模型一个"身份"
- **高级模式**
  - 思维树（Tree of Thoughts）
  - 自我反思（Self-Reflection）
  - 元提示（Meta-Prompting）
- **Prompt 模板管理**
  - 模板变量与参数化
  - 版本管理与 A/B 测试
  - Prompt 版本控制最佳实践
- **效果评估**
  - 人工评估 vs 自动评估
  - LLM-as-Judge：用 LLM 评估 LLM
  - 常用评估指标与数据集

**重点强调**：
- Prompt 不是"写一次就好"，需要持续迭代
- 不同的 LLM 可能需要不同的 Prompt
- 记录每次修改的原因和效果

**实践**：
- 设计一套文本分析的 Prompt 模板库
- 实现 Few-shot 示例的动态选择
- 搭建简单的 Prompt A/B 测试框架

**里程碑**：Prompt 模板库 + 效果评估报告

---

## 阶段二：知识增强与 RAG（Week 03-04）

### Week 03：RAG —— 让 LLM "查资料再回答"

**核心理念**：RAG 让 LLM 能够访问最新的、特定领域的知识，是企业应用的核心技术

**核心内容**：
- **为什么需要 RAG**
  - LLM 的知识截止问题
  - 幻觉（Hallucination）问题
  - 领域知识的注入
  - 知识的可更新性
- **RAG 架构解析**
  - 文档处理：加载、切分、元数据提取
  - Embedding：文本向量化
  - 向量数据库：存储与检索
  - 生成：检索结果与 Prompt 的融合
- **文本切分策略**
  - 固定长度切分
  - 语义切分（Sentence、Paragraph）
  - 递归切分
  - 切分粒度的权衡
- **Embedding 模型**
  - OpenAI Embeddings vs 开源模型
  - 中文 Embedding 模型选择
  - 多语言场景处理
- **向量数据库**
  - ChromaDB、FAISS、Milvus 对比
  - 索引类型与检索效率
  - 元数据过滤

**实践**：
- 构建一个文档知识库
- 实现基础的 RAG 检索流程
- 比较不同切分策略的效果

---

### Week 04：高级 RAG 与评估 —— 从能跑到精准

**核心理念**：基础 RAG 往往效果不佳，需要多种优化技术的组合

**核心内容**：
- **检索优化**
  - 查询重写（Query Rewriting）
  - 假设性文档嵌入（HyDE）
  - 查询扩展（Query Expansion）
  - 多查询融合（Multi-Query）
- **混合检索**
  - 向量检索 + 关键词检索（BM25）
  - 语义检索 + 精确匹配
  - 检索结果的融合策略（RRF）
- **重排序（Re-ranking）**
  - 为什么需要重排序
  - Cross-Encoder vs Bi-Encoder
  - 重排序模型选择
- **生成优化**
  - 上下文压缩（Context Compression）
  - 引用与溯源
  - 多轮对话中的 RAG
- **RAG 评估**
  - 检索评估：Recall@K、MRR、NDCG
  - 生成评估：忠实度、相关性、完整性
  - 端到端评估框架（RAGAS、TruLens）

**重点强调**：
- RAG 不是"搭建好就行"，需要持续调优
- 不同场景需要不同的优化组合
- 评估驱动优化

**实践**：
- 实现混合检索 + 重排序流程
- 搭建 RAG 评估流水线
- 针对业务数据调优

**里程碑**：完整的 RAG 系统 + 评估报告

---

## 阶段三：LLM Agents（Week 05-06）

### Week 05：让 LLM 不只是回答问题 —— 从 RAG 到 Agent

**核心理念**：Agent 让 LLM 从"回答问题"进化为"解决问题"

**核心内容**：
- **从 Chatbot 到 Agent**
  - Chatbot：回答用户问题
  - Agent：规划、执行、反思、迭代
  - Agent 的核心能力：感知、规划、执行、反思
- **工具调用（Tool Use / Function Calling）**
  - 工具的定义与描述
  - Function Calling API 使用
  - 自定义工具封装
  - 工具选择策略
- **ReAct 模式**
  - Reasoning + Acting 的循环
  - Thought → Action → Observation
  - 实现：LangChain ReAct Agent
- **规划（Planning）**
  - 任务分解（Task Decomposition）
  - 计划生成与执行
  - 动态调整与回溯
- **Agent 框架**
  - LangChain Agent
  - LlamaIndex Agent
  - 自定义 Agent 实现

**实践**：
- 封装一套文本分析工具（搜索、抽取、分析）
- 实现 ReAct 模式的 Agent
- 让 Agent 完成复杂的多步骤任务

---

### Week 06：让智能体团队协作 —— 多智能体系统与 Agentic RAG

**核心理念**：复杂任务需要多个专业 Agent 协作完成

**核心内容**：
- **多智能体架构**
  - 单 Agent 的局限性
  - 角色分工：规划者、执行者、审核者
  - 通信模式：顺序、并行、层级
- **Agent 协作模式**
  - 对话式协作（Chat）
  - 工作流编排（Workflow）
  - 竞争与共识
- **主流框架**
  - AutoGen：微软多智能体框架
  - CrewAI：角色扮演式协作
  - LangGraph：图结构工作流
- **Agentic RAG**
  - 传统 RAG vs Agentic RAG
  - 自主检索与多轮检索
  - 动态知识更新
- **人机协作（Human-in-the-Loop）**
  - 人工审核与干预点
  - 反馈收集与学习
  - 异常处理与回退

**重点强调**：
- 不是所有任务都需要多智能体
- 过度复杂的架构带来维护成本
- 从简单开始，按需扩展

**实践**：
- 设计一个多智能体文本分析系统
- 实现规划者-执行者-审核者架构
- 集成 RAG 能力

**里程碑**：多智能体文本分析系统

---

## 阶段四：商务应用与实战（Week 07-08）

### Week 07：从 Demo 到生产 —— 评估、成本优化与部署

**核心理念**：从 Demo 到 Production，需要系统性解决评估、成本和部署问题

**核心内容**：
- **LLM 应用评估**
  - 评估维度：效果、成本、延迟、稳定性
  - 评估数据集构建
  - 自动化评估流水线
  - 持续监控与告警
- **成本优化**
  - Token 优化：Prompt 精简、缓存、压缩
  - 模型选择：GPT-4 vs GPT-3.5 vs 开源模型
  - 混合策略：简单任务用小模型
  - 本地部署：开源 LLM（Llama、Qwen）
- **延迟优化**
  - 流式输出（Streaming）
  - 并行调用
  - 缓存策略
  - 模型量化与加速
- **部署实践**
  - API 服务封装（FastAPI）
  - 容器化部署（Docker）
  - 监控与日志
  - 安全与合规：数据隐私、内容审核
- **可观测性（Observability）**
  - Trace 追踪
  - 成本监控
  - 质量监控
  - 工具：LangSmith、Arize、Weights & Biases

**实践**：
- 搭建完整的评估流水线
- 实现成本监控与告警
- 部署一个可用的 API 服务

---

### Week 08：最后一公里 —— 从能跑到落地

**核心理念**：将所学整合为一个完整的、可落地的系统

**核心内容**：
- **系统设计**
  - 需求分析与技术选型
  - 架构设计：分层、模块化
  - 接口设计：API 设计、数据格式
- **典型应用场景**
  - 智能客服：多轮对话 + 知识库
  - 文档问答：RAG + 多文档推理
  - 舆情分析：实时监控 + 智能预警
  - 合同审核：信息抽取 + 风险识别
  - 报告生成：数据分析 + 自动写作
- **项目实战要点**
  - 从 Demo 到 Production 的坑
  - 用户反馈的收集与迭代
  - A/B 测试与灰度发布
  - 文档与知识传承
- **期末展示**
  - 技术方案说明（10 分钟）
  - 系统演示（5 分钟）
  - 业务价值与局限性（5 分钟）
  - Q&A（5 分钟）

**最终提交**：
1. 完整系统代码（可一键部署）
2. 技术文档（架构、API、部署指南）
3. 项目报告（`report.md` / `report.html`）
4. 演示材料（PPT/视频）
5. AI 协作日志（含审查清单）

---

## 贯穿项目：TextAgent —— Agentic 文本分析系统

### 项目设计理念

8 周课程围绕一个项目持续迭代，最终交付一个 **Agentic 文本分析系统**：

- **可扩展**：模块化设计，易于添加新能力
- **可评估**：完整的评估和监控体系
- **可部署**：生产级的 API 服务
- **可解释**：追踪每一步决策和推理

### 项目阶段（与周次对应）

| 阶段 | 周次 | TextAgent 里程碑 |
|------|------|------------------|
| 基础 | 01-02 | LLM 调用层 + Prompt 模板库 |
| 增强 | 03-04 | RAG 能力 + 知识库 |
| 智能 | 05-06 | Agent 能力 + 工具集成 + 多智能体 |
| 落地 | 07-08 | 评估体系 + 部署方案 + 文档 |

---

## 技术栈与工具

### 核心
- **LLM API**：OpenAI GPT-4/3.5、智谱 GLM-4、通义千问
- **框架**：LangChain、LlamaIndex
- **向量数据库**：ChromaDB、FAISS、Milvus

### 开发
- **语言**：Python 3.10+
- **API 框架**：FastAPI
- **验证**：Pydantic
- **测试**：pytest

### 部署
- **容器化**：Docker
- **监控**：LangSmith、Prometheus

---

## AI 协作框架

### 使用原则

1. **AI 辅助，人类决策**：AI 可以生成代码和方案，但架构决策由人做出
2. **理解优先，复制其次**：不理解的内容不要直接复制
3. **验证一切**：AI 生成的代码必须测试验证
4. **记录过程**：记录 AI 协作的过程和修改原因

### AI 审查清单

**代码质量**：
- [ ] 代码是否符合项目规范？
- [ ] 错误处理是否完整？
- [ ] 是否有安全风险（API Key 泄露等）？

**Prompt 质量**：
- [ ] Prompt 是否清晰无歧义？
- [ ] 是否处理了边界情况？
- [ ] 是否考虑了成本和延迟？

**系统设计**：
- [ ] 架构是否合理？
- [ ] 是否考虑了可扩展性？
- [ ] 评估方案是否完善？

---

## 评估体系

| 维度 | 占比 | 说明 |
|------|------|------|
| **周作业** | 30% | 8 周实践任务 |
| **贯穿项目** | 35% | TextAgent 系统完整度和质量 |
| **技术深度** | 20% | 对核心概念的理解和应用 |
| **期末展示** | 15% | 系统演示、问题回答、项目文档 |

---

## 参考资源

### 课程参考
- [Stanford CS224N](https://web.stanford.edu/class/cs224n/) - NLP with Deep Learning
- [Berkeley LLM Agents](http://rdi.berkeley.edu/llm-agents/f24) - LLM Agents Course
- [CMU 11-766](http://cmu-llms.org/) - LLM Methods and Applications
- [Stanford CS329A](https://cs329a.stanford.edu/) - Self-Improving AI Agents

### 框架文档
- [LangChain Documentation](https://python.langchain.com/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs/)

### 论文与博客
- "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
- "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)
- OpenAI Cookbook: Best Practices for Prompt Engineering

---

**最后更新**：2026-02-16
