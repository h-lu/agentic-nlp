# Week 08 作业：最后一公里 —— 从能跑到落地

8 周前，你面对的是一堆陌生的概念——LLM、Prompt、RAG、Agent。Week 01-07 你写了很多代码，学了很多技术。但现在，小北遇到了一个"幸福的烦恼"：

他的 TextAgent 每个模块都能跑，但不知道怎么整合成一个完整的系统。他想向老板演示，但准备的都是技术细节，老板关心的是"能省多少钱"。他想交付项目，但没有文档、没有部署包、没有回滚方案。

这周你要让 TextAgent 从"分散的模块"进化为"可交付的项目"——设计端到端系统架构、准备商业价值报告、实现 A/B 测试和灰度发布、撰写完整文档、生成可展示的项目报告。

---

## 作业背景

你的公司要在下周一的董事会上展示 TextAgent 项目。CEO 提出了三个要求：

1. **可展示**：有完整的演示脚本和商业价值证明
2. **可交付**：文档完整、部署包就绪、知识传承到位
3. **可迭代**：有 A/B 测试和灰度发布机制，支持持续优化

CTO 补充了一点："如果项目上线后出问题，能在 5 分钟内回滚吗？"

这周你要解决这些问题，让 TextAgent 成为一个真正能落地的项目。

---

## 核心任务（必做，60 分）

### Part 1：设计端到端系统架构（20 分）

老潘看了小北的项目结构，只说了一句话："你现在有一堆乐高积木，但还没有拼成一座城堡。你需要一张蓝图。"

#### 要求

**1.1 实现模块化架构（10 分）**

```python
# system/orchestrator.py
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
        # TODO: 初始化
        pass

    def run(self, user_input: str) -> Dict[str, Any]:
        """端到端执行

        Returns:
            {
                "task_id": 任务ID,
                "result": 执行结果,
                "review": 审核结果（可选）,
                "cost_usd": 成本,
                "latency_ms": 延迟
            }
        """
        # TODO: 实现
        # 1. 创建 TaskContext
        # 2. 规划阶段
        # 3. 执行阶段（可能需要检索）
        # 4. 审核阶段（可选）
        # 5. 返回结果
        pass
```

**1.2 实现配置管理（10 分）**

```python
# system/config.py
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
        # TODO: 实现
        pass

    def to_yaml(self, path: str):
        """保存为 YAML 文件"""
        # TODO: 实现
        pass

# 配置文件示例
# config/production.yaml
"""
agents:
  planner:
    name: planner
    llm:
      provider: openai
      model: gpt-4o
      api_key: ${OPENAI_API_KEY}
      temperature: 0.7
    system_prompt: "你是一个任务规划专家..."
    enable_cache: true

retriever:
  vector_store:
    type: chroma
    path: ./data/chroma

observability:
  enable_tracing: true
  log_level: INFO
"""
```

**1.3 实现系统初始化（额外加分，5 分）**

```python
# system/bootstrap.py
from textagent.orchestrator import WorkflowOrchestrator
from textagent.config import SystemConfig

def create_system(config_path: str) -> WorkflowOrchestrator:
    """创建完整的端到端系统

    这是 TextAgent 的"系统蓝图"——任何人看这个函数
    就知道系统是怎么组装的。

    Args:
        config_path: 配置文件路径

    Returns:
        初始化好的编排器
    """
    # TODO: 实现
    # 1. 加载配置
    # 2. 初始化能力层
    # 3. 初始化 Agent
    # 4. 初始化编排器
    # 5. 包装可观测性
    pass
```

**测试端到端系统**：

```python
# experiments/test_system.py

def test_end_to_end():
    """测试端到端系统"""
    from system.bootstrap import create_system

    # 创建系统
    system = create_system("config/production.yaml")

    # 运行测试
    result = system.run("分析客户反馈并总结主要问题")

    print(f"任务 ID: {result['task_id']}")
    print(f"成本: ${result['cost_usd']:.4f}")
    print(f"延迟: {result['latency_ms']} ms")
    print(f"结果: {result['result']}")
```

**预期输出示例**：

```text
任务 ID: task_20250217_001
成本: $0.0350
延迟: 4100 ms
结果: {
  "summary": "客户反馈主要集中在三个方面：响应速度、产品质量、售后服务...",
  "sentiment": "mixed",
  "action_items": ["优化客服响应时间", "改进产品质量", "加强售后培训"]
}
```

