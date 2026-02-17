#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：TextAgent 终稿系统整合（TextAgent Final Integration）

本例展示 Week 08 TextAgent 的终稿状态——一个端到端的、
可展示、可交付、可维护的 Agentic 文本分析系统。

核心整合：
- 端到端系统架构：WorkflowOrchestrator + TaskContext
- 配置管理：SystemConfig.from_yaml
- 商业价值计算：BusinessValueCalculator
- A/B 测试：ABTestEngine（可选）
- 灰度发布：CanaryDeployment（可选）
- 文档生成：自动生成 report.md 和 report.html

老潘说：
"这就是能落地的项目——不是能跑就行，而是可展示、
可交付、可维护、可持续。"

运行方式：
python3 chapters/week_08/examples/08_textagent_final.py

预期输出：
- 演示端到端系统运行
- 生成商业价值报告
- 展示终稿报告内容

依赖：
- pip install pydantic scipy
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


# ============================================================
# 导入之前各周的核心组件（简化版）
# ============================================================

# Week 08: 端到端系统架构
@dataclass
class TaskContext:
    """任务上下文——贯穿整个工作流"""
    task_id: str
    user_input: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value


class Capability(ABC):
    """能力抽象接口"""

    @abstractmethod
    def execute(self, context: TaskContext, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class Agent(ABC):
    """Agent 抽象接口"""

    @abstractmethod
    def plan(self, context: TaskContext) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class WorkflowOrchestrator:
    """工作流编排器——端到端系统的核心"""

    def __init__(self, agents: Dict[str, Agent], capabilities: Dict[str, Capability]):
        self.agents = agents
        self.capabilities = capabilities

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def run(self, user_input: str, enable_review: bool = False) -> Dict[str, Any]:
        """端到端执行"""
        start_time = time.time()

        # 1. 创建上下文
        context = TaskContext(
            task_id=self._generate_id(),
            user_input=user_input,
            metadata={"start_time": datetime.now().isoformat()}
        )

        try:
            # 2. 规划阶段
            planner = self.agents.get("planner")
            if planner:
                plan = planner.plan(context)
                context.set("plan", plan)

            # 3. 执行阶段
            executor = self.agents.get("executor")
            if executor:
                execution_result = executor.execute(context, plan)
                context.set("execution", execution_result)

            # 4. 审核阶段（可选）
            review_result = None
            if enable_review:
                reviewer = self.agents.get("reviewer")
                if reviewer:
                    review_result = reviewer.execute(context, execution_result)
                    context.set("review", review_result)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "task_id": context.task_id,
                "status": "completed",
                "result": execution_result,
                "review": review_result,
                "latency_ms": latency_ms,
                "cost_usd": context.get("cost_usd", 0.035)
            }

        except Exception as e:
            return {
                "task_id": context.task_id,
                "status": "failed",
                "error": str(e)
            }


# Week 08: 配置管理
from pydantic import BaseModel, Field
import yaml


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = Field(default="sk-test")
    temperature: float = 0.7
    max_tokens: int = 2000


class SystemConfig(BaseModel):
    """系统配置"""
    llm: LLMConfig
    enable_cache: bool = True
    enable_review: bool = False
    timeout_seconds: int = 30

    @classmethod
    def from_dict(cls, data: Dict) -> "SystemConfig":
        return cls.model_validate(data)


# Week 08: 商业价值计算
class BusinessValueCalculator:
    """商业价值计算器"""

    def __init__(self, cost_per_request: float, manual_cost_per_request: float):
        self.cost_per_request = cost_per_request
        self.manual_cost_per_request = manual_cost_per_request

    def calculate_savings(self, daily_requests: int, days: int = 90) -> Dict:
        total_requests = daily_requests * days
        system_cost = total_requests * self.cost_per_request
        manual_cost = total_requests * self.manual_cost_per_request
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


# ============================================================
# TextAgent 终稿系统
# ============================================================

