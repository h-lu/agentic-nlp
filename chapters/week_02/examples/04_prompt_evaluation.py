#!/usr/bin/env python3
"""
04_prompt_evaluation.py - Prompt 评估框架

本示例展示 Prompt 评估的核心概念和实现：
- 测试集构建
- 评估指标计算（准确率、格式合规率）
- Prompt 版本对比
- 错误分析

Prompt 评估的核心原则：
"感觉是不可靠的，要有测试集和量化指标"
—— 不是靠"感觉变好了"，而是用数据说话

运行前确保设置环境变量：
    export OPENAI_API_KEY="sk-..."
"""

import os
import json
import csv
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Any
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Part 1: 测试用例数据结构
# ============================================================================

@dataclass
class TestCase:
    """单个测试用例"""
    input: str
    expected_output: str
    metadata: dict = field(default_factory=dict)  # 可选的额外信息（如难度、类别）

    def to_dict(self) -> dict:
        return {
            "input": self.input,
            "expected_output": self.expected_output,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestCase":
        return cls(
            input=data["input"],
            expected_output=data["expected_output"],
            metadata=data.get("metadata", {})
        )


class TestCaseCollection(BaseModel):
    """测试用例集合"""
    name: str = Field(description="测试集名称")
    version: str = Field(default="1.0", description="版本号")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    cases: list[dict] = Field(default_factory=list, description="测试用例列表")

    def get_test_cases(self) -> list[TestCase]:
        """获取 TestCase 对象列表"""
        return [TestCase.from_dict(c) for c in self.cases]

    def save_to_csv(self, path: str) -> None:
        """保存到 CSV 文件"""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['input', 'expected_output', 'metadata'])
            writer.writeheader()
            for case in self.cases:
                writer.writerow({
                    'input': case['input'],
                    'expected_output': case['expected_output'],
                    'metadata': json.dumps(case.get('metadata', {}), ensure_ascii=False)
                })

    @classmethod
    def load_from_csv(cls, path: str, name: str = "test_set") -> "TestCaseCollection":
        """从 CSV 文件加载"""
        cases = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                metadata = json.loads(row.get('metadata', '{}'))
                cases.append({
                    'input': row['input'],
                    'expected_output': row['expected_output'],
                    'metadata': metadata
                })
        return cls(name=name, cases=cases)


# ============================================================================
# Part 2: 评估结果数据结构
# ============================================================================

@dataclass
class EvalResult:
    """单次评估结果"""
    prompt_version: str
    accuracy: float
    format_compliance: float
    avg_latency_ms: float
    total_tokens: int
    error_cases: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        """生成摘要字符串"""
        return (
            f"Prompt {self.prompt_version}:\n"
            f"  准确率: {self.accuracy:.1%}\n"
            f"  格式合规率: {self.format_compliance:.1%}\n"
            f"  平均延迟: {self.avg_latency_ms:.0f}ms\n"
            f"  总 Token: {self.total_tokens}\n"
            f"  错误数: {len(self.error_cases)}"
        )


class ComparisonReport(BaseModel):
    """Prompt 版本对比报告"""
    baseline_version: str
    comparison_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    results: list[dict] = Field(default_factory=list)

    def add_result(self, result: EvalResult) -> None:
        """添加评估结果"""
        self.results.append(result.to_dict())

    def to_markdown(self) -> str:
        """生成 Markdown 报告"""
        if len(self.results) < 2:
            return "需要至少 2 个版本的评估结果才能对比"

        lines = [
            "# Prompt 版本对比报告",
            f"\n对比日期：{self.comparison_date}",
            f"基准版本：{self.baseline_version}",
            "",
            "## 评估结果",
            "",
            "| 版本 | 准确率 | 格式合规率 | 平均延迟(ms) | 总 Token |",
            "|------|--------|-----------|-------------|----------|"
        ]

        for r in self.results:
            lines.append(
                f"| {r['prompt_version']} | {r['accuracy']:.1%} | "
                f"{r['format_compliance']:.1%} | "
                f"{r['avg_latency_ms']:.0f} | {r['total_tokens']} |"
            )

        # 计算变化
        if len(self.results) >= 2:
            baseline = self.results[0]
            latest = self.results[-1]

            lines.extend([
                "",
                "## 相对基准版本的变化",
                "",
                f"- 准确率: {latest['accuracy'] - baseline['accuracy']:+.1%}",
                f"- 格式合规率: {latest['format_compliance'] - baseline['format_compliance']:+.1%}",
                f"- 平均延迟: {latest['avg_latency_ms'] - baseline['avg_latency_ms']:+.0f}ms",
                f"- Token 消耗: {latest['total_tokens'] - baseline['total_tokens']:+d}",
            ])

        return "\n".join(lines)


# ============================================================================
# Part 3: 评估指标
# ============================================================================

