# Week 08：最后一公里 —— 从能跑到落地

> "魔鬼藏在细节里。"
> — 俗语（源自法国作家 Gustave Flaubert）

2026 年初，一家公司的技术团队完成了一个 LLM 应用 Demo。演示很成功——老板点头，用户好评，团队也觉得"我们做到了"。三个月后，这个项目被撤掉了。

问题在哪？Demo 能跑，但无法扩展：代码没人看得懂，配置硬编码在一堆脚本里，没有文档，没有测试，部署要靠"有经验的人手动操作"。当核心开发者离职后，没人敢动这堆代码，最终项目被废弃。

这个故事的教训很清楚：**一个系统的价值不仅在于"能跑"，还在于"能落地、能维护、能迭代"**。你需要完整的架构设计、清晰的文档、可复现的部署流程，以及持续优化的策略。

这周是最后一周，我们把过去 7 周学的东西整合成一个完整的、端到端的系统。你不仅要让 TextAgent 能工作，还要让它能展示、能交付、能持续改进。

---

## 前情提要

Week 07 你让 TextAgent 从"能跑"变成了"可上生产"。你添加了评估体系（知道效果好不好）、成本优化（知道钱花在哪）、API 部署（让别人能用）、可观测性（知道出没出问题）。现在的 TextAgent 是一个生产级的系统——它有服务接口、有监控、有告警。

但如果老板说"下周一给客户演示"，你会怎么准备？如果你离职了，接手的人怎么理解你的系统？如果用户量增长 10 倍，系统怎么扩展？如果你需要证明"这个系统值这么多钱"，你用什么数据说话？

这周我们会回答这些问题。你会学习端到端系统设计、商业落地策略、迭代优化方法，最终把 TextAgent 打磨成一个可展示、可交付、可持续的项目。

---

## 本章学习目标

完成本周学习后，你将能够：
1. 设计端到端系统架构，整合 LLM、RAG、Agent、评估、部署等所有模块
2. 准备完整的项目展示（技术方案、系统演示、业务价值证明）
3. 设计 A/B 测试和灰度发布策略，支持持续迭代优化
4. 撰写完整的项目文档（架构说明、API 文档、部署指南）
5. 生成可展示的项目报告 `report.md` 和 `report.html`

<!--
================================================================================
【章节规划元数据】
================================================================================

贯穿案例：TextAgent 终稿整合

- 第 1 节（端到端系统设计）：案例从"分散的模块"变成"统一的系统"——设计整体架构，整合所有组件
- 第 2 节（项目展示准备）：从"能跑的代码"变成"可展示的项目"——准备演示脚本、架构图、业务价值证明
- 第 3 节（迭代与优化）：从"固定配置"变成"可演进的系统"——设计 A/B 测试、灰度发布、反馈收集
- 第 4 节（文档与交付）：从"个人项目"变成"团队资产"——撰写完整文档、准备部署包、知识传承

最终成果：一个端到端、可展示、可交付、可维护的 TextAgent 系统，以及完整的 project report

认知负荷预算：
本周新概念（预算：4 个，"知识整合"阶段）：
1. 端到端系统设计（End-to-End System Design）— 从需求到部署的完整架构
2. 商业落地（Business Deployment）— 向利益相关方展示和证明价值
3. A/B 测试（A/B Testing）— 对比不同版本效果的实验方法
4. 灰度发布（Canary Deployment）— 逐步推广新版本的发布策略

结论：在预算内（4 个 = 上限 4 个）

循环角色出场规划：
- 小北（第 1 节）：发现"各个模块能跑但整合不起来"，引出架构设计的重要性
- 老潘（第 2 节）：分享"向老板演示项目"的实战经验——不要只演示功能，要证明价值
- 阿码（第 3 节）：在讨论 A/B 测试时追问"小样本怎么办"
- 老潘（第 4 节）：点评"文档不是写给自己的，是写给接手的人的"

回顾桥设计（至少 3 个，来自前 4 周）：
- [多智能体系统]（来自 week_06）：在第 1 节，回顾多 Agent 协作模式，作为系统架构的一部分
- [LLM 应用评估]（来自 week_07）：在第 3 节，用评估指标驱动 A/B 测试和迭代优化
- [成本优化]（来自 week_07）：在第 2 节，用成本数据证明业务价值
- [RAG 架构]（来自 week_03）：在第 1 节，整合 RAG 到端到端架构中
- [可观测性]（来自 week_07）：在第 3 节，用监控数据支持迭代决策
- [Human-in-the-Loop]（来自 week_06）：在第 3 节，设计反馈收集机制

AI 小专栏规划：
- 第 1 个（第 1-2 节之间）：AI 项目的交付陷阱 — 2025-2026 年 LLM 项目"死于维护"的案例分析
- 第 2 个（第 3-4 节之间）：AI 应用的商业价值度量 — 企业如何量化 LLM 项目的 ROI

TextAgent 本周推进：
- 上周状态：TextAgent 是可部署、可监控的生产级系统，有评估、成本优化、可观测性
- 本周改进：
  1. 设计端到端系统架构（整合所有模块为统一系统）
  2. 准备项目展示材料（架构图、演示脚本、业务价值报告）
  3. 实现 A/B 测试框架（支持 Prompt、模型、配置的对比实验）
  4. 生成完整文档（README、API 文档、部署指南）
  5. 收敛终稿 report.md，导出 report.html
- 涉及的本周概念：端到端系统设计、商业落地、A/B 测试、灰度发布
- 建议示例文件：examples/08_textagent_final.py

================================================================================
-->

---

## 1. 怎么把所有东西拼起来？—— 端到端系统设计

小北这周遇到了一个"幸福的烦恼"：Week 01-07 他写了很多代码——LLM 封装、Prompt 模板、RAG 检索、Agent 工作流、评估流水线、FastAPI 服务。每个单独都能跑，但当他想"把所有东西整合在一起"时，发现不知道从哪下手。

老潘看了小北的项目结构，只说了一句话："你现在有一堆乐高积木，但还没有拼成一座城堡。你需要一张**蓝图**。"

### 从"能跑"到"可落地"

Week 01 我们就学过 **范式转变**——从"训练模型"到"设计系统"。但什么是"系统"？系统不是一堆脚本的集合，而是有清晰边界的、模块协作的、可扩展的整体。

端到端系统设计（End-to-End System Design）回答三个问题：

1. **输入是什么**？用户怎么用你的系统？
2. **输出是什么**？系统给用户什么价值？
3. **中间怎么处理**？哪些模块、什么顺序、如何协作？

老潘给小北画了一张架构图：

