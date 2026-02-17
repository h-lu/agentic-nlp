# Week 06：让智能体团队协作 —— 多智能体系统与 Agentic RAG

> "我们中没有一个人能像我们所有人加起来那么聪明。"
> — Ken Blanchard（管理学家，《一分钟经理人》作者）

2025 年中，一家电商平台上线了"智能客服系统"——单个 LLM Agent，能查订单、能退款、能推荐产品。上线当天，客服团队很高兴："终于不用重复回答'我的快递在哪'了。"

但一周后，问题出现了。

用户问："帮我退款，但我还想换个颜色。"

Agent 先处理了退款，然后发现订单已取消，无法"换颜色"。用户很生气："我都说了要先换货！"

客服主管看着后台日志，叹了口气："它就像个只会按顺序做事的实习生，不会'思考'整个流程。"

2025 年下半年，"多智能体系统"（Multi-Agent Systems）开始在企业应用中兴起。核心思想很简单：与其让一个 Agent 做所有事，不如让多个专业 Agent 协作——一个负责理解用户意图，一个负责查订单，一个负责处理退款，一个负责审核决策。每个 Agent 只做自己擅长的事，然后互相配合。这周我们来学这波浪潮的核心：让多个 LLM Agent 协作完成复杂任务。

---

## 前情提要

Week 05 你让 TextAgent 从"被动问答"进化为"主动执行"：它能调用工具、能规划步骤、能完成多步骤任务。但它仍然是"单兵作战"——所有决策都由一个 Agent 做，既负责规划又负责执行，既负责分析又负责总结。

这周我们要让它"组队"——多个 Agent 各司其职，一个负责规划，一个负责执行，一个负责审核。这就像从"一个人包揽所有事"到"团队协作"。

---

## 本章学习目标

完成本周学习后，你将能够：
1. 理解多智能体系统的架构模式，知道何时用单 Agent、何时用多 Agent
2. 设计角色分工（规划者-执行者-审核者），实现 Agent 协作流程
3. 理解 Agentic RAG 与传统 RAG 的区别，让 Agent 自主控制检索过程
4. 实现 Human-in-the-Loop 机制，在关键决策点引入人工审核
5. 为 TextAgent 添加多智能体能力和 Agentic RAG

<!--
================================================================================
【章节规划元数据】
================================================================================

贯穿案例：智能文档分析协作系统

- 第 1 节（多智能体架构）：案例从"单个 Agent 做所有事"变成"规划者-执行者-审核者"三角色系统
- 第 2 节（Agent 协作实现）：实现角色之间的通信和协作机制
- 第 3 节（Agentic RAG）：让 Agent 自主决定何时检索、检索什么、如何使用结果
- 第 4 节（Human-in-the-Loop）：在关键决策点添加人工审核和反馈机制

最终成果：一个能自主规划、协作执行、人工审核的多智能体文档分析系统

认知负荷预算：
本周新概念（预算：5 个，"抽取与发现"阶段）：
1. 多智能体系统（Multi-Agent System）— 多个 Agent 协作完成复杂任务
2. Agentic RAG — Agent 主动控制检索过程的 RAG 系统
3. Human-in-the-Loop — 人工介入的 AI 系统设计
4. Agent 框架（Agent Frameworks）— AutoGen、CrewAI、LangGraph 等
5. Agent 协作模式（Agent Collaboration Patterns）— 顺序、并行、层级

结论：在预算内（5 个 = 上限 5 个）

循环角色出场规划：
- 小北（第 1 节）：让单个 Agent 处理复杂任务时出错，引出多智能体的必要性
- 阿码（第 2 节）：追问"如果两个 Agent 的决策冲突怎么办？"
- 老潘（第 3 节）：点评"生产环境中，每个 Agent 的决策都要有审计日志"
- 小北（第 4 节）：在人工审核时发现 Agent 的错误决策，引出 Human-in-the-Loop 的价值

回顾桥设计（至少 3 个，来自前几周）：
- [Agent 架构]（来自 week_05）：在第 1 节，对比单 Agent 和多 Agent 的架构差异
- [ReAct 模式]（来自 week_05）：在第 2 节，多 Agent 协作本质上是多个 ReAct 循环的协调
- [RAG 架构]（来自 week_03）：在第 3 节，对比传统 RAG 和 Agentic RAG 的区别
- [Chain-of-Thought]（来自 week_02）：在第 1 节，多 Agent 的规划能力依赖 CoT
- [混合检索/重排序]（来自 week_04）：在第 3 节，Agentic RAG 可以自主决定使用哪种检索策略

AI 小专栏规划：
- 第 1 个（第 1-2 节之间）：多智能体框架的爆发 — AutoGen、CrewAI、LangGrid 谁主沉浮
- 第 2 个（第 3-4 节之间）：Agentic RAG 的企业实践 — 从"检索增强"到"智能检索"

TextAgent 本周推进：
- 上周状态：TextAgent 是单个 ReAct Agent，能调用工具、规划步骤
- 本周改进：
  1. 设计多智能体架构（规划者、执行者、审核者）
  2. 实现 Agent 之间的通信机制
  3. 集成 Agentic RAG（Agent 自主决定检索策略）
  4. 添加 Human-in-the-Loop 审核点
- 涉及的本周概念：多智能体系统、Agent 协作、Agentic RAG、Human-in-the-Loop
- 建议示例文件：examples/06_textagent_multiagent.py

================================================================================
-->

---

## 1. 一个人做不完所有事 —— 为什么要多智能体

小北上周刚实现了一个能分析客户反馈的 Agent，他很兴奋。于是当老板让他"分析这 100 份产品反馈，告诉我主要问题是什么，再给出改进建议"时，他毫不犹豫地打开 TextAgent，输入任务。

TextAgent 开始工作：
1. 调用词频统计工具
2. 调用情感分析工具
3. 调用关键词提取工具
4. 生成总结

看起来很完美，直到老板问："你的分析基于哪些文档？检索策略是什么？"

小北愣住了——他不知道。TextAgent 做了所有事，但没有"记录过程"，也没有"解释决策"。

