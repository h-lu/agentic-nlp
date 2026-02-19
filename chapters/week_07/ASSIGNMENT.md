# Week 07 作业：从 Demo 到生产 —— 评估、成本优化与部署

Week 06 你让 TextAgent 从"单兵作战"进化为"团队协作"——多智能体系统能规划、执行、审核、检索。小北当时很兴奋，但老板看了一周后问了两个问题：

1. "这个系统效果到底有多好？"
2. "成本是多少？"

小北愣住了——他只能回答"它能规划、能协作"，但说不出"好多少"和"花多少"。更糟的是，财务部门随后发来邮件：API 成本是预期的 3 倍。

这周你要让 TextAgent 从"能跑"进化为"可上生产"——添加评估体系、实现成本优化、部署 API 服务、添加可观测性。

---

## 作业背景

你的公司准备把 TextAgent 上线给客服团队使用。在上线前，CTO 提出了三个要求：

1. **可评估**：能量化系统的效果、成本、延迟
2. **成本可控**：明确知道钱花在哪，能优化成本
3. **可观测**：出问题时能快速定位

你用 Week 06 的多 Agent 系统试了试，发现它每次调用都要花不少钱，但不知道哪个 Agent 最烧钱；它有时候会返回奇怪的结果，但没有记录为什么；它还是一个本地脚本，客服团队没法用。这周你要解决这些问题。

---

## 核心任务（必做，60 分）

### Part 1：实现成本追踪与评估（25 分）

老潘说："生产环境中，我们每调用一次 LLM 都会记录五件事——模型名称、输入 Token、输出 Token、延迟、Agent 名称。这样才能知道'钱花在哪'。"

#### 要求

**1.1 实现 CostTracker（10 分）**

```python
# evaluation/cost_tracker.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMMetrics:
    """LLM 调用指标"""
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    timestamp: datetime
    agent_name: Optional[str] = None

class CostTracker:
    """成本追踪器"""

    # 2026 年 2 月的参考价格（每 1M Token）
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self):
        # TODO: 初始化
        pass

    def record_call(self, metrics: LLMMetrics):
        """记录一次 LLM 调用"""
        # TODO: 实现
        pass

    def calculate_cost(self, metrics: LLMMetrics) -> float:
        """计算单次调用成本（美元）"""
        # TODO: 实现
        # 成本 = (input_tokens * input_price + output_tokens * output_price) / 1M
        pass

    def get_summary(self) -> Dict:
        """获取成本汇总

        Returns:
            {
                "total_calls": 总调用次数,
                "total_cost_usd": 总成本（美元）,
                "total_tokens": 总 Token 数,
                "cost_by_agent": {
                    "planner": {"calls": 10, "cost": 0.5},
                    "executor": {"calls": 20, "cost": 0.3},
                    ...
                },
                "avg_latency_ms": 平均延迟
            }
        """
        # TODO: 实现
        # 关键：按 agent_name 分组统计
        pass
```

**1.2 实现 LLMEvaluator（15 分）**

还记得 Week 04 我们学的 RAG 评估吗？现在我们把评估范围扩展到完整的工作流。

```python
# evaluation/llm_evaluator.py
from typing import List, Dict
from openai import OpenAI

class LLMEvaluator:
    """LLM 应用评估器"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def evaluate_batch(self, test_cases: List[Dict], system_run_func) -> Dict:
        """批量评估测试用例

        Args:
            test_cases: 测试用例列表，每个用例是一个字典
                格式：{"query": "用户问题", "expected": "期望答案", "context": "检索到的上下文"}
                注意：这与 CHAPTER.md 中的 TestCase dataclass 等价，你可以选择使用
                dataclass 或字典格式，两者都可以正常工作
            system_run_func: 运行系统的函数，接受 query，返回实际输出

        Returns:
            {
                "num_cases": 测试用例数,
                "avg_faithfulness": 平均忠实度,
                "avg_relevancy": 平均相关性,
                "details": [每个用例的详细结果]
            }
        """
        # TODO: 实现
        # 1. 运行每个测试用例
        # 2. 用 LLM 作为评判者计算忠实度和相关性
        # 3. 汇总统计
        pass

    def calculate_faithfulness(self, response: str, context: str) -> float:
        """计算忠实度（0-1）

        忠实度：回答是否基于给定的上下文，没有幻觉
        """
        # TODO: 实现
        # 提示：让 LLM 评估回答是否与上下文一致
        pass

    def calculate_relevancy(self, query: str, response: str) -> float:
        """计算相关性（0-1）

        相关性：回答是否回答了查询的问题
        """
        # TODO: 实现
        # 提示：让 LLM 评估回答是否解决了查询
        pass
```

