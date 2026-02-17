"""
示例 1: 端到端系统架构

展示了如何设计模块化、解耦的 LLM 应用系统架构。
核心概念：
- TaskContext: 任务上下文，贯穿整个工作流
- Capability: 能力抽象接口
- Agent: 智能体抽象接口
- WorkflowOrchestrator: 工作流编排器
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class TaskContext:
    """任务上下文——贯穿整个工作流

    像一辆"数据巴士"，把各个模块连起来。
    每个模块只从巴士上拿自己需要的数据，把结果放回巴士。
    """
    task_id: str
    user_input: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)  # 各模块共享的状态


class Capability(ABC):
    """能力的抽象接口"""

    @abstractmethod
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """执行能力，返回结果"""
        pass


class Agent(ABC):
    """Agent 的抽象接口"""

    @abstractmethod
    def plan(self, context: TaskContext) -> Dict[str, Any]:
        """规划任务"""
        pass

    @abstractmethod
    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行计划"""
        pass


class WorkflowOrchestrator:
    """工作流编排器——端到端系统的核心

    负责调度整个工作流：创建上下文、规划、执行、审核
    """

    def __init__(self, agents: Dict[str, Agent], capabilities: Dict[str, Capability]):
        self.agents = agents
        self.capabilities = capabilities

    def _generate_id(self) -> str:
        """生成唯一任务 ID"""
        return str(uuid.uuid4())

    def run(self, user_input: str) -> Dict[str, Any]:
        """端到端执行

        Args:
            user_input: 用户输入

        Returns:
            包含任务结果、成本、延迟等信息的字典
        """
        # 1. 创建上下文
        context = TaskContext(
            task_id=self._generate_id(),
            user_input=user_input,
            metadata={},
            state={}
        )

        # 2. 规划阶段
        plan = self.agents["planner"].plan(context)
        context.state["plan"] = plan

        # 3. 执行阶段（可能需要检索）
        if plan.get("need_retrieval"):
            retrieval_result = self.agents["retriever"].retrieve(context)
            context.state["retrieval"] = retrieval_result

        execution_result = self.agents["executor"].execute(context, plan)
        context.state["execution"] = execution_result

        # 4. 审核阶段（可选）
        if plan.get("enable_review"):
            review_result = self.agents["reviewer"].review(context, execution_result)
            context.state["review"] = review_result

        return {
            "task_id": context.task_id,
            "result": execution_result,
            "review": context.state.get("review"),
            "cost_usd": context.state.get("cost_usd", 0),
            "latency_ms": context.state.get("latency_ms", 0)
        }


# 示例：简单的 Mock 实现（用于测试）

class MockCapability(Capability):
    """Mock 能力实现"""

    def execute(self, context: TaskContext) -> Dict[str, Any]:
        return {"status": "success", "data": f"Processed: {context.user_input}"}


class MockAgent(Agent):
    """Mock Agent 实现"""

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {
            "need_retrieval": False,
            "enable_review": False,
            "steps": ["analyze"]
        }

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "completed",
            "output": f"Analyzed: {context.user_input}"
        }


class MockPlannerAgent(Agent):
    """Mock 规划 Agent"""

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        # 根据输入内容决定是否需要检索和审核
        need_retrieval = "检索" in context.user_input or "search" in context.user_input.lower()
        enable_review = "审核" in context.user_input or "review" in context.user_input.lower()

        return {
            "need_retrieval": need_retrieval,
            "enable_review": enable_review,
            "steps": ["plan", "execute"]
        }

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "planned"}


class MockExecutorAgent(Agent):
    """Mock 执行 Agent"""

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {"steps": ["execute"]}

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        # 模拟添加成本和延迟
        context.state["cost_usd"] = 0.035
        context.state["latency_ms"] = 150

        return {
            "status": "completed",
            "output": f"Executed: {context.user_input}",
            "quality_score": 0.85
        }


class MockRetrieverAgent(Agent):
    """Mock 检索 Agent"""

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {"steps": ["retrieve"]}

    def retrieve(self, context: TaskContext) -> Dict[str, Any]:
        return {
            "status": "retrieved",
            "documents": ["doc1", "doc2"]
        }

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return self.retrieve(context)


class MockReviewerAgent(Agent):
    """Mock 审核 Agent"""

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {"steps": ["review"]}

    def review(self, context: TaskContext, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "approved",
            "confidence": 0.9
        }

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "reviewed"}


def create_mock_orchestrator() -> WorkflowOrchestrator:
    """创建用于测试的 Mock Orchestrator"""
    agents = {
        "planner": MockPlannerAgent(),
        "executor": MockExecutorAgent(),
        "retriever": MockRetrieverAgent(),
        "reviewer": MockReviewerAgent()
    }

    capabilities = {
        "llm": MockCapability(),
        "rag": MockCapability()
    }

    return WorkflowOrchestrator(agents, capabilities)


if __name__ == "__main__":
    # 使用示例
    orchestrator = create_mock_orchestrator()

    result = orchestrator.run("分析这份数据")
    print("Result:", result)

    result_with_review = orchestrator.run("分析并审核这份数据")
    print("Result with review:", result_with_review)
