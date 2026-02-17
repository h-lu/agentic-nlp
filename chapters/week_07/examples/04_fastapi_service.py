#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：FastAPI 服务部署（FastAPI Deployment）

本例演示如何将 TextAgent 部署为 FastAPI 服务。
核心概念：
- Pydantic 模型：请求/响应的类型验证
- 流式输出：降低用户感知的延迟
- 错误处理：重试和降级策略

运行方式：
python3 chapters/week_07/examples/04_fastapi_service.py

然后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 指标端点：http://localhost:8000/metrics

依赖：
- pip install fastapi uvicorn pydantic tenacity
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field, ConfigDict
    import uvicorn
except ImportError:
    print("需要安装依赖：pip install fastapi uvicorn pydantic tenacity")
    exit(1)

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    print("建议安装 tenacity：pip install tenacity")
    # 定义装饰器占位符
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def stop_after_attempt(n):
        return n

    def wait_exponential(**kwargs):
        return None


# ============================================================
# 数据模型
# ============================================================

class TaskType(str, Enum):
    """任务类型"""
    ANALYZE = "analyze"
    RETRIEVE = "retrieve"
    SUMMARIZE = "summarize"


class AnalysisRequest(BaseModel):
    """分析请求"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task": "分析客户反馈的情感倾向",
                "task_type": "analyze",
                "enable_review": True,
                "use_cache": True
            }
        }
    )
    task: str = Field(..., description="任务描述", min_length=1)
    task_type: TaskType = Field(default=TaskType.ANALYZE, description="任务类型")
    enable_review: bool = Field(default=False, description="是否启用审核")
    use_cache: bool = Field(default=True, description="是否使用缓存")


class StepResult(BaseModel):
    """执行步骤结果"""
    step: int
    action: str
    result: Dict[str, Any]
    status: str = "completed"
    latency_ms: int = 0


class AnalysisResponse(BaseModel):
    """分析响应"""
    task: str
    task_type: TaskType
    plan: Dict[str, Any]
    execution: List[StepResult]
    review: Optional[Dict[str, Any]] = None
    cost_usd: float = 0
    latency_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str = "0.1.0"


# ============================================================
# 模拟 TextAgent
# ============================================================

class MockTextAgent:
    """模拟 TextAgent（用于演示）"""

    def __init__(self):
        self.cost_tracker = MockCostTracker()

    def run(self, task: str, enable_review: bool = False) -> Dict[str, Any]:
        """运行任务"""
        start_time = time.time()

        # 模拟规划
        plan = {
            "task_understanding": f"理解任务: {task}",
            "subtasks": [
                {"step": 1, "action": "分析内容", "tool": "analyze"},
                {"step": 2, "action": "生成结果", "tool": "generate"}
            ]
        }

        # 模拟执行
        execution = [
            StepResult(
                step=1,
                action="分析内容",
                result={"sentiment": "positive", "confidence": 0.85},
                status="completed",
                latency_ms=500
            ),
            StepResult(
                step=2,
                action="生成结果",
                result={"summary": "分析完成"},
                status="completed",
                latency_ms=300
            )
        ]

        # 模拟审核
        review = None
        if enable_review:
            review = {
                "status": "approved",
                "issues": [],
                "suggestions": ["结果符合预期"]
            }

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "plan": plan,
            "execution": execution,
            "review": review,
            "latency_ms": latency_ms
        }


class MockCostTracker:
    """模拟成本追踪器"""

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_calls": 5,
            "total_cost_usd": 0.0025,
            "total_tokens": 1250
        }


# ============================================================
# 错误处理与重试
# ============================================================

class RobustLLMClient:
    """
    带重试和降级的 LLM 客户端

    老潘的经验：
    "生产环境不会像开发环境那么顺。
    网络会超时、API 会限流、模型会偶尔返回乱码。
    你需要做好错误处理和重试。"
    """

    def __init__(self):
        self.call_count = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def call_with_retry(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        带重试的调用

        重试策略：
        - 最多试 3 次
        - 指数退避：2s, 4s, 8s
        """
        self.call_count += 1

        # 模拟偶尔失败
        if self.call_count % 5 == 0:
            raise Exception("API 限流")

        # 模拟响应
        return f"[{model}] 响应: {prompt[:50]}..."


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(
    title="TextAgent API",
    description="生产级 TextAgent 服务，支持流式输出和错误处理",
    version="0.1.0"
)

# 全局状态
textagent = MockTextAgent()


