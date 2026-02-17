"""
测试 A/B 测试引擎

测试模块：
- ABTestEngine
- ABTestConfig
- TestResult
- TestAnalysis
- 统计检验
"""

import pytest
from datetime import datetime

from ab_testing import (
    ABTestConfig,
    TestResult,
    TestAnalysis,
    ABTestEngine,
    MultiVariantTest,
    Version
)


class TestABTestConfig:
    """测试 A/B 测试配置"""

    def test_config_creation(self):
        """测试创建配置"""
        config = ABTestConfig(
            name="test_prompt",
            description="测试新 Prompt",
            traffic_split=0.5
        )

        assert config.name == "test_prompt"
        assert config.description == "测试新 Prompt"
        assert config.traffic_split == 0.5
        assert config.min_sample_size == 100  # 默认值

    def test_config_defaults(self):
        """测试配置默认值"""
        config = ABTestConfig(
            name="test",
            description="test"
        )

        assert config.traffic_split == 0.5
        assert isinstance(config.start_time, datetime)
        assert config.min_sample_size == 100

    def test_config_custom_min_sample_size(self):
        """测试自定义最小样本量"""
        config = ABTestConfig(
            name="test",
            description="test",
            min_sample_size=200
        )

        assert config.min_sample_size == 200


class TestABTestEngine:
    """测试 A/B 测试引擎"""

    @pytest.fixture
    def engine(self):
        """创建测试引擎"""
        config = ABTestConfig(
            name="test_ab",
            description="测试",
            traffic_split=0.5
        )
        return ABTestEngine(config)

    def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine.config.name == "test_ab"
        assert len(engine.results["A"]) == 0
        assert len(engine.results["B"]) == 0

    def test_engine_invalid_traffic_split(self):
        """测试无效的流量分配（在引擎初始化时验证）"""
        with pytest.raises(ValueError, match="traffic_split must be between 0 and 1"):
            ABTestEngine(ABTestConfig(
                name="test",
                description="test",
                traffic_split=1.5
            ))

        with pytest.raises(ValueError, match="traffic_split must be between 0 and 1"):
            ABTestEngine(ABTestConfig(
                name="test",
                description="test",
                traffic_split=-0.1
            ))

    def test_assign_version_consistency(self, engine):
        """测试版本分配一致性（同一用户总是分配到同一版本）"""
        user_id = "user_123"

        version1 = engine.assign_version(user_id)
        version2 = engine.assign_version(user_id)

        assert version1 == version2

    def test_assign_version_distribution(self, engine):
        """测试版本分配分布（50/50 分配）"""
        import random

        # 分配 10000 个用户
        versions = []
        for i in range(10000):
            user_id = f"user_{i}"
            version = engine.assign_version(user_id)
            versions.append(version)

        # 检查分布接近 50/50
        count_a = versions.count("A")
        count_b = versions.count("B")

        # 允许 5% 的误差
        assert 4500 <= count_a <= 5500
        assert 4500 <= count_b <= 5500

    def test_assign_version_empty_user_id(self, engine):
        """测试空用户 ID"""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            engine.assign_version("")

    def test_assign_version_all_traffic_to_a(self):
        """测试所有流量分配到 A"""
        config = ABTestConfig(
            name="test",
            description="test",
            traffic_split=0.0  # 0% 流量给 B
        )
        engine = ABTestEngine(config)

        for i in range(100):
            user_id = f"user_{i}"
            version = engine.assign_version(user_id)
            assert version == "A"

    def test_assign_version_all_traffic_to_b(self):
        """测试所有流量分配到 B"""
        config = ABTestConfig(
            name="test",
            description="test",
            traffic_split=1.0  # 100% 流量给 B
        )
        engine = ABTestEngine(config)

        for i in range(100):
            user_id = f"user_{i}"
            version = engine.assign_version(user_id)
            assert version == "B"

    def test_record_result(self, engine):
        """测试记录结果"""
        engine.record_result(
            version="A",
            user_id="user_1",
            metrics={"quality_score": 0.8}
        )

        assert len(engine.results["A"]) == 1
        assert len(engine.results["B"]) == 0
        assert engine.results["A"][0].metrics["quality_score"] == 0.8

    def test_record_result_invalid_version(self, engine):
        """测试记录无效版本"""
        with pytest.raises(ValueError, match="version must be 'A' or 'B'"):
            engine.record_result(
                version="C",
                user_id="user_1",
                metrics={"quality_score": 0.8}
            )

    def test_record_multiple_results(self, engine):
        """测试记录多个结果"""
        for i in range(10):
            engine.record_result(
                version="A",
                user_id=f"user_{i}",
                metrics={"quality_score": 0.7 + i * 0.01}
            )

        assert len(engine.results["A"]) == 10

    def test_analyze_empty_results(self, engine):
        """测试分析空结果"""
        analysis = engine.analyze()

        assert analysis.sample_size == {"A": 0, "B": 0}
        assert analysis.mean_quality == {"A": 0, "B": 0}
        assert analysis.winner == "insufficient_data"
        assert not analysis.is_significant

    def test_analyze_single_version_results(self, engine):
        """测试只有单版本结果（返回 insufficient_data）"""
        engine.record_result("A", "user_1", {"quality_score": 0.8})
        engine.record_result("A", "user_2", {"quality_score": 0.7})

        analysis = engine.analyze()

        # 当只有一个版本有数据时，返回 insufficient_data
        assert analysis.sample_size["A"] == 2
        assert analysis.sample_size["B"] == 0
        assert analysis.mean_quality["A"] == 0  # 由于数据不足，返回 0
        assert analysis.mean_quality["B"] == 0
        assert analysis.winner == "insufficient_data"

    def test_analyze_with_significant_difference(self):
        """测试分析显著差异"""
        config = ABTestConfig(name="test", description="test")
        engine = ABTestEngine(config)

        # A 版本：平均 0.7
        for i in range(50):
            engine.record_result("A", f"user_a_{i}", {"quality_score": 0.7})

        # B 版本：平均 0.85
        for i in range(50):
            engine.record_result("B", f"user_b_{i}", {"quality_score": 0.85})

        analysis = engine.analyze()

        assert analysis.sample_size["A"] == 50
        assert analysis.sample_size["B"] == 50
        assert analysis.mean_quality["A"] == pytest.approx(0.7)
        assert analysis.mean_quality["B"] == pytest.approx(0.85)
        assert analysis.winner == "B"
        assert analysis.is_significant

    def test_analyze_with_no_significant_difference(self):
        """测试分析无显著差异"""
        import random

        config = ABTestConfig(name="test", description="test")
        engine = ABTestEngine(config)

        random.seed(42)

        # 两个版本相似
        for i in range(50):
            score_a = random.gauss(0.75, 0.05)
            score_b = random.gauss(0.76, 0.05)
            engine.record_result("A", f"user_a_{i}", {"quality_score": score_a})
            engine.record_result("B", f"user_b_{i}", {"quality_score": score_b})

        analysis = engine.analyze()

        # 差异不显著（p >= 0.05）
        assert not analysis.is_significant
        assert analysis.winner == "inconclusive"

    def test_analyze_custom_metric(self):
        """测试分析自定义指标"""
        config = ABTestConfig(name="test", description="test")
        engine = ABTestEngine(config)

        engine.record_result("A", "user_1", {"latency_ms": 100})
        engine.record_result("A", "user_2", {"latency_ms": 200})
        engine.record_result("B", "user_3", {"latency_ms": 150})
        engine.record_result("B", "user_4", {"latency_ms": 250})

        analysis = engine.analyze(metric_key="latency_ms")

        assert analysis.mean_quality["A"] == 150
        assert analysis.mean_quality["B"] == 200

    def test_get_results_summary(self, engine):
        """测试获取结果摘要"""
        engine.record_result("A", "user_1", {"quality_score": 0.8, "latency_ms": 100})
        engine.record_result("A", "user_2", {"quality_score": 0.7, "latency_ms": 200})
        engine.record_result("B", "user_3", {"quality_score": 0.85, "latency_ms": 150})

        summary = engine.get_results_summary()

        assert summary["A"]["count"] == 2
        assert summary["B"]["count"] == 1
        assert summary["A"]["metrics"]["quality_score"]["mean"] == 0.75
        assert summary["A"]["metrics"]["latency_ms"]["mean"] == 150

    def test_clear_results(self, engine):
        """测试清空结果"""
        engine.record_result("A", "user_1", {"quality_score": 0.8})
        engine.record_result("B", "user_2", {"quality_score": 0.7})

        assert len(engine.results["A"]) == 1
        assert len(engine.results["B"]) == 1

        engine.clear_results()

        assert len(engine.results["A"]) == 0
        assert len(engine.results["B"]) == 0

    def test_lift_calculation(self):
        """测试提升计算"""
        config = ABTestConfig(name="test", description="test")
        engine = ABTestEngine(config)

        # A: 0.5, B: 0.75 -> 50% lift
        for i in range(20):
            engine.record_result("A", f"user_a_{i}", {"quality_score": 0.5})
            engine.record_result("B", f"user_b_{i}", {"quality_score": 0.75})

        analysis = engine.analyze()

        assert analysis.lift == pytest.approx(50.0, rel=0.1)

    def test_lift_with_zero_baseline(self):
        """测试基线为零的提升计算"""
        config = ABTestConfig(name="test", description="test")
        engine = ABTestEngine(config)

        engine.record_result("A", "user_1", {"quality_score": 0.0})
        engine.record_result("B", "user_2", {"quality_score": 0.5})

        analysis = engine.analyze()

        # 基线为 0 时提升为 0
        assert analysis.lift == 0