```
用户请求
    ↓
┌─────────────────────────────────────────────┐
│  API Gateway (FastAPI)                      │
│  - 鉴权、限流、路由                          │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Orchestrator (工作流编排)                   │
│  - 任务分解、Agent 调度、错误处理            │
└─────────────────────────────────────────────┘
    ↓
┌──────────┬──────────┬──────────┬──────────┐
│ Planner  │ Executor │ Retriever│ Reviewer │
│ (规划)   │ (执行)   │ (检索)   │ (审核)   │
└──────────┴──────────┴──────────┴──────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Capabilities (能力层)                       │
│  - LLM 调用、RAG、工具调用                   │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Observability (可观测性)                    │
│  - 日志、指标、Trace、告警                   │
└─────────────────────────────────────────────┘
    ↓
响应给用户
```

阿码问："这不就是多 Agent 系统吗？"

老潘说："多 Agent 是**怎么执行**，端到端设计是**从哪来、到哪去、中间怎么走**。你不仅要设计 Agent，还要设计 API 接口、鉴权、限流、错误处理、监控、部署——这是完整的系统。"

### 模块化与解耦

小北之前的问题是：代码耦合太紧。改一个 Prompt 要动三个文件，加一个工具要改五个地方。老潘的建议是：**每个模块只做一件事，通过接口通信**。

```python
# examples/01_architecture.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class TaskContext:
    """任务上下文——贯穿整个工作流"""
    task_id: str
    user_input: str
    metadata: Dict[str, Any]
    state: Dict[str, Any]  # 各模块共享的状态

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
```

老潘点评道："这个设计的核心是 `TaskContext`——它像一辆'数据巴士'，把各个模块连起来。每个模块只从巴士上拿自己需要的数据，把结果放回巴士。这样模块之间解耦，你换一个 Agent 不用改其他代码。"

### 配置管理

阿码问："那模型名称、API Key、Prompt 模板这些配置呢？硬编码在代码里？"

老潘摇头，像回忆起某个痛苦的经历："我刚工作时，接过一个项目。API Key 写在代码里，结果库泄露了，key 被刷了 5000 美元。从那以后我记住了一条铁律：**配置和代码分离**。生产环境中，你要能在不修改代码的情况下调整配置。"

```python
# examples/01_config.py
from pydantic import BaseModel
from typing import Dict, Optional
import yaml

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str  # "openai", "zhipu", "qwen"
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
    retriever: Dict[str, Any]
    observability: Dict[str, Any]

    @classmethod
    def from_yaml(cls, path: str) -> "SystemConfig":
        """从 YAML 文件加载配置"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

# 使用
config = SystemConfig.from_yaml("config/production.yaml")
planner_config = config.agents["planner"]
```

这样，你可以有 `config/development.yaml`、`config/production.yaml` 不同环境的配置，切换环境只需要改一个文件。

### 系统初始化

有了架构和配置，你需要一个"启动脚本"——把所有模块组装起来：

```python
# examples/01_bootstrap.py
from textagent.orchestrator import WorkflowOrchestrator
from textagent.agents import PlannerAgent, ExecutorAgent, RetrieverAgent, ReviewerAgent
from textagent.capabilities import LLMLLMCapability, RAGCapability, ToolCapability
from textagent.observability import ObservabilityManager

def create_system(config: SystemConfig) -> WorkflowOrchestrator:
    """创建完整的端到端系统"""

    # 1. 初始化能力层
    capabilities = {
        "llm": LLMCapability(config.agents["planner"].llm),
        "rag": RAGCapability(config.retriever),
        "tools": ToolCapability()
    }

    # 2. 初始化 Agent
    agents = {
        "planner": PlannerAgent(config.agents["planner"], capabilities),
        "executor": ExecutorAgent(config.agents["executor"], capabilities),
        "retriever": RetrieverAgent(config.agents["retriever"], capabilities),
        "reviewer": ReviewerAgent(config.agents["reviewer"], capabilities)
    }

    # 3. 初始化编排器
    orchestrator = WorkflowOrchestrator(agents, capabilities)

    # 4. 初始化可观测性
    observability = ObservabilityManager(config.observability)
    observability.wrap_orchestrator(orchestrator)

    return orchestrator

# 使用
if __name__ == "__main__":
    config = SystemConfig.from_yaml("config/production.yaml")
    system = create_system(config)
    result = system.run("分析这份数据")
    print(result)
```

老潘说："这个 `create_system` 函数是你的'系统蓝图'。任何人看这个函数，就知道系统是怎么组装的。这就是**可维护性**——新来的人读一遍代码就能理解整体架构。"

小北看着自己原来散落各处的代码——五个文件夹、十二个脚本、无数个 `import` 语句——终于明白了一个他之前一直忽视的事实：**端到端设计不是写更多代码，而是把代码组织成有结构的系统**。或者说，让代码"看起来像一个人写的"。

