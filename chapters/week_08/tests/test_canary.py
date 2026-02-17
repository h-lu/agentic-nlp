"""
测试灰度发布（Canary Deployment）

测试模块：
- CanaryDeployment
- CanaryStage
- HealthMetrics
- RollbackConfig
- 流量分配和回滚逻辑
"""

import pytest
from datetime import datetime, timedelta

from canary_deployment import (
    CanaryStage,
    HealthMetrics,
    RollbackConfig,
    CanaryDeployment,
    DeploymentStatus
)


class TestCanaryStage:
    """测试灰度阶段配置"""

    def test_stage_creation(self):
        """测试创建阶段"""
        stage = CanaryStage(
            day=1,
            traffic_percentage=5,
            description="初始发布"
        )

        assert stage.day == 1
        assert stage.traffic_percentage == 5
        assert stage.description == "初始发布"

    def test_stage_to_dict(self):
        """测试转换为字典"""
        stage = CanaryStage(
            day=3,
            traffic_percentage=25,
            description="扩大测试"
        )

        result = stage.to_dict()

        assert result["day"] == 3
        assert result["traffic_percentage"] == 25
        assert result["description"] == "扩大测试"


class TestHealthMetrics:
    """测试健康指标"""

    def test_metrics_creation(self):
        """测试创建指标"""
        metrics = HealthMetrics(
            error_rate=0.01,
            cost_increase_pct=5.0,
            latency_p95_ms=2000,
            user_satisfaction=0.85
        )

        assert metrics.error_rate == 0.01
        assert metrics.cost_increase_pct == 5.0
        assert metrics.latency_p95_ms == 2000
        assert metrics.user_satisfaction == 0.85

    def test_metrics_defaults(self):
        """测试默认值"""
        metrics = HealthMetrics()

        assert metrics.error_rate == 0.0
        assert metrics.cost_increase_pct == 0.0
        assert metrics.latency_p95_ms == 0.0
        assert metrics.user_satisfaction == 0.0

    def test_metrics_timestamp(self):
        """测试时间戳自动生成"""
        before = datetime.now()
        metrics = HealthMetrics()
        after = datetime.now()

        assert before <= metrics.timestamp <= after

    def test_metrics_to_dict(self):
        """测试转换为字典"""
        metrics = HealthMetrics(
            error_rate=0.02,
            cost_increase_pct=10.0,
            latency_p95_ms=3500,
            user_satisfaction=0.90
        )

        result = metrics.to_dict()

        assert result["error_rate"] == 0.02
        assert result["cost_increase_pct"] == 10.0
        assert result["latency_p95_ms"] == 3500
        assert result["user_satisfaction"] == 0.90
        assert "timestamp" in result


class TestRollbackConfig:
    """测试回滚配置"""

    def test_config_defaults(self):
        """测试默认配置"""
        config = RollbackConfig()

        assert config.error_rate_threshold == 0.05
        assert config.cost_threshold_pct == 20.0
        assert config.latency_threshold_ms == 10000
        assert config.satisfaction_threshold == 0.7

    def test_config_custom(self):
        """测试自定义配置"""
        config = RollbackConfig(
            error_rate_threshold=0.03,
            cost_threshold_pct=15.0,
            latency_threshold_ms=5000,
            satisfaction_threshold=0.8
        )

        assert config.error_rate_threshold == 0.03
        assert config.cost_threshold_pct == 15.0
        assert config.latency_threshold_ms == 5000
        assert config.satisfaction_threshold == 0.8

    def test_should_rollback_error_rate(self):
        """测试错误率触发回滚"""
        config = RollbackConfig(error_rate_threshold=0.05)

        # 未触发（其他指标设为安全值）
        metrics_ok = HealthMetrics(error_rate=0.01, user_satisfaction=0.8)
        assert not config.should_rollback(metrics_ok)

        # 触发
        metrics_bad = HealthMetrics(error_rate=0.08, user_satisfaction=0.8)
        assert config.should_rollback(metrics_bad)

    def test_should_rollback_cost_increase(self):
        """测试成本增加触发回滚"""
        config = RollbackConfig(cost_threshold_pct=20.0)

        metrics_ok = HealthMetrics(cost_increase_pct=10.0, user_satisfaction=0.8)
        assert not config.should_rollback(metrics_ok)

        metrics_bad = HealthMetrics(cost_increase_pct=25.0, user_satisfaction=0.8)
        assert config.should_rollback(metrics_bad)

    def test_should_rollback_latency(self):
        """测试延迟触发回滚"""
        config = RollbackConfig(latency_threshold_ms=10000)

        metrics_ok = HealthMetrics(latency_p95_ms=5000, user_satisfaction=0.8)
        assert not config.should_rollback(metrics_ok)

        metrics_bad = HealthMetrics(latency_p95_ms=15000, user_satisfaction=0.8)
        assert config.should_rollback(metrics_bad)

    def test_should_rollback_satisfaction(self):
        """测试满意度触发回滚"""
        config = RollbackConfig(satisfaction_threshold=0.7)

        metrics_ok = HealthMetrics(user_satisfaction=0.8)
        assert not config.should_rollback(metrics_ok)

        metrics_bad = HealthMetrics(user_satisfaction=0.5)
        assert config.should_rollback(metrics_bad)