**测试成本追踪与评估**：

```python
# experiments/test_cost_tracking.py

def test_cost_tracking():
    """测试成本追踪"""
    from evaluation.cost_tracker import CostTracker, LLMMetrics
    from datetime import datetime

    tracker = CostTracker()

    # 模拟多 Agent 系统的调用
    tracker.record_call(LLMMetrics(
        model="gpt-4o",
        input_tokens=500,
        output_tokens=200,
        latency_ms=1200,
        timestamp=datetime.now(),
        agent_name="planner"
    ))

    tracker.record_call(LLMMetrics(
        model="gpt-4o-mini",
        input_tokens=300,
        output_tokens=100,
        latency_ms=800,
        timestamp=datetime.now(),
        agent_name="executor"
    ))

    # 获取汇总
    summary = tracker.get_summary()
    print("成本汇总：")
    print(f"总调用次数：{summary['total_calls']}")
    print(f"总成本：${summary['total_cost_usd']:.4f}")
    print(f"按 Agent 分组：{summary['cost_by_agent']}")
```

**预期输出示例**：

```text
成本汇总：
总调用次数：2
总成本：$0.0037
按 Agent 分组：{
    "planner": {"calls": 1, "cost": 0.0030},
    "executor": {"calls": 1, "cost": 0.0007}
}
平均延迟：1000 ms
```

**提交内容**：
- `evaluation/cost_tracker.py`：成本追踪器实现
- `evaluation/llm_evaluator.py`：评估器实现
- `experiments/test_cost_tracking.py`：测试代码
- `report.md`：包含测试输出和分析（哪个 Agent 最烧钱？）

---

### Part 2：部署 FastAPI 服务（20 分）

小北的 TextAgent 还是一个本地 Python 脚本，客服团队没法用。老潘说："该部署了。你需要把它变成一个 API 服务，让任何人都可以通过 HTTP 请求调用。"

#### 要求

**2.1 实现 FastAPI 服务（15 分）**

```python
# api/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time

app = FastAPI(title="TextAgent API", version="0.1.0")

# 请求/响应模型
class AnalysisRequest(BaseModel):
    """分析请求"""
    task: str
    enable_review: bool = False
    use_cache: bool = True

class StepResult(BaseModel):
    """执行步骤结果"""
    step: int
    action: str
    result: dict

class AnalysisResponse(BaseModel):
    """分析响应"""
    task: str
    plan: dict
    execution: List[StepResult]
    review: Optional[dict]
    cost_usd: float
    latency_ms: int

# 全局状态
textagent = None

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global textagent
    # TODO: 初始化 TextAgent
    pass

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """执行文本分析任务"""
    if textagent is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    start_time = time.time()

    try:
        # TODO: 运行 TextAgent
        result = textagent.run(
            task=request.task,
            enable_review=request.enable_review
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return AnalysisResponse(
            task=request.task,
            plan=result["plan"],
            execution=result["execution"]["results"],
            review=result.get("review"),
            cost_usd=textagent.cost_tracker.get_summary()["total_cost_usd"],
            latency_ms=latency_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """获取指标"""
    if textagent is None:
        return {"error": "Service not initialized"}
    return textagent.cost_tracker.get_summary()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**2.2 实现流式输出（5 分）**

阿码试了一下 API，发现一个问题："用户每次请求都要等 6 秒才能看到结果，体验不好。能不能让它像 ChatGPT 那样'逐字输出'？"

```python
# api/streaming.py

