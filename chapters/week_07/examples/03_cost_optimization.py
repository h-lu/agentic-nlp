#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：成本优化策略（Cost Optimization）

本例演示如何通过三种策略降低 LLM 应用的成本：
1. 模型选择：按任务复杂度选择合适的模型
2. Prompt 优化：区分核心 Prompt 和扩展 Prompt
3. 缓存策略：语义缓存避免重复计算

核心原则：
- 简单任务用便宜方案，复杂任务才用贵的方案
- Prompt 越短越好，但要在效果和成本间平衡
- 最便宜的计算是不计算（用缓存）

运行方式：python3 chapters/week_07/examples/03_cost_optimization.py
预期输出：展示优化前后的成本对比

依赖：
- pip install pydantic
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod


# ============================================================
# 配置
# ============================================================

# 模型定价（2026 年 2 月，每 1M Token，美元）
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00, "quality": "high"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "quality": "medium"},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "quality": "medium-low"},
}


# ============================================================
# 策略 1：模型选择
# ============================================================

class TaskComplexity(str, Enum):
    """任务复杂度"""
    SIMPLE = "simple"       # 简单：分类、抽取
    MEDIUM = "medium"       # 中等：一般分析
    COMPLEX = "complex"     # 复杂：推理、规划


class ModelSelector:
    """
    模型选择器：按任务复杂度选择合适的模型

    老潘的经验：
    "不是所有任务都需要 GPT-4。简单任务用 GPT-4o-mini，
    成本只有 1/15，效果几乎一样。这就是把钱花在刀刃上。"
    """

    # 为每种复杂度配置推荐的模型
    COMPLEXITY_MODEL_MAP = {
        TaskComplexity.SIMPLE: "gpt-4o-mini",
        TaskComplexity.MEDIUM: "gpt-4o-mini",
        TaskComplexity.COMPLEX: "gpt-4o",
    }

    # Agent 职责到复杂度的映射
    AGENT_COMPLEXITY = {
        "planner": TaskComplexity.COMPLEX,    # 需要复杂推理
        "executor": TaskComplexity.SIMPLE,    # 简单工具调用
        "reviewer": TaskComplexity.COMPLEX,   # 需要仔细检查
        "retriever": TaskComplexity.MEDIUM,   # 中等复杂度
    }

    @classmethod
    def select_model_for_agent(cls, agent_name: str) -> str:
        """为 Agent 选择模型"""
        complexity = cls.AGENT_COMPLEXITY.get(agent_name, TaskComplexity.MEDIUM)
        return cls.COMPLEXITY_MODEL_MAP[complexity]

    @classmethod
    def estimate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """估算成本"""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
        input_cost = input_tokens * pricing["input"] / 1_000_000
        output_cost = output_tokens * pricing["output"] / 1_000_000
        return input_cost + output_cost


# ============================================================
# 策略 2：Prompt 优化
# ============================================================

