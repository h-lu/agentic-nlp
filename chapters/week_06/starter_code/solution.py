#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 06 作业参考实现

本文件是 Week 06 作业的参考实现，供学生在遇到困难时查看。
请注意：这只是基础实现的参考，进阶和挑战部分需要学生自己完成。

作业要求：
1. 实现规划者-执行者-审核者多 Agent 架构
2. 实现 Agent 间的通信机制
3. 实现 Agentic RAG（Agent 自主控制检索）
4. 实现 Human-in-the-Loop 机制

参考实现涵盖了基础要求，但不包含进阶/挑战部分。
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# 尝试导入 OpenAI
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
    print("警告：需要安装 openai 库。请运行：pip install openai")


# ============================================================
# 数据结构
# ============================================================

@dataclass
class SubTask:
    """子任务定义"""
    step: int
    action: str
    tool: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    status: str = "pending"
    result: Any = None


@dataclass
class ExecutionPlan:
    """执行计划"""
    task_understanding: str
    subtasks: List[SubTask]
    expected_output: str
    status: str = "planning"


class ApprovalStatus(str, Enum):
    """审核状态"""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


# ============================================================
# 规划者 Agent
# ============================================================

class PlannerAgent:
    """
    规划者 Agent：负责任务分解和计划制定

    职责：
    - 理解用户任务
    - 将任务分解为子任务
    - 根据反馈修订计划
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        if OpenAI is None:
            self.llm = None
        elif llm_client:
            self.llm = llm_client
        elif os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            self.llm = None

    def create_plan(self, task: str, available_tools: List[str]) -> ExecutionPlan:
        """创建执行计划"""

        if self.llm is None:
            # 模拟模式：基于规则生成计划
            return self._create_mock_plan(task, available_tools)

        # 使用 LLM 生成计划
        tools_desc = "\n".join([f"- {tool}" for tool in available_tools])

        prompt = f"""你是任务规划专家。请为以下任务制定执行计划。

任务：{task}

可用工具：
{tools_desc}

请输出 JSON 格式的计划：
{{
  "task_understanding": "任务理解",
  "subtasks": [
    {{"step": 1, "action": "动作描述", "tool": "工具名", "params": {{"参数": "值"}}}}
  ],
  "expected_output": "期望输出"
}}

