#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例：Human-in-the-Loop（人在回路）

本例演示如何在多 Agent 系统中引入人工审核和反馈。

核心概念：
- 关键决策点的人工确认
- 异常情况的人工介入
- 人工反馈的学习和应用

运行方式：python3 chapters/week_06/examples/04_human_in_loop.py
预期输出：展示如何在关键点引入人工审核

依赖：
- pip install openai
- export OPENAI_API_KEY="your-api-key"
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI


# ============================================================
# 数据结构
# ============================================================

class ReviewPoint(str, Enum):
    """审核点类型"""
    PLAN_REVIEW = "plan_review"  # 计划审核
    EXECUTION_MONITOR = "execution_monitor"  # 执行监控
    RESULT_REVIEW = "result_review"  # 结果审核


class ApprovalStatus(str, Enum):
    """审核状态"""
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"  # 有修改建议


@dataclass
class HumanReview:
    """人工审核记录"""
    stage: str  # 审核阶段
    data: Dict[str, Any]  # 审核的数据
    status: ApprovalStatus
    feedback: Optional[str] = None
    reviewer: str = "human"
    timestamp: str = field(default_factory=lambda: "")


# ============================================================
# 带人工审核的 Agent
# ============================================================

class HumanInTheLoopAgent:
    """
    带 Human-in-the-Loop 的 Agent

    核心能力：
    - 在关键决策点暂停，等待人工确认
    - 接收人工反馈并调整策略
    - 记录所有人工审核历史
    """

    def __init__(
        self,
        name: str,
        llm_client: Optional[OpenAI] = None,
        require_approval: bool = True
    ):
        self.name = name
        self.llm = llm_client
        self.require_approval = require_approval
        self.review_history: List[HumanReview] = []

    def run_with_human_review(
        self,
        task: str,
        review_points: List[ReviewPoint],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """运行工作流，在指定审核点等待人工确认"""

        if verbose:
            print(f"\n[{self.name}] 开始任务: {task}")
            print(f"审核点: {[rp.value for rp in review_points]}")

        # 审核点 1：计划审核
        plan = self._create_plan(task)
        if ReviewPoint.PLAN_REVIEW in review_points and self.require_approval:
            approved, feedback = self._request_human_approval("计划审核", plan)
            self._record_review("plan_review", plan, approved, feedback)

            if not approved:
                if feedback:
                    plan = self._revise_plan(plan, feedback)
                    # 再次审核
                    approved, feedback = self._request_human_approval("修订后计划审核", plan)
                    if not approved:
                        return {"status": "aborted", "reason": "计划被拒绝", "feedback": feedback}

        # 执行计划
        execution_result = self._execute_plan(plan)

        # 审核点 2：执行监控（检查是否有异常）
        if ReviewPoint.EXECUTION_MONITOR in review_points:
            errors = self._check_execution_errors(execution_result)
            if errors and self.require_approval:
                approved, feedback = self._request_human_approval(
                    "执行异常",
                    {"errors": errors, "execution": execution_result}
                )
                self._record_review("execution_monitor", execution_result, approved, feedback)

                if not approved:
                    return {"status": "aborted", "reason": "执行异常被拒绝", "errors": errors}

        # 生成结果
        result = self._generate_result(plan, execution_result)

        # 审核点 3：结果审核
        if ReviewPoint.RESULT_REVIEW in review_points and self.require_approval:
            approved, feedback = self._request_human_approval("结果审核", result)
            self._record_review("result_review", result, approved, feedback)

            if not approved:
                if feedback:
                    # 根据反馈修订
                    result = self._revise_result(result, feedback)
                    # 再次审核
                    approved, feedback = self._request_human_approval("修订后结果审核", result)
                    if not approved:
                        return {"status": "completed_with_revisions", "result": result, "feedback": feedback}

        return {
            "status": "completed",
            "task": task,
            "plan": plan,
            "execution": execution_result,
            "result": result,
            "reviews": len(self.review_history)
        }

    def _create_plan(self, task: str) -> Dict[str, Any]:
        """创建计划"""
        return {
            "task": task,
            "steps": [
                {"step": 1, "action": "分析需求"},
                {"step": 2, "action": "检索信息"},
                {"step": 3, "action": "生成答案"}
            ],
            "estimated_time": "30秒"
        }

    def _revise_plan(self, plan: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """根据反馈修订计划"""
        print(f"\n[{self.name}] 根据反馈修订计划...")
        # 简化实现：在计划中添加备注
        revised_plan = plan.copy()
        revised_plan["feedback"] = feedback
        revised_plan["revised"] = True
        return revised_plan

    def _execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行计划"""
        results = []
        for step in plan["steps"]:
            results.append({
                "step": step["step"],
                "action": step["action"],
                "status": "completed"
            })
        return {"results": results, "status": "success"}

    def _check_execution_errors(self, execution: Dict[str, Any]) -> List[str]:
        """检查执行错误"""
        errors = []
        for result in execution.get("results", []):
            if result.get("status") == "failed":
                errors.append(f"步骤{result['step']}失败")
        return errors

    def _generate_result(self, plan: Dict, execution: Dict) -> Dict[str, Any]:
        """生成结果"""
        return {
            "answer": "根据检索结果，这是答案...",
            "confidence": 0.85,
            "sources": ["文档1", "文档2"]
        }

    def _revise_result(self, result: Dict, feedback: str) -> Dict:
        """根据反馈修订结果"""
        print(f"\n[{self.name}] 根据反馈修订结果...")
        revised = result.copy()
        revised["feedback"] = feedback
        revised["revised"] = True
        return revised

    def _request_human_approval(self, stage: str, data: Dict) -> Tuple[bool, Optional[str]]:
        """请求人工批准"""
        print(f"\n{'='*50}")
        print(f"【人工审核 - {stage}】")
        print('='*50)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print('='*50)

        # 在实际应用中，这里可能是 Web 界面或消息通知
        # 这里简化为命令行输入
        user_input = input("\n批准？(y=批准, n=拒绝, 或输入修改建议): ").strip()

        if user_input.lower() == 'y':
            print("✅ 已批准")
            return True, None
        elif user_input.lower() == 'n':
            print("❌ 已拒绝")
            return False, "人工拒绝"
        else:
            print(f"✏️  修改建议: {user_input}")
            return False, user_input

    def _record_review(
        self,
        stage: str,
        data: Dict,
        approved: bool,
        feedback: Optional[str]
    ) -> None:
        """记录审核历史"""
        review = HumanReview(
            stage=stage,
            data=data,
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            feedback=feedback
        )
        self.review_history.append(review)
        print(f"[{self.name}] 审核已记录")

    def get_review_history(self) -> List[HumanReview]:
        """获取审核历史"""
        return self.review_history

    def export_review_log(self) -> str:
        """导出审核日志（用于审计）"""
        log_lines = ["# Human-in-the-Loop 审核日志\n"]
        for review in self.review_history:
            log_lines.append(f"## 阶段: {review.stage}")
            log_lines.append(f"状态: {review.status.value}")
            if review.feedback:
                log_lines.append(f"反馈: {review.feedback}")
            log_lines.append("")
        return "\n".join(log_lines)


# ============================================================
# 自动拒绝错误计划的 Agent（演示）
# ============================================================

class ErrorProneAgent(HumanInTheLoopAgent):
    """
    容易出错的 Agent（用于演示 Human-in-the-Loop 的必要性）

    这个 Agent 会生成明显错误的计划，需要人工纠正。
    """

    def _create_plan(self, task: str) -> Dict[str, Any]:
        """创建可能错误的计划"""
        # 有 50% 概率生成错误计划
        import random
        if random.random() < 0.5:
            # 错误计划：用情感分析来做词频统计
            return {
                "task": task,
                "steps": [
                    {"step": 1, "action": "情感分析", "note": "❌ 错误：用情感分析来统计词频"},
                    {"step": 2, "action": "词频统计", "note": "顺序错误"},
                ],
                "estimated_time": "60秒",
                "potential_error": True
            }
        else:
            # 正确计划
            return {
                "task": task,
                "steps": [
                    {"step": 1, "action": "文本预处理"},
                    {"step": 2, "action": "词频统计"},
                    {"step": 3, "action": "结果可视化"}
                ],
                "estimated_time": "30秒",
                "potential_error": False
            }


# ============================================================
# 反例：没有人工审核的系统
# ============================================================

def bad_hitl_example():
    """
    反例：没有 Human-in-the-Loop 的问题

    常见错误：
    1. Agent 自信地执行错误计划
    2. 错误在系统中传播和放大
    3. 出错后难以追溯和纠正
    """

    class AutonomousAgent:
        """❌ 完全自主的 Agent（无人工审核）"""

        def run(self, task):
            plan = self._create_plan(task)  # 可能生成错误计划
            result = self._execute_plan(plan)  # 照单全收
            return result

        def _create_plan(self, task):
            # 问题：没有人工审核，错误计划会被直接执行
            return {"steps": ["错误步骤1", "错误步骤2"]}

    print("❌ 错误做法示例：")
    print("AutonomousAgent 生成错误计划后，会自信地执行它")
    print("问题：")
    print("  1. 错误计划无法被及时发现")
    print("  2. 错误会在系统中传播")
    print("  3. 最终结果可能完全错误")
    print("\n✅ 正确做法：使用 Human-in-the-Loop")
    print("  在关键决策点引入人工审核，及时纠正错误")


# ============================================================
# 主函数
# ============================================================

def main() -> None:
    print("=" * 70)
    print("Human-in-the-Loop 演示")
    print("=" * 70)

    # 创建带人工审核的 Agent
    agent = HumanInTheLoopAgent(
        name="TextAgent",
        require_approval=True
    )

    # 演示1：正常流程
    print("\n" + "=" * 70)
    print("演示1：正常流程（人工批准）")
    print("=" * 70)

    result = agent.run_with_human_review(
        task="分析客户反馈中的主要问题",
        review_points=[
            ReviewPoint.PLAN_REVIEW,
            ReviewPoint.RESULT_REVIEW
        ],
        verbose=True
    )

    print(f"\n最终状态: {result['status']}")
    print(f"审核次数: {result['reviews']}")

    # 演示2：容易出错的 Agent（展示人工审核的价值）
    print("\n\n" + "=" * 70)
    print("演示2：容易出错的 Agent（展示人工审核的价值）")
    print("=" * 70)
    print("注意：这个 Agent 有 50% 概率生成错误计划")
    print("人工审核可以及时发现问题并纠正\n")

    error_prone_agent = ErrorProneAgent(
        name="ErrorProneAgent",
        require_approval=True
    )

    # 运行多次，展示人工审核的价值
    for i in range(2):
        print(f"\n第 {i+1} 次运行:")
        result = error_prone_agent.run_with_human_review(
            task="统计文档中的词频",
            review_points=[ReviewPoint.PLAN_REVIEW],
            verbose=True
        )

        if result.get("status") == "aborted":
            print("  → 人工审核成功阻止了错误计划的执行！")

    # 对比说明
    print("\n\n" + "=" * 70)
    print("Human-in-the-Loop 的价值")
    print("=" * 70)
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ 维度              │  无人工审核           │  有人工审核           │
├─────────────────────────────────────────────────────────────────┤
│ 错误发现          │  可能在最后才发现      │  在关键点及时发现      │
│ 错误纠正          │  需要重新运行          │  可以及时调整          │
│ 可追溯性          │  难以追溯决策过程      │  有完整的审核记录      │
│ 系统可靠性        │  依赖 Agent 的判断      │  人工作为最后一道防线  │
│ 适用场景          │  低风险任务            │  高风险/关键任务       │
└─────────────────────────────────────────────────────────────────┘

Human-in-the-Loop 的三种模式：

1. 主动审核（Active Review）
   - Agent 主动请求人工确认
   - 适用：高风险决策（如删除数据、大额转账）

2. 被动审核（Passive Review）
   - 人工可以随时介入查看
   - 适用：长时间运行的任务

3. 反馈学习（Feedback Learning）
   - 人工修正后，系统学习
   - 适用：持续优化的系统

小北的发现：
"我试着让 Agent 分析 100 份反馈，结果它生成了一个明显错误的计划——
想用'情感分析'来统计词频。幸好有人工审核，我及时纠正了它！"

老潘的点评：
"在生产环境里，任何可能造成重大影响的操作都必须有人工审核。
这不是不相信 AI，而是工程实践的基本原则——人永远是最后一道防线。

而且，人工审核的记录是宝贵的资产。你可以分析这些记录，
找出 Agent 容易出错的场景，然后改进 Prompt 或添加新工具。"

最佳实践：
✅ 在高风险决策点设置人工审核
✅ 提供清晰的审核界面和数据
✅ 记录所有审核历史（用于审计和改进）
✅ 支持一键批准/拒绝/修改建议
✅ 渐进式自动化（开始多审核，系统成熟后减少）
    """)

    # 展示审核历史
    print("\n" + "=" * 70)
    print("审核历史记录")
    print("=" * 70)
    log = agent.export_review_log()
    print(log)

    # 展示反例
    print("\n" + "=" * 70)
    print("反例：没有人工审核的系统")
    print("=" * 70)
    bad_hitl_example()


if __name__ == "__main__":
    main()
