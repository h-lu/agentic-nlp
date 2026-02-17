"""
示例 4: A/B 测试引擎

展示了如何实现 A/B 测试来对比不同版本的效果。
核心概念：
- ABTestEngine: 分配流量、收集结果、统计分析
- 使用 t 检验判断差异显著性
"""

from typing import Dict, Literal, List, Optional
from dataclasses import dataclass, field
import hashlib
from datetime import datetime


Version = Literal["A", "B"]


@dataclass
class ABTestConfig:
    """A/B 测试配置"""
    name: str
    description: str
    traffic_split: float = 0.5  # B 版本的流量比例（0.5 = 50%）
    start_time: datetime = field(default_factory=datetime.now)
    min_sample_size: int = 100  # 最小样本量要求


@dataclass
class TestResult:
    """单次测试结果"""
    version: Version
    user_id: str
    metrics: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestAnalysis:
    """A/B 测试分析结果"""
    test_name: str
    sample_size: Dict[str, int]
    mean_quality: Dict[str, float]
    lift: float
    p_value: float
    is_significant: bool
    winner: str
    confidence_interval: Optional[Dict[str, List[float]]] = None


class ABTestEngine:
    """A/B 测试引擎

    负责流量分配、结果收集和统计分析
    """

    def __init__(self, config: ABTestConfig):
        """初始化 A/B 测试引擎

        Args:
            config: A/B 测试配置
        """
        if not 0 <= config.traffic_split <= 1:
            raise ValueError("traffic_split must be between 0 and 1")

        self.config = config
        self.results: Dict[Version, List[TestResult]] = {"A": [], "B": []}

    def assign_version(self, user_id: str) -> Version:
        """为用户分配版本

        使用哈希确保同一用户总是分配到同一版本

        Args:
            user_id: 用户 ID

        Returns:
            分配的版本（"A" 或 "B"）
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")

        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return "B" if (hash_val % 100) < (self.config.traffic_split * 100) else "A"

    def record_result(
        self,
        version: Version,
        user_id: str,
        metrics: Dict[str, float]
    ) -> None:
        """记录结果

        Args:
            version: 版本（"A" 或 "B"）
            user_id: 用户 ID
            metrics: 指标字典，如 {"quality_score": 0.85, "latency_ms": 150}
        """
        if version not in ["A", "B"]:
            raise ValueError("version must be 'A' or 'B'")

        result = TestResult(
            version=version,
            user_id=user_id,
            metrics=metrics
        )

        self.results[version].append(result)

    def analyze(self, metric_key: str = "quality_score") -> TestAnalysis:
        """分析 A/B 测试结果

        Args:
            metric_key: 要分析的指标键名

        Returns:
            TestAnalysis: 分析结果
        """
        from scipy import stats
        import numpy as np

        # 提取指标
        a_values = [r.metrics.get(metric_key, 0) for r in self.results["A"]]
        b_values = [r.metrics.get(metric_key, 0) for r in self.results["B"]]

        # 检查样本量
        if len(a_values) == 0 or len(b_values) == 0:
            return TestAnalysis(
                test_name=self.config.name,
                sample_size={"A": len(a_values), "B": len(b_values)},
                mean_quality={"A": 0, "B": 0},
                lift=0,
                p_value=1.0,
                is_significant=False,
                winner="insufficient_data"
            )

        # 计算均值
        a_mean = np.mean(a_values) if a_values else 0
        b_mean = np.mean(b_values) if b_values else 0

        # t 检验（使用 Welch's t-test，不假设方差相等）
        t_stat, p_value = stats.ttest_ind(a_values, b_values, equal_var=False)

        # 判断是否显著
        is_significant = p_value < 0.05
        winner = "B" if b_mean > a_mean else "A"

        # 计算提升
        lift = ((b_mean - a_mean) / a_mean * 100) if a_mean > 0 else 0

        # 计算置信区间
        confidence_interval = None
        if len(a_values) > 1 and len(b_values) > 1:
            # 95% 置信区间
            se_diff = np.sqrt(
                np.var(a_values, ddof=1) / len(a_values) +
                np.var(b_values, ddof=1) / len(b_values)
            )
            margin = 1.96 * se_diff
            diff = b_mean - a_mean
            confidence_interval = {
                "lower": [diff - margin, diff + margin],
                "upper": [a_mean - margin, a_mean + margin]
            }

        return TestAnalysis(
            test_name=self.config.name,
            sample_size={"A": len(a_values), "B": len(b_values)},
            mean_quality={"A": a_mean, "B": b_mean},
            lift=lift,
            p_value=p_value,
            is_significant=is_significant,
            winner=winner if is_significant else "inconclusive",
            confidence_interval=confidence_interval
        )

    def get_results_summary(self) -> Dict[str, Dict[str, any]]:
        """获取结果摘要"""
        summary = {}

        for version in ["A", "B"]:
            results = self.results[version]
            if results:
                all_metrics = {}
                for r in results:
                    for k, v in r.metrics.items():
                        if k not in all_metrics:
                            all_metrics[k] = []
                        all_metrics[k].append(v)

                summary[version] = {
                    "count": len(results),
                    "metrics": {
                        k: {
                            "mean": sum(v) / len(v),
                            "min": min(v),
                            "max": max(v)
                        }
                        for k, v in all_metrics.items()
                    }
                }
            else:
                summary[version] = {"count": 0, "metrics": {}}

        return summary

    def clear_results(self) -> None:
        """清空所有结果"""
        self.results = {"A": [], "B": []}


class MultiVariantTest:
    """多变量测试（A/B/C/D...）"""

    def __init__(self, name: str, versions: List[str]):
        """初始化多变量测试

        Args:
            name: 测试名称
            versions: 版本列表，如 ["A", "B", "C"]
        """
        self.name = name
        self.versions = versions
        self.results: Dict[str, List[TestResult]] = {v: [] for v in versions}
        self.traffic_per_version = 1.0 / len(versions)

    def assign_version(self, user_id: str) -> str:
        """为用户分配版本"""
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        idx = hash_val % len(self.versions)
        return self.versions[idx]

    def record_result(self, version: str, user_id: str, metrics: Dict[str, float]) -> None:
        """记录结果"""
        if version not in self.versions:
            raise ValueError(f"Invalid version: {version}")

        result = TestResult(
            version=version,
            user_id=user_id,
            metrics=metrics
        )
        self.results[version].append(result)


if __name__ == "__main__":
    # 使用示例
    test_config = ABTestConfig(
        name="prompt_v2_vs_v1",
        description="测试优化后的 Prompt 是否提升质量",
        traffic_split=0.5
    )

    ab_engine = ABTestEngine(test_config)

    # 模拟数据
    import random

    random.seed(42)
    for i in range(100):
        user_id = f"user_{i}"
        version = ab_engine.assign_version(user_id)

        # A 版本准确率约 0.75，B 版本约 0.82
        if version == "A":
            quality_score = random.gauss(0.75, 0.1)
            latency = random.gauss(200, 50)
        else:
            quality_score = random.gauss(0.82, 0.08)
            latency = random.gauss(180, 40)

        quality_score = max(0, min(1, quality_score))  # 限制在 [0, 1]
        latency = max(0, latency)

        ab_engine.record_result(
            version,
            user_id,
            {
                "quality_score": quality_score,
                "latency_ms": latency
            }
        )

    # 分析
    analysis = ab_engine.analyze(metric_key="quality_score")
    print(f"测试名称: {analysis.test_name}")
    print(f"样本量: A={analysis.sample_size['A']}, B={analysis.sample_size['B']}")
    print(f"平均质量: A={analysis.mean_quality['A']:.3f}, B={analysis.mean_quality['B']:.3f}")
    print(f"提升: {analysis.lift:.1f}%")
    print(f"P 值: {analysis.p_value:.4f}")
    print(f"是否显著: {analysis.is_significant}")
    print(f"胜者: {analysis.winner}")

    # 延迟分析
    latency_analysis = ab_engine.analyze(metric_key="latency_ms")
    print(f"\n延迟分析:")
    print(f"平均延迟: A={latency_analysis.mean_quality['A']:.0f}ms, B={latency_analysis.mean_quality['B']:.0f}ms")
    print(f"胜者: {latency_analysis.winner}")