class TestCanaryDeployment:
    """测试灰度发布控制器"""

    @pytest.fixture
    def default_stages(self):
        """默认阶段配置"""
        return [
            CanaryStage(day=1, traffic_percentage=5, description="初始发布"),
            CanaryStage(day=3, traffic_percentage=25, description="扩大测试"),
            CanaryStage(day=7, traffic_percentage=50, description="半量发布"),
            CanaryStage(day=14, traffic_percentage=100, description="全量发布")
        ]

    @pytest.fixture
    def rollback_config(self):
        """回滚配置"""
        return RollbackConfig(
            error_rate_threshold=0.05,
            cost_threshold_pct=20.0,
            latency_threshold_ms=10000,
            satisfaction_threshold=0.7
        )

    @pytest.fixture
    def canary(self, default_stages, rollback_config):
        """创建测试用的灰度发布实例"""
        return CanaryDeployment(default_stages, rollback_config)

    def test_initialization(self, canary, default_stages):
        """测试初始化"""
        assert len(canary.stages) == 4
        assert canary.status == DeploymentStatus.PENDING
        assert not canary.rollback_triggered
        assert canary.current_stage_idx == 0

    def test_stages_sorted(self, rollback_config):
        """测试阶段按天数排序"""
        stages = [
            CanaryStage(day=7, traffic_percentage=50),
            CanaryStage(day=1, traffic_percentage=5),
            CanaryStage(day=14, traffic_percentage=100),
            CanaryStage(day=3, traffic_percentage=25)
        ]

        canary = CanaryDeployment(stages, rollback_config)

        assert canary.stages[0].day == 1
        assert canary.stages[1].day == 3
        assert canary.stages[2].day == 7
        assert canary.stages[3].day == 14

    def test_get_current_stage_before_start(self, canary):
        """测试开始前的当前阶段"""
        canary.start_date = datetime.now()

        stage = canary.get_current_stage()

        # 第 0 天应该是第一个阶段（day=1 还没到）
        assert stage.day == 1

    def test_get_current_stage_day_1(self, canary):
        """测试第 1 天的当前阶段"""
        canary.start_date = datetime.now() - timedelta(days=1)

        stage = canary.get_current_stage()

        assert stage.day == 1
        assert stage.traffic_percentage == 5

    def test_get_current_stage_day_5(self, canary):
        """测试第 5 天的当前阶段（应该在 day 3 阶段）"""
        canary.start_date = datetime.now() - timedelta(days=5)

        stage = canary.get_current_stage()

        assert stage.day == 3
        assert stage.traffic_percentage == 25

    def test_get_current_stage_day_14(self, canary):
        """测试第 14 天的当前阶段"""
        canary.start_date = datetime.now() - timedelta(days=14)

        stage = canary.get_current_stage()

        assert stage.day == 14
        assert stage.traffic_percentage == 100

    def test_get_traffic_percentage_before_start(self, canary):
        """测试开始前的流量百分比"""
        canary.start_date = datetime.now()

        traffic = canary.get_traffic_percentage()

        assert traffic == 5  # 第一个阶段

    def test_get_traffic_percentage_day_1(self, canary):
        """测试第 1 天的流量百分比"""
        canary.start_date = datetime.now() - timedelta(days=1)

        traffic = canary.get_traffic_percentage()

        assert traffic == 5

    def test_get_traffic_percentage_day_5(self, canary):
        """测试第 5 天的流量百分比"""
        canary.start_date = datetime.now() - timedelta(days=5)

        traffic = canary.get_traffic_percentage()

        assert traffic == 25

    def test_get_traffic_percentage_after_rollback(self, canary):
        """测试回滚后的流量百分比"""
        canary.rollback_triggered = True

        traffic = canary.get_traffic_percentage()

        assert traffic == 0

    def test_should_use_new_version_distribution(self, canary):
        """测试新版本使用的分布"""
        canary.start_date = datetime.now() - timedelta(days=5)  # 25% 流量

        # 测试 1000 个用户
        new_version_count = sum(
            1 for i in range(1000)
            if canary.should_use_new_version(f"user_{i}")
        )

        # 应该接近 25%
        assert 200 <= new_version_count <= 300

    def test_should_use_new_version_consistency(self, canary):
        """测试同一用户总是得到相同结果"""
        user_id = "test_user_123"

        result1 = canary.should_use_new_version(user_id)
        result2 = canary.should_use_new_version(user_id)

        assert result1 == result2

    def test_should_use_new_version_at_0_percent(self, rollback_config):
        """测试 0% 流量时都不使用新版本"""
        stages = [CanaryStage(day=0, traffic_percentage=0)]
        canary = CanaryDeployment(stages, rollback_config)

        for i in range(100):
            assert not canary.should_use_new_version(f"user_{i}")

    def test_should_use_new_version_at_100_percent(self, rollback_config):
        """测试 100% 流量时都使用新版本"""
        stages = [CanaryStage(day=0, traffic_percentage=100)]
        canary = CanaryDeployment(stages, rollback_config)

        for i in range(100):
            assert canary.should_use_new_version(f"user_{i}")

    def test_record_metrics(self, canary):
        """测试记录指标"""
        metrics = HealthMetrics(
            error_rate=0.01,
            cost_increase_pct=5.0,
            latency_p95_ms=2000,
            user_satisfaction=0.85
        )

        canary.record_metrics(metrics)

        assert len(canary.metrics_history) == 1
        assert canary.metrics_history[0].error_rate == 0.01

    def test_record_metrics_triggers_rollback(self, canary):
        """测试记录指标触发回滚"""
        bad_metrics = HealthMetrics(
            error_rate=0.08,  # 超过阈值 0.05
            cost_increase_pct=5.0,
            latency_p95_ms=2000,
            user_satisfaction=0.85
        )

        canary.record_metrics(bad_metrics)

        assert canary.rollback_triggered
        assert canary.status == DeploymentStatus.ROLLED_BACK
        assert "错误率过高" in canary.rollback_reason

    def test_record_multiple_metrics(self, canary):
        """测试记录多个指标"""
        for i in range(5):
            metrics = HealthMetrics(error_rate=0.01 * i)
            canary.record_metrics(metrics)

        assert len(canary.metrics_history) == 5

    def test_get_status(self, canary):
        """测试获取状态"""
        canary.start_date = datetime.now() - timedelta(days=5)

        status = canary.get_status()

        assert status["status"] == "pending"
        assert status["days_elapsed"] == 5
        assert status["traffic_percentage"] == 25
        assert status["total_stages"] == 4
        assert "current_stage" in status

    def test_get_status_after_rollback(self, canary):
        """测试回滚后的状态"""
        canary.rollback_triggered = True
        canary.status = DeploymentStatus.ROLLED_BACK
        canary.rollback_reason = "测试回滚"

        status = canary.get_status()

        assert status["status"] == "rolled_back"
        assert status["rollback_triggered"] is True
        assert status["traffic_percentage"] == 0
        assert status["rollback_reason"] == "测试回滚"

    def test_complete(self, canary):
        """测试标记完成"""
        canary.complete()

        assert canary.status == DeploymentStatus.COMPLETED

    def test_complete_after_rollback(self, canary):
        """测试回滚后不能标记完成"""
        canary.rollback_triggered = True
        canary.status = DeploymentStatus.ROLLED_BACK

        canary.complete()

        # 状态应该保持 ROLLED_BACK
        assert canary.status == DeploymentStatus.ROLLED_BACK

    def test_get_progress_summary(self, canary):
        """测试获取进度摘要"""
        summary = canary.get_progress_summary()

        assert "进行中" in summary or "pending" in summary.lower()

    def test_get_progress_summary_completed(self, canary):
        """测试完成后的进度摘要"""
        canary.status = DeploymentStatus.COMPLETED

        summary = canary.get_progress_summary()

        assert "完成" in summary or "completed" in summary.lower()

    def test_get_progress_summary_rolled_back(self, canary):
        """测试回滚后的进度摘要"""
        canary.rollback_triggered = True
        canary.rollback_reason = "测试原因"

        summary = canary.get_progress_summary()

        assert "回滚" in summary or "测试原因" in summary

    def test_trigger_rollback_multiple_reasons(self, rollback_config):
        """测试多个原因触发回滚"""
        stages = [CanaryStage(day=1, traffic_percentage=5)]
        canary = CanaryDeployment(stages, rollback_config)

        metrics = HealthMetrics(
            error_rate=0.08,  # 触发
            cost_increase_pct=25.0,  # 触发
            latency_p95_ms=15000,  # 触发
            user_satisfaction=0.5  # 触发
        )

        canary.record_metrics(metrics)

        assert canary.rollback_triggered
        # 所有原因都应该被记录
        assert "错误率过高" in canary.rollback_reason
        assert "成本增加过多" in canary.rollback_reason
        assert "延迟过高" in canary.rollback_reason
        assert "用户满意度过低" in canary.rollback_reason


