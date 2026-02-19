#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 07 作业参考实现（Solution）

本文件是 Week 07 作业的参考实现，供学生在遇到困难时参考。

作业要求：
1. 实现成本追踪器：记录 LLM 调用的成本
2. 实现 LLM 评估器：评估输出质量
3. 实现成本优化策略：模型选择、缓存
4. 实现 FastAPI 服务：部署 API
5. 实现可观测性：日志、指标、Trace

运行方式：
python3 chapters/week_07/starter_code/solution.py
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================
# Part 1: 成本追踪器
# ============================================================

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
    """
    成本追踪器（作业 Part 1 参考实现）

    要求：
    1. 记录每次 LLM 调用的模型名称、Token 数、延迟、Agent 名称
    2. 计算单次调用成本
    3. 按模型和 Agent 分组统计
    """

    # 2026 年 2 月的参考价格（每 1M Token，美元）
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self) -> None:
        self.calls: List[LLMMetrics] = []

    def record_call(self, metrics: LLMMetrics) -> None:
        """记录一次 LLM 调用"""
        self.calls.append(metrics)

    def calculate_cost(self, metrics: LLMMetrics) -> float:
        """计算单次调用成本（美元）"""
        pricing = self.PRICING.get(metrics.model, {"input": 0, "output": 0})
        input_cost = metrics.input_tokens * pricing.get("input", 0) / 1_000_000
        output_cost = metrics.output_tokens * pricing.get("output", 0) / 1_000_000
        return input_cost + output_cost

    def get_summary(self) -> Dict:
        """获取成本汇总"""
        if not self.calls:
            return {
                "total_calls": 0,
                "total_cost_usd": 0,
                "total_tokens": 0,
                "cost_by_agent": {},
                "cost_by_model": {},
                "avg_latency_ms": 0
            }

        total_cost = sum(self.calculate_cost(m) for m in self.calls)
        total_tokens = sum(m.input_tokens + m.output_tokens for m in self.calls)

        # 按 Agent 分组
        by_agent: Dict[str, Dict] = {}
        for m in self.calls:
            agent = m.agent_name or "unknown"
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "cost": 0, "tokens": 0}
            by_agent[agent]["calls"] += 1
            by_agent[agent]["cost"] += self.calculate_cost(m)
            by_agent[agent]["tokens"] += m.input_tokens + m.output_tokens

        # 按模型分组
        by_model: Dict[str, Dict] = {}
        for m in self.calls:
            model = m.model
            if model not in by_model:
                by_model[model] = {"calls": 0, "cost": 0, "tokens": 0}
            by_model[model]["calls"] += 1
            by_model[model]["cost"] += self.calculate_cost(m)
            by_model[model]["tokens"] += m.input_tokens + m.output_tokens

        return {
            "total_calls": len(self.calls),
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "cost_by_agent": by_agent,
            "cost_by_model": by_model,
            "avg_latency_ms": sum(m.latency_ms for m in self.calls) // len(self.calls)
        }


# ============================================================
# Part 2: LLM 评估器
# ============================================================

@dataclass
class TestCase:
    """测试用例"""
    query: str
    expected: str
    context: str = ""


@dataclass
class EvalResult:
    """评估结果"""
    query: str
    expected: str
    actual: str
    faithfulness: float
    relevancy: float


class LLMEvaluator:
    """
    LLM 评估器（作业 Part 2 参考实现）

    要求：
    1. 计算忠实度（Faithfulness）：答案是否基于上下文
    2. 计算相关性（Relevancy）：答案是否回答了问题
    3. 批量评估测试用例
    """

    def __init__(self):
        self.eval_history: List[EvalResult] = []

    def calculate_faithfulness(self, answer: str, context: str) -> float:
        """
        计算忠实度

        ⚠️ 这是教学简化实现：基于关键词重叠
        生产环境应使用 LLM-as-Judge（参考 CHAPTER.md 第 216-225 行）
        """
        if not context:
            return 0.5

        context_words = set(context.lower().split())
        answer_words = set(answer.lower().split())

        if not context_words:
            return 0.5

        overlap = len(context_words & answer_words)
        return min(0.95, 0.4 + overlap * 0.1)

    def calculate_relevancy(self, query: str, answer: str) -> float:
        """
        计算相关性

        ⚠️ 这是教学简化实现：基于答案长度和关键词匹配
        生产环境应使用 LLM-as-Judge（参考 CHAPTER.md 第 216-225 行）
        """
        if not answer:
            return 0.0

        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        # 关键词重叠
        overlap = len(query_words & answer_words)

        # 答案长度合理性
        length_score = 0.5
        if 10 <= len(answer) <= 300:
            length_score = 0.8
        elif len(answer) > 300:
            length_score = 0.6

        return min(0.95, 0.3 + overlap * 0.1 + length_score * 0.2)

    def evaluate_batch(
        self,
        test_cases: List[TestCase],
        system_fn: callable
    ) -> Dict:
        """批量评估测试用例"""
        results = []

        for case in test_cases:
            # 运行系统
            actual = system_fn(case.query)

            # 计算指标
            faithfulness = self.calculate_faithfulness(actual, case.context)
            relevancy = self.calculate_relevancy(case.query, actual)

            result = EvalResult(
                query=case.query,
                expected=case.expected,
                actual=actual,
                faithfulness=faithfulness,
                relevancy=relevancy
            )
            results.append(result)
            self.eval_history.append(result)

        # 汇总
        avg_faithfulness = sum(r.faithfulness for r in results) / len(results)
        avg_relevancy = sum(r.relevancy for r in results) / len(results)

        return {
            "num_cases": len(results),
            "avg_faithfulness": round(avg_faithfulness, 3),
            "avg_relevancy": round(avg_relevancy, 3),
            "overall_score": round((avg_faithfulness + avg_relevancy) / 2, 3),
            "details": results
        }