**提交内容**：
- `system/orchestrator.py`：编排器实现
- `system/config.py`：配置管理实现
- `system/bootstrap.py`：系统初始化实现
- `config/production.yaml`：生产环境配置
- `experiments/test_system.py`：测试代码
- `report.md`：包含架构说明和测试结果

---

### Part 2：准备商业价值报告（20 分）

小北兴冲冲地去找老板演示，结果老板问了三个问题：

1. "这比原来的人力操作好在哪里？"
2. "上这个系统要花多少钱？能省多少钱？"
3. "如果出问题了，怎么回滚？"

小北愣住了——他准备了很多技术细节，但老板关心的完全不是这些。

#### 要求

**2.1 实现商业价值计算器（10 分）**

```python
# business/value_calculator.py
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

        Returns:
            {
                "period_days": 计算周期,
                "total_requests": 总请求数,
                "system_cost_usd": 系统成本,
                "manual_cost_usd": 人力成本,
                "savings_usd": 节省金额,
                "savings_percentage": 节省比例
            }
        """
        # TODO: 实现
        pass

    def calculate_roi(self, investment_usd: float, savings_per_month: float,
                      months: int = 12) -> Dict:
        """计算投资回报率

        Args:
            investment_usd: 初始投资（开发成本）
            savings_per_month: 每月节省
            months: 计算周期（月）

        Returns:
            {
                "total_investment": 总投资,
                "total_savings": 总节省,
                "roi_percentage": ROI 百分比,
                "payback_period_days": 回本周期（天）
            }
        """
        # TODO: 实现
        pass
```

**2.2 准备演示脚本（5 分）**

创建一个 10 分钟的演示脚本（Markdown 格式）：

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

**2.3 实现回滚方案（5 分）**

```python
# business/rollback.py
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
        # TODO: 初始化回滚方案
        # 触发条件示例：
        # - 错误率 > 5%
        # - 每小时成本 > $50
        # - P95 延迟 > 10 秒
        pass

    def check_health(self) -> bool:
        """检查系统健康状态"""
        # TODO: 实现
        # 检查所有触发条件
        pass

    def run_with_safety_net(self, user_input: str) -> Dict:
        """带安全网运行"""
        # TODO: 实现
        # 1. 先检查健康状态
        # 2. 如果不健康，自动回滚
        # 3. 如果异常，回滚
        pass
```

**测试商业价值计算**：

```python
# experiments/test_business_value.py

def test_business_value():
    """测试商业价值计算"""
    from business.value_calculator import BusinessValueCalculator

    calculator = BusinessValueCalculator(
        cost_per_request=0.035,  # 优化后的成本
        manual_cost_per_request=2.50  # 人力成本
    )

    # 场景：每日 1000 个请求，计算 90 天
    report = calculator.calculate_savings(daily_requests=1000, days=90)

    print(f"90 天节省成本: ${report['savings_usd']:.2f}")
    print(f"节省比例: {report['savings_percentage']:.1f}%")

    # ROI 计算
    roi_report = calculator.calculate_roi(
        investment_usd=50000,  # 开发成本
        savings_per_month=report['savings_usd'] / 3
    )

    print(f"ROI: {roi_report['roi_percentage']:.1f}%")
    print(f"回本周期: {roi_report['payback_period_days']} 天")
```

**预期输出示例**：

```text
90 天节省成本: $220,500.00
节省比例: 98.6%
ROI: 1320.0%
回本周期: 7 天
```

**提交内容**：
- `business/value_calculator.py`：商业价值计算器
- `business/rollback.py`：回滚方案实现
- `docs/demo_script.md`：演示脚本
- `experiments/test_business_value.py`：测试代码
- `report.md`：包含商业价值报告

---

### Part 3：撰写完整项目文档（20 分）

老潘问了最后一个问题："如果你下周就离职，接手的人能在一周内上手吗？"

小北想了想，摇摇头。老潘说："所以你需要文档——不是写给自己的笔记，而是写给接手的人的手册。"

#### 要求

**3.1 撰写 README（5 分）**

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
│   ├── capabilities/ # 能力层
│   ├── orchestrator/ # 工作流编排
│   └── observability/ # 可观测性
├── tests/           # 测试
└── docs/            # 文档
\`\`\`

## 许可证

MIT License
```

