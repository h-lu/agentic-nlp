#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：可观测性（Observability）

本例演示如何为 LLM 应用添加完整的可观测性：
- 日志（Logging）：记录"发生了什么"
- 指标（Metrics）：汇总"有多少"
- Trace（追踪）：展示"完整链路"
- 告警（Alerts）：在异常时及时通知

核心原则：
- 没有可观测性的系统就是"盲开"
- 日志要结构化，便于查询和统计
- 指标要关注关键数字，不要太多
- Trace 要记录完整链路，便于定位问题

运行方式：python3 chapters/week_07/examples/05_observability.py
预期输出：展示日志、指标、Trace 的完整示例

依赖：
- pip install prometheus-client
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================
# 配置
# ============================================================

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================
# 1. 结构化日志
# ============================================================

class StructuredLogger:
    """
    结构化日志记录器

    老潘说：
    "生产环境的日志不是 print()，而是结构化的、可查询的记录。

    为什么？因为 print() 输出的东西你没法搜索、没法过滤、没法统计。
    结构化日志——把每条日志写成 JSON——你可以直接丢进 Elasticsearch
    或者数据仓库，然后问'过去一周审核者 Agent 出错超过 3 次的请求有哪些'。"
    """

    def __init__(self, service_name: str):
        self.logger = logging.getLogger(service_name)
        self.service_name = service_name

    def log_llm_call(
        self,
        agent: str,
        model: str,
        prompt: str,
        response: str,
        tokens: Dict[str, int],
        cost: float,
        latency_ms: int
    ) -> None:
        """记录 LLM 调用（结构化）"""
        log_entry = {
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "llm_call",
            "agent": agent,
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "input_tokens": tokens.get("input", 0),
            "output_tokens": tokens.get("output", 0),
            "cost_usd": cost,
            "latency_ms": latency_ms
        }
        self.logger.info("llm_call", extra={"structured": log_entry})

    def log_agent_execution(
        self,
        agent: str,
        action: str,
        status: str,
        details: Dict[str, Any]
    ) -> None:
        """记录 Agent 执行（结构化）"""
        log_entry = {
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "agent_execution",
            "agent": agent,
            "action": action,
            "status": status,
            "details": details
        }
        self.logger.info("agent_execution", extra={"structured": log_entry})

    def log_error(
        self,
        component: str,
        error: str,
        context: Dict[str, Any]
    ) -> None:
        """记录错误（结构化）"""
        log_entry = {
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "component": component,
            "error": error,
            "context": context
        }
        self.logger.error("error", extra={"structured": log_entry})


# ============================================================
# 2. 指标收集
# ============================================================

class MetricsCollector:
    """
    指标收集器

    阿码问："日志很多，怎么快速知道'系统有没有问题'？"

    老潘答：
    "所以你需要指标——关键数字的汇总。
    日志是'发生了什么'，指标是'整体怎么样'。"
    """

    def __init__(self):
        self.requests: Dict[str, int] = {}
        self.errors: Dict[str, int] = {}
        self.latencies: List[float] = []
        self.costs: Dict[str, float] = {}

    def record_request(self, agent: str, status: str, latency: float) -> None:
        """记录请求"""
        key = f"{agent}.{status}"
        self.requests[key] = self.requests.get(key, 0) + 1
        self.latencies.append(latency)

    def record_error(self, agent: str, error_type: str) -> None:
        """记录错误"""
        key = f"{agent}.{error_type}"
        self.errors[key] = self.errors.get(key, 0) + 1

    def record_cost(self, model: str, cost: float) -> None:
        """记录成本"""
        self.costs[model] = self.costs.get(model, 0) + cost

    def get_summary(self) -> Dict[str, Any]:
        """获取指标汇总"""
        total_requests = sum(self.requests.values())
        total_errors = sum(self.errors.values())

        sorted_latencies = sorted(self.latencies)
        p95_index = int(len(sorted_latencies) * 0.95) if sorted_latencies else 0

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_latency": sum(self.latencies) / len(self.latencies) if self.latencies else 0,
            "p95_latency": sorted_latencies[p95_index] if sorted_latencies else 0,
            "total_cost_usd": sum(self.costs.values()),
            "cost_by_model": self.costs,
            "requests_by_agent": self.requests,
            "errors_by_type": self.errors
        }


