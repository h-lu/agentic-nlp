#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：LLM 应用评估（LLM Application Evaluation）

本例演示如何评估 LLM 应用的质量。从 RAG 评估（Week 04）扩展到
完整的应用评估：忠实度、相关性、正确性等。

核心概念：
- LLM-as-Judge：用 LLM 评估 LLM 的输出
- 评估指标：忠实度（Faithfulness）、相关性（Relevancy）
- 批量评估：运行测试集，汇总统计

运行方式：python3 chapters/week_07/examples/02_evaluation.py
预期输出：展示不同系统的评估分数对比

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


# ============================================================
# 配置
# ============================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# 数据结构
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
    faithfulness: float  # 忠实度：答案是否基于上下文
    relevancy: float  # 相关性：答案是否回答了问题


# ============================================================
# 评估器
# ============================================================

class LLMEvaluator:
    """
    LLM 应用评估器

    阿码问："用 LLM 评估 LLM？这靠谱吗？"

    老潘答：
    "LLM-as-Judge 不是完美的，但它足够一致。
    关键不是'绝对分数'，而是'相对差异'——
    系统 A 的忠实度比系统 B 高 0.1，这才是有价值的信号。"
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        if OpenAI is None:
            self.llm = None
        elif llm_client:
            self.llm = llm_client
        elif OPENAI_API_KEY:
            self.llm = OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.llm = None

    def calculate_faithfulness(
        self,
        answer: str,
        context: str,
        judge_llm: Optional[OpenAI] = None
    ) -> float:
        """
        计算忠实度（Faithfulness）

        忠实度：答案是否基于给定的上下文，没有幻觉

        评分标准：
        - 1.0：完全基于上下文
        - 0.5：部分基于上下文
        - 0.0：完全脱离上下文（幻觉）
        """
        if not self.llm:
            return self._mock_faithfulness(answer, context)

        prompt = f"""你是一个评估专家。请评估以下答案是否基于给定的上下文。

上下文：
{context}

答案：
{answer}

请评估答案的忠实度（0-1 分），并给出简短理由。
要求只输出 JSON 格式：{{"score": 0.8, "reason": "..."}}"""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            result = json.loads(response.choices[0].message.content)
            return float(result.get("score", 0.5))
        except Exception:
            return self._mock_faithfulness(answer, context)

    def calculate_relevancy(
        self,
        query: str,
        answer: str,
        judge_llm: Optional[OpenAI] = None
    ) -> float:
        """
        计算相关性（Relevancy）

        相关性：答案是否直接回答了问题

        评分标准：
        - 1.0：完全回答
        - 0.5：部分回答
        - 0.0：没有回答
        """
        if not self.llm:
            return self._mock_relevancy(query, answer)

        prompt = f"""你是一个评估专家。请评估答案是否直接回答了问题。

问题：
{query}

答案：
{answer}

请评估答案的相关性（0-1 分），并给出简短理由。
要求只输出 JSON 格式：{{"score": 0.9, "reason": "..."}}"""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            result = json.loads(response.choices[0].message.content)
            return float(result.get("score", 0.5))
        except Exception:
            return self._mock_relevancy(query, answer)

    def evaluate_batch(
        self,
        test_cases: List[TestCase],
        system_fn: Callable[[str], str]
    ) -> Dict[str, Any]:
        """
        批量评估测试用例

        Args:
            test_cases: 测试用例列表
            system_fn: 被测试的系统函数，输入 query，输出 answer

        Returns:
            包含详细结果和汇总指标的字典
        """
        results = []

        print(f"\n评估 {len(test_cases)} 个测试用例...")

        for i, case in enumerate(test_cases, 1):
            # 运行系统
            actual = system_fn(case.query)

            # 计算指标
            faithfulness = self.calculate_faithfulness(
                actual, case.context
            )
            relevancy = self.calculate_relevancy(
                case.query, actual
            )

            results.append(EvalResult(
                query=case.query,
                expected=case.expected,
                actual=actual,
                faithfulness=faithfulness,
                relevancy=relevancy
            ))

            print(f"  [{i}/{len(test_cases)}] {case.query[:30]}... "
                  f"F={faithfulness:.2f} R={relevancy:.2f}")

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

    def _mock_faithfulness(self, answer: str, context: str) -> float:
        """模拟忠实度评估"""
        if not context:
            return 0.5
        # 简单规则：答案中是否包含上下文的关键词
        context_words = set(context.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(context_words & answer_words)
        return min(0.9, 0.3 + overlap * 0.1)

    def _mock_relevancy(self, query: str, answer: str) -> float:
        """模拟相关性评估"""
        if not answer:
            return 0.0
        # 简单规则：答案长度合理，就认为相关
        if len(answer) < 10:
            return 0.3
        elif len(answer) > 200:
            return 0.6  # 太长可能是废话
        else:
            return 0.8


# ============================================================
# 模拟系统
# ============================================================

class SystemA:
    """系统 A：单 Agent（基线）"""

    def __init__(self):
        self.name = "单 Agent 系统"

    def query(self, question: str) -> str:
        # 模拟：简单但可能不够准确
        responses = {
            "远程办公": "需要提前申请，具体流程请咨询 HR",
            "报销": "费用发生后提交发票和申请单",
            "GPU": "GPU 资源紧张，建议提前一周申请",
        }
        for key, value in responses.items():
            if key in question:
                return value
        return "抱歉，我无法回答这个问题"


class SystemB:
    """系统 B：多 Agent（改进版）"""

    def __init__(self):
        self.name = "多 Agent 系统"

    def query(self, question: str) -> str:
        # 模拟：更详细和准确
        responses = {
            "远程办公": "根据公司政策，远程办公需提前 3 天申请，每周最多 2 天。请在 OA 系统提交申请，并抄送直属领导。",
            "报销": "费用发生后 30 天内提交报销申请。请准备：1) 发票原件 2) 报销单 3) 相关证明材料。提交至财务部，审核通过后 5 个工作日到账。",
            "GPU": "GPU 申请流程：1) 填写 GPU 申请表，说明使用时长和用途 2) 主管审批 3) IT 部门分配资源。建议提前 3-5 天申请，高峰期可能需要更长时间。",
        }
        for key, value in responses.items():
            if key in question:
                return value
        return "让我检索一下相关信息...\n抱歉，我没有找到相关信息，建议您咨询相关部门。"


class SystemC:
    """系统 C：多 Agent 但有幻觉"""

    def __init__(self):
        self.name = "多 Agent 系统（有幻觉）"

    def query(self, question: str) -> str:
        # 模拟：详细但可能不准确
        responses = {
            "远程办公": "根据公司政策，远程办公需提前 5 天申请，每周最多 3 天。特殊情况可以申请长期远程办公，需副总裁批准。",
            "报销": "费用发生后 7 天内提交报销申请。支持电子发票，最高报销额度 5000 元。",
            "GPU": "GPU 资源充足，随时申请即可使用。A100 实例最多可申请 4 个，使用时长不限。",
        }
        for key, value in responses.items():
            if key in question:
                return value
        return "这个问题涉及到公司战略，我需要更多信息才能回答。"


# ============================================================
# 反例：没有评估的问题
# ============================================================

def show_evaluation_importance():
    """展示评估的重要性"""
    print("\n" + "=" * 70)
    print("为什么需要评估？")
    print("=" * 70)
    print("""