class TextAgentFinal:
    """
    TextAgent 终稿——整合 8 周所有内容

    从 Week 01 的 LLM Client 到 Week 08 的端到端系统，
    TextAgent 经历了完整的演进路径。

    Week 01: LLM 调用封装
    Week 02: Prompt 模板库
    Week 03: RAG 基础
    Week 04: 高级 RAG
    Week 05: Agent 能力
    Week 06: 多智能体系统
    Week 07: 评估、优化、部署
    Week 08: 端到端设计、展示、交付
    """

    def __init__(self, config: SystemConfig):
        self.config = config
        self.orchestrator: Optional[WorkflowOrchestrator] = None
        self.calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )
        self._initialize_system()

    def _initialize_system(self) -> None:
        """初始化系统组件"""
        # 创建能力层
        capabilities = {
            "llm": MockLLMCapability(self.config.llm.model),
            "rag": MockRAGCapability()
        }

        # 创建 Agent
        agents = {
            "planner": MockPlannerAgent(capabilities["llm"]),
            "executor": MockExecutorAgent(capabilities),
            "reviewer": MockReviewerAgent(capabilities["llm"])
        }

        # 创建编排器
        self.orchestrator = WorkflowOrchestrator(agents, capabilities)

    def run(self, task: str, enable_review: bool = False) -> Dict:
        """运行任务"""
        return self.orchestrator.run(task, enable_review)

    def generate_business_report(self, daily_requests: int = 1000, days: int = 90) -> Dict:
        """生成商业价值报告"""
        return self.calculator.calculate_savings(daily_requests, days)

    def generate_final_report(self) -> str:
        """生成终稿报告"""
        report = f"""# TextAgent 项目终稿

## 项目概述

TextAgent 是一个端到端的 Agentic 文本分析系统，经过 8 周的迭代开发，
整合了 LLM 调用、RAG 检索、多智能体协作、评估优化、部署监控等完整能力。

**开发周期**: {datetime.now().strftime("%Y年%m月")}
**技术栈**: Python + Pydantic + FastAPI + LLM APIs
**版本**: v1.0.0

---

## 技术架构

### 系统设计

TextAgent 采用模块化、可配置的设计：

- **WorkflowOrchestrator**: 工作流编排器，协调所有 Agent
- **TaskContext**: 任务上下文，贯穿整个工作流的数据巴士
- **Capability**: 能力抽象（LLM、RAG、工具）
- **Agent**: 智能体（规划、执行、审核）

### 核心模块

1. **Planner**: 任务分解与规划
2. **Executor**: 工具调用与执行
3. **Retriever**: 知识检索（RAG）
4. **Reviewer**: 结果审核

---

## 评估结果

### Week 07 优化效果

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 忠实度 | 0.75 | 0.85 | +13% |
| 成本/请求 | $0.08 | $0.035 | -56% |
| P95 延迟 | 6.2s | 4.1s | -34% |

### 质量评估

- 忠实度（Faithfulness）: 0.85
- 相关性（Relevance）: 0.88
- 用户满意度: 0.82

---

## 商业价值

### 成本节省（90 天）

- 总请求数: 90,000
- 系统成本: $3,150
- 人力成本: $225,000
- **节省: $221,850 (98.6%)**

### 效率提升

- 单请求处理时间: 30 分钟 → 4.1 秒
- 节省人力时间: 45,000 小时 ≈ 5.1 人年

---

## 持续优化

### A/B 测试框架

- 支持多版本对比（Prompt、模型、配置）
- 自动统计检验（t-test）
- 流量分配和结果收集

### 灰度发布

- 分阶段逐步推广新版本
- 自动监控和回滚
- 最小化风险

---

## 部署与运维

### 部署方式

- Docker 容器化
- FastAPI 服务
- 可选：Kubernetes 编排

### 监控指标

- 成本监控: 每小时 LLM 成本
- 延迟监控: P95 延迟
- 质量监控: 忠实度、相关性
- 错误率: 请求失败率

---

## 文档

- [README](README.md): 快速开始
- [架构文档](docs/architecture.md): 系统设计
- [API 文档](docs/api.md): 接口说明
- [运维手册](docs/operations.md): 部署排错

---

## 团队与致谢

本项目是《LLM 时代的文本智能与商务应用》课程的贯穿案例，
整合了 8 周的学习内容。

感谢小北、阿码、老潘的陪伴和指导！

---

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**TextAgent v1.0.0** - 一个能落地的 LLM 应用系统
"""
        return report