# ============================================================
# 3. Trace 追踪
# ============================================================

@dataclass
class Span:
    """Span：一个操作的记录"""
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """Trace：完整的调用链"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TraceContext:
    """
    追踪上下文

    小北发现一个棘手的问题：
    "用户投诉'回答错了'，但我们不知道是哪个 Agent 出的问题——
    是规划者的计划有问题？还是执行者理解错了？还是审核者漏掉了？"

    老潘说：
    "所以你需要 Trace——记录每个请求的完整链路。

    有了 Trace，当用户投诉时，你可以直接查这个请求的 trace_id，
    看到完整的执行链路：'规划花了 1.2 秒，执行花了 4.1 秒，审核花了 0.9 秒'。
    如果执行阶段某个步骤异常超时，你一眼就能看到。"
    """

    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: List[Span] = []
        self.metadata: Dict[str, Any] = {}

    @contextmanager
    def span(self, name: str, **metadata):
        """
        创建一个 Span

        使用方式：
        with trace.span("plan", agent="planner", task="xxx"):
            # 执行代码
        """
        span_id = str(uuid.uuid4())
        start_time = time.time()

        span = Span(
            span_id=span_id,
            name=name,
            start_time=start_time,
            metadata=metadata
        )

        try:
            yield span
        finally:
            end_time = time.time()
            span.end_time = end_time
            span.duration_ms = int((end_time - start_time) * 1000)
            self.spans.append(span)

    def get_trace(self) -> Trace:
        """获取完整 Trace"""
        return Trace(
            trace_id=self.trace_id,
            spans=self.spans,
            metadata=self.metadata
        )


# ============================================================
# 4. 告警管理
# ============================================================

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    message: str
    severity: str = "warning"


class AlertManager:
    """
    告警管理器

    老潘的建议：
    "不仅要监控，还要告警——当指标异常时及时通知。

    为什么需要告警？因为你不能 24 小时盯着仪表盘。
    告警让问题自动找你。"
    """

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Dict[str, Any]] = []

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        self.rules.append(rule)

    def check(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查所有规则"""
        new_alerts = []

        for rule in self.rules:
            if rule.condition(metrics):
                alert = {
                    "rule": rule.name,
                    "message": rule.message,
                    "severity": rule.severity,
                    "metrics": metrics,
                    "timestamp": datetime.now().isoformat()
                }
                new_alerts.append(alert)
                self.alerts.append(alert)

        return new_alerts

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃的告警"""
        return self.alerts


# ============================================================
# 5. 可观测系统（整合所有功能）
# ============================================================

class ObservableSystem:
    """
    可观测的系统：整合日志、指标、Trace
    """

    def __init__(self, service_name: str):
        self.logger = StructuredLogger(service_name)
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self._setup_alerts()

    def _setup_alerts(self) -> None:
        """设置告警规则"""
        # 规则 1：成本过高
        self.alerts.add_rule(AlertRule(
            name="high_cost",
            condition=lambda m: m.get("total_cost_usd", 0) > 10,
            message="总成本超过 $10",
            severity="warning"
        ))

        # 规则 2：延迟过高
        self.alerts.add_rule(AlertRule(
            name="high_latency",
            condition=lambda m: m.get("p95_latency", 0) > 5000,
            message="P95 延迟超过 5 秒",
            severity="warning"
        ))

        # 规则 3：错误率过高
        self.alerts.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda m: m.get("error_rate", 0) > 0.05,
            message="错误率超过 5%",
            severity="critical"
        ))

    def run_with_observability(
        self,
        task: str,
        fn: Callable[..., Any]
    ) -> Any:
        """
        运行函数并记录完整的可观测数据
        """
        trace = TraceContext()

        try:
            with trace.span("workflow", task=task):
                result = fn(task)

                # 记录成功指标
                self.metrics.record_request(
                    "workflow",
                    "success",
                    trace.get_trace().spans[0].duration_ms / 1000
                )

                # 记录日志
                self.logger.log_agent_execution(
                    "workflow",
                    "run",
                    "success",
                    {"task": task, "result": str(result)[:100]}
                )

                return result

        except Exception as e:
            # 记录错误
            self.metrics.record_error("workflow", type(e).__name__)
            self.logger.log_error("workflow", str(e), {"task": task})
            raise


# ============================================================
# 反例：没有可观测性的问题
# ============================================================

def show_observability_problems():
    """展示没有可观测性的后果"""
    print("\n" + "=" * 70)
    print("没有可观测性的后果")
    print("=" * 70)
    print("""
