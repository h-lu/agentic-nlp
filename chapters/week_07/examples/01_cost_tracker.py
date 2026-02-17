#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：成本追踪器（Cost Tracker）

本例演示如何追踪 LLM 应用的使用成本。在生产环境中，
每次 LLM 调用都会花钱，而多 Agent 系统的陷阱在于——
你以为是"一次调用"，实际上是"规划者调一次、执行者调一次、审核者调一次"。

核心功能：
- 记录每次 LLM 调用的模型名称、Token 数、延迟、Agent 名称
- 按模型和 Agent 分组统计成本
- 生成成本报告，找出"最烧钱的 Agent"

运行方式：python3 chapters/week_07/examples/01_cost_tracker.py
预期输出：展示不同 Agent 的成本分布

依赖：
- pip install pydantic
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================
# 数据结构
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

    @property
    def total_tokens(self) -> int:
        """总 Token 数"""
        return self.input_tokens + self.output_tokens


# ============================================================
# 成本追踪器
# ============================================================

class CostTracker:
    """
    成本追踪器：记录 LLM 调用并计算成本

    老潘的经验：
    "生产环境中，我们每调用一次 LLM 都会记录五件事——
    模型名称、输入 Token、输出 Token、延迟、Agent 名称。
    这样才能知道'钱花在哪'。"
    """

    # 2026 年 2 月的参考价格（每 1M Token，美元）
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    }

    def __init__(self) -> None:
        self.calls: List[LLMMetrics] = []

    def record_call(self, metrics: LLMMetrics) -> None:
        """记录一次 LLM 调用"""
        self.calls.append(metrics)

    def calculate_cost(self, metrics: LLMMetrics) -> float:
        """
        计算单次调用成本（美元）

        公式：input_tokens * input_price + output_tokens * output_price
        """
        pricing = self.PRICING.get(metrics.model, {"input": 0, "output": 0})
        input_cost = metrics.input_tokens * pricing.get("input", 0) / 1_000_000
        output_cost = metrics.output_tokens * pricing.get("output", 0) / 1_000_000
        return input_cost + output_cost

    def get_summary(self) -> Dict:
        """
        获取成本汇总

        返回：
        - total_calls: 总调用次数
        - total_cost_usd: 总成本（美元）
        - total_tokens: 总 Token 数
        - cost_by_agent: 按 Agent 分组的成本
        - cost_by_model: 按模型分组的成本
        - avg_latency_ms: 平均延迟
        """
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
        total_tokens = sum(m.total_tokens for m in self.calls)

        # 按 Agent 分组——关键！
        by_agent: Dict[str, Dict] = {}
        for m in self.calls:
            agent = m.agent_name or "unknown"
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "cost": 0, "tokens": 0}
            by_agent[agent]["calls"] += 1
            by_agent[agent]["cost"] += self.calculate_cost(m)
            by_agent[agent]["tokens"] += m.total_tokens

        # 按模型分组
        by_model: Dict[str, Dict] = {}
        for m in self.calls:
            model = m.model
            if model not in by_model:
                by_model[model] = {"calls": 0, "cost": 0, "tokens": 0}
            by_model[model]["calls"] += 1
            by_model[model]["cost"] += self.calculate_cost(m)
            by_model[model]["tokens"] += m.total_tokens

        return {
            "total_calls": len(self.calls),
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "cost_by_agent": by_agent,
            "cost_by_model": by_model,
            "avg_latency_ms": sum(m.latency_ms for m in self.calls) // len(self.calls)
        }

    def reset(self) -> None:
        """重置追踪记录"""
        self.calls.clear()


# ============================================================
# 反例：没有成本追踪的问题
# ============================================================

def bad_example():
    """
    反例：没有成本追踪的多 Agent 系统

    常见错误：
    1. 不知道哪个 Agent 最烧钱
    2. 无法发现成本异常
    3. 难以评估优化效果
    """
    print("\n" + "=" * 70)
    print("❌ 反例：没有成本追踪的问题")
    print("=" * 70)
    print("""
小北上周实现了多 Agent 系统，兴奋地让老板试用。
财务部门随后发来邮件：API 成本是预期的 3 倍。

问题在哪？小北只能回答"系统很好，能规划、能协作"，
但说不出"钱花在哪"。

没有 CostTracker 的问题：
1. 不知道哪个 Agent 调用最频繁
2. 不知道哪个 Agent 用的模型最贵
3. 无法证明优化后的成本降低效果
4. 无法预测未来成本（如日活用户增加 10 倍）

老潘的建议：
"先算账，再谈效果。在证明系统好不好之前，
你得先知道系统花了多少。"
    """)


# ============================================================
# 模拟多 Agent 调用
# ============================================================