**3.2 撰写架构文档（5 分）**

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

**3.3 撰写 API 文档（5 分）**

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

**3.4 撰写运维手册（5 分）**

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

**测试文档**：

```python
# experiments/test_documentation.py

def test_documentation():
    """测试文档完整性"""

    import os
    from pathlib import Path

    docs_path = Path("docs")

    # 检查文档是否存在
    required_docs = [
        "README.md",
        "architecture.md",
        "api.md",
        "operations.md"
    ]

    for doc in required_docs:
        assert (docs_path / doc).exists(), f"缺少文档: {doc}"
        print(f"✓ {doc} 存在")

    # 检查文档内容
    readme = (docs_path / "README.md").read_text()
    assert "快速开始" in readme, "README 缺少快速开始部分"
    assert "安装" in readme, "README 缺少安装说明"

    print("所有文档检查通过！")
```

**提交内容**：
- `README.md`：项目说明
- `docs/architecture.md`：架构文档
- `docs/api.md`：API 文档
- `docs/operations.md`：运维手册
- `experiments/test_documentation.py`：文档测试
- `report.md`：文档说明

---

## 进阶任务（选做，25 分）

### 任务 4：实现 A/B 测试框架（15 分）

阿码问："我们怎么知道 GPT-4o 真的比 GPT-4o-mini 好？能不能同时跑两个版本，对比效果？"

这就是 A/B 测试——让不同用户使用不同配置，收集数据对比效果。

#### 要求

**4.1 实现 A/B 测试引擎（10 分）**

```python
# experiments/ab_test_engine.py
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
        # TODO: 初始化
        pass

    def assign_version(self, user_id: str) -> Version:
        """为用户分配版本

        使用哈希确保同一用户总是分配到同一版本
        """
        # TODO: 实现
        # 提示：用 hash(user_id) % 100 < traffic_split * 100
        pass

    def record_result(self, version: Version, metrics: Dict):
        """记录结果"""
        # TODO: 实现
        pass

    def analyze(self) -> Dict:
        """分析 A/B 测试结果

        Returns:
            {
                "test_name": 测试名称,
                "sample_size": {"A": 100, "B": 100},
                "mean_quality": {"A": 0.82, "B": 0.85},
                "lift": 提升百分比,
                "p_value": 统计显著性,
                "is_significant": 是否显著,
                "winner": "A" 或 "B" 或 "inconclusive"
            }
        """
        # TODO: 实现
        # 提示：用 scipy.stats 做t检验
        pass
```

**4.2 A/B 测试报告（5 分）**

```markdown
### A/B 测试报告：Prompt 优化

| 指标 | 版本 A（原版） | 版本 B（优化版） | 提升 |
|------|--------------|----------------|------|
| 样本量 | 100 | 100 | - |
| 平均质量分 | 0.82 | 0.85 | +3.7% |
| 平均成本 | $0.040 | $0.038 | -5% |
| 平均延迟 | 4.5s | 4.2s | -6.7% |
| P 值 | - | 0.03 | < 0.05 |

**结论**：
- 版本 B 在质量、成本、延迟上均优于版本 A
- 差异具有统计显著性（p < 0.05）
- **建议**：采用版本 B 作为默认配置
```

**测试 A/B 测试**：

```python
# experiments/test_ab_test.py

def test_ab_test():
    """测试 A/B 测试"""
    from experiments.ab_test_engine import ABTestEngine, ABTestConfig

    config = ABTestConfig(
        name="prompt_v2_vs_v1",
        description="测试优化后的 Prompt 是否提升质量",
        traffic_split=0.5
    )

    engine = ABTestEngine(config)

    # 模拟用户请求
    test_users = [f"user_{i}" for i in range(100)]

    for user_id in test_users:
        version = engine.assign_version(user_id)
        # 模拟运行系统并记录结果
        result = run_system_with_version(version)
        engine.record_result(version, result)

    # 分析结果
    analysis = engine.analyze()
    print(f"胜者: {analysis['winner']}")
    print(f"提升: {analysis['lift']:.1f}%")
    print(f"统计显著性: {analysis['is_significant']}")
```

**提交内容**：
- `experiments/ab_test_engine.py`：A/B 测试引擎
- `experiments/test_ab_test.py`：测试代码
- `report.md`：包含 A/B 测试报告

---