class PromptOptimizer:
    """
    Prompt 优化器：区分核心 Prompt 和扩展 Prompt

    Week 02 我们学过好的 Prompt 应该清晰、一致、鲁棒。
    但还有一个原则：**简洁**。

    核心思想：
    - 核心 Prompt：每次必发，精简到极致
    - 扩展 Prompt：按需添加（复杂任务、边缘情况）
    """

    # 核心 Prompt——每次必发
    CORE_PROMPTS = {
        "planner": """分析任务并制定执行计划。

输出 JSON 格式：{{"subtasks": [{{"step": 1, "action": "...", "tool": "..."}}]}}""",

        "executor": """执行工具调用。

工具列表：analyze_sentiment, extract_keywords, count_word_freq

按工具定义执行。""",

        "reviewer": """检查结果质量。

评估标准：完整性、逻辑一致性、准确性。

输出：approved / needs_revision""",
    }

    # 扩展 Prompt——按需添加
    EXTENSION_PROMPTS = {
        "planner_examples": """
示例：
任务：分析产品反馈
计划：[{"step": 1, "action": "情感分析", "tool": "analyze_sentiment"}]""",
        "planner_edge_cases": """
注意：如果任务不清晰，先请求澄清。""",
        "executor_details": """
详细说明：
- analyze_sentiment: 返回 {sentiment, confidence}
- extract_keywords: 返回 {keywords: []}
- count_word_freq: 返回 {word_counts: {}}""",
    }

    def get_prompt(
        self,
        agent: str,
        use_extensions: bool = False,
        task_complexity: TaskComplexity = TaskComplexity.MEDIUM
    ) -> str:
        """
        获取优化的 Prompt

        Args:
            agent: Agent 名称
            use_extensions: 是否使用扩展 Prompt
            task_complexity: 任务复杂度
        """
        prompt = self.CORE_PROMPTS.get(agent, "")

        # 只在复杂任务时添加扩展内容
        if use_extensions and task_complexity == TaskComplexity.COMPLEX:
            if agent == "planner":
                prompt += self.EXTENSION_PROMPTS.get("planner_examples", "")
                prompt += self.EXTENSION_PROMPTS.get("planner_edge_cases", "")
            elif agent == "executor":
                prompt += self.EXTENSION_PROMPTS.get("executor_details", "")

        return prompt

    def estimate_token_savings(
        self,
        agent: str,
        use_extensions: bool
    ) -> Dict[str, int]:
        """估算 Token 节省"""
        core_len = len(self.CORE_PROMPTS.get(agent, ""))
        full_len = core_len + sum(
            len(self.EXTENSION_PROMPTS.get(k, ""))
            for k in ["planner_examples", "planner_edge_cases", "executor_details"]
            if k.startswith(agent) or k == "executor_details"
        )

        if use_extensions:
            return {"core": core_len, "extension": full_len - core_len, "total": full_len}
        else:
            return {"core": core_len, "extension": 0, "total": core_len}


# ============================================================
# 策略 3：缓存
# ============================================================

@dataclass
class CacheEntry:
    """缓存条目"""
    query: str
    response: str
    timestamp: datetime
    hit_count: int = 0


class SemanticCache:
    """
    语义缓存：避免重复计算

    老潘说：
    "生产环境中，30-50% 的查询是重复的。
    '怎么退款''物流多久'……为什么要每次都调用 LLM？"

    缓存规则：
    - 通用知识可以缓存（政策、流程）
    - 个性化数据要谨慎（订单状态、账户信息）
    - 设置 TTL 避免过期数据
    """

    def __init__(self, similarity_threshold: float = 0.95):
        self.cache: Dict[str, CacheEntry] = {}
        self.similarity_threshold = similarity_threshold
        self.hits = 0
        self.misses = 0

    def get(self, query: str) -> Optional[str]:
        """从缓存获取"""
        # 简化实现：精确匹配（实际应使用向量相似度）
        if query in self.cache:
            entry = self.cache[query]
            entry.hit_count += 1
            self.hits += 1
            return entry.response

        self.misses += 1
        return None

    def set(self, query: str, response: str) -> None:
        """存储到缓存"""
        self.cache[query] = CacheEntry(
            query=query,
            response=response,
            timestamp=datetime.now()
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
            "size": len(self.cache)
        }


# ============================================================
# 成本优化器（整合三种策略）
# ============================================================

@dataclass
class OptimizationResult:
    """优化结果"""
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    cached: bool = False