# ============================================================
# Mock 实现（用于演示）
# ============================================================

class MockLLMCapability(Capability):
    """Mock LLM 能力"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def execute(self, context: TaskContext, **kwargs) -> Dict[str, Any]:
        return {
            "model": self.model,
            "response": f"[{self.model}] 分析完成: {context.user_input[:30]}...",
            "tokens": {"input": 100, "output": 50}
        }

    def get_name(self) -> str:
        return f"llm({self.model})"


class MockRAGCapability(Capability):
    """Mock RAG 能力"""

    def execute(self, context: TaskContext, **kwargs) -> Dict[str, Any]:
        return {
            "query": context.user_input,
            "results": ["相关知识 1", "相关知识 2"],
            "count": 2
        }

    def get_name(self) -> str:
        return "rag"


class MockPlannerAgent(Agent):
    """Mock 规划 Agent"""

    def __init__(self, llm: Capability):
        self.llm = llm

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {
            "task_understanding": f"理解: {context.user_input}",
            "subtasks": [
                {"step": 1, "action": "分析内容"},
                {"step": 2, "action": "生成结果"}
            ],
            "need_retrieval": True,
            "enable_review": False
        }

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "planned", "plan": plan}

    def get_name(self) -> str:
        return "Planner"


class MockExecutorAgent(Agent):
    """Mock 执行 Agent"""

    def __init__(self, capabilities: Dict[str, Capability]):
        self.capabilities = capabilities

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {"status": "ready"}

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        context.set("cost_usd", 0.035)
        return {
            "status": "completed",
            "output": f"分析完成: {context.user_input}",
            "quality_score": 0.85
        }

    def get_name(self) -> str:
        return "Executor"


class MockReviewerAgent(Agent):
    """Mock 审核 Agent"""

    def __init__(self, llm: Capability):
        self.llm = llm

    def plan(self, context: TaskContext) -> Dict[str, Any]:
        return {"status": "ready"}

    def execute(self, context: TaskContext, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "approved",
            "confidence": 0.9
        }

    def get_name(self) -> str:
        return "Reviewer"


# ============================================================
# 演示运行
# ============================================================

def demo_textagent_final():
    """演示 TextAgent 终稿系统"""

    print("""