### 任务 5：实现灰度发布控制器（10 分）

A/B 测试告诉你"B 比 A 好"，但你应该立即把所有流量切到 B 吗？老潘摇头："**灰度发布**——先给小部分用户用，没问题再逐步扩大。"

#### 要求

**5.1 实现灰度发布控制器（7 分）**

```python
# deployment/canary.py
from typing import Dict, List
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
        # TODO: 初始化
        pass

    def get_traffic_percentage(self) -> float:
        """获取当前应该分配给新版本的流量比例"""
        # TODO: 实现
        # 根据当前日期计算应该处于哪个阶段
        pass

    def should_use_new_version(self, user_id: str) -> bool:
        """判断是否使用新版本"""
        # TODO: 实现
        # 基于流量比例和 user_id 哈希
        pass

    def check_rollback_conditions(self, metrics: Dict) -> bool:
        """检查是否需要回滚

        Returns:
            True 表示需要回滚
        """
        # TODO: 实现
        # 检查错误率、成本等指标
        pass

    def advance_stage(self) -> bool:
        """手动推进到下一阶段

        Returns:
            是否成功推进（False 表示已经是最后阶段）
        """
        # TODO: 实现
        pass
```

**5.2 灰度发布报告（3 分）**

```markdown
### 灰度发布报告：v2.0 上线

**发布计划**：
- 第 1 天：5% 流量
- 第 3 天：25% 流量
- 第 7 天：50% 流量
- 第 14 天：100% 流量

**实际进展**：
- 第 1 天：5% 流量，指标正常，继续
- 第 3 天：25% 流量，成本略升但在阈值内，继续
- 第 7 天：50% 流量，所有指标正常，继续
- 第 14 天：100% 流量，发布完成

**回滚事件**：无

**结论**：
- v2.0 版本已成功全量发布
- 所有关键指标在正常范围内
```

**测试灰度发布**：

```python
# experiments/test_canary.py

def test_canary_deployment():
    """测试灰度发布"""
    from deployment.canary import CanaryDeployment

    canary = CanaryDeployment([
        {"day": 1, "traffic_percentage": 5},
        {"day": 3, "traffic_percentage": 25},
        {"day": 7, "traffic_percentage": 50},
        {"day": 14, "traffic_percentage": 100}
    ])

    # 测试流量分配
    test_users = [f"user_{i}" for i in range(100)]

    new_version_count = sum(
        1 for user in test_users
        if canary.should_use_new_version(user)
    )

    print(f"当前流量比例: {canary.get_traffic_percentage()}%")
    print(f"新版本用户数: {new_version_count}/100")
```

**提交内容**：
- `deployment/canary.py`：灰度发布控制器
- `experiments/test_canary.py`：测试代码
- `report.md`：包含灰度发布报告

---

## 挑战任务（加分，20 分）

### 任务 6：生成可展示的项目终稿（20 分）

这是最后一周的挑战任务：把 8 周的学习成果整合成一份完整的项目报告，可以展示给老板、客户、或者放在简历上。

#### 要求

**6.1 生成 report.md（10 分）**