class CostOptimizer:
    """成本优化器：整合所有优化策略"""

    def __init__(self):
        self.model_selector = ModelSelector()
        self.prompt_optimizer = PromptOptimizer()
        self.cache = SemanticCache()

    def optimize_call(
        self,
        agent: str,
        query: str,
        task_complexity: TaskComplexity = TaskComplexity.MEDIUM
    ) -> OptimizationResult:
        """
        执行优化的 LLM 调用

        优化步骤：
        1. 检查缓存
        2. 选择合适的模型
        3. 使用优化的 Prompt
        """
        # 1. 检查缓存
        cached_response = self.cache.get(query)
        if cached_response:
            return OptimizationResult(
                agent=agent,
                model="cached",
                input_tokens=0,
                output_tokens=len(cached_response.split()),
                cost=0.0,
                cached=True
            )

        # 2. 选择模型
        model = self.model_selector.select_model_for_agent(agent)

        # 3. 获取优化的 Prompt
        use_extensions = (task_complexity == TaskComplexity.COMPLEX)
        prompt = self.prompt_optimizer.get_prompt(agent, use_extensions, task_complexity)

        # 模拟调用
        input_tokens = len(prompt.split()) + len(query.split())
        output_tokens = 150  # 假设固定输出

        # 计算成本
        cost = self.model_selector.estimate_cost(model, input_tokens, output_tokens)

        # 模拟响应
        response = f"[{model}] 执行结果"

        # 存储到缓存
        self.cache.set(query, response)

        return OptimizationResult(
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            cached=False
        )


# ============================================================
# 对比：优化前后
# ============================================================

def compare_optimization():
    """对比优化前后的成本"""

    print("\n" + "=" * 70)
    print("优化前后对比")
    print("=" * 70)

    # 优化前：全部用 GPT-4，全部用完整 Prompt
    print("\n【优化前】全部用 GPT-4o，全部用完整 Prompt")

    baseline_cost = 0
    baseline_tokens = 0

    for agent in ["planner", "executor", "reviewer"]:
        # 假设每次调用
        input_tokens = 800  # 长 Prompt
        output_tokens = 200
        cost = ModelSelector.estimate_cost("gpt-4o", input_tokens, output_tokens)

        baseline_cost += cost
        baseline_tokens += input_tokens + output_tokens

        print(f"  {agent:12s}: 800 input + 200 output = ${cost:.6f}")

    print(f"\n  总成本: ${baseline_cost:.6f}")
    print(f"  总 Token: {baseline_tokens}")

    # 优化后：按需选择模型和 Prompt
    print("\n【优化后】按需选择模型和 Prompt")

    optimizer = CostOptimizer()
    optimized_cost = 0
    optimized_tokens = 0

    for agent in ["planner", "executor", "reviewer"]:
        result = optimizer.optimize_call(
            agent,
            "测试查询",
            TaskComplexity.COMPLEX if agent in ["planner", "reviewer"] else TaskComplexity.SIMPLE
        )

        optimized_cost += result.cost
        optimized_tokens += result.input_tokens + result.output_tokens

        cache_marker = " [缓存]" if result.cached else ""
        print(f"  {agent:12s}: {result.model:15s} "
              f"{result.input_tokens} input + {result.output_tokens} output"
              f" = ${result.cost:.6f}{cache_marker}")

    cache_stats = optimizer.cache.get_stats()
    print(f"\n  总成本: ${optimized_cost:.6f}")
    print(f"  总 Token: {optimized_tokens}")
    print(f"  缓存命中率: {cache_stats['hit_rate']:.1%}")

    # 计算节省
    savings = baseline_cost - optimized_cost
    savings_pct = (savings / baseline_cost) * 100

    print(f"\n💰 节省: ${savings:.6f} ({savings_pct:.1f}%)")


# ============================================================
# 反例：没有优化的问题
# ============================================================