@app.post("/analyze/stream")
async def analyze_stream(request: AnalysisRequest):
    """流式执行任务——用户可以实时看到进度"""

    async def generate():
        """生成流式响应"""
        try:
            # 阶段 1：规划
            plan = textagent.planner.create_plan(request.task)
            yield f"data: {json.dumps({'stage': 'plan', 'data': plan})}\n\n"

            # 阶段 2：执行——逐步返回
            for step_result in textagent.executor.execute_plan_iter(plan):
                yield f"data: {json.dumps({'stage': 'execution', 'data': step_result})}\n\n"

            # 阶段 3：完成
            summary = textagent.cost_tracker.get_summary()
            yield f"data: {json.dumps({'stage': 'done', 'data': summary})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'stage': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
```

**测试 FastAPI 服务**：

```python
# experiments/test_api.py

def test_api():
    """测试 API 服务"""
    import requests

    # 启动服务后测试
    base_url = "http://localhost:8000"

    # 测试健康检查
    response = requests.get(f"{base_url}/health")
    print(f"健康检查：{response.json()}")

    # 测试分析接口
    response = requests.post(f"{base_url}/analyze", json={
        "task": "分析客户反馈并总结主要问题",
        "enable_review": True
    })
    result = response.json()
    print(f"分析结果：成本 ${result['cost_usd']:.4f}，延迟 {result['latency_ms']} ms")
```

**提交内容**：
- `api/server.py`：FastAPI 服务实现
- `api/streaming.py`：流式输出实现
- `experiments/test_api.py`：测试代码
- `report.md`：包含 API 测试结果和响应时间分析

---

### Part 3：添加可观测性（15 分）

系统上线一周后，老潘问了小北一个让他冷汗直流的问题："现在有 100 个用户在用，你怎么知道系统有没有出问题？"

小北想了想："用户会投诉吧？"

老潘摇头："等用户投诉就晚了。你需要监控系统，在问题影响用户之前就发现并解决。"

#### 要求

**3.1 实现结构化日志（5 分）**

```python
# observability/logger.py
import logging
from datetime import datetime

class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, service_name: str):
        self.logger = logging.getLogger(service_name)
        self.service_name = service_name

    def log_llm_call(self, agent: str, model: str, prompt: str,
                     response: str, tokens: dict, cost: float):
        """记录 LLM 调用"""
        # TODO: 实现
        # 输出 JSON 格式的日志，包含：
        # - timestamp, service, event, agent, model, tokens, cost
        pass

    def log_agent_execution(self, agent: str, action: str,
                           status: str, details: dict):
        """记录 Agent 执行"""
        # TODO: 实现
        pass
```

**3.2 实现 Trace 追踪（6 分）**

```python
# observability/tracing.py
from contextlib import contextmanager
from typing import Dict, List
import uuid
import time

class TraceContext:
    """追踪上下文"""

    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: List[Dict] = []

    @contextmanager
    def span(self, name: str, **metadata):
        """创建一个 Span——用 with 语句自动计时"""
        # TODO: 实现
        # 1. 生成 span_id
        # 2. 记录开始时间
        # 3. yield span
        # 4. 计算持续时间并添加到 spans
        pass

    def get_trace(self) -> Dict:
        """获取完整 Trace"""
        # TODO: 实现
        # 返回：{trace_id, spans, total_duration_ms}
        pass

# 使用示例
class TracedWorkflow:
    def run(self, task: str) -> Dict:
        trace = TraceContext()

        with trace.span("plan", agent="planner", task=task):
            plan = self.planner.create_plan(task)

        with trace.span("execute", agent="executor"):
            result = self.executor.execute_plan(plan)

        # 存储 Trace
        self._store_trace(trace.get_trace())

        return result
```

**3.3 实现告警规则（4 分）**

```python
# observability/alerts.py
from dataclasses import dataclass
from typing import Callable, List
from datetime import datetime

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: Callable[[Dict], bool]
    message: str

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Dict] = []

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        # TODO: 实现
        pass

    def check(self, metrics: Dict):
        """检查所有规则"""
        # TODO: 实现
        # 如果条件满足，记录告警
        pass

# 示例规则
alert_manager = AlertManager()

# 规则 1：成本过高
alert_manager.add_rule(AlertRule(
    name="high_cost",
    condition=lambda m: m.get("hourly_cost_usd", 0) > 10,
    message="每小时成本超过 $10"
))

# 规则 2：延迟过高
alert_manager.add_rule(AlertRule(
    name="high_latency",
    condition=lambda m: m.get("p95_latency_ms", 0) > 5000,
    message="P95 延迟超过 5 秒"
))
```

**测试可观测性**：

```python
# experiments/test_observability.py