def calculate_accuracy(
    predictions: list[str],
    ground_truth: list[str]
) -> float:
    """
    计算准确率。

    Args:
        predictions: 预测结果列表
        ground_truth: 真实标签列表

    Returns:
        准确率（0-1）
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("预测结果和真实标签数量不匹配")

    if len(predictions) == 0:
        return 0.0

    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    return correct / len(predictions)


def calculate_format_compliance(
    outputs: list[str],
    format_checker: Callable[[str], bool]
) -> float:
    """
    计算格式合规率。

    Args:
        outputs: LLM 输出列表
        format_checker: 格式检查函数

    Returns:
        合规率（0-1）
    """
    if len(outputs) == 0:
        return 0.0

    compliant = sum(1 for o in outputs if format_checker(o))
    return compliant / len(outputs)


def normalize_output(output: str) -> str:
    """标准化输出（去除空格、标点等）"""
    # 去除首尾空格
    output = output.strip()
    # 去除常见的前缀
    for prefix in ["分类：", "类别：", "答案：", "结果："]:
        if output.startswith(prefix):
            output = output[len(prefix):]
    return output.strip()


# ============================================================================
# Part 4: 评估器
# ============================================================================

class PromptEvaluator:
    """
    Prompt 评估器。

    核心功能：
    - 运行测试集
    - 计算评估指标
    - 生成对比报告

    Example:
        >>> evaluator = PromptEvaluator(test_cases)
        >>> result = evaluator.evaluate(build_prompt_func, parse_output_func, "v1")
        >>> print(result.summary())
    """

    def __init__(self, test_cases: list[TestCase]):
        self.test_cases = test_cases

    @classmethod
    def from_csv(cls, path: str) -> "PromptEvaluator":
        """从 CSV 文件创建评估器"""
        collection = TestCaseCollection.load_from_csv(path)
        return cls(collection.get_test_cases())

    def evaluate(
        self,
        call_llm: Callable[[str], str],
        build_prompt: Callable[[str], str],
        parse_output: Callable[[str], str],
        prompt_version: str = "v1",
        format_checker: Optional[Callable[[str], bool]] = None,
    ) -> EvalResult:
        """
        评估一个 Prompt 版本。

        Args:
            call_llm: 调用 LLM 的函数，接受 prompt，返回输出
            build_prompt: 构建 Prompt 的函数，接受输入文本，返回完整 Prompt
            parse_output: 解析输出的函数，接受原始输出，返回解析后的结果
            prompt_version: Prompt 版本号
            format_checker: 格式检查函数（可选）

        Returns:
            EvalResult 评估结果
        """
        predictions = []
        raw_outputs = []
        latencies = []
        total_tokens = 0  # 需要从 call_llm 获取，这里简化处理
        error_cases = []

        for case in self.test_cases:
            prompt = build_prompt(case.input)

            try:
                # 记录开始时间
                start = time.time()

                # 调用 LLM
                raw_output = call_llm(prompt)
                raw_outputs.append(raw_output)

                # 记录结束时间
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)

                # 解析输出
                parsed = parse_output(raw_output)
                predictions.append(parsed)

                # 检查正确性
                if parsed != case.expected_output:
                    error_cases.append({
                        "input": case.input,
                        "expected": case.expected_output,
                        "actual": parsed,
                        "raw_output": raw_output,
                    })

            except Exception as e:
                raw_outputs.append("")
                predictions.append("__PARSE_ERROR__")
                error_cases.append({
                    "input": case.input,
                    "expected": case.expected_output,
                    "error": str(e),
                })

        # 计算指标
        n = len(self.test_cases)
        correct = sum(1 for p, c in zip(predictions, [tc.expected_output for tc in self.test_cases]) if p == c)
        accuracy = correct / n if n > 0 else 0.0

        # 格式合规率
        if format_checker:
            format_compliance = calculate_format_compliance(raw_outputs, format_checker)
        else:
            # 默认：没有解析错误就算合规
            format_errors = sum(1 for p in predictions if p == "__PARSE_ERROR__")
            format_compliance = (n - format_errors) / n if n > 0 else 0.0

        # 平均延迟
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return EvalResult(
            prompt_version=prompt_version,
            accuracy=accuracy,
            format_compliance=format_compliance,
            avg_latency_ms=avg_latency,
            total_tokens=total_tokens,
            error_cases=error_cases,
        )

    def compare_versions(
        self,
        results: list[EvalResult]
    ) -> ComparisonReport:
        """对比多个 Prompt 版本"""
        if not results:
            raise ValueError("需要至少一个评估结果")

        report = ComparisonReport(baseline_version=results[0].prompt_version)
        for result in results:
            report.add_result(result)

        return report


# ============================================================================
# Part 5: 模拟 LLM 调用（用于演示）
# ============================================================================

def mock_llm_call(prompt: str) -> str:
    """
    模拟 LLM 调用（用于演示）。

    实际应用中应该替换为真实的 API 调用。
    """
    # 模拟延迟
    time.sleep(0.01)

    # 简单的关键词匹配模拟
    if "iPhone" in prompt or "芯片" in prompt or "AI" in prompt:
        return "科技"
    elif "股价" in prompt or "财报" in prompt or "央行" in prompt:
        return "财经"
    elif "比赛" in prompt or "球队" in prompt or "冠军" in prompt:
        return "体育"
    elif "演员" in prompt or "歌手" in prompt or "电影" in prompt:
        return "娱乐"
    else:
        return "其他"


# ============================================================================
# Part 6: 示例测试集
# ============================================================================

# 新闻分类测试集
NEWS_CLASSIFICATION_TEST_SET = TestCaseCollection(
    name="news_classification",
    version="1.0",
    cases=[
        {"input": "苹果公司发布新款 iPhone，搭载 A18 芯片", "expected_output": "科技", "metadata": {"difficulty": "easy"}},
        {"input": "央行宣布下调存款准备金率 0.5 个百分点", "expected_output": "财经", "metadata": {"difficulty": "easy"}},
        {"input": "中国男篮在亚运会决赛中战胜韩国队", "expected_output": "体育", "metadata": {"difficulty": "easy"}},
        {"input": "某知名演员宣布结婚消息", "expected_output": "娱乐", "metadata": {"difficulty": "easy"}},
        {"input": "特斯拉股价单日大涨 8%，创历史新高", "expected_output": "财经", "metadata": {"difficulty": "medium"}},
        {"input": "OpenAI 发布 GPT-5 模型，性能超越 GPT-4", "expected_output": "科技", "metadata": {"difficulty": "easy"}},
        {"input": "世界杯预选赛中国队战平日本队", "expected_output": "体育", "metadata": {"difficulty": "easy"}},
        {"input": "某歌手新专辑销量破百万，打破记录", "expected_output": "娱乐", "metadata": {"difficulty": "easy"}},
        {"input": "苹果财报显示营收超预期，iPhone 销量增长", "expected_output": "财经", "metadata": {"difficulty": "medium"}},
        {"input": "NBA 总决赛湖人队对阵勇士队", "expected_output": "体育", "metadata": {"difficulty": "easy"}},
    ]
)


# ============================================================================
# Part 7: 演示函数
# ============================================================================

def demo_test_set_construction() -> None:
    """演示测试集构建"""
    print("=" * 60)
    print("测试集构建")
    print("=" * 60)

    print(f"\n测试集名称: {NEWS_CLASSIFICATION_TEST_SET.name}")
    print(f"版本: {NEWS_CLASSIFICATION_TEST_SET.version}")
    print(f"用例数量: {len(NEWS_CLASSIFICATION_TEST_SET.cases)}")

    # 统计难度分布
    difficulties = {}
    for case in NEWS_CLASSIFICATION_TEST_SET.cases:
        d = case.get('metadata', {}).get('difficulty', 'unknown')
        difficulties[d] = difficulties.get(d, 0) + 1

    print(f"\n难度分布:")
    for d, count in difficulties.items():
        print(f"  {d}: {count}")

    # 显示部分用例
    print(f"\n前 3 个用例:")
    for i, case in enumerate(NEWS_CLASSIFICATION_TEST_SET.cases[:3], 1):
        print(f"  {i}. {case['input'][:30]}... -> {case['expected_output']}")

    # 保存到 CSV
    temp_path = "/tmp/test_set.csv"
    NEWS_CLASSIFICATION_TEST_SET.save_to_csv(temp_path)
    print(f"\n测试集已保存到: {temp_path}")


def demo_evaluation_metrics() -> None:
    """演示评估指标计算"""
    print("\n" + "=" * 60)
    print("评估指标计算")
    print("=" * 60)

    # 模拟预测结果
    predictions = ["科技", "财经", "体育", "娱乐", "财经", "科技", "体育", "娱乐", "财经", "体育"]
    ground_truth = ["科技", "财经", "体育", "娱乐", "财经", "科技", "体育", "娱乐", "财经", "体育"]

    # 人为添加一些错误
    predictions_with_errors = ["科技", "财经", "娱乐", "娱乐", "科技", "科技", "体育", "娱乐", "财经", "体育"]

    accuracy_perfect = calculate_accuracy(predictions, ground_truth)
    accuracy_with_errors = calculate_accuracy(predictions_with_errors, ground_truth)

    print(f"\n完美预测准确率: {accuracy_perfect:.1%}")
    print(f"有错误的预测准确率: {accuracy_with_errors:.1%}")

    # 格式合规率
    outputs = ["科技", "财经类", "体育", "这篇文章属于娱乐类", "财经", "科技", "体育", "娱乐", "财经", "体育"]

    def is_valid_format(output: str) -> bool:
        """检查输出是否是单个类别名（两个字）"""
        return output in ["科技", "财经", "体育", "娱乐"]

    compliance = calculate_format_compliance(outputs, is_valid_format)
    print(f"\n格式合规率: {compliance:.1%}")
    print(f"（8/10 个输出是有效格式）")


def demo_prompt_comparison() -> None:
    """演示 Prompt 版本对比"""
    print("\n" + "=" * 60)
    print("Prompt 版本对比")
    print("=" * 60)

    # 创建评估器
    test_cases = NEWS_CLASSIFICATION_TEST_SET.get_test_cases()
    evaluator = PromptEvaluator(test_cases)

    # 定义 Prompt 构建函数
    def build_prompt_v1(input_text: str) -> str:
        """Prompt v1: 无 Few-shot"""
        return f"""请分类以下新闻：