更糟糕的是，当小北让 TextAgent "分析这 1000 份反馈"时，它开始混乱：先调用了词频统计，然后又调用了一次；先生成了总结，然后才开始分析情感。

"它在'走回头路'，"小北盯着执行日志，有点无奈，"就像一个人同时做十件事，最后什么都没做好。"

这其实不是 Agent "笨"，而是它的**认知负荷**太高了。所谓认知负荷，就是一个人（或 Agent）在同一时间需要处理的信息量和决策数量。当你同时开车、打电话、记笔记时，每件事都分走了你一部分注意力，结果哪样都做不好——这就是认知负荷超载。Agent 也一样：它既要理解任务、又要规划步骤、还要选择工具、还要执行调用、还要检查结果……当这些职责全部挤在一个"大脑"里，出错是必然的。

老潘走过来看了一眼，说："这就是单 Agent 的局限——它既要规划，又要执行，还要审核。当任务变复杂，它就会'超载'。"

### 单 Agent vs 多 Agent：本质区别

| 维度 | 单 Agent | 多 Agent |
|------|----------|----------|
| **决策模式** | 一个 Agent 做所有决策 | 多个 Agent 各司其职，分工决策 |
| **能力边界** | 受限于单个 LLM 的上下文 | 每个专注一个领域，整体能力更强 |
| **可追踪性** | 决策过程混在一起 | 每个 Agent 的决策独立可追溯 |
| **容错性** | 一个错误可能导致全盘失败 | 单个 Agent 错误可被其他 Agent 捕获 |
| **适用场景** | 简单任务、快速原型 | 复杂任务、需要专业分工 |

### Week 05 的回顾：单 Agent 的架构

还记得 Week 05 我们学的 **Agent 架构**吗？单个 Agent 有四大核心能力：感知、规划、执行、反思。

单 Agent 的问题在于：**这四种能力都挤在一个"大脑"里**。当任务简单时没问题，但当任务变复杂，这个"大脑"就会超载——它既要规划整体步骤，又要执行具体工具，还要检查结果是否正确。

你可能会想："那就换更强的模型呗？"但问题是，更强的模型也还是会超载——就像给一个累坏的实习生加更多活，不如多雇几个人分工。

多智能体系统的核心思想是：**把不同的能力分配给不同的 Agent**。

### 多智能体架构：角色分工

一个经典的多智能体架构是 **"规划者-执行者-审核者"**（Planner-Executor-Reviewer）：

```text
┌─────────────┐
│   用户任务   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  规划者（Planner）    │  ← 理解任务，制定计划
│  - 分析任务需求       │
│  - 分解为子任务       │
│  - 确定执行顺序       │
└──────┬──────────────┘
       │ 计划
       ▼
┌─────────────────────┐
│  执行者（Executor）   │  ← 执行具体工具调用
│  - 调用检索工具       │
│  - 调用分析工具       │
│  - 收集结果          │
└──────┬──────────────┘
       │ 结果
       ▼
┌─────────────────────┐
│  审核者（Reviewer）   │  ← 检查结果质量
│  - 验证结果完整性     │
│  - 检查逻辑一致性     │
│  - 给出最终答案       │
└─────────────────────┘
```

每个 Agent 只做自己擅长的事：
- **规划者**专注思考"怎么做"，不调用工具
- **执行者**专注"做事情"，不思考整体策略
- **审核者**专注"检查质量"，不参与执行

### Week 02 的回顾：Chain-of-Thought

还记得 Week 02 的 **Chain-of-Thought**（CoT）吗？CoT 让 LLM 展示推理过程："让我一步步思考"。

多智能体系统本质上是 **CoT 的分布式版本**：
- 单 Agent 的 CoT：一个 Agent 内部的推理步骤
- 多 Agent 的 CoT：多个 Agent 之间的协作步骤

区别在于：多 Agent 的每个步骤由不同的 Agent 执行，因此每一步都更专注、更专业。

