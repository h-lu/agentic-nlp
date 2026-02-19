#!/usr/bin/env python3
"""
06_cost_tracking.py - Token 成本追踪

本示例展示如何追踪和优化 Prompt 的 Token 成本：
- 追踪每次调用的输入/输出 Token
- 比较不同 Prompt 变体的成本
- 成本感知的 Prompt 选择

成本追踪的重要性：
在 Prompt 迭代过程中，不同的 Prompt 可能产生显著不同的成本。
一个带有 5 个 Few-shot 示例的 Prompt，输入 Token 可能是没有示例的 3 倍。
追踪成本有助于在效果和成本之间做出明智的权衡。

基于 Week 01 的 LLM Client 和 Week 02 的 Prompt 模板构建。

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Part 1: Token 消耗记录
# ============================================================================

@dataclass
class TokenUsage:
    """单次调用的 Token 使用记录"""
    input_tokens: int
    output_tokens: int
    total_tokens: int

    @classmethod
    def from_dict(cls, data: dict) -> "TokenUsage":
        return cls(
            input_tokens=data.get("prompt_tokens", 0),
            output_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
        )


@dataclass
class PromptCallRecord:
    """单次 Prompt 调用记录"""
    timestamp: str
    prompt_name: str
    prompt_version: str
    input_text: str
    output_text: str
    token_usage: TokenUsage
    latency_ms: float
    cost_usd: float
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['token_usage'] = asdict(self.token_usage)
        return d


class CostTracker:
    """
    成本追踪器。

    记录每次 LLM 调用的 Token 消耗和成本。

    Example:
        >>> tracker = CostTracker()
        >>> tracker.record_call("classify", "v1", usage, cost=0.001)
        >>> print(tracker.get_summary())
    """

    # 当前主流模型的定价（美元/百万 Token）
    # 数据来源：各模型官方定价页面，2026 年 2 月
    # TODO: 定价数据需定期更新，建议在每次使用前验证最新价格
    MODEL_PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-reasoner": {"input": 0.55, "output": 2.19},
        "glm-4": {"input": 0.10, "output": 0.10},
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.records: List[PromptCallRecord] = []
        self._session_start = datetime.now()

    def get_pricing(self) -> Dict[str, float]:
        """获取当前模型的定价"""
        return self.MODEL_PRICING.get(self.model, {"input": 1.0, "output": 3.0})

    def calculate_cost(self, usage: TokenUsage) -> float:
        """计算成本（美元）"""
        pricing = self.get_pricing()
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def record_call(
        self,
        prompt_name: str,
        prompt_version: str,
        input_text: str,
        output_text: str,
        usage: TokenUsage,
        latency_ms: float = 0.0,
        metadata: dict = None,
    ) -> PromptCallRecord:
        """记录一次调用"""
        cost = self.calculate_cost(usage)

        record = PromptCallRecord(
            timestamp=datetime.now().isoformat(),
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            input_text=input_text,
            output_text=output_text,
            token_usage=usage,
            latency_ms=latency_ms,
            cost_usd=cost,
            metadata=metadata or {},
        )

        self.records.append(record)
        return record

    def get_summary(self, group_by: str = "prompt_name") -> Dict[str, Any]:
        """
        获取汇总统计。

        Args:
            group_by: 分组方式（prompt_name / prompt_version / all）

        Returns:
            汇总统计字典
        """
        if not self.records:
            return {"total_calls": 0, "total_cost": 0}

        if group_by == "all":
            return self._summarize_all()
        else:
            return self._summarize_by_field(group_by)

    def _summarize_all(self) -> Dict[str, Any]:
        """汇总所有记录"""
        total_input = sum(r.token_usage.input_tokens for r in self.records)
        total_output = sum(r.token_usage.output_tokens for r in self.records)
        total_cost = sum(r.cost_usd for r in self.records)
        avg_latency = sum(r.latency_ms for r in self.records) / len(self.records)

        return {
            "model": self.model,
            "session_start": self._session_start.isoformat(),
            "total_calls": len(self.records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": total_cost,
            "avg_latency_ms": avg_latency,
        }

    def _summarize_by_field(self, field: str) -> Dict[str, Any]:
        """按字段分组汇总"""
        groups = {}
        for record in self.records:
            key = getattr(record, field, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(record)

        result = {}
        for key, records in groups.items():
            total_input = sum(r.token_usage.input_tokens for r in records)
            total_output = sum(r.token_usage.output_tokens for r in records)
            total_cost = sum(r.cost_usd for r in records)
            avg_latency = sum(r.latency_ms for r in records) / len(records)

            result[key] = {
                "calls": len(records),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_cost_usd": total_cost,
                "avg_latency_ms": avg_latency,
            }

        return result

    def export_to_json(self, path: str) -> None:
        """导出到 JSON 文件"""
        data = {
            "model": self.model,
            "session_start": self._session_start.isoformat(),
            "records": [r.to_dict() for r in self.records]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def reset(self) -> None:
        """重置记录"""
        self.records = []
        self._session_start = datetime.now()


# ============================================================================
# Part 2: Prompt 成本预估
# ============================================================================

def estimate_prompt_cost(
    prompt_template: str,
    avg_input_length: int,
    avg_output_length: int,
    num_calls: int,
    model: str = "gpt-4o-mini",
) -> Dict[str, float]:
    """
    预估 Prompt 的成本。

    Args:
        prompt_template: Prompt 模板字符串
        avg_input_length: 平均输入文本长度（字符）
        avg_output_length: 平均输出文本长度（字符）
        num_calls: 预估调用次数
        model: 模型名称

    Returns:
        成本预估字典
    """
    # 简化的 Token 估算：中文约 1.5 字符/Token，英文约 4 字符/Token
    # 这里使用保守估计：2 字符/Token
    CHARS_PER_TOKEN = 2

    # 计算每次调用的 Token 数
    template_tokens = len(prompt_template) / CHARS_PER_TOKEN
    input_tokens_per_call = template_tokens + (avg_input_length / CHARS_PER_TOKEN)
    output_tokens_per_call = avg_output_length / CHARS_PER_TOKEN

    # 获取定价
    pricing = CostTracker.MODEL_PRICING.get(model, {"input": 1.0, "output": 3.0})

    # 计算成本
    total_input_tokens = num_calls * input_tokens_per_call
    total_output_tokens = num_calls * output_tokens_per_call

    input_cost = (total_input_tokens / 1_000_000) * pricing["input"]
    output_cost = (total_output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "num_calls": num_calls,
        "input_tokens_per_call": int(input_tokens_per_call),
        "output_tokens_per_call": int(output_tokens_per_call),
        "total_input_tokens": int(total_input_tokens),
        "total_output_tokens": int(total_output_tokens),
        "total_cost_usd": total_cost,
        "cost_per_call_usd": total_cost / num_calls,
    }


def compare_prompt_costs(
    prompt_variants: Dict[str, str],
    avg_input_length: int,
    avg_output_length: int,
    num_calls: int,
    models: List[str] = None,
) -> Dict[str, Any]:
    """
    比较不同 Prompt 变体的成本。

    Args:
        prompt_variants: Prompt 变体字典 {name: template}
        avg_input_length: 平均输入文本长度
        avg_output_length: 平均输出文本长度
        num_calls: 预估调用次数
        models: 要比较的模型列表

    Returns:
        比较结果字典
    """
    if models is None:
        models = ["gpt-4o-mini", "gpt-4o", "deepseek-chat"]

    results = {}
    for model in models:
        model_results = {}
        for name, template in prompt_variants.items():
            model_results[name] = estimate_prompt_cost(
                template, avg_input_length, avg_output_length, num_calls, model
            )
        results[model] = model_results

    return results


# ============================================================================
# Part 3: 成本感知的 Prompt 选择
# ============================================================================

@dataclass
class PromptVariant:
    """Prompt 变体"""
    name: str
    template: str
    version: str = "1.0"
    expected_accuracy: float = 0.8  # 预期准确率（来自评估）
    use_cot: bool = False


class CostAwarePromptSelector:
    """
    成本感知的 Prompt 选择器。

    根据预算和性能要求选择最优的 Prompt 变体。

    Example:
        >>> selector = CostAwarePromptSelector(budget_usd=10.0)
        >>> selector.add_variant("v1", template_v1, accuracy=0.8)
        >>> selector.add_variant("v2", template_v2, accuracy=0.9)
        >>> best = selector.select_best(num_calls=1000)
    """

    def __init__(
        self,
        budget_usd: Optional[float] = None,
        min_accuracy: float = 0.8,
        model: str = "gpt-4o-mini",
    ):
        self.budget_usd = budget_usd
        self.min_accuracy = min_accuracy
        self.model = model
        self.variants: List[PromptVariant] = []

    def add_variant(
        self,
        name: str,
        template: str,
        version: str = "1.0",
        accuracy: float = 0.8,
        use_cot: bool = False,
    ) -> None:
        """添加 Prompt 变体"""
        self.variants.append(PromptVariant(
            name=name,
            template=template,
            version=version,
            expected_accuracy=accuracy,
            use_cot=use_cot,
        ))

    def estimate_cost(
        self,
        variant: PromptVariant,
        num_calls: int,
        avg_input_length: int = 100,
        avg_output_length: int = 50,
    ) -> float:
        """估算变体的成本"""
        estimate = estimate_prompt_cost(
            variant.template,
            avg_input_length,
            avg_output_length,
            num_calls,
            self.model,
        )
        return estimate["total_cost_usd"]

    def select_best(
        self,
        num_calls: int,
        avg_input_length: int = 100,
        avg_output_length: int = 50,
        strategy: str = "cost_effective",
    ) -> Optional[PromptVariant]:
        """
        选择最优的 Prompt 变体。

        Args:
            num_calls: 预估调用次数
            avg_input_length: 平均输入长度
            avg_output_length: 平均输出长度
            strategy: 选择策略
                - "cost_effective": 成本效益最优（准确率/成本）
                - "accuracy_first": 准确率优先（在预算内选最高的）
                - "cost_first": 成本优先（在准确率达标的前提下选最便宜的）

        Returns:
            最优的 Prompt 变体
        """
        if not self.variants:
            return None

        # 计算每个变体的成本
        variant_costs = []
        for v in self.variants:
            cost = self.estimate_cost(v, num_calls, avg_input_length, avg_output_length)
            variant_costs.append((v, cost))

        # 过滤掉低于准确率要求的
        qualified = [(v, c) for v, c in variant_costs if v.expected_accuracy >= self.min_accuracy]

        if not qualified:
            # 如果没有达标的，返回准确率最高的
            return max(self.variants, key=lambda v: v.expected_accuracy)

        # 如果有预算限制，过滤掉超预算的
        if self.budget_usd is not None:
            qualified = [(v, c) for v, c in qualified if c <= self.budget_usd]

        if not qualified:
            return None

        if strategy == "cost_effective":
            # 成本效益比 = 准确率 / 成本
            return max(qualified, key=lambda vc: vc[0].expected_accuracy / vc[1])[0]

        elif strategy == "accuracy_first":
            return max(qualified, key=lambda vc: vc[0].expected_accuracy)[0]

        elif strategy == "cost_first":
            return min(qualified, key=lambda vc: vc[1])[0]

        return qualified[0][0]


# ============================================================================
# Part 4: 示例 Prompt 变体
# ============================================================================

# Prompt 变体示例：从简单到复杂
PROMPT_VARIANTS = {
    "v1_minimal": """请分类以下新闻：