def show_optimization_problems():
    """展示没有优化的后果"""
    print("\n" + "=" * 70)
    print("没有成本优化的后果")
    print("=" * 70)
    print("""
场景：一个电商智能客服系统

❌ 没有优化：
  - 所有查询都用 GPT-4o
  - Prompt 长达 2000 tokens（包含大量示例）
  - 每次都重新计算（无缓存）

结果：
  - 日均 10 万次查询
  - 每次 1000 input tokens + 200 output tokens
  - 日成本: 100K * (1000 * $2.5 + 200 * $10) / 1M = $450

✅ 优化后：
  - 简单查询用 GPT-4o-mini（60%）
  - Prompt 精简到 500 tokens
  - 添加缓存（40% 命中率）

结果：
  - 60K 次 * (500 * $0.15 + 200 * $0.60) / 1M = $9
  - 40K 次 * (500 * $2.5 + 200 * $10) / 1M = $120
  - 总成本: $129

节省: $321/天 = $9,630/月 = $117,165/年

老潘的点评：
"成本优化不是'不花钱'，而是'把钱花在刀刃上'。
简单任务用便宜方案，复杂任务才用贵的方案。
这就是工程中的 trade-off。"
    """)


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    """主入口"""

    print("=" * 70)
    print("成本优化策略演示")
    print("=" * 70)

    # 策略 1：模型选择
    print("\n" + "=" * 70)
    print("策略 1：模型选择（按 Agent 职责）")
    print("=" * 70)

    for agent in ["planner", "executor", "reviewer", "retriever"]:
        model = ModelSelector.select_model_for_agent(agent)
        complexity = ModelSelector.AGENT_COMPLEXITY[agent]
        cost = ModelSelector.estimate_cost(model, 500, 150)
        print(f"\n{agent:12s} ({complexity.value:8s}):")
        print(f"  → 推荐模型: {model}")
        print(f"  → 单次成本: ${cost:.6f}")

    # 策略 2：Prompt 优化
    print("\n" + "=" * 70)
    print("策略 2：Prompt 优化（核心 vs 扩展）")
    print("=" * 70)

    optimizer = PromptOptimizer()

    for agent in ["planner", "executor"]:
        simple = optimizer.estimate_token_savings(agent, use_extensions=False)
        complex_prompt = optimizer.estimate_token_savings(agent, use_extensions=True)

        print(f"\n{agent}:")
        print(f"  简单任务: {simple['core']} tokens (仅核心)")
        print(f"  复杂任务: {complex_prompt['total']} tokens (核心+扩展)")
        print(f"  节省: {complex_prompt['extension']} tokens "
              f"({complex_prompt['extension'] / complex_prompt['total'] * 100:.1f}%)")

    # 策略 3：缓存
    print("\n" + "=" * 70)
    print("策略 3：缓存（避免重复计算）")
    print("=" * 70)

    cache = SemanticCache()

    # 第一次调用
    cache.set("怎么退款", "请在订单页面申请退款")
    cache.set("物流多久", "一般3-5个工作日")

    # 重复调用
    queries = ["怎么退款", "物流多久", "怎么退款", "物流多久", "新品上架"]
    for q in queries:
        result = cache.get(q)
        if result:
            print(f"  ✅ 缓存命中: {q}")
        else:
            print(f"  ❌ 缓存未命中: {q}")

    stats = cache.get_stats()
    print(f"\n缓存统计:")
    print(f"  命中率: {stats['hit_rate']:.1%}")
    print(f"  缓存大小: {stats['size']}")

    # 对比优化前后
    compare_optimization()

    # 展示问题
    show_optimization_problems()

    # 总结
    print("\n" + "=" * 70)
    print("成本优化最佳实践")
    print("=" * 70)
    print("""
1. 模型选择
   ✅ 按任务复杂度选择模型
   ✅ 简单任务用小模型
   ✅ 复杂任务用大模型

2. Prompt 优化
   ✅ 区分核心 Prompt 和扩展 Prompt
   ✅ 简单任务用核心 Prompt
   ✅ 复杂任务才添加扩展内容

3. 缓存策略
   ✅ 通用知识可以缓存
   ✅ 个性化数据要谨慎
   ✅ 设置 TTL 避免过期

4. 持续监控
   ✅ 跟踪成本和效果
   ✅ 定期评估优化效果
   ✅ 平衡质量和成本

记住：
成本优化的目标不是"最便宜"，
而是"在可接受的质量下成本最优"。
    """)


if __name__ == "__main__":
    main()