> **AI 时代小专栏：多智能体框架的爆发 — AutoGen、CrewAI、LangGraph 谁主沉浮**
>
> 2024-2025 年，多智能体开发框架经历了爆发式增长。微软的 AutoGen 最早提出了"对话式协作"模式，让 Agent 通过自然语言对话完成任务。CrewAI 则借鉴了"角色扮演"思想，让开发者定义 Agent 的"角色、目标、背景故事"。LangChain 的 LangGraph 则用"图结构"定义 Agent 工作流，支持复杂的分支和循环。
>
> 2025-2026 年的主流实践是：**从简单开始，按需升级**。简单的"规划者-执行者"模式用原生 Function Calling 即可实现；复杂的"层级调度"或"动态工作流"才考虑框架。CrewAI 官方数据显示，其平台每月运行 4.5 亿次 agentic workflows，财富 500 强中 60% 在使用——但这不代表你需要立即上框架。
>
> 对你来说，这周的课后练习用原生 Python 实现"规划者-执行者"就够了。当你发现需要复杂的 Agent 协作、动态工作流编排、或者需要可视化调试时，再考虑框架。过早抽象会带来"调试地狱"——你不知道问题出在 Prompt、工具调用，还是框架的中间层。
>
> 参考（访问日期：2026-02-17）：
> - [AutoGen: Enabling Next-Gen LLM Applications](https://microsoft.github.io/autogen/)
> - [CrewAI: Framework for orchestrating role-playing AI agents](https://www.crewai.com/)
> - [LangGraph: Building Stateful Agents](https://langchain-ai.github.io/langgraph/)

---

## 2. 让 Agent 们对话 —— 协作机制实现

阿码盯着第 1 节的架构图，眉头紧锁。突然他举手："等等，这些 Agent 之间怎么'对话'？是用自然语言，还是用结构化消息？如果两个 Agent 的决策冲突怎么办？"

这是个好问题——而且是个"一旦选错，后期重构很痛苦"的问题。

### 通信方式：自然语言 vs 结构化消息

有两种主流方式：

| 方式 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **自然语言对话** | Agent 之间用自然语言消息交流 | 灵活、易调试、可解释性强 | 解析困难、可能误解 |
| **结构化消息** | Agent 之间用 JSON 等结构化数据交流 | 精确、可控、易验证 | 不够灵活、需要预定义格式 |

**AutoGen** 框架采用自然语言对话，每个 Agent 发送"消息"（message），其他 Agent 接收并回复。

**LangGraph** 框架采用结构化消息，Agent 之间传递"状态"（state），包含任务、结果、决策等。

这周我们用**结构化消息**——因为它更可控，也更容易调试。

### Agent 协作模式

确定通信方式后，另一个关键问题是：Agent 之间如何协作？有三种基本模式：

| 模式 | 描述 | 示例 |
|------|------|------|
| **顺序协作** | Agent 按顺序执行，前一个的输出是后一个的输入 | 规划者 → 执行者 → 审核者 |
| **并行协作** | 多个 Agent 同时执行不同任务，最后汇总 | 多个执行者同时分析不同文档 |
| **层级协作** | 高层 Agent 负责调度，低层 Agent 负责执行 | 管理者调度多个专业 Agent |

这周我们主要学**顺序协作**和**层级协作**。

### 实现"规划者-执行者"协作

让我们从最简单的两 Agent 协作开始：规划者制定计划，执行者按计划执行。

```python
# examples/02_planner_executor.py
from typing import Dict, List
from openai import OpenAI
import json

class PlannerAgent:
    """规划者 Agent：理解任务，制定计划"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def create_plan(self, task: str) -> Dict:
        """创建任务计划"""

        prompt = f"""你是一个任务规划专家。请分析以下任务，制定执行计划。

任务：{task}

请按以下 JSON 格式输出计划：

{{
  "task_understanding": "对任务的理解",
  "subtasks": [
    {{"step": 1, "action": "做什么", "tool": "工具名称", "params": {{"参数": "值"}}}},
    ...
  ],
  "expected_output": "期望的最终输出"
}}

计划："""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        # 解析 JSON（实际应用中需要更robust的解析）
        plan_text = response.choices[0].message.content
        return json.loads(plan_text)

class ExecutorAgent:
    """执行者 Agent：按计划执行工具调用"""

    def __init__(self, tools: Dict):
        self.tools = tools

    def execute_plan(self, plan: Dict) -> Dict:
        """执行计划"""

        results = []

        for subtask in plan["subtasks"]:
            tool_name = subtask["tool"]
            params = subtask["params"]

            # 执行工具
            if tool_name in self.tools:
                result = self.tools[tool_name](**params)
                results.append({
                    "step": subtask["step"],
                    "action": subtask["action"],
                    "result": result
                })
            else:
                results.append({
                    "step": subtask["step"],
                    "action": subtask["action"],
                    "error": f"Unknown tool: {tool_name}"
                })

        return {
            "plan": plan,
            "results": results,
            "status": "completed"
        }

# 工具定义
def search_documents(query: str, top_k: int = 5) -> Dict:
    """搜索文档（简化实现）"""
    return {"documents": [f"文档{i}: {query}相关内容" for i in range(top_k)]}

def analyze_sentiment(text: str) -> Dict:
    """分析情感（简化实现）"""
    return {"sentiment": "positive", "confidence": 0.8}

# 初始化
tools = {
    "search_documents": search_documents,
    "analyze_sentiment": analyze_sentiment
}

planner = PlannerAgent(OpenAI())
executor = ExecutorAgent(tools)

# 任务
task = "分析客户反馈中的主要问题，并给出改进建议"

# 执行
plan = planner.create_plan(task)
print("计划:", json.dumps(plan, ensure_ascii=False, indent=2))

result = executor.execute_plan(plan)
print("结果:", json.dumps(result, ensure_ascii=False, indent=2))
```

### Week 05 的回顾：ReAct 模式

还记得 Week 05 的 **ReAct 模式**吗？单 Agent 的 ReAct 循环是：Thought → Action → Observation。

多 Agent 的协作本质上是 **多个 ReAct 循环的协调**：
- 规划者的 ReAct：思考任务 → 生成计划 → 输出计划
- 执行者的 ReAct：接收计划 → 执行工具 → 输出结果
- 审核者的 ReAct：接收结果 → 检查质量 → 输出最终答案

每个 Agent 都有自己的 ReAct 循环，它们之间通过消息传递连接起来。

### 阿码的问题：决策冲突怎么办？

阿码问："如果两个 Agent 的决策冲突怎么办？比如规划者说'先检索'，但执行者觉得'先分析'更好？"

好问题。这涉及到 **Agent 之间的权力结构**：

| 结构 | 决策方式 | 示例 |
|------|----------|------|
| **层级制** | 高层 Agent 决策，低层 Agent 执行 | 规划者决策，执行者服从 |
| **民主制** | Agent 通过协商达成共识 | 两个 Agent 讨论，投票决定 |
| **仲裁制** | 第三方 Agent 仲裁冲突 | 审核者裁决规划者和执行者的分歧 |

这周我们用**层级制**——规划者负责制定计划，执行者按计划执行。如果执行者发现计划有问题，它可以向审核者报告，由审核者决定是否修改计划。

这里有一个反直觉的事实：**民主制听起来很美好，但在多 Agent 系统中往往是最差的选择**。为什么？因为 LLM 没有"真正的信念"——如果你让两个 Agent 讨论，它们很容易被对方的论点说服，最终可能达成一个"平庸的共识"而不是"最优的决策"。就像两个都没去过目的地的人争论走哪条路，最后可能选了一条最远的路。

层级制之所以有效，是因为它**明确了一个事实：有人负责决策，有人负责执行**。这不是"不民主"，而是"各司其职"。

### 添加审核者 Agent

现在让我们添加第三个 Agent：审核者（Reviewer）。

```python
class ReviewerAgent:
    """审核者 Agent：检查执行结果"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def review_result(self, plan: Dict, execution_result: Dict) -> Dict:
        """审核执行结果"""

        prompt = f"""你是一个质量审核专家。请审核以下任务执行结果。

原始计划：
{json.dumps(plan, ensure_ascii=False, indent=2)}

执行结果：
{json.dumps(execution_result, ensure_ascii=False, indent=2)}

请按以下 JSON 格式输出审核报告：

{{
  "status": "approved/needs_revision",
  "issues": ["问题1", "问题2"],
  "final_answer": "最终答案（如果 approved）",
  "revision_suggestions": ["修改建议1", "修改建议2"]
}}

审核报告："""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        review_text = response.choices[0].message.content
        return json.loads(review_text)
```

### 完整的三 Agent 协作流程

现在让我们把三个 Agent 连起来：

```python
def run_multi_agent_workflow(task: str) -> Dict:
    """运行完整的多 Agent 工作流"""

    # 1. 规划者制定计划
    print("\n=== 规划阶段 ===")
    plan = planner.create_plan(task)

    # 2. 执行者执行计划
    print("\n=== 执行阶段 ===")
    execution_result = executor.execute_plan(plan)

    # 3. 审核者检查结果
    print("\n=== 审核阶段 ===")
    review = reviewer.review_result(plan, execution_result)

    # 4. 如果需要修订，返回规划者重新规划
    if review["status"] == "needs_revision":
        print("\n=== 修订阶段 ===")
        revised_plan = planner.revise_plan(plan, review["revision_suggestions"])
        execution_result = executor.execute_plan(revised_plan)
        review = reviewer.review_result(revised_plan, execution_result)

    return {
        "task": task,
        "plan": plan,
        "execution": execution_result,
        "review": review
    }

# 测试
result = run_multi_agent_workflow("分析客户反馈并给出建议")
```

老潘看到这个实现会点评："多 Agent 的关键是**责任分离**——规划者不对执行负责，执行者不对整体策略负责，审核者不对具体操作负责。这样每个 Agent 都能专注自己的领域，整体系统也更可靠。"

---

## 3. 让 Agent 自主检索 —— Agentic RAG

小北突然想起一个问题："Week 03-04 我们学的 RAG，是'用户问题 → 检索 → 生成答案'。但多 Agent 系统里，谁来决定'什么时候检索、检索什么、怎么用结果'？"

这个问题直击痛点。传统 RAG 系统的检索逻辑是**硬编码**的：用户问问题，系统就检索一次，用固定的策略（向量或混合）。但如果问题需要分步解决呢？如果第一次检索结果不够好呢？如果不同子问题需要不同检索策略呢？

你还记得 Week 04 学的 **查询优化**吗？我们当时学习了如何重写查询、如何扩展关键词、如何用查询路由选择不同的检索器。但那些优化仍然是"静态的"——规则是预先写好的。

Agentic RAG 把检索策略的控制权从系统转移给了 Agent：**Agent 自己决定什么时候检索、用什么策略检索、检索结果够不够好**。

### 传统 RAG vs Agentic RAG

| 维度 | 传统 RAG（Week 03-04） | Agentic RAG |
|------|---------------------|-------------|
| **触发方式** | 用户问问题就检索 | Agent 自主决定是否检索 |
| **检索策略** | 固定（向量/混合） | 动态选择（向量/关键词/多轮） |
| **检索次数** | 一次检索 | 可能多轮检索 |
| **结果使用** | 直接用于生成 | Agent 可能拒绝或重新检索 |
| **控制权** | 系统控制 | Agent 控制 |

### Week 03 的回顾：RAG 架构

还记得 Week 03 的 **RAG 架构**吗？

```text
传统 RAG: 用户问题 → 检索 → LLM 生成答案
```

Agentic RAG 则是：

```text
Agentic RAG: 用户问题 → Agent 思考 → 决定是否检索 → (如需要) 检索 → Agent 评估 → 可能重新检索 → 生成答案
```

区别在于：**检索权从系统转移到了 Agent**。

### 实现一个检索 Agent

让我们先实现一个专门的"检索 Agent"（Retriever Agent），它由其他 Agent 调用，自主决定检索策略。

```python
# examples/03_agentic_rag.py
from typing import Dict, List, Optional
from openai import OpenAI
import json

class RetrieverAgent:
    """检索 Agent：自主决定检索策略"""

    def __init__(self, llm_client: OpenAI, vector_db, keyword_db):
        self.llm = llm_client
        self.vector_db = vector_db  # 向量数据库（Week 03）
        self.keyword_db = keyword_db  # 关键词数据库（Week 04）

    def retrieve(self, query: str, context: Optional[str] = None) -> Dict:
        """自主检索"""

        # 第一步：Agent 决定检索策略
        strategy = self._decide_strategy(query, context)

        # 第二步：按策略检索
        if strategy["method"] == "vector":
            results = self.vector_db.search(query, top_k=strategy["top_k"])
        elif strategy["method"] == "hybrid":
            results = self._hybrid_search(query, strategy["top_k"])
        elif strategy["method"] == "multi_round":
            results = self._multi_round_search(query, strategy)
        else:
            results = {"error": f"Unknown strategy: {strategy['method']}"}

        # 第三步：Agent 评估检索结果
        assessment = self._assess_results(query, results)

        # 第四步：如果结果不够好，可能重新检索
        if assessment["sufficient"]:
            return {"results": results, "strategy": strategy, "assessment": assessment}
        else:
            # 重新检索（用改进的查询）
            improved_query = strategy["improved_query"]
            return self.retrieve(improved_query, context)

    def _decide_strategy(self, query: str, context: Optional[str]) -> Dict:
        """决定检索策略"""

        prompt = f"""你是一个检索策略专家。请分析以下查询，决定最佳检索策略。

查询：{query}
上下文：{context or "无"}

请按以下 JSON 格式输出决策：

{{
  "method": "vector/hybrid/multi_round",
  "top_k": 数字,
  "reasoning": "选择该策略的原因",
  "improved_query": "改进后的查询（如需要）"
}}

决策："""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        decision_text = response.choices[0].message.content
        return json.loads(decision_text)

    def _hybrid_search(self, query: str, top_k: int) -> Dict:
        """混合检索（Week 04 的技术）"""
        # 向量检索 + 关键词检索 + RRF 融合
        vector_results = self.vector_db.search(query, top_k=top_k * 2)
        keyword_results = self.keyword_db.search(query, top_k=top_k * 2)
        return self._rrf_fusion(vector_results, keyword_results, top_k)

    def _multi_round_search(self, query: str, strategy: Dict) -> Dict:
        """多轮检索：先检索，再根据结果扩展查询"""
        first_results = self.vector_db.search(query, top_k=strategy["top_k"])
        # 从结果中提取关键词，扩展查询
        expanded_query = f"{query} {' '.join([r['keyword'] for r in first_results[:3]])}"
        return self.vector_db.search(expanded_query, top_k=strategy["top_k"])

    def _assess_results(self, query: str, results: Dict) -> Dict:
        """评估检索结果是否足够"""

        prompt = f"""请评估以下检索结果是否足够回答用户查询。

查询：{query}
结果：{json.dumps(results, ensure_ascii=False)[:500]}...

请按以下 JSON 格式输出评估：

{{
  "sufficient": true/false,
  "confidence": 数字(0-1),
  "missing_aspects": ["缺失的方面1", "缺失的方面2"]
}}

评估："""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        assessment_text = response.choices[0].message.content
        return json.loads(assessment_text)
```

### Week 04 的回顾：混合检索与重排序

还记得 Week 04 的 **混合检索**和**重排序**吗？

Agentic RAG 的优势在于：**Agent 可以自主决定是否使用这些技术**。

- 如果查询是精确匹配（如订单号），Agent 可能选择纯关键词检索
- 如果查询是语义相似（如"类似的产品"），Agent 可能选择向量检索
- 如果查询很复杂，Agent 可能选择混合检索 + 重排序

这种"动态策略选择"是传统 RAG 做不到的。

### 将检索 Agent 集成到多 Agent 系统

现在让我们把检索 Agent 加入到"规划者-执行者-审核者"系统中：

```python
class AgenticRAGWorkflow:
    """集成了 Agentic RAG 的多 Agent 工作流"""

    def __init__(self, planner: PlannerAgent, retriever: RetrieverAgent,
                 executor: ExecutorAgent, reviewer: ReviewerAgent):
        self.planner = planner
        self.retriever = retriever
        self.executor = executor
        self.reviewer = reviewer

    def run(self, task: str) -> Dict:
        """运行完整工作流"""

        # 1. 规划者制定计划
        plan = self.planner.create_plan(task)

        # 2. 执行者执行计划（遇到需要检索时，调用检索 Agent）
        execution_result = self.executor.execute_plan(
            plan,
            retriever=self.retriever
        )

        # 3. 审核者检查结果
        review = self.reviewer.review_result(plan, execution_result)

        return {
            "task": task,
            "plan": plan,
            "execution": execution_result,
            "review": review
        }
```

老潘看到这个实现会点评："Agentic RAG 的核心价值是**可解释性**——传统 RAG 你不知道'为什么检索这些文档'，Agentic RAG 每个检索决策都有明确的理由（strategy['reasoning']）。这对企业应用很重要，因为审计需要知道'系统为什么给出这个答案'。"

> **AI 时代小专栏：Agentic RAG 的企业实践 — 从"检索增强"到"智能检索"**
>
> 2024-2025 年，Agentic RAG 在企业应用中快速增长。传统 RAG 的痛点是"一刀切"——无论什么查询都用相同的检索策略，效果不稳定。Agentic RAG 让 LLM 自主决定检索策略，根据查询类型动态选择向量检索、关键词检索或多轮检索。
>
> LangChain 和 LlamaIndex 都在 2025 年发布了 Agentic RAG 的最佳实践指南。核心思想是：**检索权从系统转移到 Agent**。传统 RAG 中，检索逻辑是硬编码的；Agentic RAG 中，Agent 会思考"这个问题需要什么样的信息"，然后选择最合适的检索策略。
>
> 但这带来了一个新问题：**成本**。每次检索决策都需要 LLM 调用，复杂查询可能需要多轮检索。企业实践中的折中方案是"混合模式"：简单查询用传统 RAG（低成本），复杂查询用 Agentic RAG（高准确率）。
>
> 所以你刚学的 Agentic RAG 设计——让 Agent 决定策略、评估结果、必要时重新检索——在 AI 时代不是过度设计，而是企业级应用的标准实践。它让你在"效果"和"成本"之间有更细粒度的控制。
>
> 参考（访问日期：2026-02-17）：
> - [LangChain - Query Analysis / Agentic RAG](https://python.langchain.com/docs/use_cases/query_analysis/)
> - [LlamaIndex - Agentic RAG Examples](https://docs.llamaindex.ai/en/stable/examples/agentic_rag/)

---

## 4. 人必须在场 —— Human-in-the-Loop 机制

小北试了上面的多 Agent 系统，发现一个让人哭笑不得的问题。

"有一次规划者制定了一个明显错误的计划——它想用'情感分析'来统计词频，这完全是两回事。但执行者还是照做了，最后浪费了很多时间。"

"执行者为什么不指出问题？"小北不解地问。

阿码笑了："因为它是个'听话的执行者'——你让它执行计划，它就执行，不会质疑。"

老潘听到这里，接了一句："这就像实习生不敢纠正老板的错误指令。"

这就是问题所在：**Agent 可能会坚持错误的决策**，而且会"自信地犯错"——更糟糕的是，多 Agent 系统中错误会传播，规划者的错误会被执行者放大，最后审核者可能也"相信"了错误的结果。

解决方案：**Human-in-the-Loop**（人在回路）——在关键决策点引入人工审核。

### 什么是 Human-in-the-Loop？

Human-in-the-Loop 不是"人在旁边看着"，而是**在关键点让系统暂停，等待人工确认或修正**。

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| **主动审核** | 系统主动请求人工确认 | 高风险决策（退款、删除数据） |
| **被动审核** | 人工可以随时介入检查 | 长时间运行的任务 |
| **反馈学习** | 人工修正后，系统学习 | 持续优化的系统 |

### 设计审核点

多 Agent 系统中，哪里需要人工审核？

```text
┌─────────────┐
│   用户任务   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  规划者（Planner）    │
│  - 制定计划          │  ← 审核点 1：计划是否合理？
│  [人工确认]          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  执行者（Executor）   │
│  - 执行工具          │  ← 审核点 2：执行是否异常？
│  [异常时人工介入]     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  审核者（Reviewer）   │
│  - 检查结果          │  ← 审核点 3：结果是否可接受？
│  [人工确认最终答案]   │
└─────────────────────┘
```

### 实现人工审核机制

```python
# examples/04_human_in_the_loop.py
from typing import Dict, Optional

class HumanInTheLoopAgent:
    """带人工审核的 Agent"""

    def __init__(self, agent, require_approval: bool = True):
        self.agent = agent
        self.require_approval = require_approval

    def run_with_human_review(self, task: str, review_points: List[str]) -> Dict:
        """运行工作流，在指定审核点等待人工确认"""

        # 审核点 1：规划审核
        if "plan_review" in review_points:
            plan = self.agent.create_plan(task)

            if self.require_approval:
                approved, feedback = self._request_human_approval(
                    "计划审核",
                    plan
                )

                if not approved:
                    # 人工拒绝，重新规划
                    revised_task = f"{task}\n\n修改建议：{feedback}"
                    return self.run_with_human_review(revised_task, review_points)
        else:
            plan = self.agent.create_plan(task)

        # 审核点 2：执行监控
        execution_result = self.agent.execute_plan(plan)

        if "execution_monitor" in review_points:
            # 检查是否有异常
            if any("error" in step for step in execution_result["results"]):
                approved, feedback = self._request_human_approval(
                    "执行异常",
                    execution_result
                )

                if not approved:
                    # 人工中止或修改
                    return {"status": "aborted_by_human", "feedback": feedback}

        # 审核点 3：结果审核
        review = self.agent.review_result(plan, execution_result)

        if "result_review" in review_points:
            approved, feedback = self._request_human_approval(
                "结果审核",
                review
            )

            if not approved:
                # 人工拒绝结果，返回修订建议
                revised_plan = self.agent.revise_plan(plan, feedback)
                execution_result = self.agent.execute_plan(revised_plan)
                review = self.agent.review_result(revised_plan, execution_result)

        return {
            "task": task,
            "plan": plan,
            "execution": execution_result,
            "review": review
        }

    def _request_human_approval(self, stage: str, data: Dict) -> tuple:
        """请求人工批准（简化实现）"""

        print(f"\n{'='*40}")
        print(f"【人工审核 - {stage}】")
        print(f"{'='*40}")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"{'='*40}")

        # 在实际应用中，这里可能是 Web 界面或消息通知
        user_input = input("\n是否批准？(y/n/修改建议): ")

        if user_input.lower() == 'y':
            return True, None
        elif user_input.lower() == 'n':
            return False, "人工拒绝，请重新执行"
        else:
            return False, user_input  # 用户输入了修改建议
```

### Human-in-the-Loop 的最佳实践

老潘看到这个实现，给出了几条实战建议。

**第一，明确审核标准**。告诉人工"审核什么"，不是笼统地"看一下"。比如审核计划时，检查三点就够了：步骤是否完整、工具是否正确、顺序是否合理。审核结果时，检查：答案是否回答了问题、是否有遗漏、是否有矛盾。

**第二，提供完整上下文**。审核时展示完整的决策链——计划是什么、执行了什么、结果是什么。不要让人工自己去翻日志。

**第三，让操作尽可能简单**。一键批准/拒绝，不要让人工填复杂表单。如果需要修改，最好支持"修改建议"而不是让人工重写整个计划。

**第四，记录所有审核历史**。这不仅是为了审计，更是为了优化——你可以分析"哪些类型的决策经常被人工拒绝"，然后改进 Agent 的 Prompt。

**第五，渐进式自动化**。开始时多审核，随着系统成熟逐步减少审核点。最终目标是"只在高风险决策点审核"，而不是"每一步都审核"。

小北试了 Human-in-the-Loop 之后，说："虽然每次都要人工确认有点麻烦，但确实能避免很多错误。而且我发现，人工审核的记录可以用来改进 Agent 的 Prompt。"

没错。Human-in-the-Loop 不仅是"纠错"，也是"学习"——系统可以从人工审核中学习，逐渐减少需要人工介入的情况。

---

## TextAgent 进度

Week 05 结束时，TextAgent 是单个 ReAct Agent，能调用工具、规划步骤。但它仍然是"单兵作战"——既要规划又要执行，既要分析又要审核。

这周我们让 TextAgent 变成了一个"团队"：多个 Agent 各司其职，协作完成复杂任务。

### 本周改进

```python
# src/textagent/multiagent/__init__.py（新增）
from .planner import PlannerAgent
from .executor import ExecutorAgent
from .reviewer import ReviewerAgent
from .retriever import RetrieverAgent
from .workflow import MultiAgentWorkflow

__all__ = [
    "PlannerAgent",
    "ExecutorAgent",
    "ReviewerAgent",
    "RetrieverAgent",
    "MultiAgentWorkflow"
]
```

### 1. 实现规划者 Agent

```python
# src/textagent/multiagent/planner.py
from typing import Dict
from openai import OpenAI
import json

class PlannerAgent:
    """规划者 Agent：理解任务，制定计划"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def create_plan(self, task: str, context: Dict = None) -> Dict:
        """创建任务计划"""

        prompt = f"""你是一个文档分析任务规划专家。

任务：{task}
上下文：{json.dumps(context or {}, ensure_ascii=False)}

请分析任务并制定执行计划。计划包含：
1. 任务理解
2. 子任务分解（步骤、工具、参数）
3. 期望输出

按 JSON 格式输出计划。"""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        plan_text = response.choices[0].message.content
        return json.loads(plan_text)

    def revise_plan(self, original_plan: Dict, feedback: str) -> Dict:
        """根据反馈修订计划"""

        prompt = f"""原计划：
{json.dumps(original_plan, ensure_ascii=False, indent=2)}

反馈：
{feedback}

请根据反馈修订计划，输出新的 JSON 格式计划。"""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        plan_text = response.choices[0].message.content
        return json.loads(plan_text)
```

### 2. 实现执行者 Agent

```python
# src/textagent/multiagent/executor.py
from typing import Dict, Callable
from textagent.agent.tools import TextAnalyzerTools

class ExecutorAgent:
    """执行者 Agent：按计划执行工具调用"""

    def __init__(self, tools: Dict[str, Callable]):
        self.tools = tools

    def execute_plan(self, plan: Dict, retriever=None) -> Dict:
        """执行计划"""

        results = []

        for subtask in plan.get("subtasks", []):
            tool_name = subtask.get("tool")
            params = subtask.get("params", {})

            # 如果需要检索，调用检索 Agent
            if tool_name == "retrieve_documents" and retriever:
                result = retriever.retrieve(params.get("query", ""))
            elif tool_name in self.tools:
                result = self.tools[tool_name](**params)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            results.append({
                "step": subtask.get("step"),
                "action": subtask.get("action"),
                "result": result
            })

        return {
            "plan": plan,
            "results": results,
            "status": "completed"
        }
```

### 3. 实现审核者 Agent

```python
# src/textagent/multiagent/reviewer.py
from typing import Dict
from openai import OpenAI
import json

class ReviewerAgent:
    """审核者 Agent：检查执行结果"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def review_result(self, plan: Dict, execution_result: Dict) -> Dict:
        """审核执行结果"""

        prompt = f"""请审核以下任务执行结果。

计划：
{json.dumps(plan, ensure_ascii=False, indent=2)}

执行结果：
{json.dumps(execution_result, ensure_ascii=False, indent=2)}

请检查：
1. 任务是否完成
2. 结果是否完整
3. 逻辑是否一致

按 JSON 格式输出审核报告。"""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        review_text = response.choices[0].message.content
        return json.loads(review_text)
```

### 4. 实现检索 Agent

```python
# src/textagent/multiagent/retriever.py
from typing import Dict, Optional
from openai import OpenAI
import json

class RetrieverAgent:
    """检索 Agent：自主决定检索策略"""

    def __init__(self, llm_client: OpenAI, vector_store, keyword_index=None):
        self.llm = llm_client
        self.vector_store = vector_store
        self.keyword_index = keyword_index

    def retrieve(self, query: str, top_k: int = 5) -> Dict:
        """自主检索"""

        # 决定检索策略
        strategy = self._decide_strategy(query)

        # 按策略检索
        if strategy["method"] == "vector":
            results = self.vector_store.search(query, top_k=top_k)
        elif strategy["method"] == "hybrid" and self.keyword_index:
            results = self._hybrid_search(query, top_k)
        else:
            results = self.vector_store.search(query, top_k=top_k)

        # 评估结果
        assessment = self._assess_results(query, results)

        return {
            "query": query,
            "results": results,
            "strategy": strategy,
            "assessment": assessment
        }

    def _decide_strategy(self, query: str) -> Dict:
        """决定检索策略"""

        prompt = f"""分析查询，决定最佳检索策略。

查询：{query}

输出 JSON 格式决策：{{"method": "vector/hybrid", "reasoning": "原因"}}"""

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return json.loads(response.choices[0].message.content)

    def _hybrid_search(self, query: str, top_k: int) -> Dict:
        """混合检索"""
        # 实现向量 + 关键词检索 + RRF 融合
        vector_results = self.vector_store.search(query, top_k=top_k * 2)
        # ... 与关键词结果融合
        return vector_results  # 简化

    def _assess_results(self, query: str, results: Dict) -> Dict:
        """评估检索结果"""
        # 简化实现
        return {"sufficient": True, "confidence": 0.8}
```

### 5. 实现多 Agent 工作流

```python
# src/textagent/multiagent/workflow.py
from typing import Dict, List, Optional

class MultiAgentWorkflow:
    """多 Agent 工作流"""

    def __init__(
        self,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        reviewer: ReviewerAgent,
        retriever: Optional[RetrieverAgent] = None
    ):
        self.planner = planner
        self.executor = executor
        self.reviewer = reviewer
        self.retriever = retriever

    def run(
        self,
        task: str,
        context: Dict = None,
        enable_human_review: bool = False
    ) -> Dict:
        """运行完整工作流"""

        # 1. 规划
        plan = self.planner.create_plan(task, context)

        if enable_human_review:
            approved, feedback = self._human_review("计划", plan)
            if not approved:
                plan = self.planner.revise_plan(plan, feedback)

        # 2. 执行
        execution_result = self.executor.execute_plan(plan, self.retriever)

        if enable_human_review:
            if any("error" in r.get("result", {}) for r in execution_result.get("results", [])):
                approved, feedback = self._human_review("执行异常", execution_result)
                if not approved:
                    return {"status": "aborted", "feedback": feedback}

        # 3. 审核
        review = self.reviewer.review_result(plan, execution_result)

        if enable_human_review:
            if review.get("status") != "approved":
                approved, feedback = self._human_review("结果", review)
                if not approved:
                    plan = self.planner.revise_plan(plan, feedback)
                    execution_result = self.executor.execute_plan(plan, self.retriever)
                    review = self.reviewer.review_result(plan, execution_result)

        return {
            "task": task,
            "plan": plan,
            "execution": execution_result,
            "review": review
        }

    def _human_review(self, stage: str, data: Dict) -> tuple:
        """人工审核（简化实现）"""
        print(f"\n【人工审核 - {stage}】")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        user_input = input("\n批准？(y/n/修改): ")

        if user_input.lower() == 'y':
            return True, None
        else:
            return False, user_input or "人工拒绝"
```

### 6. 使用示例

```python
# examples/06_textagent_multiagent.py
from textagent.multiagent import (
    PlannerAgent, ExecutorAgent, ReviewerAgent,
    RetrieverAgent, MultiAgentWorkflow
)
from textagent.agent.tools import TextAnalyzerTools
from textagent.rag.vector_store import VectorStore
from openai import OpenAI

# 初始化
llm = OpenAI()
vector_store = VectorStore()  # Week 03 的向量存储

# 创建 Agent
planner = PlannerAgent(llm)
executor = ExecutorAgent({
    "analyze_sentiment": TextAnalyzerTools.analyze_sentiment,
    "extract_keywords": TextAnalyzerTools.extract_keywords,
    "count_word_freq": TextAnalyzerTools.count_word_freq,
})
reviewer = ReviewerAgent(llm)
retriever = RetrieverAgent(llm, vector_store)

# 创建工作流
workflow = MultiAgentWorkflow(planner, executor, reviewer, retriever)

# 任务
task = """
分析以下产品反馈，找出主要问题并给出改进建议：
1. "产品质量很好，但物流太慢了"
2. "客服态度很差，问题没解决"
3. "价格合理，物流也快"
"""

# 运行
result = workflow.run(
    task,
    enable_human_review=True  # 启用人工审核
)

print("\n最终结果：")
print(result["review"].get("final_answer", "任务完成"))
```

### 在 report.md 中记录

```markdown
## Week 06：多智能体协作

### 新增功能

1. 多智能体架构
   - 规划者 Agent（PlannerAgent）
   - 执行者 Agent（ExecutorAgent）
   - 审核者 Agent（ReviewerAgent）
   - 检索 Agent（RetrieverAgent）

2. Agentic RAG
   - Agent 自主决定检索策略
   - 动态选择向量/混合检索
   - 检索结果质量评估

3. Human-in-the-Loop
   - 计划审核
   - 执行监控
   - 结果审核

### 示例任务

任务："分析产品反馈并给出建议"

执行流程：
1. Planner 制定计划（3 步）
2. Executor 执行（调用检索、分析工具）
3. Retriever 自主检索（向量策略）
4. Reviewer 审核结果（approved）

### 下一步

- Week 07：评估与优化
```

TextAgent 现在不再是一个"单兵"，而是一个"团队"。每个 Agent 专注自己的领域，协作完成复杂任务。

---

## Git 本周要点

本周必会命令：
- `git log --graph --all` — 图形化查看分支历史
- `git blame file.py` — 查看每行代码的修改记录
- `git revert HEAD` — 撤销最近一次提交（创建新提交）
- `git cherry-pick <commit>` — 应用指定提交到当前分支

常见坑：
- **Agent 配置管理**：多 Agent 系统的配置（工具定义、Prompt 模板）应该单独管理，不要硬编码
- **执行历史追踪**：每个 Agent 的执行历史应该有独立的日志文件，方便调试
- **人工审核记录**：人工审核的决策应该记录到 `report.md`，这是审计的关键

推荐的 `.gitignore` 补充：

```text
# Week 06：多智能体
agent_configs/       # Agent 配置文件（可能含敏感信息）
execution_logs/      # Agent 执行日志
human_reviews/       # 人工审核记录
```

---

## 本周小结（供下周参考）

这周你让 TextAgent 从"单兵作战"进化为"团队协作"。

一切从那个电商客服的真实故事开始：单个 Agent 在复杂任务中会"超载"，它会走回头路、会坚持错误决策、会因为认知负荷过高而崩溃。多智能体系统的核心思想是**责任分离**——规划者专注思考"怎么做"，执行者专注"做事情"，审核者专注"检查质量"。

然后你实现了 Agent 之间的协作机制。Agent 之间用结构化消息通信，每个 Agent 都有自己的 ReAct 循环。阿码担心的"决策冲突"问题通过层级制解决——规划者决策，执行者服从，有问题由审核者裁决。

接下来是 Agentic RAG。你还记得 Week 03-04 的传统 RAG 吗？它是"被动检索"——用户问问题就检索一次。Agentic RAG 则是"主动检索"——Agent 自主决定检索策略。它会分析查询、选择向量或混合检索、评估结果质量、必要时重新检索。这正是 Week 04 查询优化的"动态版本"——优化规则从硬编码变成了 Agent 的实时决策。

最后是 Human-in-the-Loop。小北发现的"执行者盲目执行错误计划"问题提醒我们：Agent 会"自信地犯错"，而且错误会在多 Agent 系统中传播。解决方案是在关键点引入人工审核——计划审核、执行监控、结果审核。老潘的点评很到位：多 Agent 系统的关键是**可追溯性**——每个 Agent 的决策都要有日志，出了问题能找到责任方。

Week 05 你学了"让 LLM 做事"（单 Agent），这周你学了"让多个 LLM 协作"（多 Agent）。但多 Agent 系统也带来了新的问题：成本更高、延迟更大、调试更难。而且，你怎么知道你的多 Agent 系统"真的比单 Agent 好"？下周我们会学习如何评估和优化 LLM 应用——不仅看"效果"，还要看"成本"和"效率"。

---

## Definition of Done（学生自测清单）

学完本章后，你应该能够回答以下问题：

- [ ] 我能解释单 Agent 和多 Agent 的区别了吗？（Hint：一个包揽所有事 vs 分工协作）
- [ ] 我能设计"规划者-执行者-审核者"架构了吗？（Hint：每个 Agent 专注一个职责）
- [ ] 我能实现 Agent 之间的通信机制了吗？（Hint：结构化消息 + 循环调用）
- [ ] 我理解 Agentic RAG 与传统 RAG 的区别了吗？（Hint：Agent 自主控制检索过程）
- [ ] 我能实现一个检索 Agent 吗？（Hint：决策策略 → 执行检索 → 评估结果）
- [ ] 我知道何时需要 Human-in-the-Loop 了吗？（Hint：高风险决策、容易出错的场景）
- [ ] 我的 TextAgent 有多智能体能力了吗？（Hint：试试让它分析复杂文档）

如果以上都打勾，恭喜你完成 Week 06！你现在已经掌握让多个 LLM Agent 协作的核心技术。下周我们会学习如何评估和优化 LLM 应用——不仅让系统"能工作"，还要让它"高效、低成本、可监控"。这就像从"做 Demo"到"上生产"的关键一步。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考）】
================================================================================

本章新术语：
1. 多智能体系统（Multi-Agent System）
2. Agentic RAG（Agentic RAG）
3. Human-in-the-Loop（Human-in-the-Loop）
4. Agent 框架（Agent Frameworks）
5. Agent 协作模式（Agent Collaboration Patterns）

待合入 shared/glossary.yml

================================================================================
-->
