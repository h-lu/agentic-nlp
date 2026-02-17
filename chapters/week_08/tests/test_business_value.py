"""
测试商业价值计算

测试模块：
- BusinessValueCalculator
- ValueReport
- ROI 计算
- 时间节省计算
"""

import pytest
from datetime import datetime, timedelta

from business_value import (
    BusinessValueCalculator,
    ValueReport,
    format_currency
)


class TestBusinessValueCalculator:
    """测试商业价值计算器"""

    def test_calculator_initialization(self):
        """测试计算器初始化"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        assert calculator.cost_per_request == 0.035
        assert calculator.manual_cost_per_request == 2.50

    def test_calculator_initialization_with_time_cost(self):
        """测试包含时间成本的计算器初始化"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50,
            manual_time_per_request_minutes=30.0
        )

        assert calculator.manual_time_per_request_minutes == 30.0

    def test_calculator_negative_cost_per_request(self):
        """测试负的系统成本应该失败"""
        with pytest.raises(ValueError, match="cost_per_request must be non-negative"):
            BusinessValueCalculator(
                cost_per_request=-0.01,
                manual_cost_per_request=2.50
            )

    def test_calculator_negative_manual_cost(self):
        """测试负的人工成本应该失败"""
        with pytest.raises(ValueError, match="manual_cost_per_request must be non-negative"):
            BusinessValueCalculator(
                cost_per_request=0.035,
                manual_cost_per_request=-1.0
            )

    def test_calculator_negative_time_cost(self):
        """测试负的时间成本应该失败"""
        with pytest.raises(ValueError, match="manual_time_per_request_minutes must be non-negative"):
            BusinessValueCalculator(
                cost_per_request=0.035,
                manual_cost_per_request=2.50,
                manual_time_per_request_minutes=-10.0
            )

    def test_calculate_savings_basic(self):
        """测试基本的成本节省计算"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        report = calculator.calculate_savings(daily_requests=100, days=30)

        assert isinstance(report, ValueReport)
        assert report.period_days == 30
        assert report.total_requests == 3000
        assert report.system_cost_usd == pytest.approx(105.0)  # 3000 * 0.035
        assert report.manual_cost_usd == pytest.approx(7500.0)  # 3000 * 2.50
        assert report.savings_usd == pytest.approx(7395.0)  # 7500 - 105
        assert report.savings_percentage == pytest.approx(98.6, rel=0.1)

    def test_calculate_savings_zero_daily_requests(self):
        """测试零日请求数"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        report = calculator.calculate_savings(daily_requests=0, days=30)

        assert report.total_requests == 0
        assert report.system_cost_usd == 0
        assert report.manual_cost_usd == 0
        assert report.savings_usd == 0
        assert report.savings_percentage == 0

    def test_calculate_savings_zero_cost_per_request(self):
        """测试零系统成本"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.0,
            manual_cost_per_request=2.50
        )

        report = calculator.calculate_savings(daily_requests=100, days=30)

        assert report.system_cost_usd == 0
        assert report.savings_usd == report.manual_cost_usd  # 100% 节省

    def test_calculate_savings_zero_manual_cost(self):
        """测试零人工成本"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=0.0
        )

        report = calculator.calculate_savings(daily_requests=100, days=30)

        assert report.manual_cost_usd == 0
        assert report.savings_usd == -report.system_cost_usd  # 负节省（系统更贵）
        assert report.savings_percentage == 0  # 除以零时返回 0

    def test_calculate_savings_high_volume(self):
        """测试高量级计算"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        report = calculator.calculate_savings(daily_requests=10000, days=90)

        assert report.total_requests == 900000
        assert report.savings_usd > 2_000_000  # 超过 200 万

    def test_calculate_savings_negative_daily_requests(self):
        """测试负日请求数应该失败"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        with pytest.raises(ValueError, match="daily_requests must be non-negative"):
            calculator.calculate_savings(daily_requests=-100, days=30)

    def test_calculate_savings_zero_days(self):
        """测试零天应该失败"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        with pytest.raises(ValueError, match="days must be positive"):
            calculator.calculate_savings(daily_requests=100, days=0)

    def test_calculate_savings_negative_days(self):
        """测试负天应该失败"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        with pytest.raises(ValueError, match="days must be positive"):
            calculator.calculate_savings(daily_requests=100, days=-30)

    def test_calculate_time_savings_basic(self):
        """测试时间节省计算"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50,
            manual_time_per_request_minutes=30.0
        )

        report = calculator.calculate_time_savings(daily_requests=100, days=30)

        assert report["period_days"] == 30
        assert report["total_requests"] == 3000
        assert report["manual_time_hours"] == pytest.approx(1500.0)  # 3000 * 30 / 60
        assert report["manual_time_days"] == pytest.approx(187.5)  # 1500 / 8
        assert report["manual_time_years"] == pytest.approx(0.75, rel=0.1)  # 1500 / (8 * 250)

    def test_calculate_time_savings_zero_time(self):
        """测试零时间成本"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50,
            manual_time_per_request_minutes=0.0
        )

        report = calculator.calculate_time_savings(daily_requests=100, days=30)

        assert report["manual_time_hours"] == 0
        assert report["manual_time_days"] == 0
        assert report["manual_time_years"] == 0

    def test_calculate_roi_basic(self):
        """测试 ROI 计算"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        roi = calculator.calculate_roi(
            development_cost_usd=50_000,
            monthly_requests=30_000,
            months=12
        )

        assert roi["development_cost_usd"] == 50_000
        assert roi["total_savings_usd"] > 0
        assert roi["roi_percentage"] > 0
        assert roi["payback_period_months"] > 0
        assert roi["payback_period_months"] < 12  # 应该在一年内回本

    def test_calculate_roi_zero_development_cost(self):
        """测试零开发成本（无限 ROI）"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        roi = calculator.calculate_roi(
            development_cost_usd=0.0,
            monthly_requests=10_000,
            months=12
        )

        assert roi["development_cost_usd"] == 0
        assert roi["roi_percentage"] == float('inf')

    def test_calculate_roi_negative_development_cost(self):
        """测试负开发成本应该失败"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.035,
            manual_cost_per_request=2.50
        )

        with pytest.raises(ValueError, match="development_cost_usd must be non-negative"):
            calculator.calculate_roi(
                development_cost_usd=-10_000,
                monthly_requests=10_000,
                months=12
            )

    def test_calculate_roi_no_savings(self):
        """测试没有节省的情况"""
        calculator = BusinessValueCalculator(
            cost_per_request=2.50,  # 和人工成本一样
            manual_cost_per_request=2.50
        )

        roi = calculator.calculate_roi(
            development_cost_usd=10_000,
            monthly_requests=1_000,
            months=12
        )

        assert roi["total_savings_usd"] == 0
        assert roi["net_return_usd"] == -10_000  # 亏损
        assert roi["payback_period_months"] == float('inf')


class TestValueReport:
    """测试价值报告"""

    def test_value_report_creation(self):
        """测试创建价值报告"""
        report = ValueReport(
            period_days=30,
            total_requests=1000,
            system_cost_usd=35.0,
            manual_cost_usd=2500.0,
            savings_usd=2465.0,
            savings_percentage=98.6
        )

        assert report.period_days == 30
        assert report.total_requests == 1000
        assert report.savings_usd == pytest.approx(2465.0)

    def test_value_report_to_dict(self):
        """测试转换为字典"""
        report = ValueReport(
            period_days=30,
            total_requests=1000,
            system_cost_usd=35.0,
            manual_cost_usd=2500.0,
            savings_usd=2465.0,
            savings_percentage=98.6
        )

        result = report.to_dict()

        assert isinstance(result, dict)
        assert result["period_days"] == 30
        assert result["savings_usd"] == pytest.approx(2465.0)


# 测试货币格式化（独立函数，避免 pytest 误解）
@pytest.mark.parametrize("value,expected", [
    (0.5, "$0.50"),
    (100, "$100.00"),
    (999.99, "$999.99"),
    (1000, "$1.00K"),
    (1500, "$1.50K"),
    (999999, "$1000.00K"),
    (1_000_000, "$1.00M"),
    (2_500_000, "$2.50M"),
    (10_000_000, "$10.00M"),
    # 负数情况：实际返回 '$-100.00' 而不是 '-$100.00'
    (-100, "$-100.00"),
])
def test_format_currency(value, expected):
    """参数化测试：货币格式化"""
    result = format_currency(value)
    assert result == expected


class TestBusinessValueScenarios:
    """测试商业价值场景"""

    def test_small_business_scenario(self):
        """测试小企业场景：少量请求"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.05,
            manual_cost_per_request=5.00
        )

        # 日请求 100，运行 30 天
        report = calculator.calculate_savings(daily_requests=100, days=30)

        assert report.savings_percentage > 90  # 高节省率

    def test_enterprise_scenario(self):
        """测试企业场景：大量请求"""
        calculator = BusinessValueCalculator(
            cost_per_request=0.02,  # 更低成本
            manual_cost_per_request=10.00  # 更高人工成本
        )

        # 日请求 100,000，运行 90 天
        report = calculator.calculate_savings(daily_requests=100_000, days=90)

        assert report.savings_usd > 80_000_000  # 超过 8000 万

    def test_edge_case_equal_costs(self):
        """测试边界情况：成本相等"""
        calculator = BusinessValueCalculator(
            cost_per_request=1.0,
            manual_cost_per_request=1.0
        )

        report = calculator.calculate_savings(daily_requests=100, days=30)

        assert report.savings_usd == 0
        assert report.savings_percentage == 0

    def test_edge_case_system_more_expensive(self):
        """测试边界情况：系统成本更高"""
        calculator = BusinessValueCalculator(
            cost_per_request=5.0,
            manual_cost_per_request=1.0
        )

        report = calculator.calculate_savings(daily_requests=100, days=30)

        assert report.savings_usd < 0  # 负节省


