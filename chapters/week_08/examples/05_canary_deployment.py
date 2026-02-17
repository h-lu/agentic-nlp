#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：灰度发布控制器（Canary Deployment）

本例演示如何实现灰度发布——逐步推广新版本。
核心概念：
- CanaryDeployment：分阶段逐步扩大新版本流量
- 监控指标：错误率、成本、延迟
- 自动回滚：触发条件满足时回滚到旧版本

老潘的经验：
"灰度发布的核心是风险控制。你不需要一次性把所有用户
都暴露在新版本下。如果发现问题，只有 5% 的用户受影响，
而不是 100%。宁可让少数人失望，不要让所有人崩溃。"

运行方式：python3 chapters/week_08/examples/05_canary_deployment.py
预期输出：展示灰度发布流程和回滚决策

依赖：
- pip install pydantic
"""

from __future__ import annotations

import hashlib
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


# ============================================================
# 数据结构
# ============================================================

class DeploymentStatus(str, Enum):
    """部署状态"""
    PENDING = "pending"
    ROLLING_OUT = "rolling_out"
    STABLE = "stable"
    ROLLED_BACK = "rolled_back"
    COMPLETED = "completed"


@dataclass
class CanaryStage:
    """灰度阶段配置"""
    day: int
    traffic_percentage: float
    description: str = ""

    def to_dict(self) -> Dict:
        return {
            "day": self.day,
            "traffic_percentage": self.traffic_percentage,
            "description": self.description
        }


@dataclass
class HealthMetrics:
    """健康指标"""
    error_rate: float = 0.0
    cost_increase_pct: float = 0.0
    latency_p95_ms: float = 0.0
    user_satisfaction: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "error_rate": self.error_rate,
            "cost_increase_pct": self.cost_increase_pct,
            "latency_p95_ms": self.latency_p95_ms,
            "user_satisfaction": self.user_satisfaction,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RollbackConfig:
    """回滚配置"""
    error_rate_threshold: float = 0.05  # 错误率 > 5%
    cost_threshold_pct: float = 20.0  # 成本增加 > 20%
    latency_threshold_ms: float = 10000  # P95 延迟 > 10s
    satisfaction_threshold: float = 0.7  # 满意度 < 0.7

    def should_rollback(self, metrics: HealthMetrics) -> bool:
        """判断是否需要回滚"""
        if metrics.error_rate > self.error_rate_threshold:
            return True
        if metrics.cost_increase_pct > self.cost_threshold_pct:
            return True
        if metrics.latency_p95_ms > self.latency_threshold_ms:
            return True
        if metrics.user_satisfaction < self.satisfaction_threshold:
            return True
        return False


# ============================================================
# 灰度发布控制器
# ============================================================

class CanaryDeployment:
    """
    灰度发布控制器

    阿码问："为什么不直接切 100% 流量？"

    老潘答：
    "因为生产环境充满了意外。你以为准备好了，
    但可能会有：数据库负载过高、第三方 API 限流、
    特殊用户输入导致崩溃。灰度发布让你在小规模
    用户上先验证，出了问题影响可控。"
    """

    def __init__(
        self,
        stages: List[CanaryStage],
        rollback_config: Optional[RollbackConfig] = None
    ):
        """
        初始化灰度发布

        Args:
            stages: 灰度阶段列表，按天数递增
            rollback_config: 回滚配置
        """
        # 按天数排序
        self.stages = sorted(stages, key=lambda x: x.day)
        self.rollback_config = rollback_config or RollbackConfig()

        self.start_date = datetime.now()
        self.current_stage_idx = 0
        self.status = DeploymentStatus.PENDING
        self.metrics_history: List[HealthMetrics] = []
        self.rollback_triggered = False
        self.rollback_reason: Optional[str] = None

    def get_current_stage(self) -> CanaryStage:
        """获取当前应该处于的阶段"""
        days_elapsed = (datetime.now() - self.start_date).days

        # 找到当前应该处于的阶段
        for i, stage in enumerate(self.stages):
            if days_elapsed >= stage.day:
                self.current_stage_idx = i

        return self.stages[self.current_stage_idx]

    def get_traffic_percentage(self) -> float:
        """获取当前应该分配给新版本的流量比例"""
        if self.rollback_triggered:
            return 0.0

        stage = self.get_current_stage()
        return stage.traffic_percentage

    def should_use_new_version(self, user_id: str) -> bool:
        """
        判断是否使用新版本

        Args:
            user_id: 用户 ID

        Returns:
            True 表示使用新版本，False 表示使用旧版本
        """
        traffic_pct = self.get_traffic_percentage()

        # 使用哈希确保一致性
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (hash_val % 100) < traffic_pct

    def record_metrics(self, metrics: HealthMetrics) -> None:
        """记录健康指标"""
        self.metrics_history.append(metrics)

        # 检查是否需要回滚
        if self.rollback_config.should_rollback(metrics):
            self._trigger_rollback(metrics)

    def _trigger_rollback(self, metrics: HealthMetrics) -> None:
        """触发回滚"""
        self.rollback_triggered = True
        self.status = DeploymentStatus.ROLLED_BACK

        # 找出触发原因
        reasons = []
        if metrics.error_rate > self.rollback_config.error_rate_threshold:
            reasons.append(f"错误率过高: {metrics.error_rate:.2%}")
        if metrics.cost_increase_pct > self.rollback_config.cost_threshold_pct:
            reasons.append(f"成本增加过多: {metrics.cost_increase_pct:.1f}%")
        if metrics.latency_p95_ms > self.rollback_config.latency_threshold_ms:
            reasons.append(f"延迟过高: {metrics.latency_p95_ms:.0f}ms")
        if metrics.user_satisfaction < self.rollback_config.satisfaction_threshold:
            reasons.append(f"用户满意度过低: {metrics.user_satisfaction:.2f}")

        self.rollback_reason = "; ".join(reasons)

    def get_status(self) -> Dict:
        """获取发布状态"""
        current_stage = self.get_current_stage()
        days_elapsed = (datetime.now() - self.start_date).days

        return {
            "status": self.status.value,
            "days_elapsed": days_elapsed,
            "current_stage": current_stage.to_dict(),
            "traffic_percentage": self.get_traffic_percentage(),
            "rollback_triggered": self.rollback_triggered,
            "rollback_reason": self.rollback_reason,
            "total_stages": len(self.stages),
            "remaining_stages": len(self.stages) - self.current_stage_idx - 1
        }

    def complete(self) -> None:
        """标记发布完成"""
        if not self.rollback_triggered:
            self.status = DeploymentStatus.COMPLETED

    def get_progress_summary(self) -> str:
        """获取进度摘要"""
        status = self.get_status()

        if self.rollback_triggered:
            return f"❌ 回滚: {self.rollback_reason}"

        if status["status"] == DeploymentStatus.COMPLETED.value:
            return "✅ 发布完成"

        progress_pct = (self.current_stage_idx + 1) / len(self.stages) * 100
        return f"🔄 进行中: 阶段 {self.current_stage_idx + 1}/{len(self.stages)} ({progress_pct:.0f}%)"


# ============================================================
# 反例：没有灰度发布的问题
# ============================================================

def bad_example():
    """反例：没有灰度发布的问题"""
    print("\n" + "=" * 70)
    print("❌ 反例：没有灰度发布的问题")
    print("=" * 70)
    print("""
