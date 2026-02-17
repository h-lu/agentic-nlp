# Week 07：从 Demo 到生产 —— 评估、成本优化与部署

> "凡事预则立，不预则废。"
> — 《礼记·中庸》

2025 年，一家初创公司上线了基于 LLM 的智能客服系统。Demo 阶段效果惊艳：能回答问题、能查订单、能处理退款。但上线一周后，CTO 看着账单愣住了——单日 API 成本是预期的 5 倍。更糟的是，用户开始投诉"回答太慢""有时候会胡说八道"。

问题在哪？团队只关注了"能不能做"，没关注"做得怎么样、花多少成本、多快能响应"。他们没有评估体系，不知道成本从哪来；没有监控，不知道系统什么时候出错；没有优化策略，成本飙升也无从下手。

LLM 时代的应用开发，最大的坑不是"做不出来"，而是"能跑但不能上生产"。从 Demo 到 Production，你需要三件事：**评估**（知道系统好不好）、**优化**（让系统更好更便宜）、**部署**（让系统稳定可用）。这周我们来学这套"从 Demo 到生产"的完整流程。

---

## 前情提要

Week 06 你让 TextAgent 从"单兵作战"进化为"团队协作"——多智能体系统。一个 Agent 负责规划，一个负责执行，一个负责审核，还有一个负责检索。它们各司其职，协作完成复杂任务。

但你有没有想过：这个多 Agent 系统"真的比单 Agent 好"吗？它花了多少 Token？响应有多慢？如果成本超出预算，你该从哪里优化？如果要部署给用户使用，你该怎么监控它的运行状态？

这周我们会解决这些问题。你会搭建完整的评估流水线，实现成本监控与告警，部署一个可用的 API 服务，并添加可观测性——让系统从"能跑"变成"可上生产"。

---

## 本章学习目标

完成本周学习后，你将能够：
1. 设计 LLM 应用的评估体系，从效果、成本、延迟多维度评估系统
2. 实现成本优化策略，包括 Prompt 精简、模型选择、缓存策略
3. 部署 FastAPI 服务，支持流式输出和错误处理
4. 添加可观测性（Trace、日志、指标），监控生产环境的系统状态
5. 为 TextAgent 添加评估、优化和部署能力

<!--
================================================================================
【章节规划元数据】
================================================================================

贯穿案例：TextAgent 生产化改造

- 第 1 节（评估体系）：案例从"能跑的系统"变成"可评估的系统"——添加效果、成本、延迟的完整监控
- 第 2 节（成本优化）：从"不计成本"变成"成本可控"——通过模型选择、缓存、Prompt 优化降低成本
- 第 3 节（API 部署）：从"本地脚本"变成"Web 服务"——用 FastAPI 部署，支持流式输出
- 第 4 节（可观测性）：从"黑盒运行"变成"透明可追踪"——添加 Trace、日志、监控告警

最终成果：一个可部署、可监控、可优化的生产级 TextAgent 系统

认知负荷预算：
本周新概念（预算：4 个，"知识整合"阶段）：
1. LLM 应用评估（LLM Application Evaluation）— 从效果、成本、延迟多维度评估系统
2. 成本优化（Cost Optimization）— 通过模型选择、缓存、Prompt 精简降低成本
3. 可观测性（Observability）— Trace、日志、指标的全面监控
4. 部署实践（Deployment Practices）— FastAPI 服务、容器化、监控告警

结论：在预算内（4 个 = 上限 4 个）

循环角色出场规划：
- 小北（第 1 节）：发现系统成本超支，引出评估的重要性
- 老潘（第 2 节）：分享"生产环境中我们怎么降成本"的实战经验
- 阿码（第 3 节）：在部署 API 时遇到"流式输出怎么处理"的问题
- 老潘（第 4 节）：点评"没有可观测性的系统就是盲开"

回顾桥设计（至少 3 个，来自前 4 周）：
- [RAG 评估]（来自 week_04）：在第 1 节，从 RAGAS 评估扩展到完整的应用评估体系
- [Human-in-the-Loop]（来自 week_06）：在第 2 节，讨论人工审核对成本的影响
- [多智能体系统]（来自 week_06）：在第 1 节，评估多 Agent vs 单 Agent 的成本和效果
- [Prompt 设计原则]（来自 week_02）：在第 2 节，通过 Prompt 精简来优化成本
- [Token 与成本]（来自 week_01）：在第 1 节，回顾 Token 计价机制，作为成本优化的基础

AI 小专栏规划：
- 第 1 个（第 1-2 节之间）：LLM 应用的成本陷阱 — 2025-2026 年企业实践中的成本超支案例
- 第 2 个（第 3-4 节之间）：可观测性工具爆发 — LangSmith、Arize、Weights & Biases 谁主沉浮

TextAgent 本周推进：
- 上周状态：TextAgent 是多智能体系统，有规划者、执行者、审核者、检索者四个 Agent
- 本周改进：
  1. 添加评估模块（效果、成本、延迟的完整监控）
  2. 实现成本优化策略（模型选择、缓存、Prompt 优化）
  3. 部署 FastAPI 服务（支持流式输出、错误处理）
  4. 集成可观测性（Trace、日志、监控告警）
- 涉及的本周概念：LLM 应用评估、成本优化、部署实践、可观测性
- 建议示例文件：examples/07_textagent_production.py

================================================================================
-->

---

## 1. 你能证明它真的好吗？—— LLM 应用评估体系

小北上周刚实现了多 Agent 系统，兴奋地让老板试用。老板问了两个问题：

1. "这比原来的单 Agent 好多少？"
2. "成本增加了多少？"

小北愣住了——他只能回答"它能规划、能协作、能检索"，但说不出"好多少"和"贵多少"。更糟的是，财务部门随后发来邮件：API 成本是以前的三倍。

这是一个真实发生的故事。2025 年，多家企业在上线 LLM 应用后才发现成本远超预期——原因很相似：**只关注"能做"，不关注"做得怎么样"**。你有一个能跑的系统，但无法证明它"比旧方案好"，也不知道"成本花在哪"。

### 先算账，再谈效果

老潘看到小北的困境，说的第一句话不是"优化代码"，而是：**"先算账，再谈效果。"**

