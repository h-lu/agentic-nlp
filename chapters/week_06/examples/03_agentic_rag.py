#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：Agentic RAG（Agent 自主控制检索）

本例演示 Agentic RAG 与传统 RAG 的区别：
- 传统 RAG：系统硬编码检索逻辑，用户问问题就检索一次
- Agentic RAG：Agent 自主决定是否检索、用什么策略、检索结果够不够好

核心思想：
- 检索权从系统转移到 Agent
- Agent 可以动态选择检索策略
- Agent 可以评估检索结果质量
- Agent 可以决定是否重新检索

运行方式：python3 chapters/week_06/examples/03_agentic_rag.py
预期输出：展示 Agent 如何自主控制检索过程

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI


# ============================================================
# 数据结构
# ============================================================

class RetrievalStrategy(str, Enum):
    """检索策略"""
    VECTOR = "vector"  # 向量检索
    KEYWORD = "keyword"  # 关键词检索
    HYBRID = "hybrid"  # 混合检索
    MULTI_ROUND = "multi_round"  # 多轮检索


@dataclass
class RetrievalDecision:
    """检索决策"""
    method: RetrievalStrategy
    top_k: int
    reasoning: str  # 为什么选择这个策略
    improved_query: Optional[str] = None  # 改进后的查询


@dataclass
class RetrievalAssessment:
    """检索结果评估"""
    sufficient: bool
    confidence: float  # 0-1
    missing_aspects: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    strategy: RetrievalDecision
    documents: List[Dict[str, Any]]
    assessment: RetrievalAssessment
    iterations: int = 1  # 检索轮次


# ============================================================
# 模拟的存储
# ============================================================

class VectorStore:
    """向量存储（模拟）"""

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """向量检索"""
        # 模拟：返回基于查询的"相关"文档
        return [
            {"id": i, "content": f"向量检索结果{i}：关于{query}的语义相关内容", "score": 0.9 - i * 0.1}
            for i in range(1, min(top_k + 1, 6))
        ]


class KeywordIndex:
    """关键词索引（模拟）"""

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """关键词检索"""
        # 模拟：返回包含关键词的文档
        return [
            {"id": i + 10, "content": f"关键词检索结果{i}：{query}完全匹配的内容", "score": 1.0 - i * 0.1}
            for i in range(1, min(top_k + 1, 6))
        ]


# ============================================================
# 检索 Agent
# ============================================================