{input}""",

    "v2_basic": """角色：你是一个新闻分类助手。
任务：判断以下新闻属于哪个类别。
格式：财经、科技、体育、娱乐

{input}""",

    "v3_with_constraints": """角色：你是一个新闻分类助手。

任务：判断以下新闻属于哪个类别。

约束：
- 只输出类别名称
- 不要解释原因

格式：从以下选项中选一个：财经、科技、体育、娱乐

{input}""",

    "v4_with_examples": """角色：你是一个新闻分类助手。

示例：
输入："苹果公司发布新款 iPhone"
输出：科技

输入："央行宣布下调存款准备金率"
输出：财经

输入："中国男篮战胜韩国队"
输出：体育

任务：判断以下新闻属于哪个类别。

约束：
- 只输出类别名称
- 格式与示例一致

格式：从以下选项中选一个：财经、科技、体育、娱乐

{input}""",

    "v5_cot": """角色：你是一个新闻分类助手。

任务：判断以下新闻属于哪个类别。

请按以下步骤思考：
1. 新闻中提到了哪些关键信息？
2. 这些信息最可能与哪个领域相关？
3. 最终分类结果是什么？

格式：从以下选项中选一个：财经、科技、体育、娱乐

{input}""",
}


# ============================================================================
# Part 5: 演示函数
# ============================================================================

def demo_cost_tracking() -> None:
    """演示成本追踪"""
    print("=" * 60)
    print("成本追踪演示")
    print("=" * 60)

    tracker = CostTracker(model="gpt-4o-mini")

    # 模拟几次调用
    calls = [
        ("news_classify", "v1", "苹果发布新 iPhone", "科技", 150, 2),
        ("news_classify", "v2", "央行宣布降息", "财经", 200, 2),
        ("news_classify", "v2", "中国男篮夺冠", "体育", 200, 2),
        ("ticket_classify", "v1", "无法登录账户", "技术支持", 180, 3),
        ("ticket_classify", "v1", "申请退款", "账务问题", 180, 3),
    ]

    for prompt_name, version, input_text, output_text, input_tokens, output_tokens in calls:
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
        tracker.record_call(
            prompt_name=prompt_name,
            prompt_version=version,
            input_text=input_text,
            output_text=output_text,
            usage=usage,
            latency_ms=100.0,
        )

    # 打印汇总
    print("\n【总体统计】")
    summary = tracker.get_summary(group_by="all")
    print(f"  模型: {summary['model']}")
    print(f"  总调用: {summary['total_calls']}")
    print(f"  总 Token: {summary['total_tokens']}")
    print(f"  总成本: ${summary['total_cost_usd']:.4f}")

    print("\n【按 Prompt 分组】")
    by_prompt = tracker.get_summary(group_by="prompt_name")
    for name, stats in by_prompt.items():
        print(f"\n  {name}:")
        print(f"    调用次数: {stats['calls']}")
        print(f"    总成本: ${stats['total_cost_usd']:.4f}")


def demo_prompt_cost_comparison() -> None:
    """演示 Prompt 变体成本比较"""
    print("\n" + "=" * 60)
    print("Prompt 变体成本比较")
    print("=" * 60)

    # 比较不同变体
    num_calls = 1000
    avg_input_length = 100
    avg_output_length = 5  # 分类任务输出很短

    print(f"\n假设处理 {num_calls} 条新闻（分类任务）")
    print(f"平均输入长度: {avg_input_length} 字符，平均输出长度: {avg_output_length} 字符")
    print()

    results = {}
    for name, template in PROMPT_VARIANTS.items():
        estimate = estimate_prompt_cost(
            template, avg_input_length, avg_output_length, num_calls, "gpt-4o-mini"
        )
        results[name] = estimate

    # 打印结果
    print(f"{'变体':<20} {'模板 Token':>12} {'总成本':>12}")
    print("-" * 48)
    for name, est in results.items():
        print(f"{name:<20} {est['input_tokens_per_call']:>12} ${est['total_cost_usd']:>10.4f}")

    # 计算差异
    min_cost = min(r['total_cost_usd'] for r in results.values())
    max_cost = max(r['total_cost_usd'] for r in results.values())
    print(f"\n成本范围: ${min_cost:.4f} - ${max_cost:.4f}")
    print(f"最大差异: ${max_cost - min_cost:.4f}（{(max_cost / min_cost - 1) * 100:.0f}%）")


def demo_model_comparison() -> None:
    """演示不同模型的成本比较"""
    print("\n" + "=" * 60)
    print("不同模型的成本比较")
    print("=" * 60)

    # 使用 v4（带示例的版本）进行比较
    template = PROMPT_VARIANTS["v4_with_examples"]
    num_calls = 10000
    avg_input_length = 100
    avg_output_length = 5

    models = ["gpt-4o-mini", "gpt-4o", "deepseek-chat", "glm-4"]

    print(f"\n使用 v4_with_examples 模板处理 {num_calls} 条新闻")
    print()
    print(f"{'模型':<20} {'每次调用':>15} {'总成本':>15}")
    print("-" * 52)

    for model in models:
        estimate = estimate_prompt_cost(
            template, avg_input_length, avg_output_length, num_calls, model
        )
        print(f"{model:<20} ${estimate['cost_per_call_usd']:>14.6f} ${estimate['total_cost_usd']:>14.2f}")


def demo_cost_aware_selection() -> None:
    """演示成本感知的 Prompt 选择"""
    print("\n" + "=" * 60)
    print("成本感知的 Prompt 选择")
    print("=" * 60)

    # 创建选择器
    selector = CostAwarePromptSelector(
        budget_usd=5.0,  # 预算 $5
        min_accuracy=0.85,  # 最低准确率 85%
        model="gpt-4o-mini",
    )

    # 添加变体（假设我们通过评估知道了准确率）
    accuracies = {
        "v1_minimal": 0.75,
        "v2_basic": 0.82,
        "v3_with_constraints": 0.88,
        "v4_with_examples": 0.92,
        "v5_cot": 0.95,
    }

    for name, template in PROMPT_VARIANTS.items():
        selector.add_variant(
            name=name,
            template=template,
            accuracy=accuracies.get(name, 0.8),
        )

    num_calls = 10000

    print(f"\n选择条件：")
    print(f"  预算: ${selector.budget_usd}")
    print(f"  最低准确率: {selector.min_accuracy:.0%}")
    print(f"  调用次数: {num_calls}")

    # 不同策略的选择结果
    strategies = ["cost_effective", "accuracy_first", "cost_first"]

    print(f"\n【不同策略的选择结果】")
    for strategy in strategies:
        best = selector.select_best(num_calls, strategy=strategy)
        if best:
            cost = selector.estimate_cost(best, num_calls)
            print(f"\n  策略: {strategy}")
            print(f"    选择: {best.name}")
            print(f"    预期准确率: {best.expected_accuracy:.0%}")
            print(f"    预估成本: ${cost:.4f}")


def demo_cot_cost_impact() -> None:
    """演示 CoT 对成本的影响"""
    print("\n" + "=" * 60)
    print("CoT 对成本的影响")
    print("=" * 60)

    # 普通 Prompt vs CoT Prompt
    normal_template = PROMPT_VARIANTS["v4_with_examples"]
    cot_template = PROMPT_VARIANTS["v5_cot"]

    num_calls = 1000

    # CoT 的输出会明显更长
    normal_output = 5  # 普通分类只需 5 Token
    cot_output = 80  # CoT 需要输出推理过程

    print(f"\n假设处理 {num_calls} 条工单")
    print()

    normal_cost = estimate_prompt_cost(
        normal_template, 200, normal_output, num_calls, "gpt-4o-mini"
    )
    cot_cost = estimate_prompt_cost(
        cot_template, 200, cot_output, num_calls, "gpt-4o-mini"
    )

    print(f"{'方法':<20} {'输出 Token':>15} {'总成本':>15}")
    print("-" * 52)
    print(f"{'普通分类':<20} {normal_output:>15} ${normal_cost['total_cost_usd']:>14.4f}")
    print(f"{'CoT 分类':<20} {cot_output:>15} ${cot_cost['total_cost_usd']:>14.4f}")

    increase = cot_cost['total_cost_usd'] / normal_cost['total_cost_usd'] - 1
    print(f"\nCoT 成本增加: {(increase) * 100:.0f}%")

    print("\n【老潘的建议】")
    print("  'CoT 的成本确实会翻好几倍。所以我们只对高价值工单用 CoT——")
    print("  VIP 用户、涉及金额大的投诉。简单工单用快速分类就够了。")
    print("  不是一刀切，而是分级处理。'")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("Token 成本追踪演示")
    print("=" * 60)

    # 1. 成本追踪
    demo_cost_tracking()

    # 2. Prompt 变体成本比较
    demo_prompt_cost_comparison()

    # 3. 模型成本比较
    demo_model_comparison()

    # 4. 成本感知选择
    demo_cost_aware_selection()

    # 5. CoT 成本影响
    demo_cot_cost_impact()


if __name__ == "__main__":
    main()