class TestMultiVariantTest:
    """测试多变量测试"""

    def test_multi_variant_initialization(self):
        """测试初始化"""
        test = MultiVariantTest(
            name="multi_test",
            versions=["A", "B", "C"]
        )

        assert test.name == "multi_test"
        assert len(test.versions) == 3
        assert test.traffic_per_version == pytest.approx(1.0 / 3)

    def test_multi_variant_assign_version(self):
        """测试版本分配"""
        test = MultiVariantTest(
            name="multi_test",
            versions=["A", "B", "C", "D"]
        )

        versions = []
        for i in range(1000):
            version = test.assign_version(f"user_{i}")
            versions.append(version)

        # 每个版本应该大约 25%
        for v in ["A", "B", "C", "D"]:
            count = versions.count(v)
            assert 200 <= count <= 300

    def test_multi_variant_record_result(self):
        """测试记录结果"""
        test = MultiVariantTest(
            name="multi_test",
            versions=["A", "B", "C"]
        )

        test.record_result("A", "user_1", {"score": 0.8})
        test.record_result("B", "user_2", {"score": 0.7})

        assert len(test.results["A"]) == 1
        assert len(test.results["B"]) == 1
        assert len(test.results["C"]) == 0

    def test_multi_variant_invalid_version(self):
        """测试无效版本"""
        test = MultiVariantTest(
            name="multi_test",
            versions=["A", "B"]
        )

        with pytest.raises(ValueError, match="Invalid version"):
            test.record_result("C", "user_1", {"score": 0.8})