@pytest.mark.parametrize("day,expected_traffic,expected_stage_day", [
    (0, 5, 1),
    (1, 5, 1),
    (2, 5, 1),
    (3, 25, 3),
    (5, 25, 3),
    (7, 50, 7),
    (14, 100, 14),
    (20, 100, 14),
])
def test_traffic_percentage_by_day(day, expected_traffic, expected_stage_day):
    """参数化测试：按天获取流量百分比"""
    stages = [
        CanaryStage(day=1, traffic_percentage=5),
        CanaryStage(day=3, traffic_percentage=25),
        CanaryStage(day=7, traffic_percentage=50),
        CanaryStage(day=14, traffic_percentage=100)
    ]
    canary = CanaryDeployment(stages)
    canary.start_date = datetime.now() - timedelta(days=day)

    traffic = canary.get_traffic_percentage()
    stage = canary.get_current_stage()

    assert traffic == expected_traffic
    assert stage.day == expected_stage_day


@pytest.mark.parametrize("error_rate,should_rollback", [
    (0.0, False),
    (0.01, False),
    (0.04, False),
    (0.05, False),  # 等于阈值不触发
    (0.06, True),
    (0.10, True),
])
def test_error_rate_rollback(error_rate, should_rollback):
    """参数化测试：错误率回滚阈值"""
    config = RollbackConfig(error_rate_threshold=0.05)
    metrics = HealthMetrics(error_rate=error_rate, user_satisfaction=0.8)  # 设为安全值

    result = config.should_rollback(metrics)

    assert result == should_rollback


@pytest.mark.parametrize("traffic_pct,lower_bound,upper_bound", [
    (0, 0, 0),
    (5, 30, 70),  # 5% of 1000 users
    (25, 200, 300),
    (50, 450, 550),
    (100, 1000, 1000),
])
def test_should_use_new_version_distribution_by_percentage(traffic_pct, lower_bound, upper_bound):
    """参数化测试：按流量百分比测试新版本使用分布"""
    stages = [CanaryStage(day=0, traffic_percentage=traffic_pct)]
    canary = CanaryDeployment(stages)

    new_version_count = sum(
        1 for i in range(1000)
        if canary.should_use_new_version(f"user_{i}")
    )

    assert lower_bound <= new_version_count <= upper_bound