# ============================================================
# Part 3: 成本优化
# ============================================================

class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ModelSelector:
    """
    模型选择器（作业 Part 3 参考实现）

    要求：
    1. 为每个 Agent 选择合适的模型
    2. 估算不同模型的成本
    """

    # Agent 职责到模型的映射
    AGENT_MODELS = {
        "planner": "gpt-4o",
        "executor": "gpt-4o-mini",
        "reviewer": "gpt-4o",
        "retriever": "gpt-4o-mini"
    }

    @classmethod
    def select_model_for_agent(cls, agent_name: str) -> str:
        """为 Agent 选择模型"""
        return cls.AGENT_MODELS.get(agent_name, "gpt-4o-mini")

    @classmethod
    def estimate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """估算成本"""
        pricing = CostTracker.PRICING.get(model, CostTracker.PRICING["gpt-4o-mini"])
        input_cost = input_tokens * pricing["input"] / 1_000_000
        output_cost = output_tokens * pricing["output"] / 1_000_000
        return input_cost + output_cost


class SemanticCache:
    """
    语义缓存（作业 Part 3 参考实现）

    ⚠️ 当前实现是精确匹配（字符串相等）
    真正的语义缓存应使用向量相似度（如 cosine similarity > 0.9）
    参考 CHAPTER.md 第 435-443 行

    要求：
    1. 支持精确匹配缓存
    2. 记录缓存命中率
    """

    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.hits = 0
        self.misses = 0

    def get(self, query: str) -> Optional[str]:
        """从缓存获取"""
        if query in self.cache:
            self.hits += 1
            return self.cache[query]
        self.misses += 1
        return None

    def set(self, query: str, response: str) -> None:
        """存储到缓存"""
        self.cache[query] = response

    def get_stats(self) -> Dict:
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
# Part 4: FastAPI 服务（简化实现）
# ============================================================

class SimpleAPIService:
    """
    简化的 API 服务（作业 Part 4 参考实现）

    实际作业中应使用 FastAPI
    这里提供简化的实现展示核心概念
    """

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.request_count = 0

    def handle_request(self, task: str, agent: str = "executor") -> Dict:
        """
        处理请求（模拟）

        实际应用中：
        - 使用 FastAPI 的 @app.post 装饰器
        - 使用 Pydantic 模型验证请求
        - 返回 JSON 响应
        """
        self.request_count += 1

        # 模拟 LLM 调用
        start_time = time.time()
        time.sleep(0.01)  # 模拟延迟

        # 记录成本
        self.cost_tracker.record_call(LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            latency_ms=int((time.time() - start_time) * 1000),
            timestamp=datetime.now(),
            agent_name=agent
        ))

        return {
            "task": task,
            "result": f"处理完成: {task}",
            "request_id": self.request_count,
            "cost_usd": self.cost_tracker.get_summary()["total_cost_usd"]
        }


# ============================================================
# Part 5: 可观测性
# ============================================================