def simulate_multi_agent_workflow(tracker: CostTracker) -> None:
    """模拟多 Agent 工作流，展示成本追踪"""

    print("\n" + "=" * 70)
    print("模拟多 Agent 工作流")
    print("=" * 70)

    # 场景 1：规划者调用 GPT-4o（贵，但值得）
    print("\n[阶段 1] 规划者制定计划...")
    start = time.time()
    time.sleep(0.1)  # 模拟延迟
    tracker.record_call(LLMMetrics(
        model="gpt-4o",
        input_tokens=500,
        output_tokens=300,
        latency_ms=int((time.time() - start) * 1000),
        timestamp=datetime.now(),
        agent_name="planner"
    ))
    print("  ✓ 规划者使用 GPT-4o（需要复杂推理）")

    # 场景 2：执行者调用 GPT-4o-mini（便宜）
    print("\n[阶段 2] 执行者执行任务（3 个子步骤）...")
    for i in range(3):
        start = time.time()
        time.sleep(0.05)
        tracker.record_call(LLMMetrics(
            model="gpt-4o-mini",
            input_tokens=200,
            output_tokens=150,
            latency_ms=int((time.time() - start) * 1000),
            timestamp=datetime.now(),
            agent_name="executor"
        ))
    print("  ✓ 执行者使用 GPT-4o-mini（任务简单，小模型够用）")

    # 场景 3：审核者调用 GPT-4o（贵，但值得）
    print("\n[阶段 3] 审核者检查结果...")
    start = time.time()
    time.sleep(0.08)
    tracker.record_call(LLMMetrics(
        model="gpt-4o",
        input_tokens=800,
        output_tokens=200,
        latency_ms=int((time.time() - start) * 1000),
        timestamp=datetime.now(),
        agent_name="reviewer"
    ))
    print("  ✓ 审核者使用 GPT-4o（需要仔细检查）")


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    """主入口"""

    print("=" * 70)
    print("成本追踪器演示（Cost Tracker）")
    print("=" * 70)

    # 创建追踪器
    tracker = CostTracker()

    # 模拟工作流
    simulate_multi_agent_workflow(tracker)

    # 生成报告
    print("\n" + "=" * 70)
    print("成本报告")
    print("=" * 70)

    summary = tracker.get_summary()

    print(f"""
总调用次数: {summary['total_calls']} 次
总 Token 数: {summary['total_tokens']:,}
总成本: ${summary['total_cost_usd']:.6f}
平均延迟: {summary['avg_latency_ms']} ms

按 Agent 分组:
""")
    for agent, data in summary["cost_by_agent"].items():
        print(f"  {agent:12s}: {data['calls']:2d} 次调用, "
              f"{data['tokens']:4d} tokens, ${data['cost']:.6f}")

    print(f"\n按模型分组:")
    for model, data in summary["cost_by_model"].items():
        print(f"  {model:15s}: {data['calls']:2d} 次调用, "
              f"{data['tokens']:4d} tokens, ${data['cost']:.6f}")

    # 分析
    print("\n" + "=" * 70)
    print("成本分析")
    print("=" * 70)

    most_expensive_agent = max(
        summary["cost_by_agent"].items(),
        key=lambda x: x[1]["cost"]
    )
    print(f"\n最烧钱的 Agent: {most_expensive_agent[0]} "
          f"(${most_expensive_agent[1]['cost']:.6f})")

    if most_expensive_agent[0] == "executor":
        print("  → 执行者调用最频繁，但用的是便宜模型，合理")
    elif most_expensive_agent[0] == "reviewer":
        print("  → 审核者花的钱比规划者还多")
        print("  → 建议：检查审核 Prompt 是否太长，或者考虑降低审核频率")

    # 对比优化前后的成本
    print("\n" + "=" * 70)
    print("优化潜力分析")
    print("=" * 70)
    print("""
场景 A：全部用 GPT-4o
  预估成本: ${:.6f}
  当前成本: ${:.6f}
  节省: {:.1f}%

场景 B：审核者降级到 GPT-4o-mini
  预估成本: ${:.6f}
  节省: ${:.6f} ({:.1f}%)
  风险: 审核质量可能下降

老潘的点评：
"成本追踪不是要省钱，而是要'把钱花在刀刃上'。
规划者和审核者需要复杂推理，用 GPT-4 值得；
执行者只是简单工具调用，用 GPT-4o-mini 就够了。
这就是工程中的 trade-off。"
""".format(
        summary["total_cost_usd"] * 2.5,  # 假设全用 GPT-4o
        summary["total_cost_usd"],
        (1 - summary["total_cost_usd"] / (summary["total_cost_usd"] * 2.5)) * 100,
        summary["total_cost_usd"] - summary["cost_by_agent"].get("reviewer", {}).get("cost", 0) * 0.85,
        summary["cost_by_agent"].get("reviewer", {}).get("cost", 0) * 0.15,
        (summary["cost_by_agent"].get("reviewer", {}).get("cost", 0) * 0.15 /
         summary["total_cost_usd"]) * 100
    ))

    # 展示反例
    bad_example()


if __name__ == "__main__":
    main()
