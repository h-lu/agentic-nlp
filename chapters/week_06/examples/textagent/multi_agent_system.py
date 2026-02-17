#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：TextAgent 多智能体系统（Week 06）

本例是 Week 06 的 TextAgent 超级线代码，在 Week 05 单 Agent 基础之上，
增加了多智能体协作能力：
1. 规划者 Agent（PlannerAgent）：任务分解和计划制定
2. 执行者 Agent（ExecutorAgent）：工具调用和结果收集
3. 审核者 Agent（ReviewerAgent）：结果质量检查
4. 检索 Agent（RetrieverAgent）：Agentic RAG 能力
5. Human-in-the-Loop：关键决策点的人工审核

运行方式：
python3 chapters/week_06/examples/textagent/multi_agent_system.py

预期输出：
- 展示多 Agent 协作完成复杂任务
- 生成更新的 report.md

主要更新（Week 06）：
1. 多智能体架构（规划者-执行者-审核者）
2. Agent 间通信机制
3. Agentic RAG（自主检索策略）
4. Human-in-the-Loop 机制
"""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ============================================================
# 配置
# ============================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHAT_MODEL = "gpt-4o-mini"
REPORT_PATH = Path(__file__).parent.parent.parent / "report.md"


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


@dataclass
class Message:
    """Agent 之间的消息"""
    sender: str
    receiver: str
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


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
    规划者 Agent：专注于任务分解和计划制定

    职责：
    - 理解用户任务的意图
    - 将复杂任务分解为可执行的子任务
    - 根据反馈修订计划
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

    def create_plan(self, task: str, available_tools: List[str]) -> ExecutionPlan:
        """创建任务计划"""

        if self.llm is None:
            return self._mock_plan(task, available_tools)

        tools_desc = "\n".join([f"- {tool}" for tool in available_tools])

        prompt = f"""你是一个文档分析任务规划专家。

任务：{task}

可用工具：
{tools_desc}

请分析任务并制定执行计划。按 JSON 格式输出：

{{
  "task_understanding": "对任务的理解",
  "subtasks": [
    {{"step": 1, "action": "做什么", "tool": "工具名", "params": {{"参数": "值"}}}}
  ],
  "expected_output": "期望输出"
}}

