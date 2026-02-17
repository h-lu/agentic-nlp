"""
Week 08 参考实现
包含端到端系统、商业价值计算、A/B 测试、灰度发布等核心功能
"""

import hashlib
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel


# ============================================================================
# Part 1: 端到端系统架构
# ============================================================================

@dataclass
class TaskContext:
    """任务上下文——贯穿整个工作流"""
    task_id: str
    user_input: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)


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
    """工作流编排器——端到端系统的核心"""

    def __init__(self, agents: Dict[str, Agent], capabilities: Dict[str, Capability]):
        self.agents = agents
        self.capabilities = capabilities

    def run(self, user_input: str) -> Dict[str, Any]:
        """端到端执行"""
        # 1. 创建上下文
        context = TaskContext(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            user_input=user_input,
            metadata={},
            state={}
        )

        start_time = time.time()

        try:
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
            review_result = None
            if plan.get("enable_review"):
                review_result = self.agents["reviewer"].review(context, execution_result)
                context.state["review"] = review_result

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "task_id": context.task_id,
                "result": execution_result,
                "review": review_result,
                "cost_usd": context.state.get("cost_usd", 0.035),
                "latency_ms": latency_ms
            }

        except Exception as e:
            return {
                "task_id": context.task_id,
                "error": str(e),
                "cost_usd": 0,
                "latency_ms": int((time.time() - start_time) * 1000)
            }


# ============================================================================
# Part 1.2: 配置管理
# ============================================================================

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    llm: LLMConfig
    system_prompt: str
    enable_cache: bool = True
    timeout_seconds: int = 30


