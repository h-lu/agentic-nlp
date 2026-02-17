"""
示例 3: 商业价值计算

展示了如何计算和展示系统的商业价值。
核心概念：
- BusinessValueCalculator: 计算成本节省和效率提升
- 将技术指标转化为商业语言
"""

from typing import Dict
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ValueReport:
    """商业价值报告"""
    period_days: int
    total_requests: int
    system_cost_usd: float
    manual_cost_usd: float
    savings_usd: float
    savings_percentage: float

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "period_days": self.period_days,
            "total_requests": self.total_requests,
            "system_cost_usd": self.system_cost_usd,
            "manual_cost_usd": self.manual_cost_usd,
            "savings_usd": self.savings_usd,
            "savings_percentage": self.savings_percentage
        }


class BusinessValueCalculator:
    """商业价值计算器

    用于计算自动化系统相比人工操作的成本节省
    """

    def __init__(
        self,
        cost_per_request: float,
        manual_cost_per_request: float,
        manual_time_per_request_minutes: float = 30.0
    ):
        """初始化计算器

        Args:
            cost_per_request: 系统每次请求成本（美元）
            manual_cost_per_request: 人工每次请求成本（美元）
            manual_time_per_request_minutes: 人工每次请求耗时（分钟）
        """
        if cost_per_request < 0:
            raise ValueError("cost_per_request must be non-negative")
        if manual_cost_per_request < 0:
            raise ValueError("manual_cost_per_request must be non-negative")
        if manual_time_per_request_minutes < 0:
            raise ValueError("manual_time_per_request_minutes must be non-negative")

        self.cost_per_request = cost_per_request
        self.manual_cost_per_request = manual_cost_per_request
        self.manual_time_per_request_minutes = manual_time_per_request_minutes

    def calculate_savings(
        self,
        daily_requests: int,
        days: int = 30
    ) -> ValueReport:
        """计算节省的成本

        Args:
            daily_requests: 每日请求数
            days: 计算周期（天）

        Returns:
            ValueReport: 包含详细节省信息的报告
        """
        if daily_requests < 0:
            raise ValueError("daily_requests must be non-negative")
        if days <= 0:
            raise ValueError("days must be positive")

        total_requests = daily_requests * days

        # 系统成本
        system_cost = total_requests * self.cost_per_request

        # 人力成本
        manual_cost = total_requests * self.manual_cost_per_request

        # 节省
        savings = manual_cost - system_cost
        savings_percentage = (
            (savings / manual_cost) * 100
            if manual_cost > 0
            else 0.0
        )

        return ValueReport(
            period_days=days,
            total_requests=total_requests,
            system_cost_usd=system_cost,
            manual_cost_usd=manual_cost,
            savings_usd=savings,
            savings_percentage=savings_percentage
        )

    def calculate_time_savings(
        self,
        daily_requests: int,
        days: int = 30
    ) -> Dict[str, float]:
        """计算时间节省

        Args:
            daily_requests: 每日请求数
            days: 计算周期（天）

        Returns:
            包含时间节省信息的字典
        """
        if daily_requests < 0:
            raise ValueError("daily_requests must be non-negative")
        if days <= 0:
            raise ValueError("days must be positive")

        total_requests = daily_requests * days
        total_manual_minutes = total_requests * self.manual_time_per_request_minutes

        return {
            "period_days": days,
            "total_requests": total_requests,
            "manual_time_hours": total_manual_minutes / 60,
            "manual_time_days": total_manual_minutes / (60 * 8),  # 按 8 小时工作日计算
            "manual_time_years": total_manual_minutes / (60 * 8 * 250)  # 按 250 工作日/年计算
        }

    def calculate_roi(
        self,
        development_cost_usd: float,
        monthly_requests: int,
        months: int = 12
    ) -> Dict[str, float]:
        """计算投资回报率（ROI）

        Args:
            development_cost_usd: 开发成本
            monthly_requests: 月请求数
            months: 计算周期（月）

        Returns:
            包含 ROI 信息的字典
        """
        if development_cost_usd < 0:
            raise ValueError("development_cost_usd must be non-negative")
        if monthly_requests < 0:
            raise ValueError("monthly_requests must be non-negative")
        if months <= 0:
            raise ValueError("months must be positive")

        report = self.calculate_savings(
            daily_requests=monthly_requests // 30,
            days=months * 30
        )

        total_savings = report.savings_usd
        net_return = total_savings - development_cost_usd
        roi_percentage = (
            (net_return / development_cost_usd) * 100
            if development_cost_usd > 0
            else float('inf')
        )

        payback_period_months = (
            development_cost_usd / (report.savings_usd / months)
            if report.savings_usd > 0
            else float('inf')
        )

        return {
            "development_cost_usd": development_cost_usd,
            "total_savings_usd": total_savings,
            "net_return_usd": net_return,
            "roi_percentage": roi_percentage,
            "payback_period_months": payback_period_months
        }


def format_currency(value: float) -> str:
    """格式化货币"""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


if __name__ == "__main__":
    # 使用示例（基于 Week 07 的优化结果）
    calculator = BusinessValueCalculator(
        cost_per_request=0.035,  # 优化后的成本
        manual_cost_per_request=2.50,  # 人力成本
        manual_time_per_request_minutes=30.0
    )

    # 场景：每日 1000 个请求，计算 90 天
    report = calculator.calculate_savings(daily_requests=1000, days=90)

    print(f"90 天节省成本: {format_currency(report.savings_usd)}")
    print(f"节省比例: {report.savings_percentage:.1f}%")

    # 时间节省
    time_report = calculator.calculate_time_savings(daily_requests=1000, days=90)
    print(f"节省人力时间: {time_report['manual_time_days']:.1f} 天")
    print(f"相当于: {time_report['manual_time_years']:.2f} 人年")

    # ROI 计算
    roi_report = calculator.calculate_roi(
        development_cost_usd=50_000,  # 开发成本 5 万美元
        monthly_requests=30_000,  # 月请求 3 万
        months=12
    )
    print(f"ROI: {roi_report['roi_percentage']:.1f}%")
    print(f"回本周期: {roi_report['payback_period_months']:.1f} 月")