```markdown
# TextAgent 项目终稿

## 项目概述

TextAgent 是一个端到端的 Agentic 文本分析系统，基于 LLM 技术，能够自动分析用户需求、制定执行计划、调用多种工具、从知识库检索相关信息、并审核结果质量。

### 核心价值

- **自动化**：替代人工文本分析，节省 98% 成本
- **智能化**：多智能体协作，处理复杂任务
- **可控性**：人工审核介入，确保输出质量
- **可扩展**：模块化设计，易于添加新功能

## 技术架构

### 系统设计

```
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
```

### 核心模块

1. **Planner**：任务分解与规划
   - 分析用户需求
   - 制定执行计划
   - 决定是否需要检索

2. **Executor**：工具调用与执行
   - 情感分析
   - 关键词提取
   - 词频统计

3. **Retriever**：知识检索（RAG）
   - 向量检索
   - 混合检索
   - 查询重写

4. **Reviewer**：结果审核
   - 质量检查
   - 人工介入
   - 反馈收集

### 技术栈

- **LLM**：OpenAI GPT-4o / GPT-4o-mini
- **向量数据库**：ChromaDB
- **API 框架**：FastAPI
- **监控**：Prometheus + Grafana
- **追踪**：LangSmith
- **部署**：Docker + Kubernetes

## 评估结果

### 效果指标

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 忠实度 | 0.75 | 0.85 | +13% |
| 相关性 | 0.78 | 0.87 | +12% |
| 准确率 | 0.82 | 0.88 | +7% |

### 成本指标

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 成本/请求 | $0.08 | $0.035 | -56% |
| P95 延迟 | 6.2s | 4.1s | -34% |

## 商业价值

### 成本节省

- 90 天节省成本：$220,500
- 节省比例：98.6%
- ROI：1320%
- 回本周期：7 天

### 效率提升

- 处理时间：从 30 分钟降到 30 秒（60x）
- 并发能力：支持 100+ 并发请求
- 自动化率：95%

## 持续优化

- **A/B 测试框架**：支持 Prompt、模型、配置的对比
- **灰度发布**：逐步推广新版本，降低风险
- **反馈收集**：用户满意度追踪，持续改进

## 部署与运维

- **容器化**：Docker 镜像
- **编排**：Kubernetes 部署
- **监控**：Prometheus + Grafana
- **告警**：自动告警规则
- **日志**：结构化日志 + Trace

## 项目演进

### Week 01-02：基础
- LLM API 封装
- Prompt Engineering
- 基础评估

### Week 03-04：RAG
- 向量检索
- 混合检索
- 重排序
- RAG 评估

### Week 05-06：Agent
- 单 Agent 工作流
- 多智能体协作
- Agentic RAG

### Week 07：生产化
- 成本优化
- API 部署
- 可观测性

### Week 08：落地
- 端到端架构
- 商业价值证明
- A/B 测试
- 灰度发布
- 完整文档

## 文档

- [README](README.md)：快速开始
- [架构文档](docs/architecture.md)：系统设计
- [API 文档](docs/api.md)：接口说明
- [运维手册](docs/operations.md)：部署排错

## 团队与致谢

本项目由 [你的名字] 开发，历时 8 周，从零构建了一个完整的 Agentic 文本分析系统。

特别感谢：
- 课程讲师提供的指导
- 开源社区（LangChain、LangSmith）的支持
- 同学和同事的反馈与建议

## 许可证

MIT License

---

**项目地址**：[GitHub 链接]
**联系方式**：[你的邮箱]
**完成日期**：2026 年 2 月
```

**6.2 生成 report.html（10 分）**

```python
# scripts/generate_report.py
import markdown
from pathlib import Path

def generate_html_report(markdown_path: str, output_path: str):
    """从 Markdown 生成 HTML 报告

    Args:
        markdown_path: Markdown 文件路径
        output_path: 输出 HTML 文件路径
    """
    # TODO: 实现
    # 1. 读取 Markdown
    # 2. 转换为 HTML
    # 3. 添加 CSS 样式
    # 4. 写入文件
    pass

# CSS 样式示例
REPORT_CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    color: #333;
}

h1 {
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}

h2 {
    border-bottom: 1px solid #ccc;
    padding-bottom: 5px;
    margin-top: 30px;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

table th {
    background-color: #f2f2f2;
}

code {
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
}

pre {
    background-color: #f4f4f4;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
}
"""

if __name__ == "__main__":
    generate_html_report("report.md", "report.html")
    print("报告已生成：report.html")
```

**测试报告生成**：

```python
# experiments/test_report_generation.py

def test_report_generation():
    """测试报告生成"""
    from scripts.generate_report import generate_html_report
    from pathlib import Path

    # 生成 HTML
    generate_html_report("report.md", "report.html")

    # 检查文件是否存在
    assert Path("report.html").exists(), "report.html 未生成"

    # 检查内容
    html_content = Path("report.html").read_text()
    assert "<html>" in html_content, "HTML 格式不正确"
    assert "TextAgent" in html_content, "内容缺失"

    print("✓ 报告生成成功")
    print(f"文件大小: {len(html_content)} 字节")
```

**提交内容**：
- `report.md`：完整项目报告
- `report.html`：HTML 格式报告
- `scripts/generate_report.py`：报告生成脚本
- `experiments/test_report_generation.py`：测试代码
- `docs/demo_slides.md`：（可选）演示幻灯片

---

## AI 协作练习（可选）

Week 08 处于"主导期"，你可以让 AI 深度参与作业。但请记住：**AI 是结对开发伙伴，不是答案生成器。你必须对代码负责。**

