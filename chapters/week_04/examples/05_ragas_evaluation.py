#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGAS 评估框架演示

本示例演示如何使用 RAGAS 框架评估 RAG 系统的效果，
包括 Faithfulness、Answer Relevance、Context Precision、Context Recall 等指标。

运行方式：python3 chapters/week_04/examples/05_ragas_evaluation.py
预期输出：stdout 输出评估结果和对比分析

依赖：ragas, 需要设置 OPENAI_API_KEY
"""

from __future__ import annotations

import os
from typing import List, Dict
from dataclasses import dataclass

# 尝试导入，如果失败则提供友好的错误信息
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False


# ============================================================
# 数据结构
# ============================================================

@dataclass
class EvaluationResult:
    """评估结果"""
    faithfulness: float  # 忠实度：回答是否基于上下文
    answer_relevancy: float  # 答案相关性：回答是否针对问题
    context_precision: float  # 上下文精确度：检索到的文档有多少相关
    context_recall: float  # 上下文召回率：是否找到所有需要的文档


# ============================================================
# 模拟评估器（用于演示，不依赖 RAGAS）
# ============================================================

class MockRagasEvaluator:
    """模拟 RAGAS 评估器（用于演示）"""

    def __init__(self):
        print("使用模拟 RAGAS 评估器")
        print("（实际使用时请安装 ragas：pip install ragas）")

    def evaluate(self, dataset: Dict) -> Dict:
        """模拟评估"""
        questions = dataset["question"]
        answers = dataset["answer"]
        contexts = dataset["contexts"]
        ground_truths = dataset.get("ground_truth", [""] * len(questions))

        results = []
        for i, (q, a, ctx) in enumerate(zip(questions, answers, contexts)):
            # 简单的模拟评分逻辑
            # 实际 RAGAS 会用 LLM 进行更复杂的评估

            # Faithfulness：检查答案是否包含上下文中没有的信息
            faith = self._mock_faithfulness(a, ctx)

            # Answer Relevance：检查答案是否回答了问题
            relevance = self._mock_relevance(a, q)

            # Context Precision：检查上下文有多少相关
            precision = self._mock_precision(q, ctx)

            # Context Recall：检查是否找到所有需要的上下文
            recall = self._mock_recall(q, ctx, ground_truths[i] if i < len(ground_truths) else "")

            results.append({
                "faithfulness": faith,
                "answer_relevancy": relevance,
                "context_precision": precision,
                "context_recall": recall,
            })

        # 计算平均值
        avg_result = {
            "faithfulness": sum(r["faithfulness"] for r in results) / len(results),
            "answer_relevancy": sum(r["answer_relevancy"] for r in results) / len(results),
            "context_precision": sum(r["context_precision"] for r in results) / len(results),
            "context_recall": sum(r["context_recall"] for r in results) / len(results),
        }

        return avg_result

    def _mock_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """模拟忠实度评估"""
        # 简化：答案长度适中则认为忠实
        if 20 <= len(answer) <= 200:
            return 0.85 + (hash(answer) % 10) / 100
        return 0.7

    def _mock_relevance(self, answer: str, question: str) -> float:
        """模拟相关性评估"""
        # 简化：问题和答案有共同词则认为相关
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        overlap = len(q_words & a_words) / max(len(q_words), 1)
        return min(0.9, 0.6 + overlap)

    def _mock_precision(self, question: str, contexts: List[str]) -> float:
        """模拟精确度评估"""
        # 简化：假设 70-90% 的上下文相关
        return 0.75 + (hash(question) % 15) / 100

    def _mock_recall(self, question: str, contexts: List[str], ground_truth: str) -> float:
        """模拟召回率评估"""
        # 简化：假设 70-85% 的召回
        return 0.72 + (hash(question) % 13) / 100


# ============================================================
# 演示：RAGAS 评估指标
# ============================================================

def demo_ragas_metrics():
    """演示 RAGAS 的评估指标"""
    print("=" * 70)
    print("场景 1：RAG 评估的三个维度")
    print("=" * 70)

    metrics_explanation = [
        {
            "维度": "检索质量",
            "指标": "Context Precision\nContext Recall",
            "含义": "检索到的文档相关吗？\n找到所有需要的文档了吗？",
            "重要性": "决定了 LLM 有多少"正确材料"可用",
        },
        {
            "维度": "生成质量",
            "指标": "Faithfulness\nAnswer Relevance",
            "含义": "回答是否基于检索到的文档？\n回答是否针对问题？",
            "重要性": "决定了回答的质量和准确性",
        },
        {
            "维度": "端到端效果",
            "指标": "用户满意度\n任务完成率",
            "含义": "用户是否满意？\n用户是否完成了目标？",
            "重要性": "最终的业务价值",
        },
    ]

    print("\n评估维度：\n")
    for item in metrics_explanation:
        print(f"【{item['维度']}】")
        print(f"  指标：{item['指标']}")
        print(f"  含义：{item['含义']}")
        print(f"  重要性：{item['重要性']}")
        print()

    print("【指标解读】")
    print("- Faithfulness > 0.8：优秀（没有幻觉）")
    print("- Answer Relevance > 0.8：优秀（回答针对问题）")
    print("- Context Precision > 0.8：优秀（检索精准）")
    print("- Context Recall > 0.7：良好（找到足够信息）")


# ============================================================
# 演示：运行评估
# ============================================================

def demo_run_evaluation():
    """演示运行一次评估"""
    print("\n" + "=" * 70)
    print("场景 2：运行评估 - 量化你的 RAG 系统")
    print("=" * 70)

    # 准备评估数据
    evaluation_data = {
        "question": [
            "2024年报假政策是什么？",
            "GPU资源怎么申请？",
            "TB级别存储怎么申请？"
        ],
        "answer": [
            "根据2024年报假政策，员工每年可享受5天年假，需提前7天申请。",
            "GPU资源需要填写资源申请表，经部门经理审批后由IT部门分配。",
            "单个项目最多申请10TB存储空间，需提交存储资源申请表。"
        ],
        "contexts": [
            ["2024年报假政策：员工每年可享受5天年假，需提前7天申请。"],
            ["GPU资源申请流程：需要填写资源申请表，经部门经理审批。"],
            ["TB级别存储申请：单个项目最多申请10TB存储空间。"]
        ],
        "ground_truth": [
            "5天年假，提前7天申请",
            "填写申请表，部门经理审批",
            "最多10TB"
        ]
    }

    print("\n【测试数据】")
    for i, q in enumerate(evaluation_data["question"], 1):
        print(f"{i}. 问题：{q}")
        print(f"   回答：{evaluation_data['answer'][i-1][:50]}...")
        print()

    # 运行评估
    print("【运行评估】\n")

    if RAGAS_AVAILABLE:
        # 使用真实的 RAGAS
        dataset = Dataset.from_dict(evaluation_data)
        result = evaluate(
            dataset,
            metrics=[
                context_precision,
                faithfulness,
                answer_relevancy,
                context_recall
            ]
        )
        print("评估完成！\n")
        print(result.to_pandas())
    else:
        # 使用模拟评估器
        print("（使用模拟评估器演示）\n")
        evaluator = MockRagasEvaluator()
        result = evaluator.evaluate(evaluation_data)

        print("\n评估结果：\n")
        print(f"{'指标':<20} | {'分数':<10} | {'评级'}")
        print("-" * 45)
        print(f"{'Faithfulness':<20} | {result['faithfulness']:<10.2f} | {'优秀' if result['faithfulness'] > 0.8 else '良好'}")
        print(f"{'Answer Relevance':<20} | {result['answer_relevancy']:<10.2f} | {'优秀' if result['answer_relevancy'] > 0.8 else '良好'}")
        print(f"{'Context Precision':<20} | {result['context_precision']:<10.2f} | {'优秀' if result['context_precision'] > 0.8 else '良好'}")
        print(f"{'Context Recall':<20} | {result['context_recall']:<10.2f} | {'优秀' if result['context_recall'] > 0.7 else '良好'}")


# ============================================================
# 演示：A/B 测试对比
# ============================================================

def demo_ab_testing():
    """演示 A/B 测试对比不同配置"""
    print("\n" + "=" * 70)
    print("场景 3：A/B 测试 - 数据驱动优化")
    print("=" * 70)

    # 模拟不同配置的评估结果
    configs = [
        {
            "name": "A: 纯向量检索",
            "faithfulness": 0.72,
            "answer_relevancy": 0.68,
            "context_precision": 0.65,
            "context_recall": 0.78,
        },
        {
            "name": "B: 混合检索",
            "faithfulness": 0.79,
            "answer_relevancy": 0.75,
            "context_precision": 0.76,
            "context_recall": 0.82,
        },
        {
            "name": "C: 混合检索 + 重排序",
            "faithfulness": 0.89,
            "answer_relevancy": 0.85,
            "context_precision": 0.87,
            "context_recall": 0.85,
        },
    ]

    print("\n不同配置的评估结果：\n")
    print(f"{'配置':<25} | {'忠实度':<10} | {'答案相关性':<12} | {'上下文精确度':<14} | {'召回率':<10}")
    print("-" * 90)

    for config in configs:
        print(f"{config['name']:<25} | {config['faithfulness']:<10} | {config['answer_relevancy']:<12} | {config['context_precision']:<14} | {config['context_recall']:<10}")

    print("\n【分析】")
    print("- 配置 A → B：混合检索带来显著提升")
    print("  - Context Precision: 0.65 → 0.76 (+17%)")
    print("  - Faithfulness: 0.72 → 0.79 (+10%)")
    print("\n- 配置 B → C：重排序进一步提升")
    print("  - Faithfulness: 0.79 → 0.89 (+13%)")
    print("  - Context Precision: 0.76 → 0.87 (+15%)")

    print("\n【老潘点评】")
    print('"在公司里，我们不会凭感觉说"变好了"——必须有数据和 A/B 对比。')
    print('现在你可以说：混合检索 + 重排序相比纯向量检索，')
    print('忠实度提升了 23%，上下文精确度提升了 34%。')
    print('这才是能说服老板的报告。'")


# ============================================================
# 演示：如何改进低分指标
# ============================================================

def demo_improvement_guide():
    """演示如何针对低分指标进行改进"""
    print("\n" + "=" * 70)
    print("场景 4：改进指南 - 低分指标怎么办？")
    print("=" * 70)

    issues_and_solutions = [
        {
            "问题": "Faithfulness 低 (< 0.7)",
            "原因": "LLM 产生幻觉，编造了上下文中没有的信息",
            "解决方案": [
                "改进 Prompt，明确要求只基于上下文回答",
                "添加 Source 引用，让 LLM 标注信息来源",
                "降低 temperature 参数，减少随机性",
                "使用重排序，提升输入上下文的质量",
            ]
        },
        {
            "问题": "Answer Relevance 低 (< 0.7)",
            "原因": "回答没有直接针对问题，或者答非所问",
            "解决方案": [
                "改进 Prompt，要求直接回答问题",
                "使用查询重写，让问题更清晰",
                "增加检索的文档数量，提供更多上下文",
                "检查检索到的上下文是否真的相关",
            ]
        },
        {
            "问题": "Context Precision 低 (< 0.7)",
            "原因": "检索到的很多文档不相关",
            "解决方案": [
                "使用混合检索（向量 + BM25）",
                "使用重排序，过滤不相关文档",
                "调整 chunk_size，让文档块更聚焦",
                "使用查询重写，提升检索准确性",
            ]
        },
        {
            "问题": "Context Recall 低 (< 0.6)",
            "原因": "没有找到所有需要的文档",
            "解决方案": [
                "增加检索的文档数量（top_k）",
                "使用查询扩展，从多个角度检索",
                "检查文档分块策略，避免信息被切断",
                "添加更多相关文档到知识库",
            ]
        },
    ]

    for item in issues_and_solutions:
        print(f"\n【{item['问题']}】")
        print(f"原因：{item['原因']}")
        print(f"解决方案：")
        for i, solution in enumerate(item['解决方案'], 1):
            print(f"  {i}. {solution}")


# ============================================================
# 演示：评估报告模板
# ============================================================

def demo_report_template():
    """演示评估报告的模板"""
    print("\n" + "=" * 70)
    print("场景 5：评估报告模板 - 记录到 report.md")
    print("=" * 70)

    report_template = """```markdown
## Week 04：高级 RAG 优化评估

### 优化内容

1. 混合检索（向量 + BM25）
   - 解决精确匹配问题（年份、型号、专有名词）
   - RRF 融合策略：alpha=0.5（向量和 BM25 各占一半）

2. 查询重写
   - 用 LLM 将模糊查询改写为清晰查询
   - 示例："报销" → "费用报销申请流程和所需材料"

3. 重排序
   - 使用 BGE-reranker-base 模型
   - 从 Top-20 候选中精选 Top-3

### 效果对比（RAGAS 评估）

| 配置 | 忠实度 | 答案相关性 | 上下文精确度 | 召回率 | 平均延迟 |
|------|--------|-----------|-------------|--------|---------|
| 纯向量（Week 03） | 0.72 | 0.68 | 0.65 | 0.78 | 0.8s |
| + 混合检索 | 0.79 | 0.75 | 0.76 | 0.82 | 1.2s |
| + 查询重写 | 0.82 | 0.79 | 0.78 | 0.84 | 1.5s |
| + 重排序（完整版） | 0.89 | 0.85 | 0.87 | 0.85 | 2.1s |

### 结论

- 混合检索显著提升精确匹配场景（+11% 上下文精确度）
- 重排序是性价比最高的优化（+10% 忠实度，+0.9s 延迟）
- 查询重写对模糊查询特别有效（+5%），但对清晰查询帮助有限

### 下一步

- Week 05：Agent 能力——让 TextAgent 会调用工具
```
"""

    print("\n【报告模板】\n")
    print(report_template)


# ============================================================
# 主函数
# ============================================================

def main():
    """主入口"""
    print("\n" + "=" * 70)
    print("    RAGAS 评估框架完整演示")
    print("    从"感觉好多了"到"忠实度提升 23%"")
    print("=" * 70 + "\n")

    # 检查依赖
    if not RAGAS_AVAILABLE:
        print("注意：ragas 未安装，使用模拟评估器演示")
        print("安装命令：pip install ragas")
        print("（实际使用时需要安装并设置 OPENAI_API_KEY）\n")

    # 运行演示
    demo_ragas_metrics()
    demo_run_evaluation()
    demo_ab_testing()
    demo_improvement_guide()
    demo_report_template()

    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n【关键要点】")
    print("1. RAGAS 用 LLM-as-Judge 评估 RAG 系统")
    print("2. 四个核心指标：Faithfulness、Answer Relevance、Context Precision、Context Recall")
    print("3. A/B 测试：用数据对比不同配置的效果")
    print("4. 低分指标：有对应的改进策略")
    print("5. 评估报告：记录优化过程和效果")
    print("\n【下一步】")
    print("- Week 04 完整示例：99_textagent.py - 将所有优化集成到 TextAgent")


if __name__ == "__main__":
    main()