def test_tracing():
    """测试追踪"""
    from observability.tracing import TraceContext

    trace = TraceContext()

    with trace.span("llm_call", agent="planner", model="gpt-4o"):
        # 模拟 LLM 调用
        time.sleep(0.1)

    with trace.span("llm_call", agent="executor", model="gpt-4o-mini"):
        time.sleep(0.05)

    trace_data = trace.get_trace()
    print(f"Trace ID: {trace_data['trace_id']}")
    print(f"总耗时: {trace_data['total_duration_ms']} ms")
    print(f"Spans: {len(trace_data['spans'])}")
```

**提交内容**：
- `observability/logger.py`：结构化日志实现
- `observability/tracing.py`：Trace 追踪实现
- `observability/alerts.py`：告警规则实现
- `experiments/test_observability.py`：测试代码
- `report.md`：包含追踪示例和告警规则说明

---

## 进阶任务（选做，25 分）

### 任务 4：实现成本优化策略（15 分）

阿码看了成本报告，皱着眉头说："多 Agent 效果确实好，但成本是单 Agent 的 4 倍。老板肯定不会批准——有没有办法在不降低太多效果的前提下降低成本？"

老潘说："成本优化不是'不花钱'，而是'把钱花在刀刃上'。"

#### 要求

**4.1 实现模型选择策略（6 分）**

```python
# optimization/model_selector.py

class ModelSelector:
    """模型选择器——按 Agent 职责选择合适的模型"""

    AGENT_MODELS = {
        "planner": "gpt-4o",        # 需要复杂推理
        "executor": "gpt-4o-mini",  # 简单工具调用
        "reviewer": "gpt-4o",       # 需要仔细检查
        "retriever": "gpt-4o-mini"  # 检索策略选择
    }

    def get_model(self, agent: str) -> str:
        """获取指定 Agent 应使用的模型"""
        # TODO: 实现
        pass

# 使用
class OptimizedWorkflow:
    def __init__(self, base_workflow):
        self.base_workflow = base_workflow
        self.model_selector = ModelSelector()

    def run(self, task: str) -> Dict:
        # 在调用 LLM 时使用 model_selector 选择模型
        ...
```

**4.2 实现语义缓存（6 分）**

```python
# optimization/cache.py
from typing import Optional

class SemanticCache:
    """语义缓存——避免重复调用 LLM"""

    def __init__(self, vector_store, similarity_threshold: float = 0.95):
        # TODO: 初始化
        pass

    def get(self, query: str) -> Optional[str]:
        """从缓存获取结果

        如果有语义相似的查询，返回缓存的结果
        """
        # TODO: 实现
        pass

    def set(self, query: str, response: str):
        """存储到缓存"""
        # TODO: 实现
        pass
```

**4.3 对比优化前后的成本（5 分）**

```python
# experiments/test_cost_optimization.py

def compare_optimization():
    """对比优化前后的成本"""

    # 优化前：所有 Agent 都用 GPT-4o
    result_before = run_workflow(use_optimization=False)
    cost_before = result_before["cost_usd"]

    # 优化后：按 Agent 选择模型 + 缓存
    result_after = run_workflow(use_optimization=True)
    cost_after = result_after["cost_usd"]

    # 对比
    print(f"优化前成本：${cost_before:.4f}")
    print(f"优化后成本：${cost_after:.4f}")
    print(f"节省：{(1 - cost_after/cost_before)*100:.1f}%")
```

**输出表格**：

```markdown
### 成本优化效果

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 成本/请求 | $0.08 | $0.035 | -56% |
| P95 延迟 | 6.2s | 4.1s | -34% |
| 忠实度 | 0.85 | 0.83 | -2% |

**结论**：
- 成本降低了 56%，效果只下降了 2%
- 延迟降低了 34%，用户体验更好
```

**提交内容**：
- `optimization/model_selector.py`：模型选择器实现
- `optimization/cache.py`：语义缓存实现
- `experiments/test_cost_optimization.py`：对比测试
- `report.md`：包含优化效果分析

---

### 任务 5：添加 Prometheus 指标（10 分）

老潘说："有了指标，你可以配 Grafana 仪表盘，一眼看到'过去 5 分钟成本是否飙升''P95 延迟是否超过阈值'。这就是监控的基础。"

#### 要求

**5.1 实现 Prometheus 指标收集（7 分）**

```python
# observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Counter：只增不减
request_count = Counter('textagent_requests_total', 'Total requests', ['agent', 'status'])
llm_cost_total = Counter('textagent_llm_cost_usd_total', 'Total LLM cost', ['model'])