### 任务：让 AI 帮你生成项目文档模板

你希望 AI 帮你生成完整的项目文档模板，包括 README、架构文档、API 文档、运维手册。

#### AI 对话提示

```
我正在开发一个多智能体文本分析系统（TextAgent），包含：
- PlannerAgent：任务规划
- ExecutorAgent：工具执行
- ReviewerAgent：结果审核
- RetrieverAgent：智能检索

技术栈：
- LLM：OpenAI GPT-4o
- 向量数据库：ChromaDB
- API 框架：FastAPI
- 部署：Docker + Kubernetes
- 监控：Prometheus + Grafana

请帮我生成以下文档的 Markdown 模板：
1. README.md（项目概述、快速开始、安装说明）
2. architecture.md（设计原则、整体架构、核心模块说明）
3. api.md（接口列表、请求/响应示例、错误码）
4. operations.md（部署步骤、监控指标、常见问题排查）

每个模板应该包含：
- 完整的章节结构
- 占位符（让我填写具体内容）
- 示例内容（让我知道怎么写）
```

#### 审查清单（必须完成）

```markdown
## AI 协作练习审查报告

### 1. 采纳的内容
- [ ] 列出你采纳的 AI 建议
- [ ] 说明为什么采纳（与你的项目匹配吗？）

### 2. 修改的内容
- [ ] 列出你修改的部分
- [ ] 说明原因（不准确？不完整？需要补充？）

### 3. 删除的内容
- [ ] 列出你删除的部分
- [ ] 说明原因（不适用？冗余？）

### 4. 新增的内容
- [ ] 列出你新增的部分
- [ ] 说明原因（AI 没覆盖到？项目特有？）

### 5. 文档质量检查
- [ ] 文档结构清晰吗？
- [ ] 内容准确吗？
- [ ] 示例代码能运行吗？
- [ ] 接手的人能看懂吗？

### 6. 收获总结
- 从这次 AI 协作中学到了什么？
- AI 在文档生成方面最有帮助的是什么？
- 哪些部分必须由人主导？
```

#### 提交内容

- `ai_collaboration/docs/`：你和 AI 协作生成的文档
- `ai_collaboration/review_report.md`：审查报告
- `report.md`：在"AI 协作"章节说明你的收获

**重要**：AI 协作练习是可选的，不影响基础任务评分。

---

## TextAgent 项目任务

本周完成 TextAgent 的最终整合，交付一个可展示、可交付的项目。

### 要求

**整合所有组件**：

```python
# src/textagent/__init__.py

class TextAgentSystem:
    """TextAgent 端到端系统"""

    def __init__(self, config_path: str):
        """从配置文件初始化系统"""
        self.config = SystemConfig.from_yaml(config_path)
        self.orchestrator = create_system(config_path)
        self.business_calculator = BusinessValueCalculator(...)
        self.ab_test_engine = None  # 按需初始化
        self.canary_deployment = None  # 按需初始化

    def run(self, user_input: str, **kwargs) -> Dict:
        """运行任务"""
        return self.orchestrator.run(user_input, **kwargs)

    def get_business_report(self, daily_requests: int, days: int) -> Dict:
        """生成商业价值报告"""
        return self.business_calculator.calculate_savings(daily_requests, days)

    def start_ab_test(self, config: ABTestConfig):
        """启动 A/B 测试"""
        self.ab_test_engine = ABTestEngine(config)

    def start_canary_deployment(self, stages: List[Dict]):
        """启动灰度发布"""
        self.canary_deployment = CanaryDeployment(stages)
```

**在 report.md 中记录最终状态**：

```markdown
## Week 08：终稿交付

### 系统架构

- 端到端编排器
- 模块化 Agent 设计
- 统一配置管理
- 完整文档体系

### 商业价值

- 90 天节省成本：$220,500
- ROI：1320%
- 回本周期：7 天

### 持续优化

- A/B 测试框架
- 灰度发布机制
- 反馈收集系统

### 交付物

- report.md：完整项目报告
- report.html：可展示的 HTML 报告
- 文档：README + 架构 + API + 运维
- 部署：Docker + Kubernetes 配置

### 项目总结

经过 8 周的开发，TextAgent 从一个简单的 LLM 调用脚本，进化为一个完整的、可交付的 Agentic 文本分析系统。它不仅能够自动处理复杂的文本分析任务，还具备完整的评估、监控、优化机制，以及清晰的文档和部署方案。

更重要的是，通过这个项目，我学会了"从训练模型到设计系统"的范式转变，掌握了 LLM 应用的完整开发流程。
```

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构