小北优化了系统，直接把 100% 流量切到新版本。

结果：
- 10 分钟后，API 延迟飙升到 30 秒
- 数据库连接数爆满
- 用户投诉涌入
- 不得不紧急回滚

问题在哪？

1. **没有小规模验证**：问题在 100% 用户面前爆发
2. **没有回滚预案**：回滚花了 20 分钟，期间系统不可用
3. **没有监控预警**：问题发生 10 分钟后才发现
4. **影响面太大**：所有用户都受影响

老潘的点评：
"这就是为什么大厂都有灰度发布流程。
先给 1% 用户试，没问题再扩大到 5%、10%、50%。
每一步都盯着监控指标，有问题立即回滚。
灰度发布是你的'安全网'——宁可慢一点，
不要让所有用户一起掉下去。"
    """)


# ============================================================
# 模拟运行
# ============================================================

def simulate_canary_deployment():
    """模拟灰度发布流程"""

    print("""
╔════════════════════════════════════════════════════════════╗
║          灰度发布控制器演示（Canary Deployment）            ║
╠════════════════════════════════════════════════════════════╣
║  场景：新版本 TextAgent 逐步推广                           ║
║    - 第 1 天：5% 流量                                       ║
║    - 第 3 天：25% 流量                                      ║
║    - 第 7 天：50% 流量                                      ║
║    - 第 14 天：100% 流量                                    ║
╚════════════════════════════════════════════════════════════╝
    """)

    # 创建灰度发布配置
    stages = [
        CanaryStage(day=1, traffic_percentage=5, description="初始灰度"),
        CanaryStage(day=3, traffic_percentage=25, description="扩大灰度"),
        CanaryStage(day=7, traffic_percentage=50, description="半量发布"),
        CanaryStage(day=14, traffic_percentage=100, description="全量发布")
    ]

    rollback_config = RollbackConfig(
        error_rate_threshold=0.05,  # 5%
        cost_threshold_pct=20.0,  # 20%
        latency_threshold_ms=10000,  # 10s
        satisfaction_threshold=0.7  # 0.7
    )

    canary = CanaryDeployment(stages, rollback_config)
    canary.status = DeploymentStatus.ROLLING_OUT

    print("\n[配置] 灰度阶段:")
    for stage in stages:
        print(f"  第 {stage.day:2d} 天: {stage.traffic_percentage:3.0f}% 流量 - {stage.description}")

    print("\n[配置] 回滚阈值:")
    print(f"  错误率 > {rollback_config.error_rate_threshold:.0%}")
    print(f"  成本增加 > {rollback_config.cost_threshold_pct:.0f}%")
    print(f"  P95 延迟 > {rollback_config.latency_threshold_ms:.0f}ms")
    print(f"  用户满意度 < {rollback_config.satisfaction_threshold:.1f}")

    # 模拟不同阶段的用户请求
    print("\n" + "=" * 70)
    print("模拟不同阶段的用户请求")
    print("=" * 70)

    # 第 1 天：5% 流量
    print("\n[第 1 天] 初始灰度（5% 流量）")
    canary.start_date = datetime.now() - timedelta(days=1)
    print(f"  当前阶段: {canary.get_current_stage().description}")
    print(f"  流量比例: {canary.get_traffic_percentage():.0f}%")

    # 模拟 100 个用户
    new_version_count = 0
    for i in range(100):
        user_id = f"user_day1_{i}"
        if canary.should_use_new_version(user_id):
            new_version_count += 1

    print(f"  模拟 100 个用户: {new_version_count} 个使用新版本")

    # 记录健康指标（正常）
    metrics = HealthMetrics(
        error_rate=0.01,
        cost_increase_pct=5.0,
        latency_p95_ms=3500,
        user_satisfaction=0.85
    )
    canary.record_metrics(metrics)
    print(f"  健康指标: 错误率 {metrics.error_rate:.1%}, 延迟 {metrics.latency_p95_ms:.0f}ms")
    print(f"  ✓ 指标正常，继续推广")

    # 第 3 天：25% 流量
    print("\n[第 3 天] 扩大灰度（25% 流量）")
    canary.start_date = datetime.now() - timedelta(days=3)
    print(f"  当前阶段: {canary.get_current_stage().description}")
    print(f"  流量比例: {canary.get_traffic_percentage():.0f}%")

    new_version_count = 0
    for i in range(100):
        user_id = f"user_day3_{i}"
        if canary.should_use_new_version(user_id):
            new_version_count += 1

    print(f"  模拟 100 个用户: {new_version_count} 个使用新版本")

    # 记录健康指标（仍然正常）
    metrics = HealthMetrics(
        error_rate=0.02,
        cost_increase_pct=8.0,
        latency_p95_ms=4200,
        user_satisfaction=0.82
    )
    canary.record_metrics(metrics)
    print(f"  健康指标: 错误率 {metrics.error_rate:.1%}, 延迟 {metrics.latency_p95_ms:.0f}ms")
    print(f"  ✓ 指标正常，继续推广")

    # 第 7 天：50% 流量（模拟出现问题）
    print("\n[第 7 天] 半量发布（50% 流量）")
    canary.start_date = datetime.now() - timedelta(days=7)
    print(f"  当前阶段: {canary.get_current_stage().description}")
    print(f"  流量比例: {canary.get_traffic_percentage():.0f}%")

    new_version_count = 0
    for i in range(100):
        user_id = f"user_day7_{i}"
        if canary.should_use_new_version(user_id):
            new_version_count += 1

    print(f"  模拟 100 个用户: {new_version_count} 个使用新版本")

    # 记录健康指标（触发回滚）
    metrics = HealthMetrics(
        error_rate=0.08,  # 超过阈值 5%
        cost_increase_pct=25.0,  # 超过阈值 20%
        latency_p95_ms=8500,
        user_satisfaction=0.65
    )
    canary.record_metrics(metrics)
    print(f"  健康指标: 错误率 {metrics.error_rate:.1%}, 延迟 {metrics.latency_p95_ms:.0f}ms")
    print(f"  ⚠️ 指标异常，触发回滚！")

    # 显示回滚状态
    print("\n" + "=" * 70)
    print("回滚决策")
    print("=" * 70)

    status = canary.get_status()
    print(f"""