# Histogram：记录分布
request_duration = Histogram('textagent_request_duration_seconds', 'Request duration')

# Gauge：可增可减
active_requests = Gauge('textagent_active_requests', 'Active requests')

class MetricsCollector:
    """指标收集器"""

    def record_request(self, agent: str, status: str, duration: float):
        """记录请求"""
        # TODO: 实现
        pass

    def record_llm_cost(self, model: str, cost: float):
        """记录 LLM 成本"""
        # TODO: 实现
        pass

    def export_metrics(self) -> bytes:
        """导出 Prometheus 格式的指标"""
        # TODO: 实现
        from prometheus_client import generate_latest
        return generate_latest()
```

**5.2 添加指标端点（3 分）**

```python
# api/metrics_endpoint.py

from fastapi.responses import Response
from observability.metrics import metrics_collector

@app.get("/metrics")
async def metrics():
    """Prometheus 会定期抓取这个端点"""
    return Response(content=metrics_collector.export_metrics(), media_type="text/plain")
```

**提交内容**：
- `observability/metrics.py`：Prometheus 指标实现
- `api/metrics_endpoint.py`：指标端点
- `report.md`：说明如何配置 Prometheus 抓取指标

---

## 挑战任务（加分，15 分）

### 任务 6：实现 A/B 测试框架（15 分）

小北问："我们怎么知道 GPT-4o 真的比 GPT-4o-mini 好？能不能同时跑两个版本，对比效果？"

这就是 A/B 测试——让不同用户使用不同配置，收集数据对比效果。

#### 要求

**6.1 实现 A/B 测试框架（10 分）**

```python
# experiments/ab_test.py
from typing import Dict, Callable
import random

class ABTestFramework:
    """A/B 测试框架"""

    def __init__(self):
        self.variants: Dict[str, Callable] = {}
        self.results: Dict[str, list] = {}

    def add_variant(self, name: str, func: Callable):
        """添加一个变体"""
        # TODO: 实现
        pass

    def assign_variant(self, user_id: str) -> str:
        """为用户分配变体（基于 user_id 哈希，保证一致性）"""
        # TODO: 实现
        # 提示：用 hash(user_id) % len(variants)
        pass

    def record_result(self, variant: str, metrics: Dict):
        """记录结果"""
        # TODO: 实现
        pass

    def get_report(self) -> Dict:
        """获取 A/B 测试报告"""
        # TODO: 实现
        # 返回每个变体的平均成本、延迟、质量
        pass

# 使用示例
ab_test = ABTestFramework()

# 变体 A：所有 Agent 用 GPT-4o
def variant_a(task):
    return run_workflow(task, model="gpt-4o")

# 变体 B：按 Agent 选择模型
def variant_b(task):
    return run_workflow_optimized(task)

ab_test.add_variant("all_gpt4", variant_a)
ab_test.add_variant("optimized", variant_b)

# 运行测试
for user_id, task in test_tasks:
    variant_name = ab_test.assign_variant(user_id)
    result = ab_test.variants[variant_name](task)
    ab_test.record_result(variant_name, result)

# 报告
report = ab_test.get_report()
print(report)
```

**6.2 A/B 测试报告（5 分）**

```markdown
### A/B 测试报告：模型选择策略

| 变体 | 平均成本 | P95 延迟 | 忠实度 | 用户满意度 |
|------|---------|---------|--------|-----------|
| A: 全部 GPT-4 | $0.08 | 6.2s | 0.85 | 4.2/5 |
| B: 优化选择 | $0.035 | 4.1s | 0.83 | 4.1/5 |