```
week08_作业_你的姓名/
├── system/
│   ├── orchestrator.py         # Part 1.1
│   ├── config.py               # Part 1.2
│   └── bootstrap.py            # Part 1.3
├── business/
│   ├── value_calculator.py     # Part 2.1
│   └── rollback.py             # Part 2.3
├── docs/
│   ├── README.md               # Part 3.1
│   ├── architecture.md         # Part 3.2
│   ├── api.md                  # Part 3.3
│   └── operations.md           # Part 3.4
├── experiments/
│   ├── test_system.py          # Part 1 测试
│   ├── test_business_value.py  # Part 2 测试
│   ├── test_documentation.py   # Part 3 测试
│   ├── test_ab_test.py         # 任务 4 测试
│   └── test_canary.py          # 任务 5 测试
├── deployment/
│   └── canary.py               # 任务 5
├── scripts/
│   └── generate_report.py      # 任务 6
├── ai_collaboration/           # AI 协作（可选）
│   └── review_report.md
├── config/
│   └── production.yaml         # 配置文件
├── src/textagent/
│   └── __init__.py             # TextAgentSystem
├── report.md                   # 任务 6 项目报告
├── report.html                 # 任务 6 HTML 报告
├── README.md                   # 项目说明
└── requirements.txt            # 依赖列表
```

### 质量检查

- [ ] 所有代码都能独立运行
- [ ] 端到端系统能完整执行任务
- [ ] 商业价值报告包含具体数字
- [ ] 文档结构完整、内容清晰
- [ ] A/B 测试引擎能正确分配流量
- [ ] 灰度发布控制器能按阶段推进
- [ ] report.md 和 report.html 生成成功
- [ ] TextAgent 整合了所有组件
- [ ] （可选）AI 协作练习包含审查报告

---

## 常见问题

**Q：为什么要用配置文件而不是直接写代码？**

A：因为配置文件让你可以在不修改代码的情况下调整系统。切换模型、改变参数、启用/禁用功能——这些都只需要改配置。更重要的是，配置文件可以版本控制，可以回滚，可以在不同环境间切换（开发、测试、生产）。

**Q：商业价值报告里的数字从哪来？**

A：从 Week 07 的成本追踪和评估结果里来。你有每请求的成本、延迟、质量指标，还有人工处理的时间成本。用这些数据计算"节省了多少"——这就是商业价值。

**Q：A/B 测试的统计显著性是什么意思？**

A：简单说，就是你观察到的差异是"真实存在的"而不是"偶然的"。p < 0.05 的意思是：如果两个版本其实没有区别，看到这种差异的概率小于 5%。换句话说，你有 95% 的信心说 B 真的比 A 好。

**Q：灰度发布和 A/B 测试有什么区别？**

A：A/B 测试是"实验"——目的是对比两个版本哪个更好。灰度发布是"部署"——目的是安全地推广新版本。A/B 测试结束后可能回滚或全量采用，灰度发布的目标是最终 100% 流量。

**Q：report.html 和 report.md 有什么区别？**

A：内容一样，格式不同。Markdown 适合编辑和版本控制，HTML 适合展示。你可以把 report.html 发给老板、放在服务器上、或者导出 PDF。

---

## 评分重点

本次作业的评分重点：

1. **系统设计能力**：能否设计清晰的端到端架构
2. **商业意识**：能否用数据证明项目价值
3. **文档能力**：能否写出清晰的文档
4. **实验设计**：能否设计有效的 A/B 测试
5. **综合能力**：能否整合 8 周的学习成果

记住老潘的话："能跑是本事，能交付是能力。一个系统的价值不仅在于'能跑'，还在于'能落地、能维护、能迭代'。"

---

## 提示

如果你遇到困难，可以参考 `starter_code/solution.py`。但记住：
1. 不要直接复制粘贴
2. 理解每一行代码的作用
3. 自己动手修改和调试

真正的学习发生在你设计架构、准备演示、撰写文档的过程中。这些是让你从"会写代码"进化为"能做项目"的关键步骤。

**恭喜你完成 8 周的学习旅程！**