他说这话的意思是：在证明"系统好不好"之前，你得先知道"系统花了多少"。多 Agent 系统的陷阱在于——你以为是"一次调用"，实际上是"规划者调一次、执行者调一次、审核者调一次、检索者调一次"。

还记得 Week 01 我们学的 **Token 与成本** 吗？LLM 按 Token 计费，每次调用都花钱。所以评估的第一步不是"准确率是多少"，而是"谁在花钱"。

### 记录每一笔钱

老潘的建议简单直接：**生产环境中，我们每调用一次 LLM 都会记录五件事**——模型名称、输入 Token、输出 Token、延迟、Agent 名称。这样才能知道"钱花在哪"。

```python
# examples/01_cost_tracker.py
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMMetrics:
    """LLM 调用指标"""
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    timestamp: datetime
    agent_name: Optional[str] = None

class CostTracker:
    """成本追踪器"""

    # 2026 年 2 月的参考价格（每 1M Token）
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self):
        self.calls: List[LLMMetrics] = []

    def record_call(self, metrics: LLMMetrics):
        """记录一次 LLM 调用"""
        self.calls.append(metrics)

    def calculate_cost(self, metrics: LLMMetrics) -> float:
        """计算单次调用成本（美元）

        成本计算公式：
        Cost = (input_tokens × input_price / 1,000,000) + (output_tokens × output_price / 1,000,000)

        例如：GPT-4o 输入 1000 Token，输出 500 Token：
        Cost = (1000 × $2.50 / 1M) + (500 × $10.00 / 1M) = $0.0025 + $0.005 = $0.0075
        """
        pricing = self.PRICING.get(metrics.model, {})
        input_cost = metrics.input_tokens * pricing.get("input", 0) / 1_000_000
        output_cost = metrics.output_tokens * pricing.get("output", 0) / 1_000_000
        return input_cost + output_cost

    def get_summary(self) -> Dict:
        """获取成本汇总"""
        total_cost = sum(self.calculate_cost(m) for m in self.calls)
        total_tokens = sum(m.input_tokens + m.output_tokens for m in self.calls)

        # 按 Agent 分组——这是关键！
        by_agent = {}
        for m in self.calls:
            agent = m.agent_name or "unknown"
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "cost": 0}
            by_agent[agent]["calls"] += 1
            by_agent[agent]["cost"] += self.calculate_cost(m)

        return {
            "total_calls": len(self.calls),
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "cost_by_agent": by_agent,
            "avg_latency_ms": sum(m.latency_ms for m in self.calls) / len(self.calls) if self.calls else 0
        }
```

这个 `CostTracker` 的关键在于 `agent_name` 字段——它让你能回答"哪个 Agent 最烧钱"这个问题。运行一周后，你可能会惊讶地发现：**审核者 Agent 花的钱比规划者还多**，因为它每次都要重新读一遍完整的计划。这就是"算账"的价值——发现意料之外的问题。

### 从 RAG 评估到完整评估

还记得 Week 04 我们学的 **RAG 评估** 吗？RAGAS 框架给了我们忠实度（Faithfulness）、答案相关性（Answer Relevancy）、上下文精确度（Context Precision）等指标。当时你可能觉得"这些指标只针对 RAG"，但其实它们适用于任何 LLM 应用。

现在我们把评估范围从"检索+生成"扩展到"完整的工作流"：

```python
# examples/01_evaluation.py
from typing import List, Dict
from textagent.evaluation.metrics import calculate_faithfulness, calculate_relevancy

class LLMEvaluator:
    """LLM 应用评估器"""

    def __init__(self, llm_client):
        self.llm = llm_client

    def evaluate_batch(self, test_cases: List[Dict]) -> Dict:
        """批量评估测试用例

        Args:
            test_cases: [
                {"query": "用户问题", "expected": "期望答案", "context": "检索到的上下文"},
                ...
            ]
        """
        results = []

        for case in test_cases:
            # 运行系统
            actual_output = self._run_system(case["query"])

            # 计算指标——用 LLM 作为评判者
            faithfulness = calculate_faithfulness(
                actual_output,
                case.get("context", ""),
                self.llm
            )
            relevancy = calculate_relevancy(
                case["query"],
                actual_output,
                self.llm
            )

            results.append({
                "query": case["query"],
                "expected": case["expected"],
                "actual": actual_output,
                "faithfulness": faithfulness,
                "relevancy": relevancy
            })

        # 汇总
        return {
            "num_cases": len(results),
            "avg_faithfulness": sum(r["faithfulness"] for r in results) / len(results),
            "avg_relevancy": sum(r["relevancy"] for r in results) / len(results),
            "details": results
        }
```

阿码举手："等等，用 LLM 评估 LLM？这靠谱吗？"

这是个好问题。Week 04 我们就讨论过——**LLM-as-Judge 不是完美的，但它足够一致**。只要评估标准固定，用同一个 LLM 评估不同系统，结果是可比较的。关键不是"绝对分数"，而是"相对差异"——系统 A 的忠实度比系统 B 高 0.1，这才是有价值的信号。

### 对比之后，真相浮现

现在你可以回答老板的问题了："多 Agent 系统真的比单 Agent 好"？

运行一周的评估数据后，小北得到了这张表：

| 系统 | 效果（忠实度） | 成本（每次请求） | 延迟（P95） |
|------|--------------|----------------|-----------|
| 单 Agent | 0.75 | $0.02 | 2.5s |
| 多 Agent | 0.85 | $0.08 | 6.2s |

老潘看到这个结果，笑了笑："这是教科书级别的 trade-off。效果提升 13%，成本翻 4 倍，延迟 2.5 倍。老板会问你：**这 0.1 的忠实度提升值不值 4 倍的钱？**"

答案取决于场景。如果是"智能客服推荐产品"，0.1 的忠实度提升可能带来额外的转化率，值这个钱。如果是"内部工具查询文档"，老板可能会说"单 Agent 够用了"。

所以评估的价值不是证明"哪个绝对好"，而是给你**决策的依据**——你知道每个选择的代价和收益，然后根据业务需求做选择。