**结论**：
- 变体 B 成本降低 56%，延迟降低 34%
- 质量仅下降 2%，用户满意度无明显差异
- **建议**：采用变体 B 作为默认配置
```

**提交内容**：
- `experiments/ab_test.py`：A/B 测试框架实现
- `report.md`：包含 A/B 测试报告和决策建议

---

## AI 协作练习（可选）

Week 07 处于"主导期"，你可以让 AI 深度参与作业。但请记住：**AI 是结对开发伙伴，不是答案生成器。你必须对代码负责。**

### 任务：让 AI 帮你设计评估流水线

你希望 AI 帮你设计一个完整的评估流水线，用于自动测试 TextAgent 的效果、成本、延迟。

#### AI 对话提示

```
我正在开发一个多智能体文本分析系统（TextAgent），包含：
- PlannerAgent：任务规划
- ExecutorAgent：工具执行
- ReviewerAgent：结果审核
- RetrieverAgent：智能检索

我需要设计一个评估流水线，能够：
1. 自动运行测试用例
2. 计算效果指标（忠实度、相关性）
3. 追踪成本和延迟
4. 生成可视化报告

请帮我设计这个评估流水线的架构，包括：
- 核心组件和职责
- 数据流
- 如何集成到现有系统

请给出具体的 Python 类设计和接口定义。
```

#### 审查清单（必须完成）

```markdown
## AI 协作练习审查报告

### 1. 采纳的设计
- [ ] 列出你采纳的 AI 建议
- [ ] 说明为什么采纳（与你的需求匹配吗？）

### 2. 拒绝/修改的设计
- [ ] 列出你拒绝或修改的 AI 建议
- [ ] 说明原因（不适用？有更好的方案？）

### 3. 代码审查
- [ ] AI 生成的代码能运行吗？
- [ ] 类和方法的职责清晰吗？
- [ ] 有没有缺少错误处理的地方？
- [ ] 边界情况处理了吗？
- [ ] 命名清晰吗？

### 4. 改动记录
- [ ] 在最终代码中标注哪些是 AI 生成的，哪些是你修改的
- [ ] 说明你的修改理由

### 5. 收获总结
- 从这次 AI 协作中学到了什么？
- AI 在哪些方面最有帮助？在哪些方面需要你主导？
```

#### 提交内容

- `ai_collaboration/evaluation_pipeline.py`：你和 AI 协作设计的评估流水线
- `ai_collaboration/review_report.md`：审查报告
- `report.md`：在"AI 协作"章节说明你的收获

**重要**：AI 协作练习是可选的，不影响基础任务评分。但完成它可以帮助你更好地理解"如何与 AI 结对编程"。

---

## TextAgent 项目任务

本周将 TextAgent 改造为生产级系统。

### 要求

**更新 TextAgent 架构**：

```python
# src/textagent/__init__.py

class ProductionTextAgent:
    """生产级 TextAgent"""

    def __init__(self):
        # 核心组件
        self.workflow = MultiAgentWorkflow(...)
        self.cost_tracker = CostTracker()
        self.evaluator = LLMEvaluator(...)
        self.cache = SemanticCache(...)
        self.logger = StructuredLogger("textagent")
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()

    def run(self, task: str, enable_optimization: bool = True) -> Dict:
        """运行任务（带追踪和监控）"""
        trace = TraceContext()

        try:
            with trace.span("workflow", task=task):
                # 检查缓存
                if enable_optimization:
                    cached = self.cache.get(task)
                    if cached:
                        return cached

                # 运行工作流
                result = self.workflow.run(task)

                # 记录指标
                self.metrics.record_request("workflow", "success", ...)

                return result

        except Exception as e:
            self.metrics.record_request("workflow", "error", ...)
            raise

        finally:
            self._store_trace(trace.get_trace())
```

**在 report.md 中记录**：

```markdown
## Week 07：生产化改造

### 新增功能

1. 评估体系
   - 效果评估（忠实度、相关性）
   - 成本追踪（按 Agent 分组）
   - 延迟监控（平均、P95）

2. 成本优化
   - 模型选择（按 Agent 职责）
   - Prompt 精简（核心 vs 扩展）
   - 语义缓存（降低 30-50% 成本）

3. API 部署
   - FastAPI 服务
   - 流式输出支持
   - 错误处理与重试

4. 可观测性
   - 结构化日志
   - Prometheus 指标
   - Trace 追踪
   - 告警规则

### 评估结果