场景：系统上线一周后，用户开始投诉

问题 1：回答质量下降
  ❌ 没有可观测性：
     - 不知道是哪个 Agent 的问题
     - 不知道是 Prompt 变了还是模型变了
     - 只能"猜测原因 → 修改代码 → 等待下一个问题"

  ✅ 有可观测性：
     - 查 Trace 发现审核者 Agent 最近失败率上升
     - 查日志发现审核 Prompt 最近被修改过
     - 回滚修改，问题解决

问题 2：成本飙升
  ❌ 没有可观测性：
     - 不知道哪个 Agent 最烧钱
     - 不知道是查询量增加还是单次成本增加

  ✅ 有可观测性：
     - 查指标发现执行者调用次数翻倍
     - 查日志发现有大量重复查询
     - 添加缓存，成本降低 50%

问题 3：延迟变慢
  ❌ 没有可观测性：
     - 不知道是哪个环节变慢
     - 只能"到处加日志，重启服务"

  ✅ 有可观测性：
     - 查 Trace 发现检索阶段从 0.5s 变成 3s
     - 查日志发现向量数据库在另一区域
     - 调整数据库位置，延迟恢复

老潘的点评：
"没有可观测性的系统就是'盲开'——
你不知道系统有没有出问题，也不知道出问题在哪。
有了可观测性，你可以直接定位问题。"
    """)


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    """主入口"""

    print("=" * 70)
    print("可观测性演示")
    print("=" * 70)

    # 创建可观测系统
    system = ObservableSystem("textagent")

    # 模拟运行
    def mock_workflow(task: str) -> str:
        """模拟工作流"""
        time.sleep(0.1)
        return f"完成: {task}"

    # 运行几次
    print("\n运行任务...")
    for i in range(5):
        try:
            result = system.run_with_observability(f"任务 {i}", mock_workflow)
            print(f"  ✓ {result}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")

    # 获取指标
    print("\n" + "=" * 70)
    print("指标汇总")
    print("=" * 70)

    metrics = system.metrics.get_summary()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    # 检查告警
    print("\n" + "=" * 70)
    print("告警检查")
    print("=" * 70)

    alerts = system.alerts.check(metrics)
    if alerts:
        print(f"触发 {len(alerts)} 条告警:")
        for alert in alerts:
            print(f"  [{alert['severity']}] {alert['rule']}: {alert['message']}")
    else:
        print("没有触发告警")

    # 展示 Trace
    print("\n" + "=" * 70)
    print("Trace 示例")
    print("=" * 70)

    trace = TraceContext()

    with trace.span("plan", agent="planner", task="分析任务"):
        time.sleep(0.05)

    with trace.span("execute", agent="executor", steps=2):
        time.sleep(0.08)

    with trace.span("review", agent="reviewer"):
        time.sleep(0.03)

    trace_data = trace.get_trace()
    print(f"\nTrace ID: {trace_data.trace_id}")
    print("\nSpans:")
    for span in trace_data.spans:
        print(f"  {span.name:12s}: {span.duration_ms}ms")

    print(f"\n总耗时: {sum(s.duration_ms for s in trace_data.spans)}ms")

    # 展示问题
    show_observability_problems()

    # 总结
    print("\n" + "=" * 70)
    print("可观测性最佳实践")
    print("=" * 70)
    print("""
1. 日志
   ✅ 使用结构化日志（JSON）
   ✅ 记录关键事件和错误
   ✅ 包含足够的上下文信息

2. 指标
   ✅ 关注关键数字（延迟、错误率、成本）
   ✅ 定期汇总和统计
   ✅ 可视化展示

3. Trace
   ✅ 记录完整调用链
   ✅ 包含时间戳和元数据
   ✅ 支持 Trace ID 查询

4. 告警
   ✅ 设置合理的阈值
   ✅ 不要太多告警（会麻木）
   ✅ 及时通知和响应

老潘的建议：
"生产环境中，不要等用户投诉才知道出问题。
用可观测性让问题自动找你。"
    """)


if __name__ == "__main__":
    main()