@dataclass
class Span:
    """Span：一个操作的记录"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TraceContext:
    """
    追踪上下文（作业 Part 5 参考实现）

    要求：
    1. 创建 Span 记录操作
    2. 计算 Span 的耗时
    3. 汇总完整 Trace
    """

    def __init__(self):
        import uuid
        self.trace_id = str(uuid.uuid4())
        self.spans: List[Span] = []

    def create_span(self, name: str, **metadata) -> Span:
        """创建一个新 Span"""
        span = Span(
            name=name,
            start_time=time.time(),
            metadata=metadata
        )
        return span

    def finish_span(self, span: Span) -> None:
        """完成 Span"""
        span.end_time = time.time()
        span.duration_ms = int((span.end_time - span.start_time) * 1000)
        self.spans.append(span)

    def get_summary(self) -> Dict:
        """获取 Trace 汇总"""
        return {
            "trace_id": self.trace_id,
            "num_spans": len(self.spans),
            "total_duration_ms": sum(s.duration_ms or 0 for s in self.spans),
            "spans": [
                {
                    "name": s.name,
                    "duration_ms": s.duration_ms,
                    "metadata": s.metadata
                }
                for s in self.spans
            ]
        }


class MetricsCollector:
    """
    指标收集器（作业 Part 5 参考实现）

    要求：
    1. 记录请求计数
    2. 记录延迟分布
    3. 计算错误率
    """

    def __init__(self):
        self.requests: Dict[str, int] = {}
        self.latencies: List[float] = []
        self.errors: Dict[str, int] = {}

    def record_request(self, agent: str, status: str, latency: float) -> None:
        """记录请求"""
        key = f"{agent}.{status}"
        self.requests[key] = self.requests.get(key, 0) + 1
        self.latencies.append(latency)

        if status == "error":
            error_key = agent
            self.errors[error_key] = self.errors.get(error_key, 0) + 1

    def get_summary(self) -> Dict:
        """获取指标汇总"""
        total_requests = sum(self.requests.values())
        total_errors = sum(self.errors.values())

        sorted_latencies = sorted(self.latencies)
        p95_index = int(len(sorted_latencies) * 0.95)

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_latency": sum(self.latencies) / len(self.latencies) if self.latencies else 0,
            "p95_latency": sorted_latencies[p95_index] if sorted_latencies else 0
        }


# ============================================================
# 整合示例
# ============================================================

class ProductionTextAgent:
    """
    生产级 TextAgent（参考实现）

    整合所有组件：
    - 成本追踪
    - 评估
    - 优化
    - 可观测性
    """

    def __init__(self):
        self.cost_tracker = CostTracker()
        self.evaluator = LLMEvaluator()
        self.model_selector = ModelSelector()
        self.cache = SemanticCache()
        self.metrics = MetricsCollector()

    def run(self, task: str, enable_cache: bool = True) -> Dict:
        """运行任务"""

        trace = TraceContext()

        # 检查缓存
        if enable_cache:
            cached = self.cache.get(task)
            if cached:
                return cached

        # 创建追踪 Span
        span = trace.create_span("workflow", task=task)

        try:
            # 模拟执行
            start_time = time.time()
            time.sleep(0.01)

            result = f"执行结果: {task}"

            # 记录成本
            self.cost_tracker.record_call(LLMMetrics(
                model="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
                latency_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
                agent_name="workflow"
            ))

            # 记录指标
            latency = time.time() - start_time
            self.metrics.record_request("workflow", "success", latency)

            # 完成追踪
            trace.finish_span(span)

            # 组装结果
            final_result = {
                "task": task,
                "result": result,
                "cost": self.cost_tracker.get_summary(),
                "trace": trace.get_summary(),
                "metrics": self.metrics.get_summary()
            }

            # 存储缓存
            if enable_cache:
                self.cache.set(task, final_result)

            return final_result

        except Exception as e:
            self.metrics.record_request("workflow", "error", 0)
            raise


# ============================================================
# 主函数：演示所有功能
# ============================================================

def main():
    """演示所有组件"""

    print("=" * 70)
    print("Week 07 参考实现演示")
    print("=" * 70)

    # 创建系统
    agent = ProductionTextAgent()

    # 运行任务
    tasks = [
        "分析客户反馈的情感倾向",
        "检索远程办公政策",
        "总结产品质量分析"
    ]

    results = []
    for task in tasks:
        print(f"\n执行任务: {task}")
        result = agent.run(task)
        results.append(result)

        print(f"  成本: ${result['cost']['total_cost_usd']:.6f}")
        print(f"  延迟: {result['trace']['total_duration_ms']}ms")
        print(f"  缓存命中率: {agent.cache.get_stats()['hit_rate']:.1%}")

    # 显示汇总
    print("\n" + "=" * 70)
    print("汇总报告")
    print("=" * 70)

    cost_summary = agent.cost_tracker.get_summary()
    print(f"\n总调用次数: {cost_summary['total_calls']}")
    print(f"总成本: ${cost_summary['total_cost_usd']:.6f}")
    print(f"总 Token: {cost_summary['total_tokens']}")

    metrics_summary = agent.metrics.get_summary()
    print(f"\n平均延迟: {metrics_summary['avg_latency']:.3f}s")
    print(f"P95 延迟: {metrics_summary['p95_latency']:.3f}s")
    print(f"错误率: {metrics_summary['error_rate']:.1%}")

    cache_stats = agent.cache.get_stats()
    print(f"\n缓存大小: {cache_stats['size']}")
    print(f"缓存命中率: {cache_stats['hit_rate']:.1%}")


if __name__ == "__main__":
    main()