class SystemConfig(BaseModel):
    """系统配置"""
    agents: Dict[str, AgentConfig]
    retriever: Dict[str, Any] = field(default_factory=dict)
    observability: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "SystemConfig":
        """从 YAML 文件加载配置"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str):
        """保存为 YAML 文件"""
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


# ============================================================================
# Part 2: 商业价值计算
# ============================================================================

class BusinessValueCalculator:
    """商业价值计算器"""

    def __init__(self, cost_per_request: float, manual_cost_per_request: float):
        self.cost_per_request = cost_per_request
        self.manual_cost_per_request = manual_cost_per_request

    def calculate_savings(self, daily_requests: int, days: int = 30) -> Dict:
        """计算节省的成本"""
        total_requests = daily_requests * days

        # 系统成本
        system_cost = total_requests * self.cost_per_request

        # 人力成本
        manual_cost = total_requests * self.manual_cost_per_request

        # 节省
        savings = manual_cost - system_cost
        savings_percentage = (savings / manual_cost * 100) if manual_cost > 0 else 0

        return {
            "period_days": days,
            "total_requests": total_requests,
            "system_cost_usd": system_cost,
            "manual_cost_usd": manual_cost,
            "savings_usd": savings,
            "savings_percentage": savings_percentage
        }

    def calculate_roi(self, investment_usd: float, savings_per_month: float,
                      months: int = 12) -> Dict:
        """计算投资回报率"""
        total_savings = savings_per_month * months
        roi_percentage = ((total_savings - investment_usd) / investment_usd * 100) if investment_usd > 0 else 0

        # 回本周期（天）
        payback_days = (investment_usd / savings_per_month * 30) if savings_per_month > 0 else float("inf")

        return {
            "total_investment": investment_usd,
            "total_savings": total_savings,
            "roi_percentage": roi_percentage,
            "payback_period_days": int(payback_days)
        }


# ============================================================================
# Part 2.3: 回滚方案
# ============================================================================

@dataclass
class RollbackPlan:
    """回滚方案"""
    trigger_conditions: Dict[str, Any]
    rollback_action: str
    fallback_system: Optional[str] = None


class ProductionSystem:
    """生产系统（带回滚能力）"""

    def __init__(self, orchestrator: WorkflowOrchestrator):
        self.orchestrator = orchestrator
        self.rollback_plan = RollbackPlan(
            trigger_conditions={
                "error_rate_threshold": 0.05,
                "cost_threshold_usd_per_hour": 50,
                "latency_threshold_ms": 10000
            },
            rollback_action="switch_to_manual",
            fallback_system="legacy_system"
        )
        self.metrics = {
            "error_rate": 0.0,
            "hourly_cost_usd": 0.0,
            "p95_latency_ms": 0.0
        }

    def check_health(self) -> bool:
        """检查系统健康状态"""
        if self.metrics["error_rate"] > self.rollback_plan.trigger_conditions["error_rate_threshold"]:
            return False
        if self.metrics["hourly_cost_usd"] > self.rollback_plan.trigger_conditions["cost_threshold_usd_per_hour"]:
            return False
        if self.metrics["p95_latency_ms"] > self.rollback_plan.trigger_conditions["latency_threshold_ms"]:
            return False
        return True

    def run_with_safety_net(self, user_input: str) -> Dict:
        """带安全网运行"""
        try:
            if not self.check_health():
                return self._fallback(user_input)

            return self.orchestrator.run(user_input)

        except Exception as e:
            return self._fallback(user_input)

    def _fallback(self, user_input: str) -> Dict:
        """降级方案"""
        if self.rollback_plan.fallback_system == "manual":
            return {"status": "escalated", "message": "转人工处理"}
        else:
            return {"status": "fallback", "message": "使用旧系统"}


# ============================================================================
# Part 4: A/B 测试框架
# ============================================================================

Version = Literal["A", "B"]


class ABTestConfig:
    """A/B 测试配置"""

    def __init__(self, name: str, description: str, traffic_split: float = 0.5):
        self.name = name
        self.description = description
        self.traffic_split = traffic_split
        self.start_time = datetime.now()


class ABTestEngine:
    """A/B 测试引擎"""

    def __init__(self, config: ABTestConfig):
        self.config = config
        self.results: Dict[Version, List[Dict]] = {"A": [], "B": []}

    def assign_version(self, user_id: str) -> Version:
        """为用户分配版本（基于哈希保证一致性）"""
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return "B" if (hash_val % 100) < (self.config.traffic_split * 100) else "A"

    def record_result(self, version: Version, metrics: Dict):
        """记录结果"""
        self.results[version].append({
            "timestamp": datetime.now().isoformat(),
            **metrics
        })

    def analyze(self) -> Dict:
        """分析 A/B 测试结果"""
        from scipy import stats

        # 提取质量分数
        a_values = [r.get("quality_score", 0) for r in self.results["A"]]
        b_values = [r.get("quality_score", 0) for r in self.results["B"]]

        if not a_values or not b_values:
            return {"error": "样本量不足"}

        # t 检验
        t_stat, p_value = stats.ttest_ind(a_values, b_values)

        # 计算均值
        a_mean = sum(a_values) / len(a_values)
        b_mean = sum(b_values) / len(b_values)

        # 判断是否显著
        is_significant = p_value < 0.05
        winner = "B" if b_mean > a_mean else "A"

        # 计算提升
        lift = ((b_mean - a_mean) / a_mean * 100) if a_mean > 0 else 0

        return {
            "test_name": self.config.name,
            "sample_size": {"A": len(a_values), "B": len(b_values)},
            "mean_quality": {"A": a_mean, "B": b_mean},
            "lift": lift,
            "p_value": p_value,
            "is_significant": is_significant,
            "winner": winner if is_significant else "inconclusive"
        }


# ============================================================================
# Part 5: 灰度发布控制器
# ============================================================================

class CanaryDeployment:
    """灰度发布控制器"""

    def __init__(self, stages: List[Dict]):
        self.stages = sorted(stages, key=lambda x: x["day"])
        self.current_stage = 0
        self.start_date = datetime.now()

    def get_traffic_percentage(self) -> float:
        """获取当前应该分配给新版本的流量比例"""
        days_elapsed = (datetime.now() - self.start_date).days

        for i, stage in enumerate(self.stages):
            if days_elapsed >= stage["day"]:
                self.current_stage = i

        return self.stages[self.current_stage]["traffic_percentage"]

    def should_use_new_version(self, user_id: str) -> bool:
        """判断是否使用新版本"""
        traffic_pct = self.get_traffic_percentage()
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_val % 100) < traffic_pct

    def check_rollback_conditions(self, metrics: Dict) -> bool:
        """检查是否需要回滚"""
        if metrics.get("error_rate", 0) > 0.05:
            return True
        if metrics.get("cost_increase_pct", 0) > 20:
            return True
        return False

    def advance_stage(self) -> bool:
        """手动推进到下一阶段"""
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            return True
        return False


# ============================================================================
# 简化的 Agent 实现（用于演示）
# ============================================================================

class SimplePlanner(Agent):
    """简化的规划 Agent"""

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {
            "need_retrieval": True,
            "enable_review": True,
            "steps": ["分析需求", "检索知识", "执行工具", "审核结果"]
        }


class SimpleExecutor(Agent):
    """简化的执行 Agent"""

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "这是一个简化的执行结果",
            "status": "completed"
        }


class SimpleRetriever(Agent):
    """简化的检索 Agent"""

    def retrieve(self, context: TaskContext) -> Dict[str, Any]:
        return {
            "docs": ["文档1", "文档2"],
            "count": 2
        }


class SimpleReviewer(Agent):
    """简化的审核 Agent"""

    def review(self, context: TaskContext, result: Dict) -> Dict[str, Any]:
        return {
            "approved": True,
            "quality_score": 0.85
        }


# ============================================================================
# 系统初始化函数
# ============================================================================

def create_system(config_path: Optional[str] = None) -> WorkflowOrchestrator:
    """创建完整的端到端系统"""
    # 创建能力层
    capabilities = {}

    # 创建 Agent
    agents = {
        "planner": SimplePlanner(),
        "executor": SimpleExecutor(),
        "retriever": SimpleRetriever(),
        "reviewer": SimpleReviewer()
    }

    # 创建编排器
    orchestrator = WorkflowOrchestrator(agents, capabilities)

    return orchestrator


# ============================================================================
# 演示代码
# ============================================================================

def demo_system():
    """演示端到端系统"""
    print("=" * 60)
    print("TextAgent 端到端系统演示")
    print("=" * 60)

    # 创建系统
    system = create_system()

    # 运行测试
    result = system.run("分析客户反馈并总结主要问题")

    print(f"\n任务 ID: {result['task_id']}")
    print(f"成本: ${result['cost_usd']:.4f}")
    print(f"延迟: {result['latency_ms']} ms")
    print(f"结果: {result['result']}")


def demo_business_value():
    """演示商业价值计算"""
    print("\n" + "=" * 60)
    print("商业价值计算演示")
    print("=" * 60)

    calculator = BusinessValueCalculator(
        cost_per_request=0.035,
        manual_cost_per_request=2.50
    )

    report = calculator.calculate_savings(daily_requests=1000, days=90)

    print(f"\n90 天节省成本: ${report['savings_usd']:.2f}")
    print(f"节省比例: {report['savings_percentage']:.1f}%")

    roi_report = calculator.calculate_roi(
        investment_usd=50000,
        savings_per_month=report['savings_usd'] / 3
    )

    print(f"ROI: {roi_report['roi_percentage']:.1f}%")
    print(f"回本周期: {roi_report['payback_period_days']} 天")


def demo_ab_test():
    """演示 A/B 测试"""
    print("\n" + "=" * 60)
    print("A/B 测试演示")
    print("=" * 60)

    config = ABTestConfig(
        name="prompt_v2_vs_v1",
        description="测试优化后的 Prompt",
        traffic_split=0.5
    )

    engine = ABTestEngine(config)

    # 模拟数据
    import random
    for i in range(50):
        user_id = f"user_{i}"
        version = engine.assign_version(user_id)
        engine.record_result(version, {
            "quality_score": 0.82 + random.uniform(-0.05, 0.05) if version == "A" else 0.87 + random.uniform(-0.05, 0.05)
        })

    analysis = engine.analyze()
    print(f"\n胜者: {analysis['winner']}")
    print(f"提升: {analysis['lift']:.1f}%")
    print(f"统计显著性: {analysis['is_significant']}")


def demo_canary():
    """演示灰度发布"""
    print("\n" + "=" * 60)
    print("灰度发布演示")
    print("=" * 60)

    canary = CanaryDeployment([
        {"day": 1, "traffic_percentage": 5},
        {"day": 3, "traffic_percentage": 25},
        {"day": 7, "traffic_percentage": 50},
        {"day": 14, "traffic_percentage": 100}
    ])

    print(f"\n当前流量比例: {canary.get_traffic_percentage()}%")

    # 测试用户分配
    test_users = [f"user_{i}" for i in range(100)]
    new_version_count = sum(1 for user in test_users if canary.should_use_new_version(user))

    print(f"新版本用户数: {new_version_count}/100")


if __name__ == "__main__":
    demo_system()
    demo_business_value()
    demo_ab_test()
    demo_canary()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