状态: {status['status'].upper()}
回滚原因: {status['rollback_reason']}

当前流量比例: {status['traffic_percentage']:.0f}% → 0%（自动切回旧版本）

老潘的点评：
"这就是灰度发布的价值。问题在第 7 天暴露，
但只影响了 50% 的用户，而且立即被监控捕获。
如果是直接切 100%，所有用户都会受影响，
而且你可能要等用户投诉才发现问题。"

阿码问："那我怎么知道问题是什么？"

老潘答：
"这就是为什么要有日志和 Trace。回滚之后，
你去查第 7 天的日志，看是什么操作导致了
错误率飙升。是某个特定用户输入？还是数据库
查询太慢？找到根因，修好后再灰度。"
    """)

    # 场景 2：顺利发布
    print("\n" + "=" * 70)
    print("场景 2：顺利发布到 100%")
    print("=" * 70)

    canary2 = CanaryDeployment(stages, rollback_config)
    canary2.status = DeploymentStatus.ROLLING_OUT
    canary2.start_date = datetime.now() - timedelta(days=14)

    status = canary2.get_status()
    print(f"""
天数: {status['days_elapsed']} 天
当前阶段: {status['current_stage']['description']}
流量比例: {status['traffic_percentage']:.0f}%
状态: {status['status'].upper()}
进度: {canary2.get_progress_summary()}
    """)

    # 记录最后阶段的健康指标（全部正常）
    final_metrics = HealthMetrics(
        error_rate=0.01,
        cost_increase_pct=3.0,
        latency_p95_ms=3800,
        user_satisfaction=0.88
    )
    canary2.record_metrics(final_metrics)

    print(f"""
最终健康指标:
  错误率: {final_metrics.error_rate:.1%} ✓
  成本增加: {final_metrics.cost_increase_pct:.1f}% ✓
  P95 延迟: {final_metrics.latency_p95_ms:.0f}ms ✓
  用户满意度: {final_metrics.user_satisfaction:.2f} ✓

✅ 发布完成！新版本已推广到所有用户。
    """)

    # 展示反例
    bad_example()


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    """主入口"""
    simulate_canary_deployment()


if __name__ == "__main__":
    main()