> **AI 时代小专栏：LLM 应用的成本陷阱**
>
> 2025 年，多家企业在上线 LLM 应用后发现成本远超预期。公开报道显示，一家电商公司的智能客服系统上线一周后，API 成本是预期的 5 倍——原因很直接：多 Agent 系统每次调用都会触发多个 LLM 请求，而开发团队没有追踪成本。
>
> LangChain 和 LlamaIndex 在 2025 年都发布了"LLM 应用成本管理最佳实践"，核心建议一致：**从第一天就追踪成本**。不是"上线后再说"，而是在开发阶段就记录每个 LLM 调用的模型名称、Token 数、成本、Agent 名称。
>
> 另一个更常见的陷阱是"过度使用大模型"。企业实践显示，超过 60% 的任务可以用更小的模型完成——GPT-4o-mini 或 GPT-3.5 在简单任务上的效果接近 GPT-4，但成本只有 1/10。问题在于：开发时默认用 GPT-4，上线后才发现"用不起"。
>
> 2025-2026 年的案例还暴露了一个"沉默的成本杀手"：**缓存不足**。很多重复的查询（如"怎么退款""物流多久"）每次都重新调用 LLM。添加语义缓存后，某些场景下成本可降低 30-50%。
>
> 你刚学的 `CostTracker`——记录每次调用、按 Agent 分组、计算汇总——在 AI 时代不是"可选功能"，而是企业级应用的"标配"。没有它，你的系统可能"能用但用不起"。
>
> 参考（访问日期：2026-02-17）：
> - [LangChain - Tracing & Cost Management](https://python.langchain.com/docs/production_monitoring/tracing/)
> - [LlamaIndex - Cost & Token Usage Tracking](https://docs.llamaindex.ai/en/stable/optimizing/usage_tracking/)

---

## 2. 怎么让它更便宜？—— 成本优化策略

阿码看了上一节的成本报告，皱着眉头说："多 Agent 效果确实好，但成本是单 Agent 的 4 倍。老板肯定不会批准——有没有办法在不降低太多效果的前提下降低成本？"

老潘笑了："这个问题我们生产环境每天都在想。成本优化不是'不花钱'，而是'把钱花在刀刃上'。"

他把白板翻到新的一页，写下八个字：**简单任务用便宜方案，复杂任务才用贵的方案**。

### 不是所有任务都需要 GPT-4

2026 年的 LLM 市场已经很成熟了——不是所有任务都需要最强的模型。老潘给阿码画了一张对照表：

| 模型 | 能力 | 成本（每 1M Token） | 每次调用成本 | 适用场景 |
|------|------|-------------------|-------------|---------|
| GPT-4o | 最强 | $2.5 输入 / $10 输出 | ~$0.03 | 复杂推理、规划、审核 |
| GPT-4o-mini | 强 | $0.15 输入 / $0.60 输出 | ~$0.002 | 一般分析、抽取 |
| GPT-3.5-turbo | 中等 | $0.5 输入 / $1.5 输出 | ~$0.006 | 简单问答、分类 |

阿码的眼睛亮了："GPT-4o-mini 的成本只有 GPT-4 的 1/15？那为什么要用 GPT-4？"

老潘说："问得好。规则是：**按 Agent 职责选择模型**。"

```python
# examples/02_model_selection.py
from typing import Dict
import time
from datetime import datetime

class MultiAgentWithCostOptimization:
    """带成本优化的多 Agent 系统"""

    # 为每个 Agent 配置模型——这是成本优化的核心
    AGENT_MODELS = {
        "planner": "gpt-4o",        # 需要复杂推理，值得花钱
        "executor": "gpt-4o-mini",  # 简单工具调用，小模型够用
        "reviewer": "gpt-4o",       # 需要仔细检查，值得花钱
        "retriever": "gpt-4o-mini"  # 检索策略选择，小模型够用
    }

    def __init__(self, llm_client, cost_tracker):
        self.llm = llm_client
        self.cost_tracker = cost_tracker

    def call_agent(self, agent_name: str, prompt: str) -> str:
        """调用指定 Agent，使用优化的模型"""
        model = self.AGENT_MODELS.get(agent_name, "gpt-4o-mini")

        # 记录开始时间
        start_time = time.time()

        # 调用 LLM
        response = self.llm.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )

        # 计算延迟
        latency_ms = int((time.time() - start_time) * 1000)

        # 记录指标
        self.cost_tracker.record_call(LLMMetrics(
            model=model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            latency_ms=latency_ms,
            timestamp=datetime.now(),
            agent_name=agent_name
        ))

        return response.choices[0].message.content
```

老潘点评道："这个配置下，规划者和审核者用 GPT-4（因为需要复杂推理），执行者和检索者用 GPT-4o-mini（因为任务简单）。成本可以降低 40-50%，而效果几乎不变——这就是把钱花在刀刃上。"

### Prompt 越短越好？看情况

还记得 Week 02 我们学的 **Prompt 设计原则** 吗？好的 Prompt 应该清晰、一致、鲁棒。但还有一个当时没讲的原则：**简洁**。

阿码喜欢写"长 Prompt"——每个 Prompt 都有详细的角色设定、任务描述、三五个示例。这确实有效，Week 02 我们也鼓励你这么做。但当系统上线后，这些 Prompt 的成本就变得显眼了。

老潘的建议是：**区分"核心 Prompt"和"扩展 Prompt"**。

- 核心 Prompt：必不可少的内容（任务描述、输出格式）
- 扩展 Prompt：示例、详细说明、边缘情况处理

```python
# examples/02_prompt_optimization.py
class PromptOptimizer:
    """Prompt 优化器"""

    # 核心 Prompt——每次必发，精简到极致
    CORE_PROMPTS = {
        "planner": """分析任务并制定执行计划。

输出 JSON 格式：{{"subtasks": [{{"step": 1, "action": "...", "tool": "...", "params": {{}}}}]}}""",
        "executor": """执行工具调用。

工具列表：
- analyze_sentiment: 分析情感
- extract_keywords: 提取关键词
- count_word_freq: 统计词频

按工具定义执行。"""
    }

    # 扩展 Prompt——按需添加
    EXTENSION_PROMPTS = {
        "planner_examples": "\n\n示例：\n任务：分析产品反馈\n计划：...",
        "planner_edge_cases": "\n\n注意：如果任务不清晰，先请求澄清。"
    }

    def get_prompt(self, agent: str, use_extensions: bool = False) -> str:
        """获取优化的 Prompt"""
        prompt = self.CORE_PROMPTS[agent]

        if use_extensions:
            # 只在复杂任务时添加扩展内容
            if agent == "planner":
                prompt += self.EXTENSION_PROMPTS.get("planner_examples", "")
                prompt += self.EXTENSION_PROMPTS.get("planner_edge_cases", "")

        return prompt
```

小北问："那简单任务就不用示例了？"

老潘点头："对。简单任务用核心 Prompt 就够了，复杂任务再追加示例。这样能节省 20-30% 的 Token 成本。"

### 最便宜的计算是不计算

老潘说了一个反直觉的事实："生产环境中，30-50% 的查询是重复的——'怎么退款''物流多久''你们支持什么支付方式'……为什么要每次都调用 LLM？"

**缓存**（Caching）就是答案——它让相同的查询直接返回之前的结果，跳过 LLM 调用。

缓存有两个层次：

1. **精确缓存**：完全相同的输入 → 返回缓存的结果（用哈希判断）
2. **语义缓存**：语义相似的输入 → 返回缓存的结果（用向量相似度判断）

```python
# examples/02_caching.py
from typing import Optional
from hashlib import md5
import json

class SemanticCache:
    """语义缓存"""

    def __init__(self, vector_store, similarity_threshold: float = 0.95):
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold

    def get(self, query: str) -> Optional[str]:
        """从缓存获取结果"""
        # 检查是否有语义相似的查询
        similar = self.vector_store.search(query, top_k=1)

        if similar and similar[0]["score"] > self.similarity_threshold:
            # 返回缓存的结果
            return similar[0].get("response")

        return None

    def set(self, query: str, response: str):
        """存储到缓存"""
        # 将查询和响应一起存储
        self.vector_store.add(
            text=query,
            metadata={"response": response}
        )

# 使用缓存
class CachedLLMClient:
    """带缓存的 LLM 客户端"""

    def __init__(self, llm_client, cache: SemanticCache):
        self.llm = llm_client
        self.cache = cache

    def call(self, prompt: str, use_cache: bool = True) -> str:
        """调用 LLM，优先使用缓存"""
        if use_cache:
            cached = self.cache.get(prompt)
            if cached:
                return cached

        # 缓存未命中，调用 LLM
        response = self.llm.call(prompt)

        # 存储到缓存
        if use_cache:
            self.cache.set(prompt, response)

        return response
```

阿码问："那如果缓存的答案过时了怎么办？"

老潘说："好问题。所以缓存要设置 TTL（过期时间）。另外，有些场景不适合缓存——比如查询实时数据（'我的订单现在在哪'）。缓存的规则是：**通用知识可以缓存，个性化数据要谨慎**。"

### 优化之后，再看账单

经过以上三个优化（模型选择 + Prompt 精简 + 缓存），小北重新运行了评估：

| 指标 | 优化前 | 优化后 | 变化 |
|------|-------|-------|------|
| 成本/请求 | $0.08 | $0.035 | **-56%** |
| P95 延迟 | 6.2s | 4.1s | -34% |
| 忠实度 | 0.85 | 0.83 | -2% |

老潘拍着小北的肩膀说："看，成本降了一半多，效果只下降了 2%。这就是工程中的'甜点'——**用最小的质量损失换取最大的成本节省**。"

阿码若有所思："那如果老板要求忠实度不低于 0.85 呢？"

老潘笑了："那你就给他说——要达到 0.85，成本是 $0.08/请求；降到 0.83，成本是 $0.035/请求。让老板选。评估的价值就是让你能用数据说话，而不是凭感觉争论。"

---

## 3. 怎么让别人用它？—— 部署 FastAPI 服务

小北终于把 TextAgent 优化好了，成本降了一半，延迟也快了不少。他兴冲冲地去找老板演示，结果老板问了两个问题：

1. "这个在哪儿运行？"
2. "客服团队怎么用它？"

小北愣住了——现在 TextAgent 还是一个本地 Python 脚本，客服团队没法用。老潘走过来说："该部署了。你需要把它变成一个 API 服务，让任何人都可以通过 HTTP 请求调用。"

### 从脚本到服务

FastAPI 是现代、快速的 Python Web 框架，特别适合部署 LLM 应用——它支持异步、自动生成文档、类型验证。小北花了一下午把 TextAgent 改造成了 API 服务：

```python
# examples/04_fastapi_service.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import time
from datetime import datetime

app = FastAPI(title="TextAgent API", version="0.1.0")

# 请求/响应模型——Pydantic 自动做类型验证
class AnalysisRequest(BaseModel):
    """分析请求"""
    task: str
    enable_review: bool = False
    use_cache: bool = True

class StepResult(BaseModel):
    """执行步骤结果"""
    step: int
    action: str
    result: dict

class AnalysisResponse(BaseModel):
    """分析响应"""
    task: str
    plan: dict
    execution: List[StepResult]
    review: Optional[dict]
    cost_usd: float
    latency_ms: int

# 全局状态
textagent = None  # 由 startup 事件初始化

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """执行文本分析任务"""
    if textagent is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    start_time = time.time()

    try:
        # 运行 TextAgent
        result = textagent.run(
            task=request.task,
            enable_review=request.enable_review
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return AnalysisResponse(
            task=request.task,
            plan=result["plan"],
            execution=result["execution"]["results"],
            review=result.get("review"),
            cost_usd=textagent.cost_tracker.get_summary()["total_cost_usd"],
            latency_ms=latency_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查——Kubernetes 会定期调这个"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """获取指标——Prometheus 会定期抓取这个"""
    if textagent is None:
        return {"error": "Service not initialized"}

    return textagent.cost_tracker.get_summary()

# 启动时初始化
@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global textagent
    from textagent.multiagent import MultiAgentWorkflow
    from openai import OpenAI

    llm = OpenAI()
    textagent = MultiAgentWorkflow(llm)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

小北运行 `python server.py`，然后在浏览器打开 `http://localhost:8000/docs`——FastAPI 自动生成了 API 文档，他可以直接在网页上测试每个接口。

### 等待的烦恼

阿码试了一下 API，发现一个问题："用户每次请求都要等 6 秒才能看到结果，体验不好。能不能让它像 ChatGPT 那样'逐字输出'？"

这就是**流式输出**（Streaming）——让 LLM 逐 Token 返回内容，用户可以实时看到生成过程，感知延迟更低。

老潘说："流式输出还有一个隐藏的好处——**用户会觉得系统更快**。6 秒的等待如果能看到东西在动，感觉上会短很多。"

```python
# examples/03_streaming.py
from fastapi.responses import StreamingResponse
import json
import asyncio

@app.post("/analyze/stream")
async def analyze_stream(request: AnalysisRequest):
    """流式执行任务——用户可以实时看到进度"""

    async def generate():
        """生成流式响应"""
        try:
            # 阶段 1：规划
            plan = textagent.planner.create_plan(request.task)
            yield f"data: {json.dumps({'stage': 'plan', 'data': plan})}\n\n"

            # 阶段 2：执行——逐步骤返回
            for step_result in textagent.executor.execute_plan_iter(plan):
                yield f"data: {json.dumps({'stage': 'execution', 'data': step_result})}\n\n"

            # 阶段 3：审核
            if request.enable_review:
                review = textagent.reviewer.review_result(plan, step_result)
                yield f"data: {json.dumps({'stage': 'review', 'data': review})}\n\n"

            # 阶段 4：完成
            summary = textagent.cost_tracker.get_summary()
            yield f"data: {json.dumps({'stage': 'done', 'data': summary})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'stage': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
```

前端可以这样处理流式响应：

```javascript
const eventSource = new EventSource('/analyze/stream?task=分析这份数据');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.stage === 'plan') {
        console.log('计划已生成:', data.data);
    } else if (data.stage === 'execution') {
        console.log('执行步骤:', data.data);
    } else if (data.stage === 'done') {
        console.log('完成，成本:', data.data.total_cost_usd);
        eventSource.close();
    }
};
```

阿码问："这跟普通 API 有什么区别？"

老潘说："普通 API 是'等 6 秒，一次性返回所有结果'。流式输出是'等 0.5 秒看到计划，然后每秒看到一个新的执行步骤'。用户感知的延迟从 6 秒降到了 0.5 秒——这就是心理学。"

### 生产环境不会一帆风顺

小北的 API 上线第一天就遇到了三个问题：网络超时、API 限流、模型偶尔返回乱码。老潘看了日志，说："生产环境不会像你的开发环境那么顺。你需要做好错误处理和重试。"

**tenacity** 是一个专门做重试的库，它让代码不用写一堆 try-except：

```python
# examples/03_error_handling.py
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustLLMClient:
    """带重试和降级的 LLM 客户端"""

    @retry(
        stop=stop_after_attempt(3),      # 最多试 3 次
        wait=wait_exponential(multiplier=1, min=2, max=10)  # 指数退避：2s, 4s, 8s
    )
    def call_with_retry(self, model: str, messages: List[dict]) -> str:
        """带重试的调用"""
        try:
            response = self.llm.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content

        except RateLimitError:
            # 限流：降级到更小的模型
            if model == "gpt-4o":
                return self.call_with_retry("gpt-4o-mini", messages)
            raise

        except APITimeoutError:
            # 超时：返回缓存的结果或降级响应
            return self._get_fallback_response(messages)
```

阿码问："为什么要指数退避？不能每次间隔一样？"

老潘说："如果 API 限流是因为服务器过载，你每秒重试一次只会让问题更严重。指数退避给服务器'喘息'的时间——2 秒后重试，不行就 4 秒，再不行就 8 秒。大多数临时错误会在几次重试内解决。"

> **AI 时代小专栏：可观测性工具爆发**
>
> 2025-2026 年，LLM 应用的"可观测性"（Observability）工具市场快速爆发。LangSmith、Arize Phoenix、Weights & Biases、Helicone 等工具纷纷推出 LLM 应用监控平台。
>
> 核心功能趋同：**Trace（追踪）、成本监控、质量监控、调试工具**。Trace 记录每次 LLM 调用的完整链路——哪个 Agent、什么 Prompt、什么结果。成本监控追踪 Token 和费用。质量监控通过 LLM-as-Judge 自动评估输出质量。
>
> 差异化在于：LangSmith 与 LangChain 深度集成，开箱即用；Arize 强调"开源自托管"，适合对数据敏感的企业；Weights & Biases 专注实验追踪，适合研发团队。2026 年的趋势是"全栈可观测"——不仅监控 LLM 调用，还监控整个应用（数据库、缓存、API 延迟）。
>
> 企业实践中的建议是：**从第一天就接入可观测性工具**。它能帮你快速定位问题（"为什么成本突然飙升？""哪个 Agent 的 Prompt 最常出错"），也能支持持续优化（"A/B 测试不同模型的效果"）。
>
> 你刚学的 `CostTracker` 和 `TraceContext` 是"手工版"的可观测性——足以理解原理，但生产环境中建议使用 LangSmith 等工具，它们提供更强大的可视化、告警、调试能力。
>
> 参考（访问日期：2026-02-17）：
> - [LangSmith - LLM Application Observability](https://smith.langchain.com/)
> - [Arize Phoenix - Open Source LLM Observability](https://docs.arize.com/phoenix/)
> - [Weights & Biases - LLM Monitoring](https://wandb.ai/sweeps)

---

## 4. 怎么知道它在正常工作？—— 可观测性与监控

系统上线一周后，老潘问了小北一个让他冷汗直流的问题："现在有 100 个用户在用，你怎么知道系统有没有出问题？"

小北想了想："用户会投诉吧？"

老潘摇头："等用户投诉就晚了。你需要监控系统，在问题影响用户之前就发现并解决。"

他打开白板，写下三个词：**日志、指标、Trace**。这就是**可观测性**（Observability）的核心——通过这三样东西，你可以"看见"系统内部的状态，而不是等用户告诉你"出问题了"。

### 三个问题，三个答案

可观测性的三个支柱分别回答三个问题：

| 支柱 | 回答的问题 | 示例 |
|------|-----------|------|
| **日志** | 发生了什么？ | "Agent X 在 14:32 调用了 LLM，成本 $0.05，返回成功" |
| **指标** | 有多少？ | "过去 5 分钟每分钟 100 次请求，平均延迟 3s，错误率 0.5%" |
| **Trace** | 为什么这样？ | "请求 A → Agent B → LLM C → Agent D 的完整链路，耗时 6.2s" |

### 日志不是 print()

老潘说的第一件事是："生产环境的日志不是 `print()`，而是结构化的、可查询的记录。"

为什么？因为 `print()` 输出的东西你没法搜索、没法过滤、没法统计。结构化日志——把每条日志写成 JSON——你可以直接丢进 Elasticsearch 或者数据仓库，然后问"过去一周审核者 Agent 出错超过 3 次的请求有哪些"。

```python
# examples/04_logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, service_name: str):
        self.logger = logging.getLogger(service_name)
        self.service_name = service_name

    def log_llm_call(self, agent: str, model: str, prompt: str, response: str, tokens: dict, cost: float):
        """记录 LLM 调用"""
        self.logger.info("llm_call", extra={
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "llm_call",
            "agent": agent,
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "input_tokens": tokens.get("input"),
            "output_tokens": tokens.get("output"),
            "cost_usd": cost
        })

    def log_agent_execution(self, agent: str, action: str, status: str, details: dict):
        """记录 Agent 执行"""
        self.logger.info("agent_execution", extra={
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "agent_execution",
            "agent": agent,
            "action": action,
            "status": status,
            "details": details
        })
```

小北问："这跟 `print(f"Agent {agent} called {model}")` 有什么区别？"

老潘说："区别是一周后，你想知道'哪个 Agent 花钱最多'。用 print 你得去日志文件里 grep；用结构化日志，你直接写 SQL `SELECT agent, SUM(cost_usd) FROM logs GROUP BY agent`。"

### 指标让你一眼看穿

阿码问："日志很多，怎么快速知道'系统有没有问题'？"

老潘说："所以你需要指标——关键数字的汇总。日志是'发生了什么'，指标是'整体怎么样'。"

**Prometheus** 是工业标准的指标系统，它用四个核心类型覆盖所有场景：

```python
# examples/04_metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Counter：只增不减（请求总数、成本总额）
request_count = Counter('textagent_requests_total', 'Total requests', ['agent', 'status'])
llm_cost_total = Counter('textagent_llm_cost_usd_total', 'Total LLM cost', ['model'])

# Histogram：记录分布（延迟分布）
request_duration = Histogram('textagent_request_duration_seconds', 'Request duration')

# Gauge：可增可减（当前活跃请求数）
active_requests = Gauge('textagent_active_requests', 'Active requests')

class MetricsCollector:
    """指标收集器"""

    def record_request(self, agent: str, status: str, duration: float):
        """记录请求"""
        request_count.labels(agent=agent, status=status).inc()
        request_duration.observe(duration)

    def record_llm_cost(self, model: str, cost: float):
        """记录 LLM 成本"""
        llm_cost_total.labels(model=model).inc(cost)

    def export_metrics(self) -> bytes:
        """导出 Prometheus 格式的指标"""
        return generate_latest()

# FastAPI 集成
@app.get("/metrics")
async def metrics():
    """Prometheus 会定期抓取这个端点"""
    return Response(content=metrics_collector.export_metrics(), media_type="text/plain")
```

老潘说："有了指标，你可以配 Grafana 仪表盘，一眼看到'过去 5 分钟成本是否飙升''P95 延迟是否超过阈值'。这就是监控的基础。"

### Trace 让问题无处遁形

小北发现一个棘手的问题："用户投诉'回答错了'，但我们不知道是哪个 Agent 出的问题——是规划者的计划有问题？还是执行者理解错了？还是审核者漏掉了？"

老潘说："所以你需要 Trace——记录每个请求的完整链路。"

**Trace** 是分布式系统中的概念，它用"一个 Trace 包含多个 Span"的方式记录完整调用链。每个 Span 是一个操作的记录（开始时间、结束时间、元数据），Trace 把这些 Span 串起来。

```python
# examples/04_tracing.py
from contextlib import contextmanager
from typing import Dict, List
import uuid
import time

class TraceContext:
    """追踪上下文"""

    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: List[Dict] = []

    @contextmanager
    def span(self, name: str, **metadata):
        """创建一个 Span——用 with 语句自动计时"""
        span_id = str(uuid.uuid4())
        start_time = time.time()

        span = {
            "span_id": span_id,
            "name": name,
            "start_time": start_time,
            "metadata": metadata
        }

        try:
            yield span
        finally:
            span["end_time"] = time.time()
            span["duration_ms"] = int((span["end_time"] - span["start_time"]) * 1000)
            self.spans.append(span)

    def get_trace(self) -> Dict:
        """获取完整 Trace"""
        return {
            "trace_id": self.trace_id,
            "spans": self.spans,
            "total_duration_ms": sum(s["duration_ms"] for s in self.spans)
        }

# 使用
class TracedMultiAgentWorkflow:
    """带追踪的多 Agent 工作流"""

    def run(self, task: str) -> Dict:
        trace = TraceContext()

        with trace.span("plan", agent="planner", task=task):
            plan = self.planner.create_plan(task)

        with trace.span("execute", agent="executor", steps=len(plan.get("subtasks", []))):
            result = self.executor.execute_plan(plan)

        with trace.span("review", agent="reviewer"):
            review = self.reviewer.review_result(plan, result)

        # 存储 Trace（可发送到 LangSmith 等）
        self._store_trace(trace.get_trace())

        return {"plan": plan, "execution": result, "review": review}
```

有了 Trace，当用户投诉时，你可以直接查这个请求的 `trace_id`，看到完整的执行链路："规划花了 1.2 秒，执行花了 4.1 秒，审核花了 0.9 秒"。如果执行阶段某个步骤异常超时，你一眼就能看到。

老潘说："没有 Trace 的系统就是'盲开'——你不知道用户的问题出在哪，每次都是'猜测原因 → 修改代码 → 等待下一个问题'。有了 Trace，你可以直接定位问题。"

### 告警：问题自动找你

老潘的最后一条建议是："不仅要监控，还要告警——当指标异常时及时通知。"

为什么需要告警？因为你不能 24 小时盯着仪表盘。告警让问题自动找你。

```python
# examples/04_alerts.py
from dataclasses import dataclass
from typing import Callable, List
from datetime import datetime

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: Callable[[Dict], bool]
    message: str

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Dict] = []

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)

    def check(self, metrics: Dict):
        """检查所有规则"""
        for rule in self.rules:
            if rule.condition(metrics):
                self.alerts.append({
                    "rule": rule.name,
                    "message": rule.message,
                    "metrics": metrics,
                    "timestamp": datetime.now().isoformat()
                })
                # 这里可以发送邮件/短信/钉钉通知

# 示例规则
alert_manager = AlertManager()

# 规则 1：成本过高
alert_manager.add_rule(AlertRule(
    name="high_cost",
    condition=lambda m: m.get("hourly_cost_usd", 0) > 10,
    message="每小时成本超过 $10"
))

# 规则 2：延迟过高
alert_manager.add_rule(AlertRule(
    name="high_latency",
    condition=lambda m: m.get("p95_latency_ms", 0) > 5000,
    message="P95 延迟超过 5 秒"
))

# 规则 3：错误率过高
alert_manager.add_rule(AlertRule(
    name="high_error_rate",
    condition=lambda m: m.get("error_rate", 0) > 0.05,
    message="错误率超过 5%"
))
```

老潘看到这些，说："生产环境中，告警不要太多，否则会'狼来了'。3-5 个核心告警就够了：成本、延迟、错误率、质量下降。太多告警你会麻木，最后直接关掉通知。"

---

## TextAgent 进度

Week 06 结束时，TextAgent 是一个多智能体系统，能规划、执行、审核、检索。小北当时很兴奋，但现在回头看——它仍然是个"能跑但不能上生产"的脚本：没有评估体系（不知道效果好不好）、没有成本控制（不知道钱花在哪）、没有监控（出问题才知道）。

这周我们让 TextAgent 从"能跑"进化为"可上生产"。

### 本周改进

**1. 添加评估模块**

首先让 TextAgent "能度量自己"——添加评估功能，从效果、成本、延迟三个维度量化系统质量。

```python
# src/textagent/evaluation/evaluator.py
from textagent.evaluation.metrics import LLMMetrics, CostTracker, LLMEvaluator

class TextAgentEvaluator:
    """TextAgent 评估器"""

    def __init__(self, workflow):
        self.workflow = workflow
        self.cost_tracker = CostTracker()
        self.evaluator = LLMEvaluator(workflow.llm)

    def evaluate_system(self, test_cases: List[Dict]) -> Dict:
        """评估系统整体效果"""
        # 运行测试集
        results = self.evaluator.evaluate_batch(test_cases)

        # 成本报告
        cost_report = self.cost_tracker.get_summary()

        return {
            "quality": {
                "avg_faithfulness": results["avg_faithfulness"],
                "avg_relevancy": results["avg_relevancy"]
            },
            "cost": {
                "total_cost_usd": cost_report["total_cost_usd"],
                "cost_per_request": cost_report["total_cost_usd"] / len(test_cases),
                "cost_by_agent": cost_report["cost_by_agent"]
            },
            "performance": {
                "avg_latency_ms": cost_report["avg_latency_ms"]
            }
        }
```

现在 TextAgent 可以回答"我表现怎么样"这个问题了。

**2. 实现成本优化**

接下来让 TextAgent "更省钱"——通过模型选择、Prompt 精简、缓存降低成本。

```python
# src/textagent/optimization/cost_optimizer.py
from textagent.optimization.model_selector import ModelSelector
from textagent.optimization.prompt_optimizer import PromptOptimizer
from textagent.optimization.cache import SemanticCache

class CostOptimizedWorkflow:
    """成本优化的工作流"""

    def __init__(self, base_workflow):
        self.base_workflow = base_workflow

        # 优化组件
        self.model_selector = ModelSelector({
            "planner": "gpt-4o",
            "executor": "gpt-4o-mini",
            "reviewer": "gpt-4o",
            "retriever": "gpt-4o-mini"
        })
        self.prompt_optimizer = PromptOptimizer()
        self.cache = SemanticCache(vector_store)

    def run(self, task: str, enable_cache: bool = True) -> Dict:
        """运行优化后的工作流"""

        # 检查缓存
        if enable_cache:
            cached = self.cache.get(task)
            if cached:
                return cached

        # 使用优化的模型和 Prompt
        result = self.base_workflow.run(
            task,
            model_selector=self.model_selector,
            prompt_optimizer=self.prompt_optimizer
        )

        # 存储到缓存
        if enable_cache:
            self.cache.set(task, result)

        return result
```

**3. 部署 FastAPI 服务**

然后让 TextAgent "可以被别人用"——部署成 API 服务。

```python
# src/textagent/api/server.py
from fastapi import FastAPI
from textagent.api.models import AnalysisRequest, AnalysisResponse

app = FastAPI(title="TextAgent API")

# 全局工作流
workflow = None

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global workflow
    from textagent.multiagent import MultiAgentWorkflow
    from openai import OpenAI

    llm = OpenAI()
    workflow = MultiAgentWorkflow(llm)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """执行分析任务"""
    result = workflow.run(
        task=request.task,
        enable_review=request.enable_review
    )

    return AnalysisResponse(
        task=request.task,
        plan=result["plan"],
        execution=result["execution"]["results"],
        review=result.get("review"),
        cost_usd=workflow.cost_tracker.get_summary()["total_cost_usd"],
        latency_ms=result["latency_ms"]
    )
```

**4. 集成可观测性**

最后让 TextAgent "可以被看见"——添加日志、指标、Trace、告警。

```python
# src/textagent/observability/tracer.py
from textagent.observability.trace import TraceContext
from textagent.observability.logger import StructuredLogger
from textagent.observability.metrics import MetricsCollector
from textagent.observability.alerts import AlertManager

class ObservableWorkflow:
    """可观测的工作流"""

    def __init__(self, base_workflow):
        self.base_workflow = base_workflow
        self.logger = StructuredLogger("textagent")
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()

        # 添加告警规则
        self._setup_alerts()

    def run(self, task: str) -> Dict:
        """运行带追踪的工作流"""
        trace = TraceContext()

        try:
            with trace.span("workflow", task=task):
                result = self.base_workflow.run(task)

                # 记录指标
                self.metrics.record_request(
                    agent="workflow",
                    status="success",
                    duration=trace.get_trace()["total_duration_ms"] / 1000
                )

                # 记录日志
                self.logger.log_agent_execution(
                    agent="workflow",
                    action="run",
                    status="success",
                    details={"task": task, "cost": result.get("cost_usd")}
                )

                return result

        except Exception as e:
            self.metrics.record_request("workflow", "error", 0)
            self.logger.log_agent_execution("workflow", "run", "error", {"error": str(e)})
            raise

    def _setup_alerts(self):
        """设置告警规则"""
        # 在定时任务中检查指标，触发告警
        pass
```

### 在 report.md 中记录

```markdown
## Week 07：生产化改造

### 新增功能

1. 评估体系
   - 效果评估（忠实度、相关性）
   - 成本追踪（按 Agent 分组）
   - 延迟监控（平均、P95）

2. 成本优化
   - 模型选择（按 Agent 职责）
   - Prompt 精简（核心 vs 扩展）
   - 语义缓存（降低 30-50% 成本）

3. API 部署
   - FastAPI 服务
   - 流式输出支持
   - 错误处理与重试

4. 可观测性
   - 结构化日志
   - Prometheus 指标
   - Trace 追踪
   - 告警规则

### 评估结果

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 忠实度 | 0.85 | 0.83 | -2% |
| 成本/请求 | $0.08 | $0.035 | -56% |
| P95 延迟 | 6.2s | 4.1s | -34% |

### 下一步

- Week 08：端到端系统集成与终稿
```

TextAgent 现在是一个可部署、可监控、可优化的生产级系统了。它不仅能工作，而且你能知道它工作得怎么样、成本花在哪、有没有出问题。老潘看了会说："这才是能上生产的东西——不是能跑就行，而是可观测、可优化、可维护。"

---

## Git 本周要点

本周必会命令：
- git status
- git diff
- git add -A
- git commit -m "draft: ..."
- git log --oneline -n 10

常见坑：
- 只改文件不提交：下周找不到"当时怎么改的"。至少做 draft + verify 两次提交。

Pull Request (PR)：
- Gitea 上也叫 Pull Request，流程等价 GitHub：push 分支 -> 开 PR -> review -> merge。

---

## 本周小结（供下周参考）

这周你完成了 TextAgent 的"生产化改造"。首先是评估体系——从效果、成本、延迟三个维度量化系统质量。`CostTracker` 记录每次 LLM 调用的 Token 数、成本、Agent 名称，让你知道"钱花在哪"。`LLMEvaluator` 用忠实度、相关性等指标评估输出质量，这是 Week 04 RAG 评估的扩展。

然后是成本优化。老潘的实战经验很实用：按 Agent 职责选择模型（规划者和审核者用 GPT-4，执行者用 GPT-4o-mini），通过 Prompt 精简减少 Token 消耗，用缓存避免重复计算。优化后成本降低了 56%，效果只下降了 2%——这就是工程中的"权衡"。

接下来是部署。FastAPI 让 TextAgent 从本地脚本变成 Web 服务，任何人都可以通过 HTTP 调用。流式输出让用户实时看到生成过程，感知延迟更低。错误处理与重试（用 tenacity 库）让系统更健壮。

最后是可观测性。日志记录"发生了什么"，指标汇总"有多少"，Trace 追踪"完整链路"。告警规则在异常时及时通知。没有可观测性的系统就像"盲开"——不知道它有没有出问题，也不知道出问题在哪。

Week 06 你学了"让多个 Agent 协作"，这周你学了"让协作可评估、可优化、可监控"。TextAgent 现在是一个生产级的系统了——它不仅能工作，而且你能证明它工作得好、知道成本花在哪、能及时发现和解决问题。

但还有一个问题：TextAgent 的各个模块（LLM 调用、RAG、Agent、评估、部署）是分散的，没有整合成一个"端到端"的系统。下周我们会学习如何设计一个完整的、从用户输入到最终输出的系统，并收敛成终稿报告 `report.md`——这是 8 周学习的"大结局"。

---

## Definition of Done（学生自测清单）

学完本章后，你应该能够回答以下问题：

- [ ] 我能解释 LLM 应用评估的三个维度了吗？（Hint：效果、成本、延迟）
- [ ] 我能实现成本追踪了吗？（Hint：记录每次 LLM 调用的 Token 数和成本）
- [ ] 我知道如何优化成本了吗？（Hint：模型选择、Prompt 精简、缓存）
- [ ] 我能部署 FastAPI 服务了吗？（Hint：定义请求/响应模型、处理路由、返回 JSON）
- [ ] 我理解流式输出的价值了吗？（Hint：降低用户感知的延迟）
- [ ] 我能实现基本的可观测性了吗？（Hint：日志、指标、Trace）
- [ ] 我的 TextAgent 有评估和监控能力了吗？（Hint：试试运行测试集，看成本报告）

如果以上都打勾，恭喜你完成 Week 07！你现在已经掌握了让 LLM 应用从 Demo 到生产的核心技术。下周我们会学习如何设计一个完整的端到端系统，并收敛成终稿——这是 8 周学习的"大结局"。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考）
================================================================================

本章新术语（待合入 shared/glossary.yml）：
1. LLM 应用评估（LLM Application Evaluation）
2. 成本优化（Cost Optimization）
3. 可观测性（Observability）
4. 部署实践（Deployment Practices）

已有术语的本周强化（回顾桥设计目标）：
- RAG 评估（RAG Evaluation）— 来自 week_04
- Token 与成本（Token and Cost）— 来自 week_01
- Prompt 设计原则（Prompt Design Principles）— 来自 week_02
- 多智能体系统（Multi-Agent System）— 来自 week_06
- Human-in-the-Loop（Human-in-the-Loop）— 来自 week_06

================================================================================
-->