class RetrieverAgent:
    """
    检索 Agent：自主决定检索策略

    核心能力：
    - 分析查询，决定最佳检索策略
    - 执行检索
    - 评估检索结果质量
    - 决定是否需要重新检索
    """

    def __init__(
        self,
        vector_store: VectorStore,
        keyword_index: KeywordIndex,
        llm_client: Optional[OpenAI] = None
    ):
        self.vector_store = vector_store
        self.keyword_index = keyword_index
        self.llm = llm_client
        self.max_iterations = 3  # 最多检索轮次

    def retrieve(self, query: str, context: Optional[str] = None) -> RetrievalResult:
        """自主检索"""

        iteration = 0
        current_query = query

        while iteration < self.max_iterations:
            iteration += 1

            # 第一步：Agent 决定检索策略
            decision = self._decide_strategy(current_query, context, iteration)

            # 第二步：按策略检索
            documents = self._execute_retrieval(current_query, decision)

            # 第三步：Agent 评估检索结果
            assessment = self._assess_results(current_query, documents, context)

            # 第四步：如果结果足够好，返回结果
            if assessment.sufficient:
                return RetrievalResult(
                    query=query,
                    strategy=decision,
                    documents=documents,
                    assessment=assessment,
                    iterations=iteration
                )

            # 第五步：如果结果不够好，准备重新检索
            if iteration < self.max_iterations:
                current_query = decision.improved_query or self._improve_query(current_query, assessment)
                context = f"上一次检索未找到足够的信息。缺失的方面：{', '.join(assessment.missing_aspects)}"
                print(f"  [检索 Agent] 结果不够充分，改进查询后重新检索...")

        # 达到最大迭代次数
        return RetrievalResult(
            query=query,
            strategy=decision,
            documents=documents,
            assessment=assessment,
            iterations=iteration
        )

    def _decide_strategy(
        self,
        query: str,
        context: Optional[str],
        iteration: int
    ) -> RetrievalDecision:
        """决定检索策略"""

        if self.llm is None:
            # 模拟模式：基于规则
            return self._rule_based_decision(query, iteration)

        prompt = f"""你是一个检索策略专家。请分析以下查询，决定最佳检索策略。

查询：{query}
上下文：{context or "无"}
当前检索轮次：{iteration}

可用策略：
- vector: 向量检索，适合语义相似查询
- keyword: 关键词检索，适合精确匹配查询
- hybrid: 混合检索，结合向量和关键词，适合复杂查询
- multi_round: 多轮检索，先检索再扩展查询

请按以下 JSON 格式输出决策：

{{
  "method": "vector/keyword/hybrid/multi_round",
  "top_k": 数字（建议3-10）,
  "reasoning": "选择该策略的原因",
  "improved_query": "改进后的查询（如需要，否则为null）"
}}

决策："""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            decision_text = response.choices[0].message.content
            decision_data = json.loads(decision_text)

            return RetrievalDecision(
                method=RetrievalStrategy(decision_data["method"]),
                top_k=decision_data.get("top_k", 5),
                reasoning=decision_data["reasoning"],
                improved_query=decision_data.get("improved_query")
            )
        except Exception as e:
            print(f"  [检索 Agent] 决策失败: {e}，使用规则决策")
            return self._rule_based_decision(query, iteration)

    def _rule_based_decision(
        self,
        query: str,
        iteration: int
    ) -> RetrievalDecision:
        """基于规则的决策（模拟模式）"""
        # 第一次检索：如果是精确匹配类型，用关键词；否则用向量
        if iteration == 1:
            if any(keyword in query for keyword in ["政策", "流程", "编号", "订单号"]):
                return RetrievalDecision(
                    method=RetrievalStrategy.KEYWORD,
                    top_k=5,
                    reasoning="查询包含精确匹配关键词，使用关键词检索",
                    improved_query=None
                )
            else:
                return RetrievalDecision(
                    method=RetrievalStrategy.VECTOR,
                    top_k=5,
                    reasoning="查询是语义相似类型，使用向量检索",
                    improved_query=None
                )

        # 第二次检索：使用混合检索
        elif iteration == 2:
            return RetrievalDecision(
                method=RetrievalStrategy.HYBRID,
                top_k=8,
                reasoning="上一次检索结果不足，使用混合检索获取更多结果",
                improved_query=self._expand_query(query)
            )

        # 第三次检索：多轮检索
        else:
            return RetrievalDecision(
                method=RetrievalStrategy.MULTI_ROUND,
                top_k=10,
                reasoning="使用多轮检索，先检索再扩展",
                improved_query=None
            )

    def _expand_query(self, query: str) -> str:
        """扩展查询（添加相关词）"""
        expansions = {
            "政策": ["规定", "制度", "办法"],
            "流程": ["步骤", "方法", "操作"],
            "申请": ["请求", "提交", "办理"],
        }
        for key, values in expansions.items():
            if key in query:
                return f"{query} {' '.join(values)}"
        return query

    def _improve_query(self, query: str, assessment: RetrievalAssessment) -> str:
        """根据评估结果改进查询"""
        if assessment.missing_aspects:
            # 添加缺失的方面
            return f"{query} {' '.join(assessment.missing_aspects)}"
        return self._expand_query(query)

    def _execute_retrieval(self, query: str, decision: RetrievalDecision) -> List[Dict[str, Any]]:
        """执行检索"""

        print(f"  [检索 Agent] 使用策略: {decision.method.value}")
        print(f"  [检索 Agent] 检索数量: {decision.top_k}")
        print(f"  [检索 Agent] 决策理由: {decision.reasoning}")

        if decision.method == RetrievalStrategy.VECTOR:
            return self.vector_store.search(query, decision.top_k)
        elif decision.method == RetrievalStrategy.KEYWORD:
            return self.keyword_index.search(query, decision.top_k)
        elif decision.method == RetrievalStrategy.HYBRID:
            # 混合检索：合并向量和关键词结果
            vector_results = self.vector_store.search(query, decision.top_k // 2 + 1)
            keyword_results = self.keyword_index.search(query, decision.top_k // 2 + 1)
            # 简单合并
            return vector_results[:decision.top_k // 2] + keyword_results[:decision.top_k // 2]
        else:  # MULTI_ROUND
            # 先向量检索，再扩展查询
            results = self.vector_store.search(query, decision.top_k)
            expanded_query = self._expand_query(query)
            additional = self.vector_store.search(expanded_query, decision.top_k // 2)
            return results + additional

    def _assess_results(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        context: Optional[str]
    ) -> RetrievalAssessment:
        """评估检索结果是否足够"""

        if self.llm is None:
            # 模拟模式：基于规则
            return self._rule_based_assessment(documents, len(documents))

        prompt = f"""请评估以下检索结果是否足够回答用户查询。

查询：{query}
上下文：{context or "无"}
检索到的文档数：{len(documents)}
文档摘要：{json.dumps(documents[:3], ensure_ascii=False)[:200]}...

请按以下 JSON 格式输出评估：

{{
  "sufficient": true/false,
  "confidence": 数字(0-1),
  "missing_aspects": ["缺失的方面1", "缺失的方面2"],
  "reasoning": "评估理由"
}}

评估："""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            assessment_text = response.choices[0].message.content
            assessment_data = json.loads(assessment_text)

            return RetrievalAssessment(
                sufficient=assessment_data["sufficient"],
                confidence=assessment_data.get("confidence", 0.5),
                missing_aspects=assessment_data.get("missing_aspects", []),
                reasoning=assessment_data.get("reasoning", "")
            )
        except Exception as e:
            print(f"  [检索 Agent] 评估失败: {e}，使用规则评估")
            return self._rule_based_assessment(documents, len(documents))

    def _rule_based_assessment(
        self,
        documents: List[Dict[str, Any]],
        doc_count: int
    ) -> RetrievalAssessment:
        """基于规则的评估（模拟模式）"""
        # 简化规则：如果文档数 >= 3 且有高分文档，就认为足够
        high_score_docs = [d for d in documents if d.get("score", 0) > 0.7]

        if doc_count >= 3 and len(high_score_docs) >= 2:
            return RetrievalAssessment(
                sufficient=True,
                confidence=0.8,
                reasoning=f"检索到 {doc_count} 个文档，其中 {len(high_score_docs)} 个高质量文档"
            )
        else:
            return RetrievalAssessment(
                sufficient=False,
                confidence=0.4,
                missing_aspects=["更多相关文档", "更高质量的内容"],
                reasoning=f"仅检索到 {doc_count} 个文档，质量可能不足"
            )


# ============================================================
# 反例：传统 RAG
# ============================================================

def traditional_rag_example():
    """
    反例：传统 RAG 的局限性

    传统 RAG 的问题：
    1. 检索策略硬编码，无法根据查询类型调整
    2. 只检索一次，结果不好无法改进
    3. 没有结果评估，不知道检索质量如何
    """

    class TraditionalRAG:
        """❌ 传统 RAG（硬编码检索逻辑）"""

        def __init__(self, vector_store):
            self.vector_store = vector_store

        def query(self, user_query: str):
            # 问题1: 硬编码的检索策略
            results = self.vector_store.search(user_query, top_k=5)

            # 问题2: 不评估结果质量
            # 问题3: 无法重新检索
            return {
                "results": results,
                "answer": f"基于检索结果生成答案：{results[0]['content'] if results else '未找到相关内容'}"
            }

    print("❌ 传统 RAG 的问题：")
    print("  1. 检索策略硬编码（永远是向量检索，top_k=5）")
    print("  2. 只检索一次，结果不好就没办法了")
    print("  3. 不评估结果质量，不知道检索是否成功")
    print("\n✅ Agentic RAG 的优势：")
    print("  1. Agent 自主决定检索策略")
    print("  2. 可以多轮检索，不断改进")
    print("  3. 评估结果质量，知道何时足够")


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("Agentic RAG 演示")
    print("=" * 70)

    # 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n警告：未设置 OPENAI_API_KEY 环境变量")
        print("请运行：export OPENAI_API_KEY='your-api-key'")
        print("\n将使用模拟模式演示...")
        demo_mode = True
    else:
        demo_mode = False
    llm_client = None if demo_mode else OpenAI()

    # 初始化存储
    vector_store = VectorStore()
    keyword_index = KeywordIndex()

    # 创建检索 Agent
    retriever = RetrieverAgent(
        vector_store=vector_store,
        keyword_index=keyword_index,
        llm_client=llm_client
    )

    # 测试查询
    test_queries = [
        "远程办公政策是什么？",  # 适合关键词检索
        "如何提高工作效率？",  # 适合向量检索
        "GPU申请流程和审批要求",  # 复杂查询，可能需要混合检索
    ]

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"用户查询: {query}")
        print('='*70)

        # 执行 Agentic RAG
        result = retriever.retrieve(query)

        # 显示结果
        print(f"\n{'='*70}")
        print("检索结果:")
        print('='*70)
        print(f"检索轮次: {result.iterations}")
        print(f"最终策略: {result.strategy.method.value}")
        print(f"策略理由: {result.strategy.reasoning}")
        print(f"结果充分: {result.assessment.sufficient}")
        print(f"评估置信度: {result.assessment.confidence if hasattr(result.assessment, 'confidence') else 'N/A'}")
        print(f"检索到的文档数: {len(result.documents)}")

        print("\n文档列表:")
        for doc in result.documents:
            print(f"  - [{doc['id']}] {doc['content']} (score: {doc.get('score', 'N/A')})")

    # 对比说明
    print("\n" + "=" * 70)
    print("传统 RAG vs Agentic RAG")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 维度              │  传统 RAG          │  Agentic RAG          │
├─────────────────────────────────────────────────────────────────┤
│ 触发方式          │  用户问问题就检索    │  Agent 决定是否检索   │
│ 检索策略          │  硬编码（固定）      │  动态选择             │
│ 检索次数          │  一次               │  可能多轮             │
│ 结果使用          │  直接使用           │  Agent 评估后决定     │
│ 控制权            │  系统控制           │  Agent 控制           │
│ 可解释性          │  低（为什么检索这些？）│ 高（有决策理由）      │
└─────────────────────────────────────────────────────────────────┘

Agentic RAG 的核心价值：
1. 检索权从系统转移到 Agent
2. Agent 可以"思考"后再检索
3. Agent 可以评估结果质量
4. Agent 可以不断改进检索策略

老潘的点评：
"传统 RAG 像是'无脑检索'——无论什么问题都用同样的策略。
Agentic RAG 像是'专业检索员'——会根据问题类型选择最合适的检索方式。
在企业应用中，这种智能检索能大幅提高准确率和用户满意度。"

阿码的追问：那 Agentic RAG 成本不是更高吗？

答案：是的，每次检索决策都需要 LLM 调用。
但有两种优化方案：
1. 简单查询用传统 RAG（低成本）
2. 复杂查询用 Agentic RAG（高准确率）
3. 缓存常见查询的检索策略

这就是 Week 04 学的"查询路由"的动态版本！
    """)

    # 展示反例
    print("\n" + "=" * 70)
    print("反例：传统 RAG 的局限性")
    print("=" * 70)
    traditional_rag_example()


if __name__ == "__main__":
    main()