> **AI 时代小专栏：AI 项目的交付陷阱**
>
> 2025-2026 年，一个令人意外的现象出现了：大量 LLM 项目死于"交付后无人维护"。公开案例显示，某金融公司的智能投顾系统在演示阶段惊艳全场，但 6 个月后被撤掉——原因只有一条：核心开发者离职后，没人能理解系统是如何工作的。
>
> 这有点反直觉：Demo 越成功，交付越危险。因为演示时没人关心代码质量、没人问文档在哪、没人想过"如果开发者走了怎么办"——大家只看效果。等到项目真的要维护，才发现是一堆"能跑但改不动"的代码。
>
> 问题不在技术，而在**工程实践**。代码能跑，但架构不清晰；功能全，但没有文档；配置硬编码，换个环境要改一堆文件。LangChain 在 2025 年发布了"LLM 项目工程化最佳实践"，核心建议很简单：**从第一天就用模块化、配置化、文档化的方式开发**。
>
> 另一个常见陷阱是"过度依赖特定模型"。2025 年 GPT-4o 发布时，很多之前用 GPT-4 的系统发现：迁移新模型要动核心代码。最佳实践是把"模型"作为配置项，而不是硬编码在 Prompt 里——这样切换模型只需要改配置文件，不动代码。
>
> 企业实践中的共识是：**LLM 项目的价值不在于 Demo，而在于可持续性**。一个架构清晰、文档完整、可扩展的系统，比一个功能炫酷但无法维护的项目更有价值。你刚学的模块化、配置管理、系统初始化——这些不是"附加题"，而是"必答题"。
>
> 参考（访问日期：2026-02-17）：
> > - [LangChain - Production Best Practices](https://python.langchain.com/docs/production/)
> > - <!-- TODO: 需联网搜索 "LlamaIndex production guide 2026" 补充最新参考链接 -->

---

## 2. 让老板买单 —— 项目展示与商业落地

小北的系统终于能跑了。他兴冲冲地去找老板演示，结果老板问了三个问题：

1. "这比原来的人力操作好在哪里？"
2. "上这个系统要花多少钱？能省多少钱？"
3. "如果出问题了，怎么回滚？"

小北愣住了——他准备了很多技术细节（模型选择、Agent 架构、RAG 策略），但老板关心的完全不是这些。老潘走过来说："你准备的是**技术演示**，老板要的是**商业价值证明**。"

### 演示的两个层次

老潘把演示分成两层：

| 层次 | 受众 | 关注点 | 展示内容 |
|------|------|-------|---------|
| **技术层** | 开发团队、架构师 | 怎么实现的？架构、代码、技术选型 | 系统架构图、关键代码、技术难点 |
| **商业层** | 老板、客户、业务部门 | 有什么价值？成本、收益、风险 | 业务指标、成本对比、风险控制 |

小北的问题是他只准备了技术层，没准备商业层。老潘说："老板不懂什么是 RAG，但他懂'每小时处理 1000 个请求，节省 3 个人力'。你要用**商业语言**说话。"

### 准备商业价值报告

还记得 Week 07 我们学的 **成本优化** 吗？现在这些数据派上用场了。你需要一份"商业价值报告"：

```python
# examples/02_business_value.py
from typing import Dict
from datetime import datetime, timedelta

class BusinessValueCalculator:
    """商业价值计算器"""

    def __init__(self, cost_per_request: float, manual_cost_per_request: float):
        self.cost_per_request = cost_per_request  # 系统成本
        self.manual_cost_per_request = manual_cost_per_request  # 人力成本

    def calculate_savings(self, daily_requests: int, days: int = 30) -> Dict:
        """计算节省的成本

        Args:
            daily_requests: 每日请求数
            days: 计算周期（天）
        """
        total_requests = daily_requests * days

        # 系统成本
        system_cost = total_requests * self.cost_per_request

        # 人力成本（假设人工操作）
        manual_cost = total_requests * self.manual_cost_per_request

        # 节省
        savings = manual_cost - system_cost
        savings_percentage = (savings / manual_cost) * 100 if manual_cost > 0 else 0

        return {
            "period_days": days,
            "total_requests": total_requests,
            "system_cost_usd": system_cost,
            "manual_cost_usd": manual_cost,
            "savings_usd": savings,
            "savings_percentage": savings_percentage
        }

# 使用示例（基于 Week 07 的优化结果）
calculator = BusinessValueCalculator(
    cost_per_request=0.035,  # 优化后的成本
    manual_cost_per_request=2.50  # 人力成本（假设）
)

# 场景：每日 1000 个请求，计算 90 天
report = calculator.calculate_savings(daily_requests=1000, days=90)

print(f"90 天节省成本: ${report['savings_usd']:.2f}")
print(f"节省比例: {report['savings_percentage']:.1f}%")
```

输出示例：
```
90 天节省成本: $220,500.00
节省比例: 98.6%
```

老潘说："这才是老板想看的数字——你不用解释什么是 RAG，直接告诉他'90 天节省 22 万美元'。商业价值报告是你的'门票'，有了这个，老板才会愿意听技术细节。"

### 准备演示脚本

有了数据，你还要设计演示流程。老潘的建议是：**从简单到复杂，从高频到低频**。

演示脚本示例（10 分钟）：

```markdown
# TextAgent 演示脚本

## 第 1 部分：业务场景（2 分钟）
- "这是客服团队每天要处理的 1000 个用户咨询"
- 展示 3 个真实案例（简单、中等、复杂）

## 第 2 部分：系统演示（5 分钟）
- 案例 1（简单）：实时演示，突出速度
- 案例 2（中等）：展示 Agent 协作过程
- 案例 3（复杂）：展示检索 + 审核

## 第 3 部分：价值证明（2 分钟）
- 展示成本对比、节省比例
- 展示质量指标（准确率提升）

## 第 4 部分：风险控制（1 分钟）
- 演示人工审核介入点
- 说明回滚方案
```

阿码问："演示时出错了怎么办？"

老潘笑了，像想起了什么有趣的事："我刚工作时第一次给老板演示，结果系统报错了。我站在那里，不知所措，老板说：'没关系，讲讲你的设计思路吧。'后来我学到了：你要准备**备选方案**。如果 LLM 调用失败，展示缓存的结果；如果网络延迟，展示预先录制的演示视频。关键不是'不能出错'，而是'出错时怎么应对'。"

### 风险与回滚

老板问的第三个问题——"如果出问题怎么回滚"——其实是商业落地中最重要的一环。你需要回答：

1. **什么算"出问题"**？错误率超过 5%？成本超过预算？用户投诉超过阈值？
2. **怎么回滚**？关闭新功能？切回人工操作？降级到旧版本？

```python
# examples/02_rollback.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class RollbackPlan:
    """回滚方案"""
    trigger_conditions: Dict[str, Any]  # 触发条件
    rollback_action: str  # 回滚动作
    fallback_system: Optional[str] = None  # 降级系统

class ProductionSystem:
    """生产系统（带回滚能力）"""

    def __init__(self):
        self.rollback_plan = RollbackPlan(
            trigger_conditions={
                "error_rate_threshold": 0.05,  # 错误率 > 5%
                "cost_threshold_usd_per_hour": 50,  # 每小时成本 > $50
                "latency_threshold_ms": 10000  # P95 延迟 > 10s
            },
            rollback_action="switch_to_manual",  # 切换到人工
            fallback_system="legacy_system"  # 旧系统
        )

    def check_health(self) -> bool:
        """检查系统健康状态"""
        metrics = self.observability.get_current_metrics()

        # 检查触发条件
        if metrics["error_rate"] > self.rollback_plan.trigger_conditions["error_rate_threshold"]:
            return False
        if metrics["hourly_cost_usd"] > self.rollback_plan.trigger_conditions["cost_threshold_usd_per_hour"]:
            return False
        if metrics["p95_latency_ms"] > self.rollback_plan.trigger_conditions["latency_threshold_ms"]:
            return False

        return True

    def run_with_safety_net(self, user_input: str) -> Dict:
        """带安全网运行"""
        try:
            # 先检查健康状态
            if not self.check_health():
                # 自动回滚
                return self._fallback(user_input)

            # 运行系统
            result = self.orchestrator.run(user_input)
            return result

        except Exception as e:
            # 异常时回滚
            self.observability.log_rollback(error=str(e))
            return self._fallback(user_input)

    def _fallback(self, user_input: str) -> Dict:
        """降级方案"""
        if self.rollback_plan.fallback_system == "manual":
            return {"status": "escalated", "message": "转人工处理"}
        else:
            return {"status": "fallback", "result": self._call_legacy_system(user_input)}
```

老潘说："有了这个，老板才会放心。商业落地不是'技术完美'，而是**风险可控**。你能证明'出了问题有办法解决'，老板才敢让你上生产。"

---

## 3. 用数据说话 —— A/B 测试与灰度发布

阿码这周有了一个新问题："我怎么知道换个 Prompt 会更好？或者换个模型会更快？"

老潘说："这就是 **A/B 测试**要解决的问题。不是'我觉得更好'，而是'数据证明更好'。"

### A/B 测试的基本原理

A/B 测试（A/B Testing）的核心思想很简单：同时运行两个版本（A 版本和 B 版本），随机分配流量，然后比较效果。

关键点：

| 要素 | 说明 | 示例 |
|------|------|------|
| **对照版本（A）** | 当前线上版本 | 现有的 Prompt |
| **实验版本（B）** | 新版本 | 优化后的 Prompt |
| **流量分配** | 随机分配 | 50% 用户用 A，50% 用 B |
| **评估指标** | 对比的关键数据 | 准确率、成本、延迟 |
| **统计检验** | 判断差异是否显著 | t 检验、置信区间 |

```python
# examples/03_ab_testing.py
from typing import Dict, Literal, List
import hashlib
from datetime import datetime

Version = Literal["A", "B"]

class ABTestConfig:
    """A/B 测试配置"""

    def __init__(self, name: str, description: str, traffic_split: float = 0.5):
        self.name = name
        self.description = description
        self.traffic_split = traffic_split  # B 版本的流量比例（0.5 = 50%）
        self.start_time = datetime.now()

class ABTestEngine:
    """A/B 测试引擎"""

    def __init__(self, config: ABTestConfig):
        self.config = config
        self.results = {"A": [], "B": []}

    def assign_version(self, user_id: str) -> Version:
        """为用户分配版本

        使用哈希确保同一用户总是分配到同一版本
        """
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

        # 提取指标
        a_values = [r.get("quality_score", 0) for r in self.results["A"]]
        b_values = [r.get("quality_score", 0) for r in self.results["B"]]

        # t 检验
        t_stat, p_value = stats.ttest_ind(a_values, b_values)

        # 计算均值
        a_mean = sum(a_values) / len(a_values) if a_values else 0
        b_mean = sum(b_values) / len(b_values) if b_values else 0

        # 判断是否显著
        is_significant = p_value < 0.05
        winner = "B" if b_mean > a_mean else "A"

        return {
            "test_name": self.config.name,
            "sample_size": {"A": len(a_values), "B": len(b_values)},
            "mean_quality": {"A": a_mean, "B": b_mean},
            "lift": (b_mean - a_mean) / a_mean * 100 if a_mean > 0 else 0,
            "p_value": p_value,
            "is_significant": is_significant,
            "winner": winner if is_significant else "inconclusive"
        }

# 使用
test_config = ABTestConfig(
    name="prompt_v2_vs_v1",
    description="测试优化后的 Prompt 是否提升质量",
    traffic_split=0.5
)

ab_engine = ABTestEngine(test_config)

# 模拟运行
for user_id, user_input in mock_user_requests:
    version = ab_engine.assign_version(user_id)
    result = system.run_with_version(user_input, version)
    ab_engine.record_result(version, {"quality_score": result["quality"]})

# 分析
analysis = ab_engine.analyze()
print(f"胜者: {analysis['winner']}")
print(f"提升: {analysis['lift']:.1f}%")
```

阿码举手："等等，p < 0.05 是什么意思？"

小北也跟着点头，他其实也一直没搞懂这个。

老潘说："问得好。很多人用了一辈子 p 值，但不知道它在说什么。p < 0.05 的意思是：**如果 A 和 B 其实没有区别，看到这种差异的概率小于 5%**。换句话说，你有 95% 的信心说 B 真的比 A 好。这是统计显著性的标准。"

### 灰度发布：逐步推广

A/B 测试告诉你"B 比 A 好"，但你应该立即把所有流量切到 B 吗？老潘摇头："**灰度发布**（Canary Deployment）——先给小部分用户用，没问题再逐步扩大。"

灰度发布的流程：

```
第 1 天：5% 流量 → 监控指标
  ↓ 无问题
第 3 天：25% 流量 → 监控指标
  ↓ 无问题
第 7 天：50% 流量 → 监控指标
  ↓ 无问题
第 14 天：100% 流量
```

```python
# examples/03_canary.py
from typing import Dict
from datetime import datetime

class CanaryDeployment:
    """灰度发布控制器"""

    def __init__(self, stages: List[Dict]):
        """
        stages: [
            {"day": 1, "traffic_percentage": 5},
            {"day": 3, "traffic_percentage": 25},
            ...
        ]
        """
        self.stages = sorted(stages, key=lambda x: x["day"])
        self.current_stage = 0
        self.start_date = datetime.now()

    def get_traffic_percentage(self) -> float:
        """获取当前应该分配给新版本的流量比例"""
        days_elapsed = (datetime.now() - self.start_date).days

        # 找到当前应该处于的阶段
        for i, stage in enumerate(self.stages):
            if days_elapsed >= stage["day"]:
                self.current_stage = i

        return self.stages[self.current_stage]["traffic_percentage"]

    def should_use_new_version(self, user_id: str) -> bool:
        """判断是否使用新版本"""
        import hashlib
        traffic_pct = self.get_traffic_percentage()

        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_val % 100) < traffic_pct

    def check_rollback_conditions(self, metrics: Dict) -> bool:
        """检查是否需要回滚"""
        # 如果错误率突然升高，回滚
        if metrics.get("error_rate", 0) > 0.05:
            return True
        # 如果成本突然升高，回滚
        if metrics.get("cost_increase_pct", 0) > 20:
            return True
        return False

# 使用
canary = CanaryDeployment([
    {"day": 1, "traffic_percentage": 5},
    {"day": 3, "traffic_percentage": 25},
    {"day": 7, "traffic_percentage": 50},
    {"day": 14, "traffic_percentage": 100}
])

# 每次请求时判断
if canary.should_use_new_version(user_id):
    result = new_system.run(user_input)
else:
    result = old_system.run(user_input)
```

老潘说："灰度发布的核心是**风险控制**。你不需要一次性把所有用户都暴露在新版本下。如果发现问题，只有 5% 的用户受影响，而不是 100%。换句话说：宁可让少数人失望，不要让所有人崩溃。"

阿码听了，若有所思："这和我上次改代码的教训一样。我想着'一次性优化所有东西'，结果改出了一个所有人都讨厌的版本。要是当时用灰度发布，第一天就能发现问题，只有 5% 的人受罪。"

### 反馈收集与迭代

阿码问："那用户觉得好不好用，怎么知道？"

老潘说："所以你需要**反馈收集**机制。不是'我觉得好'，而是'用户说好'。"

```python
# examples/03_feedback.py
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class UserFeedback:
    """用户反馈"""
    request_id: str
    user_id: str
    rating: int  # 1-5 星
    comment: str
    timestamp: str

class FeedbackCollector:
    """反馈收集器"""

    def __init__(self):
        self.feedbacks: List[UserFeedback] = []

    def collect(self, feedback: UserFeedback):
        """收集反馈"""
        self.feedbacks.append(feedback)

    def get_summary(self) -> Dict:
        """获取反馈摘要"""
        if not self.feedbacks:
            return {"avg_rating": 0, "count": 0}

        ratings = [f.rating for f in self.feedbacks]
        return {
            "avg_rating": sum(ratings) / len(ratings),
            "count": len(self.feedbacks),
            "distribution": {
                5: sum(1 for r in ratings if r == 5),
                4: sum(1 for r in ratings if r == 4),
                3: sum(1 for r in ratings if r == 3),
                2: sum(1 for r in ratings if r == 2),
                1: sum(1 for r in ratings if r == 1)
            }
        }

# 在 API 中收集反馈
@app.post("/feedback")
async def submit_feedback(request_id: str, rating: int, comment: str):
    """提交反馈"""
    feedback_collector.collect(UserFeedback(
        request_id=request_id,
        user_id=get_current_user_id(),
        rating=rating,
        comment=comment,
        timestamp=datetime.now().isoformat()
    ))
    return {"status": "received"}
```

老潘说："有了反馈数据，你就可以做**数据驱动的迭代**。不是'我觉得该改什么'，而是'用户抱怨最多的地方是什么'。这就是持续优化的基础。"

阿码突然问了一个好问题："那如果用户说 A，数据说 B，听谁的？"

老潘笑了："这是个好问题。我的经验是：用户说的和用户做的，经常不一样。用户会说什么'我喜欢简洁的界面'，但数据可能显示他们最常用的是那个复杂的高级功能。所以你要两边都看：用户反馈告诉你'他们认为自己想要什么'，使用数据告诉你'他们实际想要什么'。两者结合，才能做对决策。"

这是一个"哦！"时刻——小北和阿码都恍然大悟。用户不总是对的，但用户总是值得倾听的。关键是怎么听。

> **AI 时代小专栏：AI 应用的商业价值度量**
>
> 2025-2026 年，企业对 LLM 项目的态度发生了一个微妙但重要的变化：问题从"能不能做"变成了"值不值钱"。这有点讽刺——技术团队花了半年时间做出一个功能炫酷的系统，结果老板问的第一句话是："能省多少钱？"
>
> 公开讨论中，成功落地的 LLM 项目都有一个共同点：**清晰的商业价值度量指标**。不是"准确率提升 5%"这种技术术语，而是"每月节省 200 个人力小时"这种老板能听懂的话。
>
> 常见的度量维度包括：
> - **成本节省**：自动化替代人力，直接对比成本
> - **效率提升**：处理时间缩短（如从 30 分钟到 30 秒）
> - **质量提升**：准确率、错误率下降
> - **收入增长**：转化率提升、客单价增加
>
> LangSmith 在 2025 年推出了"业务价值追踪"功能——不仅追踪技术指标（延迟、成本），还追踪业务指标（用户满意度、转化率）。企业实践中的建议是：**从 Day 1 就定义清楚"用什么指标证明成功"**。
>
> 另一个趋势是"实验驱动优化"。Google 和 Meta 内部都有完善的 A/B 测试平台，任何改动（包括 Prompt 调整）都必须通过 A/B 测试。2026 年的共识是：**不要相信直觉，要相信数据**。你刚学的 A/B 测试和灰度发布，在企业环境中不是"可选项"，而是"必选项"。
>
> 参考（访问日期：2026-02-17）：
> > - <!-- TODO: 需联网搜索 "McKinsey generative AI ROI 2026" 补充最新报告链接 -->
> > - [LangSmith - Business Metrics](https://smith.langchain.com/business-metrics)
> > - <!-- TODO: 需联网搜索 "Arize LLM ROI calculator 2026" 补充参考链接 -->

---

## 4. 交付的艺术 —— 文档与知识传承

小北的系统终于要交付了。老潘问了最后一个问题："如果你下周就离职，接手的人能在一周内上手吗？"

小北想了想，摇摇头。老潘说："所以你需要**文档**——不是写给自己的笔记，而是写给接手的人的手册。"

### 文档的四个层次

老潘把文档分成四层，每层写给不同的受众。他说："文档不是'写一遍就完'的任务，而是'写给不同的读者'的作品。"

| 层次 | 受众 | 内容 | 位置 |
|------|------|------|------|
| **README** | 所有人 | 项目是什么、怎么快速开始 | 项目根目录 |
| **架构文档** | 开发者 | 系统怎么设计、模块怎么协作 | `docs/architecture.md` |
| **API 文档** | 集成方 | 接口怎么调用、参数是什么 | `docs/api.md` 或自动生成 |
| **运维手册** | 运维 | 怎么部署、怎么监控、怎么排错 | `docs/operations.md` |

### README：项目的门面

README 是项目的"门面"，它应该回答五个问题：

```markdown
# TextAgent — Agentic 文本分析系统

> 一个基于 LLM 的智能文本分析系统，支持规划、执行、检索、审核的多智能体协作。

## 它是什么？

TextAgent 是一个端到端的文本分析系统，能够：
- 自动分析用户需求并制定执行计划
- 调用多种工具（情感分析、关键词提取、词频统计）
- 从知识库检索相关信息（RAG）
- 审核结果质量（Human-in-the-Loop）

## 快速开始

### 安装

\`\`\`bash
git clone https://github.com/your-org/textagent.git
cd textagent
pip install -r requirements.txt
\`\`\`

### 配置

\`\`\`bash
cp config/development.yaml.example config/development.yaml
# 编辑 development.yaml，填入你的 API Key
\`\`\`

### 运行

\`\`\`bash
python -m textagent.main
\`\`\`

### 测试

\`\`\`bash
pytest tests/ -v
\`\`\`

## 项目结构

\`\`\`
textagent/
├── config/          # 配置文件
├── src/
│   ├── agents/      # Agent 模块
│   ├── capabilities/# 能力层
│   ├── orchestrator/# 工作流编排
│   └── observability/# 可观测性
├── tests/           # 测试
└── docs/            # 文档
\`\`\`

## 许可证

MIT License
```

### 架构文档：系统的蓝图

架构文档解释"为什么这样设计"，不是"代码是什么"：

```markdown
# TextAgent 架构文档

## 设计原则

1. **模块化**：每个模块只做一件事，通过接口通信
2. **可配置**：所有配置外置，不硬编码在代码中
3. **可观测**：每个关键步骤都有日志和指标
4. **可回滚**：出问题时能快速降级

## 整体架构

\`\`\`
用户请求 → API Gateway → Orchestrator → Agents → Capabilities
                                          ↓
                                    Observability
\`\`\`

## 核心模块

### Orchestrator（编排器）

负责整个工作流的调度和错误处理。

**为什么需要**：多 Agent 系统的协调中心，确保任务按正确顺序执行。

**关键方法**：
- `run(user_input)`：端到端执行
- `_handle_error()`：统一错误处理

### Agent（智能体）

- **Planner**：任务分解和规划
- **Executor**：工具调用和执行
- **Retriever**：知识检索（RAG）
- **Reviewer**：结果审核

### Capability（能力层）

- **LLM**：统一的 LLM 调用接口
- **RAG**：检索增强生成
- **Tools**：外部工具封装

## 数据流

1. 用户请求 → API Gateway
2. Orchestrator 创建 TaskContext
3. Planner 制定计划
4. Retriever 检索相关知识（如需）
5. Executor 执行计划
6. Reviewer 审核结果（如需）
7. Observability 记录全链路
8. 返回结果给用户

## 扩展指南

### 添加新的 Agent

1. 继承 `Agent` 基类
2. 实现 `plan()` 和 `execute()` 方法
3. 在 `config.yaml` 中注册
4. 在 `create_system()` 中初始化

### 添加新的工具

1. 在 `tools/` 中定义工具函数
2. 在 `ToolCapability` 中注册
3. 更新 Agent 的 Prompt 模板
```

### API 文档：接口手册

API 文档说明"怎么调用系统"：

```markdown
# TextAgent API 文档

## 基础信息

- Base URL: `http://localhost:8000`
- 认证方式: Bearer Token
- Content-Type: `application/json`

## 接口列表

### 1. 执行分析

\`\`\`
POST /analyze
\`\`\`

**请求体**：

\`\`\`json
{
  "task": "分析这份数据",
  "enable_review": true,
  "use_cache": true
}
\`\`\`

**响应**：

\`\`\`json
{
  "task_id": "12345",
  "result": {...},
  "review": {...},
  "cost_usd": 0.035,
  "latency_ms": 4100
}
\`\`\`

**错误码**：

- 400: 请求参数错误
- 401: 认证失败
- 429: 请求过于频繁（限流）
- 500: 服务器内部错误

### 2. 流式执行

\`\`\`
POST /analyze/stream
\`\`\`

返回 Server-Sent Events (SSE) 流。

### 3. 健康检查

\`\`\`
GET /health
\`\`\`

返回系统健康状态。

### 4. 指标查询

\`\`\`
GET /metrics
\`\`\`

返回 Prometheus 格式的指标。

## 示例代码

\`\`\`python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"task": "分析用户反馈", "enable_review": True},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

result = response.json()
print(result["cost_usd"])
\`\`\`
```

### 运维手册：部署与排错

运维手册说明"怎么让系统持续运行"：

```markdown
# TextAgent 运维手册

## 部署

### 本地开发

\`\`\`bash
docker-compose up -d
\`\`\`

### 生产环境

\`\`\`bash
kubectl apply -f k8s/
\`\`\`

## 监控

### 关键指标

- **成本**：每小时 LLM 成本（阈值：$50/小时）
- **延迟**：P95 延迟（阈值：5 秒）
- **错误率**：请求失败率（阈值：5%）
- **质量**：忠实度、相关性（阈值：0.8）

### 告警规则

见 `config/alerts.yaml`

## 排错

### 常见问题

**1. 成本突然飙升**

可能原因：
- 某个 Agent 的 Prompt 过长
- 缓存失效

排查步骤：
1. 查看 `/metrics` 端点
2. 检查 `cost_by_agent` 分布
3. 查看 Trace，找到最烧钱的 Agent

**2. 延迟过高**

可能原因：
- LLM API 响应慢
- 检索结果过多

排查步骤：
1. 查看 Trace，找到最慢的步骤
2. 检查 `top_k` 参数是否过大
3. 考虑启用流式输出

**3. 质量下降**

可能原因：
- Prompt 被意外修改
- 知识库未更新

排查步骤：
1. 检查 `config/` 中的 Prompt 模板
2. 验证知识库是否是最新的
3. 运行测试集，对比历史基线

### 回滚

\`\`\`bash
kubectl rollout undo deployment/textagent
\`\`\`

或手动切换到旧版本：

\`\`\`bash
kubectl set image deployment/textagent textagent=textagent:v1.0.0
\`\`\`

## 日志

- 应用日志：`/var/log/textagent/app.log`
- 访问日志：`/var/log/textagent/access.log`
- Trace 日志：发送到 LangSmith
```

老潘说："有了这四层文档，任何人都能在一天内理解你的系统、一周内上手修改、一个月内成为专家。**文档是项目的生命线**，不是'可选项'。"

小北听了，有点不好意思："我之前的文档就是……写给自己看的注释，过两个月自己都看不懂了。"

老潘笑了："这是正常的。好消息是，从今天开始改变还来得及。记住一个原则：**文档不是写给未来的自己的，而是写给未来的陌生人的**。如果陌生人能看懂，未来的你也一定能看懂。"

### 交付清单

最后，你需要一个"交付清单"，确保所有东西都交给了接手的人：

```markdown
# TextAgent 交付清单

## 代码

- [ ] 源代码已推送到 Git 仓库
- [ ] 所有依赖已列在 `requirements.txt` 中
- [ ] 配置文件示例已提供（`.example` 后缀）
- [ ] 测试覆盖核心功能（pytest 通过）

## 文档

- [ ] README 完整（快速开始、项目结构）
- [ ] 架构文档清晰（设计原则、模块说明）
- [ ] API 文档完整（接口列表、示例代码）
- [ ] 运维手册实用（部署、监控、排错）

## 部署

- [ ] Docker 镜像已构建并推送到镜像仓库
- [ ] Kubernetes 配置文件已准备
- [ ] 环境变量已文档化
- [ ] 数据库迁移脚本已准备

## 监控

- [ ] Prometheus 指标已配置
- [ ] Grafana 仪表盘已设置
- [ ] 告警规则已配置
- [ ] 日志收集已启用

## 知识传承

- [ ] 架构评审已完成
- [ ] 代码 walkthrough 已录制
- [ ] 接手人培训已完成
- [ ] 联系方式已提供

## 业务

- [ ] 商业价值报告已提交
- [ ] 演示脚本已准备
- [ ] 风险评估已完成
- [ ] 回滚方案已确认
```

老潘说："这个清单就是你的'交付保险'。每打一个勾，接手的人就少一个坑。当所有勾都打完，你才能放心地离开。"

---

## TextAgent 进度

Week 07 结束时，TextAgent 是一个可部署、可监控的生产级系统。它有评估、成本优化、可观测性，但仍然是"分散的模块"——没有统一的架构、没有文档、没有交付物。

这周我们让 TextAgent 从"生产级"进化为"可交付"。

### 本周改进

**1. 设计端到端系统架构**

首先给 TextAgent 一个统一的蓝图——把所有模块整合成一个有结构的系统。

```python
# src/textagent/system/bootstrap.py
from textagent.system.orchestrator import WorkflowOrchestrator
from textagent.system.config import SystemConfig

def create_system(config_path: str) -> WorkflowOrchestrator:
    """创建完整的端到端系统

    这是 TextAgent 的"系统蓝图"——任何人看这个函数
    就知道系统是怎么组装的。
    """
    # 加载配置
    config = SystemConfig.from_yaml(config_path)

    # 初始化能力层
    capabilities = create_capabilities(config)

    # 初始化 Agent
    agents = create_agents(config, capabilities)

    # 初始化编排器
    orchestrator = WorkflowOrchestrator(agents, capabilities)

    # 包装可观测性
    observability = create_observability(config)
    observability.wrap_system(orchestrator)

    return orchestrator

if __name__ == "__main__":
    system = create_system("config/production.yaml")
    result = system.run("分析这份数据")
    print(result)
```

**2. 准备项目展示材料**

然后让 TextAgent "能展示价值"——准备商业价值报告、演示脚本、架构图。

```python
# src/textagent/business/value_report.py
from textagent.business.calculator import BusinessValueCalculator

def generate_value_report(daily_requests: int, days: int = 90) -> Dict:
    """生成商业价值报告"""
    calculator = BusinessValueCalculator(
        cost_per_request=0.035,  # 优化后的成本
        manual_cost_per_request=2.50
    )

    return calculator.calculate_savings(daily_requests, days)

# 报告示例
# 90 天节省成本: $220,500
# 节省比例: 98.6%
```

**3. 实现 A/B 测试框架**

接下来让 TextAgent "能持续优化"——支持 Prompt、模型、配置的对比实验。

```python
# src/textagent/experiments/ab_test.py
from textagent.experiments.engine import ABTestEngine

def run_ab_test(config: ABTestConfig) -> Dict:
    """运行 A/B 测试"""
    engine = ABTestEngine(config)

    # 分配流量、收集结果、分析数据
    for user_id, user_input in get_test_traffic():
        version = engine.assign_version(user_id)
        result = system.run_with_version(user_input, version)
        engine.record_result(version, result)

    return engine.analyze()
```

**4. 生成完整文档**

最后让 TextAgent "能被接手"——撰写 README、架构文档、API 文档、运维手册。

```markdown
# TextAgent 项目文档（docs/）

├── README.md              # 项目概述、快速开始
├── architecture.md        # 架构设计、模块说明
├── api.md                 # API 接口、示例代码
├── operations.md          # 部署、监控、排错
└── delivery_checklist.md  # 交付清单
```

**5. 收敛终稿 report.md**

所有内容整合成终稿报告：

```markdown
# TextAgent 项目终稿

## 项目概述

TextAgent 是一个端到端的 Agentic 文本分析系统...

## 技术架构

### 系统设计
- 模块化设计：Orchestrator + Agents + Capabilities
- 可配置化：所有配置外置
- 可观测性：日志、指标、Trace

### 核心模块
1. Planner：任务分解与规划
2. Executor：工具调用与执行
3. Retriever：知识检索（RAG）
4. Reviewer：结果审核

## 评估结果

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 忠实度 | 0.75 | 0.85 | +13% |
| 成本/请求 | $0.08 | $0.035 | -56% |
| P95 延迟 | 6.2s | 4.1s | -34% |

## 商业价值

- 90 天节省成本：$220,500
- 节省比例：98.6%
- 质量提升：13%

## 持续优化

- A/B 测试框架：支持 Prompt、模型、配置的对比
- 灰度发布：逐步推广新版本
- 反馈收集：用户满意度追踪

## 部署与运维

- Docker 容器化
- Kubernetes 编排
- Prometheus + Grafana 监控
- 自动告警

## 文档

- [README](README.md)：快速开始
- [架构文档](docs/architecture.md)：系统设计
- [API 文档](docs/api.md)：接口说明
- [运维手册](docs/operations.md)：部署排错

## 团队与致谢

...
```

**6. 导出 report.html**

```python
# scripts/generate_report.py
import markdown
from pathlib import Path

def generate_html_report(markdown_path: str, output_path: str):
    """从 Markdown 生成 HTML 报告"""
    with open(markdown_path) as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)

    # 添加 CSS 样式
    html_with_style = f"""
    <html>
    <head>
        <link rel="stylesheet" href="styles.css">
        <title>TextAgent 项目报告</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    Path(output_path).write_text(html_with_style)

if __name__ == "__main__":
    generate_html_report("report.md", "report.html")
```

### 最终成果

Week 08 结束时，你将拥有：

1. **一个完整的系统**：端到端的 TextAgent，整合了所有模块
2. **一份完整的报告**：`report.md` + `report.html`，可展示给老板/客户
3. **一套完整的文档**：README、架构、API、运维
4. **一个可部署的包**：Docker 镜像、Kubernetes 配置
5. **一个可持续的项目**：A/B 测试、灰度发布、反馈收集

老潘看到这个，会说："这才是能落地的项目——不是能跑就行，而是可展示、可交付、可维护、可持续。"

---

## Git 本周要点

这是最后一周的 Git 操作，也是一个重要里程碑：**发布你的第一个版本**。

本周必会命令：
```bash
git tag -a v1.0.0 -m "Release TextAgent v1.0"
git push origin v1.0.0
git log --oneline --graph -n 20
```

常见坑：
- 提交前忘记更新文档：代码改了但文档没改，接手的人会困惑
- 提交前忘记跑测试：坏了的功能合并到主分支

Release（发布）的完整流程：
1. Git tag 标记版本号（如 v1.0.0）
2. Push tag 到远程仓库
3. 在 Gitea 上创建 Release，附上变更说明

老潘说："打 tag 是一个仪式感。当你敲下 `git tag -a v1.0.0` 那一行，你是在告诉自己：这个版本是可以交付的、可以展示给别人的、可以放在简历上的。这不是小事。"

---

## 本周小结（供下周参考）

这是最后一周。8 周前，你面对的是一堆陌生的概念——LLM、Prompt、RAG、Agent。现在，你拥有的是一个完整的、端到端的智能文本分析系统。这不仅仅是学习技术的结果，更是思维方式转变的成果。

**端到端系统设计**是从"能跑"到"可落地"的第一步。小北的问题很有代表性——Week 01-07 写了很多代码，但不知道怎么整合。老潘的"蓝图"比喻很关键：你需要一个清晰的架构图，定义各模块的职责和接口。`WorkflowOrchestrator` 是核心，它调度 Agent、协调能力层、处理错误。配置管理让系统更灵活——切换模型、调整参数都不用改代码。你学到的是：**系统的价值不在于代码多少，而在于结构是否清晰**。

**项目展示与商业落地**是从"技术正确"到"商业价值"的转变。技术演示和商业演示是两回事。老板不关心什么是 RAG，他关心"能省多少钱"。`BusinessValueCalculator` 把技术指标转换成商业语言——"90 天节省 22 万美元"比"准确率提升 13%"更有说服力。风险控制和回滚方案是商业落地的"保险"，有了这个老板才敢让你上生产。

**A/B 测试与灰度发布**是从"直觉驱动"到"数据驱动"的进化。A/B 测试不是"我觉得更好"，而是"数据证明更好"。`ABTestEngine` 分配流量、收集结果、做统计检验——这是科学实验的方法。灰度发布控制风险——先给 5% 用户用，没问题再逐步扩大。反馈收集让优化有方向——不是"猜用户要什么"，而是"听用户说什么"。阿码问的那个问题——"用户说 A，数据说 B，听谁的"——值得你长期思考。

**文档与交付**是从"个人项目"到"团队资产"的最后一跃。老潘的四层文档框架很实用：README 给所有人看，架构文档给开发者看，API 文档给集成方看，运维手册给运维看。交付清单是"保险"——每打一个勾，接手的人就少一个坑。老潘说的那句话值得记住："**文档不是写给未来的自己的，而是写给未来的陌生人的**"。

回顾 8 周的学习，你会发现这是一条从"会用 API"到"能做系统"的完整路径。Week 01-02 你学了 Prompt Engineering，让 LLM 听懂你的需求。Week 03-04 你学了 RAG，给 LLM 装上外部记忆。Week 05-06 你学了 Agent，让 LLM 会规划、会调用工具。Week 07 你学了评估、优化、部署，让系统能上生产。Week 08 你学了端到端设计、展示、迭代、交付，让项目能落地。

TextAgent 现在不仅是一个能跑的代码，而是一个**可展示、可交付、可维护、可持续的智能文本分析系统**。它有完整的架构、清晰的文档、可复现的部署、持续优化的机制。

更重要的是：你学会了"从训练模型到设计系统"的范式转变。在 LLM 时代，核心能力不是"如何训练更好的模型"，而是"如何用 LLM 构建有价值的应用"。Prompt、RAG、Agent、评估、部署、优化——这些是你的工具，系统设计是你的能力。

8 周结束，你不再只是"会用 API 的开发者"，而是"能设计 LLM 应用的工程师"。

**恭喜你完成这门课程！**

但这不是终点。LLM 技术仍在快速发展——新的模型、新的工具、新的范式会不断出现。你学到的是一套可迁移的思维方式：理解问题、设计系统、验证假设、持续优化。这些能力不会过时。

下一步？把 TextAgent 变成你的项目作品集，或者用它来解决真实的问题。或者，去探索更广阔的 LLM 应用世界。无论你走哪条路，这 8 周学到的都是你的基石。

**LLM 时代才刚刚开始。**

---

## Definition of Done（学生自测清单）

学完本章后，你应该能够回答以下问题：

- [ ] 我能设计端到端系统架构了吗？（Hint：定义输入、输出、中间流程，画出架构图）
- [ ] 我能模块化组织代码了吗？（Hint：每个模块只做一件事，通过接口通信）
- [ ] 我能准备商业价值报告了吗？（Hint：把技术指标转换成成本节省、效率提升）
- [ ] 我能设计 A/B 测试了吗？（Hint：定义对照版本、实验版本、评估指标、统计检验）
- [ ] 我能实现灰度发布了吗？（Hint：逐步扩大流量，监控指标，必要时回滚）
- [ ] 我能写完整的项目文档了吗？（Hint：README、架构、API、运维四层文档）
- [ ] 我的 TextAgent 是一个可交付的项目了吗？（Hint：检查交付清单）

如果以上都打勾，恭喜你完成 Week 08！你现在已经掌握了端到端 LLM 应用系统的完整开发流程。从会用 API 到能设计系统，从能跑代码到能交付项目——这是 8 周学习的"大结局"，也是你的新起点。

老潘会说："能跑是本事，能交付是能力。"现在你两者都有了。

<!--
================================================================================
【术语登记（供 TERMS.yml 参考）
================================================================================

本章新术语（待合入 shared/glossary.yml）：
1. 端到端系统设计（End-to-End System Design）
2. 商业落地（Business Deployment）
3. A/B 测试（A/B Testing）
4. 灰度发布（Canary Deployment）

已有术语的本周强化（回顾桥设计目标）：
- 多智能体系统（Multi-Agent System）— 来自 week_06，第 1 节回顾
- LLM 应用评估（LLM Application Evaluation）— 来自 week_07，第 3 节回顾
- 成本优化（Cost Optimization）— 来自 week_07，第 2 节回顾
- RAG 架构（RAG Architecture）— 来自 week_03，第 1 节回顾
- 可观测性（Observability）— 来自 week_07，第 3 节回顾
- Human-in-the-Loop（Human-in-the-Loop）— 来自 week_06，第 3 节回顾

================================================================================
-->