计划（JSON）："""

        try:
            response = self.llm.chat.completions.create(
                model=CHAT_MODEL,
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
            print(f"[规划者] 计划生成失败: {e}")
            return self._mock_plan(task, available_tools)

    def revise_plan(self, original_plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """根据反馈修订计划"""
        if self.llm is None:
            print(f"[规划者] 模拟修订，反馈: {feedback}")
            revised = original_plan
            revised.status = "revised"
            return revised

        # 简化实现：添加修订标记
        revised = original_plan
        revised.status = "revised"
        return revised

    def _mock_plan(self, task: str, available_tools: List[str]) -> ExecutionPlan:
        """模拟模式：生成预设计划"""
        if "分析" in task and ("情感" in task or "态度" in task):
            return ExecutionPlan(
                task_understanding="分析文本的情感倾向",
                subtasks=[
                    SubTask(step=1, action="情感分析", tool="analyze_sentiment",
                           params={"text": "待分析文本"}),
                ],
                expected_output="情感分析结果"
            )
        elif "检索" in task or "搜索" in task or "政策" in task:
            return ExecutionPlan(
                task_understanding="检索相关文档",
                subtasks=[
                    SubTask(step=1, action="文档检索", tool="retrieve_documents",
                           params={"query": "查询词", "top_k": 5}),
                    SubTask(step=2, action="生成答案", tool="generate_answer",
                           params={}),
                ],
                expected_output="基于检索的答案"
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
    执行者 Agent：专注于按计划执行工具调用

    职责：
    - 按计划逐步执行子任务
    - 调用相应的工具
    - 收集执行结果
    """

    def __init__(self, tools: Dict[str, Callable]):
        self.tools = tools

    def execute_plan(
        self,
        plan: ExecutionPlan,
        retriever: Optional[RetrieverAgent] = None
    ) -> Dict[str, Any]:
        """执行计划"""

        results = []

        for subtask in plan.subtasks:
            subtask.status = "in_progress"

            print(f"  [执行者] 步骤 {subtask.step}: {subtask.action}")

            # 如果需要检索
            if subtask.tool == "retrieve_documents" and retriever:
                result = retriever.retrieve(subtask.params.get("query", ""))
                subtask.result = result
            elif subtask.tool and subtask.tool in self.tools:
                result = self.tools[subtask.tool](**subtask.params)
                subtask.result = result
            elif subtask.tool == "generate_answer":
                # 生成答案（简化）
                result = "基于检索结果生成的答案"
                subtask.result = result
            else:
                result = {"error": f"未知工具: {subtask.tool}"}
                subtask.result = result

            subtask.status = "completed"
            results.append({
                "step": subtask.step,
                "action": subtask.action,
                "result": result
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
    审核者 Agent：专注于结果质量检查

    职责：
    - 检查执行结果的完整性
    - 验证逻辑一致性
    - 给出最终评估
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

    def review_result(
        self,
        plan: ExecutionPlan,
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审核执行结果"""

        if self.llm is None:
            return self._mock_review(plan, execution_result)

        # 简化实现：基于规则的审核
        has_errors = any("error" in r.get("result", {}) for r in execution_result.get("results", []))

        if has_errors:
            return {
                "status": ApprovalStatus.NEEDS_REVISION,
                "issues": ["执行过程中出现错误"],
                "final_answer": None
            }
        else:
            return {
                "status": ApprovalStatus.APPROVED,
                "issues": [],
                "final_answer": "任务已完成"
            }

    def _mock_review(self, plan: ExecutionPlan, execution_result: Dict) -> Dict:
        """模拟审核"""
        return {
            "status": ApprovalStatus.APPROVED,
            "issues": [],
            "final_answer": "审核通过"
        }


# ============================================================
# 检索 Agent（Agentic RAG）
# ============================================================

class RetrievalStrategy(str, Enum):
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class RetrievalDecision:
    method: RetrievalStrategy
    top_k: int
    reasoning: str


@dataclass
class RetrievalResult:
    query: str
    strategy: RetrievalDecision
    documents: List[Dict[str, Any]]
    sufficient: bool


class RetrieverAgent:
    """
    检索 Agent：自主决定检索策略

    Week 06 新增：Agentic RAG 能力
    """

    def __init__(self, llm_client: Optional[OpenAI] = None):
        self.llm = llm_client or (OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY and OpenAI else None)
        # 模拟存储
        self.documents = [
            {"id": 1, "content": "远程办公政策：需提前3天申请，每周最多2天", "category": "政策"},
            {"id": 2, "content": "报销政策：费用发生后30天内提交", "category": "政策"},
            {"id": 3, "content": "GPU申请：需说明使用时长和用途", "category": "IT支持"},
        ]

    def retrieve(self, query: str) -> RetrievalResult:
        """自主检索"""

        # 决定检索策略
        decision = self._decide_strategy(query)

        # 执行检索
        documents = self._execute_retrieval(query, decision)

        return RetrievalResult(
            query=query,
            strategy=decision,
            documents=documents,
            sufficient=len(documents) >= 2
        )

    def _decide_strategy(self, query: str) -> RetrievalDecision:
        """决定检索策略"""
        if any(kw in query for kw in ["政策", "流程", "规定"]):
            return RetrievalDecision(
                method=RetrievalStrategy.KEYWORD,
                top_k=5,
                reasoning="查询包含精确匹配关键词，使用关键词检索"
            )
        else:
            return RetrievalDecision(
                method=RetrievalStrategy.VECTOR,
                top_k=5,
                reasoning="语义相似查询，使用向量检索"
            )

    def _execute_retrieval(self, query: str, decision: RetrievalDecision) -> List[Dict]:
        """执行检索"""
        # 简化实现：返回模拟文档
        return [
            {"id": d["id"], "content": d["content"], "score": 0.9 - i * 0.1}
            for i, d in enumerate(self.documents[:decision.top_k])
        ]


# ============================================================
# 多 Agent 工作流
# ============================================================

class MultiAgentWorkflow:
    """
    多 Agent 工作流：协调多个 Agent 协作完成复杂任务

    Week 06 核心更新：
    - 整合规划者、执行者、审核者、检索者
    - 实现 Agent 间协作
    - 支持 Human-in-the-Loop
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

        # 消息历史
        self.message_history: List[Dict] = []

    def run(
        self,
        task: str,
        enable_human_review: bool = False,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """运行完整工作流"""

        if verbose:
            print(f"\n{'='*60}")
            print(f"任务: {task}")
            print('='*60)

        # 1. 规划阶段
        if verbose:
            print("\n[阶段1] 规划者制定计划...")

        available_tools = list(self.executor.tools.keys())
        if self.retriever:
            available_tools.append("retrieve_documents")

        plan = self.planner.create_plan(task, available_tools)

        if verbose:
            print(f"  任务理解: {plan.task_understanding}")
            print(f"  子任务数: {len(plan.subtasks)}")

        # 人工审核（计划）
        if enable_human_review:
            approved, feedback = self._human_review("计划审核", plan)
            if not approved:
                plan = self.planner.revise_plan(plan, feedback)
                if verbose:
                    print(f"  计划已修订")

        # 2. 执行阶段
        if verbose:
            print("\n[阶段2] 执行者执行计划...")

        execution_result = self.executor.execute_plan(plan, self.retriever)

        # 人工审核（执行异常）
        if enable_human_review:
            errors = [r for r in execution_result.get("results", [])
                     if "error" in r.get("result", {})]
            if errors:
                approved, feedback = self._human_review("执行异常", {"errors": errors})
                if not approved:
                    return {"status": "aborted", "reason": "执行异常被拒绝"}

        # 3. 审核阶段
        if verbose:
            print("\n[阶段3] 审核者检查结果...")

        review = self.reviewer.review_result(plan, execution_result)

        if verbose:
            print(f"  审核状态: {review['status'].value}")

        # 人工审核（最终结果）
        if enable_human_review:
            if review["status"] != ApprovalStatus.APPROVED:
                approved, feedback = self._human_review("结果审核", review)
                if not approved:
                    # 修订计划并重新执行
                    plan = self.planner.revise_plan(plan, feedback)
                    execution_result = self.executor.execute_plan(plan, self.retriever)
                    review = self.reviewer.review_result(plan, execution_result)

        # 记录消息历史
        self._log_message(task, plan, execution_result, review)

        return {
            "task": task,
            "plan": plan,
            "execution": execution_result,
            "review": review,
            "status": "completed"
        }

    def _human_review(self, stage: str, data: Any) -> Tuple[bool, Optional[str]]:
        """人工审核"""
        print(f"\n【人工审核 - {stage}】")
        print(json.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, dict) else str(data))

        user_input = input("\n批准？(y=批准, n=拒绝, 或输入建议): ").strip()

        if user_input.lower() == 'y':
            print("✅ 已批准")
            return True, None
        else:
            print(f"❌ 拒绝/建议: {user_input if user_input else 'n'}")
            return False, user_input or "人工拒绝"

    def _log_message(self, task: str, plan: Any, execution: Any, review: Any) -> None:
        """记录消息历史"""
        self.message_history.append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "plan_steps": len(plan.subtasks) if hasattr(plan, 'subtasks') else 0,
            "execution_status": execution.get("status") if isinstance(execution, dict) else "unknown",
            "review_status": review.get("status").value if isinstance(review, dict) and "status" in review else "unknown"
        })


# ============================================================
# 工具定义
# ============================================================

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """情感分析（模拟）"""
    positive_words = ["满意", "好", "棒", "优秀", "喜欢"]
    negative_words = ["不满意", "差", "糟糕", "讨厌"]

    score = sum(1 for w in positive_words if w in text) - sum(1 for w in negative_words if w in text)

    if score > 0:
        return {"sentiment": "positive", "confidence": 0.8}
    elif score < 0:
        return {"sentiment": "negative", "confidence": 0.8}
    else:
        return {"sentiment": "neutral", "confidence": 0.5}


def extract_keywords(text: str, top_k: int = 5) -> Dict[str, Any]:
    """关键词提取（模拟）"""
    return {"keywords": ["产品", "质量", "服务", "客户"][:top_k]}


def direct_answer(message: str) -> str:
    """直接回答"""
    return f"收到: {message}"


# ============================================================
# 主函数
# ============================================================

def main():
    """主入口"""

    print("=" * 70)
    print("TextAgent 多智能体系统（Week 06）")
    print("=" * 70)

    # 检查依赖
    if OpenAI is None:
        print("\n错误：需要安装 openai 库")
        print("请运行：pip install openai")
        return

    if not OPENAI_API_KEY:
        print("\n警告：未设置 OPENAI_API_KEY")
        print("将使用模拟模式...")
        demo_mode = True
    else:
        demo_mode = False

    # 初始化 Agent
    print("\n[初始化] 创建多 Agent 系统...")

    llm_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    planner = PlannerAgent(llm_client)
    executor = ExecutorAgent({
        "analyze_sentiment": analyze_sentiment,
        "extract_keywords": extract_keywords,
        "direct_answer": direct_answer,
    })
    reviewer = ReviewerAgent(llm_client)
    retriever = RetrieverAgent(llm_client)

    # 创建工作流
    workflow = MultiAgentWorkflow(planner, executor, reviewer, retriever)

    print("✓ Agent 系统初始化完成")

    # 测试任务
    test_tasks = [
        "检索远程办公政策",
        "分析这句话的情感：我对公司的服务很满意",
        "总结并分析：产品质量好，但物流太慢",
    ]

    results = []

    for task in test_tasks:
        try:
            result = workflow.run(task, enable_human_review=False, verbose=True)
            results.append(result)
        except Exception as e:
            print(f"\n错误: {e}")
            results.append({"task": task, "error": str(e)})

    # 生成报告
    print("\n" + "=" * 70)
    print("生成报告...")
    print("=" * 70)

    generate_report(results, workflow)

    print(f"\n报告已写入: {REPORT_PATH}")

    # 总结
    print("\n" + "=" * 70)
    print("Week 06 更新总结")
    print("=" * 70)
    print("""
✨ 新增功能：
  1. 多智能体架构（规划者-执行者-审核者）
  2. Agentic RAG（自主检索策略）
  3. Human-in-the-Loop（关键决策点审核）
  4. Agent 间协作机制

📊 架构演进：
  Week 05: 单 Agent（ReAct）
  Week 06: 多 Agent（规划者-执行者-审核者-检索者）

🔄 下一步（Week 07）：
  - 评估与优化
  - 成本监控
  - 部署准备
    """)


def generate_report(results: List[Dict], workflow: MultiAgentWorkflow) -> None:
    """生成报告"""

    report_content = f"""# TextAgent 项目报告

## Week 06：多智能体协作系统

### 更新日期
{datetime.now().strftime("%Y-%m-%d")}

### 新增功能

1. **多智能体架构**
   - 规划者 Agent（PlannerAgent）：任务分解和计划制定
   - 执行者 Agent（ExecutorAgent）：工具调用和结果收集
   - 审核者 Agent（ReviewerAgent）：结果质量检查
   - 检索 Agent（RetrieverAgent）：Agentic RAG 能力

2. **Agentic RAG**
   - Agent 自主决定检索策略（向量/关键词/混合）
   - 检索结果质量评估
   - 支持多轮检索

3. **Human-in-the-Loop**
   - 计划审核：人工审核执行计划
   - 执行监控：异常时人工介入
   - 结果审核：最终结果人工确认

4. **Agent 协作机制**
   - 结构化消息传递
   - 共享状态管理
   - 完整的消息历史

### 架构演进

```
Week 04: 用户 → RAG → 检索 → LLM → 回答
Week 05: 用户 → Agent → [RAG | 工具] → 回答
Week 06: 用户 → 规划者 → 执行者 → 审核者 → 回答
               ↕ 检索者（Agentic RAG）
               ↕ 人工审核（Human-in-the-Loop）
```

### 评估结果

| 任务 | 计划步骤 | 执行状态 | 审核状态 |
|------|----------|----------|----------|
"""

    for r in results:
        if "error" not in r:
            plan_steps = len(r.get("plan", {}).get("subtasks", []))
            exec_status = r.get("execution", {}).get("status", "unknown")
            review_status = r.get("review", {}).get("status", "unknown")
            task_short = r.get("task", "")[:20]
            report_content += f"| {task_short} | {plan_steps} | {exec_status} | {review_status} |\n"

    report_content += f"""
### 消息历史

总消息数：{len(workflow.message_history)}

### 技术栈

- **LLM**: GPT-4o-mini
- **多智能体**: 自研框架
- **Agentic RAG**: 自主检索策略
- **通信**: 结构化消息 + 共享状态

### 下一步（Week 07）

- 评估与优化
- 成本监控
- 可观测性（Trace、日志）
- 部署准备（FastAPI）

---

*本报告由 TextAgent 多智能体系统自动生成*
"""

    # 写入报告
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)


if __name__ == "__main__":
    main()