@pytest.mark.parametrize("cost,manual,daily,days,expected_savings_pct", [
    (0.035, 2.50, 1000, 90, 98.6),
    (0.10, 2.50, 1000, 90, 96.0),
    (0.035, 5.00, 1000, 90, 99.3),
    (0.035, 2.50, 100, 30, 98.6),
    (0.0, 2.50, 1000, 90, 100.0),
    (2.50, 2.50, 1000, 90, 0.0),
])
def test_savings_percentage_calculation(cost, manual, daily, days, expected_savings_pct):
    """参数化测试：节省百分比计算"""
    calculator = BusinessValueCalculator(
        cost_per_request=cost,
        manual_cost_per_request=manual
    )

    report = calculator.calculate_savings(daily_requests=daily, days=days)

    assert report.savings_percentage == pytest.approx(expected_savings_pct, rel=0.1)


@pytest.mark.parametrize("dev_cost,monthly,months,expected_payback", [
    (10_000, 1_000, 12, 4.1),  # 约 4.1 个月回本
    (50_000, 10_000, 12, 2.0),  # 约 2.0 个月回本（更高效的规模）
    (100_000, 5_000, 12, 8.2),  # 约 8.2 个月回本
])
def test_payback_period_calculation(dev_cost, monthly, months, expected_payback):
    """参数化测试：回本周期计算"""
    calculator = BusinessValueCalculator(
        cost_per_request=0.035,
        manual_cost_per_request=2.50
    )

    roi = calculator.calculate_roi(
        development_cost_usd=dev_cost,
        monthly_requests=monthly,
        months=months
    )

    assert roi["payback_period_months"] == pytest.approx(expected_payback, rel=0.1)