计划："""

        try:
            response = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            plan_data = json.loads(response.choices[0].message.content)

            subtasks = []
            for st in plan_data.get("subtasks", []):
                subtasks.append(SubTask(
                    step=st["step"],
                    action=st["action"],
                    tool=st.get("tool"),
                    params=st.get("params"),
                ))

            return ExecutionPlan(
                task_understanding=plan_data["task_understanding"],
                subtasks=subtasks,
                expected_output=plan_data["expected_output"]
            )

        except Exception as e:
            print(f"规划失败: {e}")
            return self._create_mock_plan(task, available_tools)

    def revise_plan(self, plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """根据反馈修订计划"""
        # 简化实现：添加修订标记
        revised_plan = plan
        revised_plan.status = "revised"
        return revised_plan

    def _create_mock_plan(self, task: str, available_tools: List[str]) -> ExecutionPlan:
        """创建模拟计划"""
        if "分析" in task and "情感" in task:
            return ExecutionPlan(
                task_understanding="分析文本情感",
                subtasks=[
                    SubTask(step=1, action="情感分析", tool="analyze_sentiment",
                           params={"text": "待分析文本"}),
                ],
                expected_output="情感分析结果"
            )
        elif "检索" in task or "搜索" in task:
            return ExecutionPlan(
                task_understanding="检索相关文档",
                subtasks=[
                    SubTask(step=1, action="文档检索", tool="retrieve_documents",
                           params={"query": "查询词"}),
                ],
                expected_output="检索结果"
            )
        else:
            return ExecutionPlan(
                task_understanding=f"处理任务: {task}",
                subtasks=[
                    SubTask(step=1, action="直接响应", tool="direct_answer",
                           params={"message": task}),
                ],
                expected_output="响应结果"
            )


# ============================================================
# 执行者 Agent
# ============================================================

class ExecutorAgent:
    """
    执行者 Agent：负责按计划执行工具调用

    职责：
    - 按计划逐步执行子任务
    - 调用相应的工具
    - 收集执行结果
    """

    def __init__(self, tools: Dict[str, Callable]):
        self.tools = tools

    def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """执行计划"""

        results = []

        for subtask in plan.subtasks:
            subtask.status = "in_progress"

            print(f"[执行者] 步骤 {subtask.step}: {subtask.action}")

            if subtask.tool and subtask.tool in self.tools:
                try:
                    result = self.tools[subtask.tool](**subtask.params)
                    subtask.result = result
                    subtask.status = "completed"
                    results.append({
                        "step": subtask.step,
                        "action": subtask.action,
                        "result": result
                    })
                except Exception as e:
                    subtask.result = {"error": str(e)}
                    subtask.status = "failed"
                    results.append({
                        "step": subtask.step,
                        "action": subtask.action,
                        "error": str(e)
                    })
            else:
                # 没有指定工具或工具不存在
                subtask.status = "completed"
                results.append({
                    "step": subtask.step,
                    "action": subtask.action,
                    "result": "无需工具"
                })

        return {
            "plan": plan,
            "results": results,
            "status": "completed"
        }


# ============================================================
# 审核者 Agent
# ============================================================

class ReviewerAgent:
    """
    审核者 Agent：负责检查执行结果

    职责：
    - 检查结果完整性
    - 验证逻辑一致性
    - 给出审核结论
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        if OpenAI is None:
            self.llm = None
        elif llm_client:
            self.llm = llm_client
        elif os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            self.llm = None

    def review_result(
        self,
        plan: ExecutionPlan,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审核执行结果"""

        # 检查是否有错误
        errors = []
        for r in execution_result.get("results", []):
            if "error" in r:
                errors.append(r["error"])

        if errors:
            return {
                "status": ApprovalStatus.NEEDS_REVISION,
                "issues": errors,
                "final_answer": None
            }
        else:
            return {
                "status": ApprovalStatus.APPROVED,
                "issues": [],
                "final_answer": "审核通过"
            }


# ============================================================
# 检索 Agent（Agentic RAG）
# ============================================================

class RetrievalStrategy(str, Enum):
    """检索策略"""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class RetrievalDecision:
    """检索决策"""
    method: RetrievalStrategy
    top_k: int
    reasoning: str


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    strategy: RetrievalDecision
    documents: List[Dict[str, Any]]
    sufficient: bool


class RetrieverAgent:
    """
    检索 Agent：自主决定检索策略

    Week 06 核心功能：Agentic RAG
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        # LLM 客户端初始化：优先使用传入的客户端，其次尝试环境变量
        if llm_client is not None:
            self.llm = llm_client
        elif OpenAI is not None and os.environ.get("OPENAI_API_KEY"):
            self.llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            self.llm = None

        # 模拟文档存储
        self.documents = [
            {"id": 1, "content": "远程办公政策：需提前3天申请", "category": "政策"},
            {"id": 2, "content": "报销政策：30天内提交发票", "category": "政策"},
        ]

    def retrieve(self, query: str) -> RetrievalResult:
        """自主检索"""

        # 决定检索策略
        decision = self._decide_strategy(query)

        # 执行检索
        documents = self._execute_retrieval(query, decision)

        # 评估结果
        sufficient = len(documents) >= 2

        return RetrievalResult(
            query=query,
            strategy=decision,
            documents=documents,
            sufficient=sufficient
        )

    def _decide_strategy(self, query: str) -> RetrievalDecision:
        """决定检索策略"""
        # 简化实现：基于关键词选择
        if any(kw in query for kw in ["政策", "流程"]):
            return RetrievalDecision(
                method=RetrievalStrategy.KEYWORD,
                top_k=5,
                reasoning="查询包含精确关键词"
            )
        else:
            return RetrievalDecision(
                method=RetrievalStrategy.VECTOR,
                top_k=5,
                reasoning="语义相似查询"
            )

    def _execute_retrieval(self, query: str, decision: RetrievalDecision) -> List[Dict]:
        """执行检索"""
        # 简化实现：返回所有文档
        return [
            {"id": d["id"], "content": d["content"], "score": 0.9 - i * 0.1}
            for i, d in enumerate(self.documents[:decision.top_k])
        ]


# ============================================================
# 多 Agent 工作流
# ============================================================

class MultiAgentWorkflow:
    """
    多 Agent 工作流：协调多个 Agent 协作

    整合规划者、执行者、审核者、检索者
    """

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

    def run(self, task: str, verbose: bool = True) -> Dict[str, Any]:
        """运行完整工作流"""

        if verbose:
            print(f"\n任务: {task}")
            print("=" * 50)

        # 1. 规划阶段
        if verbose:
            print("\n[阶段1] 规划")

        available_tools = list(self.executor.tools.keys())
        if self.retriever:
            available_tools.append("retrieve_documents")

        plan = self.planner.create_plan(task, available_tools)

        if verbose:
            print(f"  理解: {plan.task_understanding}")
            print(f"  步骤: {len(plan.subtasks)}")

        # 2. 执行阶段
        if verbose:
            print("\n[阶段2] 执行")

        execution_result = self.executor.execute_plan(plan)

        # 3. 审核阶段
        if verbose:
            print("\n[阶段3] 审核")

        review = self.reviewer.review_result(plan, execution_result)

        if verbose:
            print(f"  状态: {review['status'].value}")

        return {
            "task": task,
            "plan": plan,
            "execution": execution_result,
            "review": review,
            "status": "completed"
        }


# ============================================================
# 工具函数（模拟）
# ============================================================

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """情感分析（模拟）"""
    if "满意" in text or "好" in text:
        return {"sentiment": "positive", "confidence": 0.8}
    elif "不满意" in text or "差" in text:
        return {"sentiment": "negative", "confidence": 0.8}
    else:
        return {"sentiment": "neutral", "confidence": 0.5}


def retrieve_documents(query: str) -> Dict[str, Any]:
    """检索文档（模拟）"""
    return {
        "query": query,
        "documents": [
            {"id": 1, "content": f"关于{query}的文档1"},
            {"id": 2, "content": f"关于{query}的文档2"},
        ]
    }


def direct_answer(message: str) -> str:
    """直接回答"""
    return f"收到: {message}"


# ============================================================
# 主函数（演示）
# ============================================================

def main():
    """主函数：演示多 Agent 系统"""

    print("=" * 60)
    print("Week 06 作业参考实现 - 多 Agent 系统")
    print("=" * 60)

    # 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n注意：未设置 OPENAI_API_KEY，使用模拟模式")

    # 初始化工具
    tools = {
        "analyze_sentiment": analyze_sentiment,
        "retrieve_documents": retrieve_documents,
        "direct_answer": direct_answer,
    }

    # 创建 Agent
    planner = PlannerAgent()
    executor = ExecutorAgent(tools)
    reviewer = ReviewerAgent()
    retriever = RetrieverAgent()

    # 创建工作流
    workflow = MultiAgentWorkflow(planner, executor, reviewer, retriever)

    # 测试任务
    test_tasks = [
        "分析这句话的情感：我对服务很满意",
        "检索远程办公政策",
    ]

    for task in test_tasks:
        result = workflow.run(task, verbose=True)

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)
    print("""
本参考实现展示了：
1. 规划者-执行者-审核者架构
2. Agent 间的基本协作
3. Agentic RAG 的简化实现

进阶挑战（未实现）：
- Human-in-the-Loop 机制
- 更复杂的 Agentic RAG（多轮检索）
- 消息总线通信机制
- 更完善的错误处理
    """)


if __name__ == "__main__":
    main()
