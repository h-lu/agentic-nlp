"""
TextAgent 生产化改造（Week 07）

本模块在 Week 06 多智能体系统基础上，添加：
1. 评估模块（效果、成本、延迟监控）
2. 成本优化（模型选择、Prompt 优化、缓存）
3. 可观测性（日志、指标、Trace、告警）
4. FastAPI 服务部署

Week 07 核心更新：
- 从"能跑"进化为"可上生产"
- 从"不能评估"到"可度量、可优化"
- 从"本地脚本"到"Web 服务"
"""

from .production_system import (
    ProductionTextAgent,
    EvaluationModule,
    CostOptimizer,
    ObservabilityManager,
)

__all__ = [
    "ProductionTextAgent",
    "EvaluationModule",
    "CostOptimizer",
    "ObservabilityManager",
]