{input_text}"""

    def build_prompt_v2(input_text: str) -> str:
        """Prompt v2: 有四要素"""
        return f"""角色：你是一个新闻分类助手。

任务：判断以下新闻属于哪个类别。

约束：
- 只输出类别名称
- 不要解释原因

格式：从以下选项中选一个：财经、科技、体育、娱乐

新闻内容：{input_text}"""

    def parse_category(output: str) -> str:
        """解析分类结果"""
        return normalize_output(output)

    # 评估两个版本（使用模拟 LLM）
    print("\n评估 Prompt v1（无四要素）...")
    result_v1 = evaluator.evaluate(
        call_llm=mock_llm_call,
        build_prompt=build_prompt_v1,
        parse_output=parse_category,
        prompt_version="v1"
    )

    print("评估 Prompt v2（有四要素）...")
    result_v2 = evaluator.evaluate(
        call_llm=mock_llm_call,
        build_prompt=build_prompt_v2,
        parse_output=parse_category,
        prompt_version="v2"
    )

    # 打印结果
    print("\n" + "-" * 40)
    print(result_v1.summary())
    print("-" * 40)
    print(result_v2.summary())

    # 生成对比报告
    report = evaluator.compare_versions([result_v1, result_v2])
    print("\n" + report.to_markdown())


def demo_error_analysis() -> None:
    """演示错误分析"""
    print("\n" + "=" * 60)
    print("错误分析")
    print("=" * 60)

    # 模拟评估结果中的错误用例
    error_cases = [
        {
            "input": "苹果财报显示营收超预期，iPhone 销量增长",
            "expected": "财经",
            "actual": "科技",
            "raw_output": "科技"
        },
        {
            "input": "特斯拉发布新款电动车，同时宣布降价",
            "expected": "科技",
            "actual": "财经",
            "raw_output": "财经"
        },
    ]

    print("\n【错误用例分析】")

    for i, case in enumerate(error_cases, 1):
        print(f"\n错误 {i}:")
        print(f"  输入: {case['input']}")
        print(f"  期望: {case['expected']}")
        print(f"  实际: {case['actual']}")

        # 分析错误原因
        if "财报" in case['input'] or "营收" in case['input']:
            analysis = "可能是科技关键词干扰了财经判断"
        elif "降价" in case['input']:
            analysis = "可能是价格相关词汇触发了财经分类"
        else:
            analysis = "需要进一步分析"

        print(f"  分析: {analysis}")


def demo_avoiding_overfitting() -> None:
    """演示避免过拟合"""
    print("\n" + "=" * 60)
    print("避免过拟合测试集")
    print("=" * 60)

    tips = [
        ("测试集多样化", "覆盖不同长度、风格、来源的输入"),
        ("保留验证集", "测试集调参，验证集最终评估，只在上线前看一次"),
        ("定期更新测试集", "每周加入几条新的真实案例，防止 Prompt '老化'"),
        ("关注泛化能力", "不要只看测试集准确率，要看实际业务表现"),
    ]

    print("\n【避免过拟合的建议】")
    for i, (title, desc) in enumerate(tips, 1):
        print(f"{i}. {title}")
        print(f"   {desc}")

    print("\n【老潘的建议】")
    print("  '在公司里，我们还会做 A/B 测试——让新旧 Prompt 同时处理线上流量，")
    print("  看真实业务指标的变化。这比离线测试集更可靠，但成本也更高。'")


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("Prompt 评估框架演示")
    print("=" * 60)

    # 1. 测试集构建
    demo_test_set_construction()

    # 2. 评估指标
    demo_evaluation_metrics()

    # 3. Prompt 版本对比
    demo_prompt_comparison()

    # 4. 错误分析
    demo_error_analysis()

    # 5. 避免过拟合
    demo_avoiding_overfitting()


if __name__ == "__main__":
    main()