小北上周实现了多 Agent 系统，兴奋地向老板演示。

老板问两个问题：
1. "这比原来的单 Agent 好多少？"
2. "成本增加了多少？"

小北愣住了——他只能回答"它能规划、能协作、能检索"，
但说不出"好多少"和"贵多少"。

老潘点评：
"没有评估，你就是在卖'感觉'而不是'数据'。
老板不会为'感觉'买单，但会为'数据'买单。

评估的价值：
1. 对比不同系统的性能
2. 发现系统的弱点
3. 指导优化方向
4. 向利益相关者证明价值
    """)


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    """主入口"""

    print("=" * 70)
    print("LLM 应用评估演示")
    print("=" * 70)

    # 创建评估器
    evaluator = LLMEvaluator()

    # 准备测试集
    test_cases = [
        TestCase(
            query="远程办公怎么申请？",
            expected="需要提前3天申请，每周最多2天",
            context="公司政策：远程办公需提前3天申请，每周最多2天，需在OA系统提交。"
        ),
        TestCase(
            query="报销流程是什么？",
            expected="费用发生后30天内提交",
            context="财务政策：费用发生后30天内提交报销申请，需发票和申请单。"
        ),
        TestCase(
            query="怎么申请GPU？",
            expected="需说明使用时长和用途",
            context="IT支持：GPU申请需说明使用时长和用途，建议提前申请。"
        ),
    ]

    # 创建系统
    systems = [SystemA(), SystemB(), SystemC()]

    # 评估所有系统
    results = {}

    for system in systems:
        print(f"\n{'='*70}")
        print(f"评估: {system.name}")
        print('='*70)

        result = evaluator.evaluate_batch(test_cases, system.query)
        results[system.name] = result

    # 对比结果
    print("\n" + "=" * 70)
    print("评估结果对比")
    print("=" * 70)

    print(f"\n{'系统':<25} {'忠实度':<10} {'相关性':<10} {'总分':<10}")
    print("-" * 70)

    for name, result in results.items():
        print(f"{name:<25} {result['avg_faithfulness']:<10.3f} "
              f"{result['avg_relevancy']:<10.3f} {result['overall_score']:<10.3f}")

    # 分析
    print("\n" + "=" * 70)
    print("分析")
    print("=" * 70)

    best_system = max(results.items(), key=lambda x: x[1]["overall_score"])
    print(f"\n最佳系统: {best_system[0]} (总分: {best_system[1]['overall_score']:.3f})")

    # 找出问题
    for name, result in results.items():
        if result["avg_faithfulness"] < 0.7:
            print(f"\n⚠️ {name} 的忠实度偏低 ({result['avg_faithfulness']:.3f})")
            print("   建议：检查系统是否产生幻觉，答案是否基于检索到的上下文")

        if result["avg_relevancy"] < 0.7:
            print(f"\n⚠️ {name} 的相关性偏低 ({result['avg_relevancy']:.3f})")
            print("   建议：检查系统是否真正回答了用户问题")

    # 展示评估的重要性
    show_evaluation_importance()

    # 使用建议
    print("\n" + "=" * 70)
    print("评估最佳实践")
    print("=" * 70)
    print("""
1. 建立测试集
   - 覆盖常见场景
   - 包含边界情况
   - 定期更新

2. 选择合适的指标
   - 忠实度：基于 RAG 场景
   - 相关性：所有场景
   - 正确性：有标准答案的场景

3. 持续评估
   - 每次代码改动后运行
   - 记录评估历史
   - 设置质量阈值

4. 理解指标含义
   - 绝对分数不如相对差异
   - 关注趋势而非单次结果
   - 结合业务理解

老潘的建议：
"评估不是为了证明系统'足够好'，
而是为了发现'哪里还不够好'。
把评估当作质量雷达，而不是成绩单。"
    """)


if __name__ == "__main__":
    main()