╔════════════════════════════════════════════════════════════╗
║         TextAgent 终稿系统演示（Final Integration）          ║
╠════════════════════════════════════════════════════════════╣
║  整合 8 周内容：                                            ║
║    - Week 01-02: LLM 调用 + Prompt                         ║
║    - Week 03-04: RAG 检索                                   ║
║    - Week 05-06: Agent + 多智能体                            ║
║    - Week 07: 评估 + 优化 + 部署                             ║
║    - Week 08: 端到端设计 + 展示 + 交付                       ║
╚════════════════════════════════════════════════════════════╝
    """)

    # 1. 创建配置
    print("\n[初始化] 加载系统配置...")
    config = SystemConfig.from_dict({
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "sk-test-key",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "enable_cache": True,
        "enable_review": True,
        "timeout_seconds": 30
    })
    print(f"  ✓ 模型: {config.llm.model}")
    print(f"  ✓ 启用缓存: {config.enable_cache}")
    print(f"  ✓ 启用审核: {config.enable_review}")

    # 2. 创建系统
    print("\n[初始化] 创建 TextAgent 系统...")
    textagent = TextAgentFinal(config)
    print("  ✓ 系统就绪!")

    # 3. 运行任务
    print("\n" + "=" * 70)
    print("运行任务")
    print("=" * 70)

    tasks = [
        "分析 TextAgent 系统的架构设计",
        "评估当前系统的性能瓶颈",
        "生成优化建议报告"
    ]

    for task in tasks:
        print(f"\n任务: {task}")
        result = textagent.run(task, enable_review=True)

        if result["status"] == "completed":
            print(f"  ✓ 完成")
            print(f"    - 延迟: {result['latency_ms']}ms")
            print(f"    - 成本: ${result['cost_usd']:.4f}")
            print(f"    - 审核: {result['review']['status']}")
        else:
            print(f"  ✗ 失败: {result.get('error', 'Unknown')}")

    # 4. 生成商业价值报告
    print("\n" + "=" * 70)
    print("商业价值报告")
    print("=" * 70)

    business_report = textagent.generate_business_report(daily_requests=1000, days=90)

    print(f"""
周期: {business_report['period_days']} 天
总请求数: {business_report['total_requests']:,}

成本对比:
  系统成本: ${business_report['system_cost_usd']:,.2f}
  人力成本: ${business_report['manual_cost_usd']:,.2f}

节省: ${business_report['savings_usd']:,.2f} ({business_report['savings_percentage']:.1f}%)

老潘的点评:
"这就是老板想看的数字。不用解释什么是 RAG、
什么是 Agent，直接告诉他'90 天节省 22 万美元'。
商业价值是你的'门票'，有了这个，老板才会
愿意听技术细节。"
    """)

    # 5. 生成终稿报告
    print("\n" + "=" * 70)
    print("生成终稿报告")
    print("=" * 70)

    final_report = textagent.generate_final_report()

    # 保存到文件
    report_path = Path(__file__).parent.parent / "report_final.md"
    report_path.write_text(final_report, encoding="utf-8")

    print(f"\n✓ 终稿报告已生成: {report_path}")
    print("\n报告预览:")
    print("-" * 70)
    # 显示前 30 行
    for i, line in enumerate(final_report.split("\n")[:30], 1):
        print(f"{i:2d}. {line}")
    print("-" * 70)
    print("... (完整报告见 report_final.md)")

    # 6. 系统总结
    print("\n" + "=" * 70)
    print("TextAgent 终稿总结")
    print("=" * 70)
    print("""
🎉 恭喜！你完成了从"会用 API"到"能做系统"的完整旅程。

TextAgent 现在是一个：
  ✓ 端到端的系统（有清晰的架构和模块边界）
  ✓ 可展示的项目（有商业价值证明）
  ✓ 可交付的资产（有完整文档和部署指南）
  ✓ 可持续的演进（有 A/B 测试和灰度发布）

老潘说：
"8 周前，你面对的是一堆陌生的概念。
现在，你拥有的是一个完整的、生产级的系统。
这不仅仅是学习技术的结果，更是思维方式
转变的成果——从'训练模型'到'设计系统'。"

阿码问："接下来呢？"

老潘答：
"把 TextAgent 变成你的项目作品集，
或者用它来解决真实的问题。
LLM 时代才刚刚开始，你学到的这套
思维方式——理解问题、设计系统、
验证假设、持续优化——会一直伴随你。"

**LLM 时代的文本智能与商务应用**
**Week 08: 最后一公里 —— 从能跑到落地**
**恭喜你完成这门课程！🎓**
    """)


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    """主入口"""
    # 检查依赖
    try:
        import yaml
        import pydantic
    except ImportError as e:
        print(f"需要安装依赖：pip install pydantic pyyaml")
        print(f"错误详情: {e}")
        return

    demo_textagent_final()


if __name__ == "__main__":
    main()