| 指标 | 优化前 | 优化后 | 改进 |
|------|-------|-------|------|
| 忠实度 | 0.85 | 0.83 | -2% |
| 成本/请求 | $0.08 | $0.035 | -56% |
| P95 延迟 | 6.2s | 4.1s | -34% |

### 下一步

- Week 08：端到端系统集成与终稿
```

---

## 提交清单

在提交作业前，请确认以下内容：

### 文件结构

```
week07_作业_你的姓名/
├── evaluation/
│   ├── cost_tracker.py         # Part 1.1
│   └── llm_evaluator.py        # Part 1.2
├── api/
│   ├── server.py               # Part 2.1
│   └── streaming.py            # Part 2.2
├── observability/
│   ├── logger.py               # Part 3.1
│   ├── tracing.py              # Part 3.2
│   ├── alerts.py               # Part 3.3
│   └── metrics.py              # 任务 5
├── optimization/
│   ├── model_selector.py       # 任务 4.1
│   └── cache.py                # 任务 4.2
├── experiments/
│   ├── test_cost_tracking.py   # Part 1 测试
│   ├── test_api.py             # Part 2 测试
│   ├── test_observability.py   # Part 3 测试
│   ├── test_cost_optimization.py  # 任务 4 测试
│   └── ab_test.py              # 任务 6
├── ai_collaboration/           # AI 协作（可选）
│   ├── evaluation_pipeline.py
│   └── review_report.md
├── src/textagent/
│   └── __init__.py             # ProductionTextAgent
├── report.md                   # 完整实验报告
└── README.md                   # 简要说明
```

### 质量检查

- [ ] 所有代码都能独立运行
- [ ] 成本追踪显示了每个 Agent 的成本
- [ ] FastAPI 服务能正常启动和响应
- [ ] 流式输出能正确显示阶段性结果
- [ ] 追踪能记录完整的执行链路
- [ ] report.md 包含所有实验结果
- [ ] TextAgent 整合了评估和监控能力
- [ ] （可选）AI 协作练习包含审查报告

---

## 常见问题

**Q：为什么成本追踪要按 Agent 分组？**

A：因为多 Agent 系统的瓶颈往往在某个特定的 Agent。例如，审核者 Agent 可能因为每次都重新读完整计划而花费过多。只有按 Agent 分组，你才能知道"谁最烧钱"，从而针对性优化。

**Q：流式输出和普通输出有什么区别？**

A：普通 API 是"等 6 秒，一次性返回所有结果"。流式输出是"等 0.5 秒看到计划，然后每秒看到一个新的执行步骤"。用户感知的延迟从 6 秒降到了 0.5 秒——这就是心理学。

**Q：为什么要用结构化日志而不是 print？**

A：因为 `print()` 输出的东西你没法搜索、没法过滤、没法统计。结构化日志（JSON 格式）可以直接丢进 Elasticsearch 或数据仓库，然后问"过去一周审核者 Agent 出错超过 3 次的请求有哪些"。

**Q：缓存什么情况下不能用？**

A：查询实时数据时不能用（如"我的订单现在在哪"）。通用知识可以缓存（如"怎么退款"）。缓存要设置 TTL（过期时间），防止返回过时信息。

**Q：A/B 测试的变体分配为什么要基于 user_id 哈希？**

A：为了保证同一个用户始终使用同一个变体。如果用随机分配，用户刷新页面可能看到不同版本，体验会很混乱。基于 user_id 哈希可以保证一致性。

---

## 评分重点

本次作业的评分重点：

1. **理解评估的价值**：不只是"能跑"，而是能量化"跑得怎么样"
2. **成本意识**：知道钱花在哪，能针对性优化
3. **工程化思维**：日志、指标、Trace 是生产环境的标配
4. **API 设计**：清晰的请求/响应模型，错误处理

记住老潘的话："没有可观测性的系统就是'盲开'——不知道它有没有出问题，也不知道出问题在哪。从 Demo 到 Production，评估和监控比功能更重要。"

---

## 提示

如果你遇到困难，可以参考 `starter_code/solution.py`。但记住：
1. 不要直接复制粘贴
2. 理解每一行代码的作用
3. 自己动手修改和调试

真正的学习发生在你设计评估指标、分析成本瓶颈、调试 API 问题的过程中。