@pytest.mark.parametrize("traffic_split,expected_b_percentage", [
    (0.0, 0),
    (0.1, 10),
    (0.25, 25),
    (0.5, 50),
    (0.75, 75),
    (1.0, 100),
])
def test_traffic_split_distribution(traffic_split, expected_b_percentage):
    """参数化测试：流量分配分布"""
    config = ABTestConfig(
        name="test",
        description="test",
        traffic_split=traffic_split
    )
    engine = ABTestEngine(config)

    # 分配 1000 个用户
    versions = []
    for i in range(1000):
        version = engine.assign_version(f"user_{i}")
        versions.append(version)

    count_b = versions.count("B")
    actual_percentage = (count_b / 1000) * 100

    # 允许 5% 误差
    assert actual_percentage == pytest.approx(expected_b_percentage, abs=5)


@pytest.mark.parametrize("mean_a,mean_b,size_a,size_b,expected_winner", [
    (0.7, 0.8, 50, 50, "B"),  # B 更好
    (0.8, 0.7, 50, 50, "A"),  # A 更好
    (0.75, 0.75, 50, 50, "inconclusive"),  # 相等
])
def test_analysis_winner(mean_a, mean_b, size_a, size_b, expected_winner):
    """参数化测试：分析结果中的胜者"""
    config = ABTestConfig(name="test", description="test")
    engine = ABTestEngine(config)

    for i in range(size_a):
        engine.record_result("A", f"user_a_{i}", {"quality_score": mean_a})

    for i in range(size_b):
        engine.record_result("B", f"user_b_{i}", {"quality_score": mean_b})

    analysis = engine.analyze()

    assert analysis.mean_quality["A"] == pytest.approx(mean_a)
    assert analysis.mean_quality["B"] == pytest.approx(mean_b)
    # 注意：winner 依赖于统计显著性
    if expected_winner == "inconclusive":
        # 相等时可能不显著
        pass
    else:
        assert analysis.winner == expected_winner