# ============================================================
# 路由定义
# ============================================================

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """根路径"""
    return {
        "message": "TextAgent API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    健康检查端点

    Kubernetes 会定期调这个来检查服务是否健康
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """
    执行文本分析任务

    这是主要的 API 端点，接收分析请求并返回结果
    """
    start_time = time.time()

    try:
        # 运行 TextAgent
        result = textagent.run(
            task=request.task,
            enable_review=request.enable_review
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return AnalysisResponse(
            task=request.task,
            task_type=request.task_type,
            plan=result["plan"],
            execution=result["execution"],
            review=result.get("review"),
            cost_usd=textagent.cost_tracker.get_summary()["total_cost_usd"],
            latency_ms=latency_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """
    指标端点

    Prometheus 会定期抓取这个端点
    """
    return textagent.cost_tracker.get_summary()


# ============================================================
# 流式输出
# ============================================================

@app.post("/analyze/stream")
async def analyze_stream(request: AnalysisRequest) -> StreamingResponse:
    """
    流式执行任务——用户可以实时看到进度

    阿码问："为什么要流式输出？"

    老潘答：
    "普通 API 是'等 6 秒，一次性返回所有结果'。
    流式输出是'等 0.5 秒看到计划，然后每秒看到新的执行步骤'。
    用户感知的延迟从 6 秒降到了 0.5 秒——这就是心理学。"
    """

    async def generate():
        """生成流式响应"""
        try:
            # 阶段 1：规划
            yield f"event: plan\ndata: {{'stage': 'plan', 'message': '正在制定计划...'}}\n\n"
            await asyncio.sleep(0.5)

            plan = {
                "task_understanding": f"理解任务: {request.task}",
                "subtasks": [
                    {"step": 1, "action": "分析内容"},
                    {"step": 2, "action": "生成结果"}
                ]
            }
            yield f"event: plan\ndata: {{'stage': 'plan', 'data': {plan}}}\n\n"

            # 阶段 2：执行
            yield f"event: execution\ndata: {{'stage': 'execution', 'message': '开始执行...'}}\n\n"

            for i in range(1, 3):
                await asyncio.sleep(0.3)
                yield f"event: execution\ndata: {{'stage': 'execution', 'data': {{'step': {i}, 'action': '执行步骤 {i}'}}}}\n\n"

            # 阶段 3：审核（可选）
            if request.enable_review:
                await asyncio.sleep(0.2)
                yield f"event: review\ndata: {{'stage': 'review', 'data': {{'status': 'approved'}}}}\n\n"

            # 阶段 4：完成
            cost = textagent.cost_tracker.get_summary()["total_cost_usd"]
            yield f"event: done\ndata: {{'stage': 'done', 'data': {{'cost_usd': {cost}}}}}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {{'stage': 'error', 'message': '{str(e)}'}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================
# 错误处理示例
# ============================================================

@app.get("/error-demo")
async def error_demo() -> Dict[str, str]:
    """
    错误处理演示

    展示不同类型的错误如何处理
    """
    # 这个端点会触发一个错误
    raise HTTPException(
        status_code=418,
        detail="这是一个示例错误",
        headers={"X-Error-Type": "demo"}
    )


# ============================================================
# 启动事件
# ============================================================

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    print("\n" + "=" * 70)
    print("TextAgent API 启动中...")
    print("=" * 70)
    print("  文档地址: http://localhost:8000/docs")
    print("  健康检查: http://localhost:8000/health")
    print("  指标端点: http://localhost:8000/metrics")
    print("=" * 70 + "\n")


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理"""
    print("\nTextAgent API 关闭中...\n")


# ============================================================
# 主函数
# ============================================================

def main():
    """启动服务"""
    print("""
╔════════════════════════════════════════════════════════════╗
║          TextAgent API - 生产级 FastAPI 服务              ║
╠════════════════════════════════════════════════════════════╣
║  端点：                                                   ║
║    - POST /analyze         : 执行分析任务                  ║
║    - POST /analyze/stream  : 流式执行                      ║
║    - GET  /health          : 健康检查                      ║
║    - GET  /metrics         : 指标数据                      ║
║    - GET  /docs            : API 文档（Swagger UI）        ║
╠════════════════════════════════════════════════════════════╣
║  测试命令：                                              ║
║    # 普通请求                                             ║
║    curl -X POST http://localhost:8000/analyze \\          ║
║      -H 'Content-Type: application/json' \\              ║
║      -d '{{"task": "分析客户反馈"}}'                      ║
║                                                           ║
║    # 流式请求                                             ║
║    curl -N http://localhost:8000/analyze/stream \\        ║
║      -H 'Content-Type: application/json' \\              ║
║      -d '{{"task": "分析客户反馈"}}'                      ║
╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
