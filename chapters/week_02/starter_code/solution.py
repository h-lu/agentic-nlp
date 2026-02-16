#!/usr/bin/env python3
"""
Week 02 Assignment Solution - Prompt Engineering 实战

这是作业的参考解决方案，包含：
1. PromptTemplate 类 - 支持 Prompt 四要素
2. FewShotManager 类 - Few-shot 示例管理
3. PromptEvaluator 类 - Prompt 评估框架
4. 完整的工单分类系统实现

学生应参考此解决方案的结构，但不应直接复制。
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
import yaml

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Part 1: Pydantic 模型定义
# ============================================================================

class TicketClassification(BaseModel):
    """工单分类的输出格式"""
    category: str = Field(description="工单分类：技术支持/账户问题/投诉建议/其他")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0-1")
    reasoning: Optional[str] = Field(default=None, description="分类理由（可选）")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid_categories = ['技术支持', '账户问题', '投诉建议', '其他']
        if v not in valid_categories:
            raise ValueError(f'分类必须是以下之一: {valid_categories}')
        return v


class TicketSummary(BaseModel):
    """工单摘要的输出格式"""
    title: str = Field(description="摘要标题（10字以内）")
    key_issue: str = Field(description="核心问题（50字以内）")
    urgency: str = Field(description="紧急程度：高/中/低")

    @field_validator('urgency')
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        valid_urgencies = ['高', '中', '低']
        if v not in valid_urgencies:
            raise ValueError(f'紧急程度必须是以下之一: {valid_urgencies}')
        return v


class EntityExtraction(BaseModel):
    """实体抽取的输出格式"""
    order_id: Optional[str] = Field(default=None, description="订单号")
    product_name: Optional[str] = Field(default=None, description="产品名称")
    contact_info: Optional[str] = Field(default=None, description="联系方式")
    date_mentioned: Optional[str] = Field(default=None, description="提及的日期")


# ============================================================================
# Part 2: PromptTemplate 类实现
# ============================================================================

@dataclass
class PromptTemplate:
    """
    支持 Prompt 四要素的模板类
    
    四要素：
    - Role: 角色定义（如"你是一个专业的客服分类专家"）
    - Task: 任务描述（如"请对以下工单进行分类"）
    - Constraints: 约束条件（如"只输出分类名称，不要解释"）
    - Format: 输出格式（如 JSON Schema）
    """
    role: str
    task: str
    constraints: list[str] = field(default_factory=list)
    output_format: Optional[str] = None
    examples: list[dict[str, str]] = field(default_factory=list)
    
    def render(self, input_text: str) -> str:
        """渲染完整的 Prompt"""
        parts = []
        
        # 1. Role
        parts.append(f"角色：{self.role}\n")
        
        # 2. Task
        parts.append(f"任务：{self.task}\n")
        
        # 3. Constraints
        if self.constraints:
            parts.append("约束条件：")
            for constraint in self.constraints:
                parts.append(f"- {constraint}")
            parts.append("")
        
        # 4. Few-shot Examples
        if self.examples:
            parts.append("示例：")
            for i, example in enumerate(self.examples, 1):
                parts.append(f"\n示例 {i}:")
                parts.append(f"输入: {example.get('input', '')}")
                parts.append(f"输出: {example.get('output', '')}")
            parts.append("")
        
        # 5. Output Format
        if self.output_format:
            parts.append(f"输出格式：\n{self.output_format}\n")
        
        # 6. Actual Input
        parts.append(f"现在请处理以下输入：\n{input_text}")
        
        return "\n".join(parts)
    
    def add_example(self, input_text: str, output_text: str) -> None:
        """添加 Few-shot 示例"""
        self.examples.append({"input": input_text, "output": output_text})
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "role": self.role,
            "task": self.task,
            "constraints": self.constraints,
            "output_format": self.output_format,
            "examples": self.examples,
        }
    
    @classmethod
    def from_yaml(cls, path: Path) -> "PromptTemplate":
        """从 YAML 文件加载模板"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


# ============================================================================
# Part 3: FewShotManager 类实现
# ============================================================================

@dataclass
class FewShotExample:
    """Few-shot 示例数据结构"""
    input_text: str
    output_text: str
    category: Optional[str] = None  # 用于分类过滤


class FewShotManager:
    """
    Few-shot 示例管理器
    
    功能：
    - 从 YAML 文件加载示例
    - 按类别过滤示例
    - 随机或按顺序选择示例
    - 限制示例数量
    """
    
    def __init__(self, examples: Optional[list[FewShotExample]] = None):
        self.examples = examples or []
    
    def load_from_yaml(self, path: Path) -> None:
        """从 YAML 文件加载示例"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        self.examples = []
        for item in data.get('examples', []):
            self.examples.append(FewShotExample(
                input_text=item['input'],
                output_text=item['output'],
                category=item.get('category'),
            ))
    
    def select_examples(
        self,
        count: int = 3,
        category: Optional[str] = None,
        strategy: str = "balanced",
    ) -> list[FewShotExample]:
        """
        选择示例
        
        Args:
            count: 要选择的示例数量
            category: 按类别过滤（可选）
            strategy: 选择策略 - "random" / "balanced" / "sequential"
        
        Returns:
            选中的示例列表
        """
        import random
        
        # 过滤
        candidates = self.examples
        if category:
            candidates = [e for e in candidates if e.category == category]
        
        # 选择策略
        if strategy == "random":
            return random.sample(candidates, min(count, len(candidates)))
        elif strategy == "sequential":
            return candidates[:count]
        elif strategy == "balanced":
            # 按类别平衡选择
            categories = {}
            for ex in candidates:
                cat = ex.category or "其他"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(ex)
            
            result = []
            per_category = max(1, count // len(categories))
            for cat_examples in categories.values():
                result.extend(cat_examples[:per_category])
            return result[:count]
        
        return candidates[:count]
    
    def to_template_examples(self, examples: list[FewShotExample]) -> list[dict[str, str]]:
        """转换为 PromptTemplate 可用的格式"""
        return [
            {"input": ex.input_text, "output": ex.output_text}
            for ex in examples
        ]


# ============================================================================
# Part 4: PromptEvaluator 类实现
# ============================================================================

@dataclass
class TestCase:
    """测试用例"""
    input_text: str
    expected_category: str
    expected_format: type[BaseModel]
    actual_output: Optional[dict] = None


@dataclass
class EvalResult:
    """评估结果"""
    test_case: TestCase
    is_correct: bool
    format_valid: bool
    error_message: Optional[str] = None


class PromptEvaluator:
    """
    Prompt 评估框架
    
    功能：
    - 加载测试集
    - 计算准确率
    - 计算格式合规率
    - 生成评估报告
    """
    
    def __init__(self, test_cases: Optional[list[TestCase]] = None):
        self.test_cases = test_cases or []
        self.results: list[EvalResult] = []
    
    def load_test_set(self, path: Path) -> None:
        """从 JSON 文件加载测试集"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.test_cases = []
        for item in data:
            self.test_cases.append(TestCase(
                input_text=item['input'],
                expected_category=item['expected_category'],
                expected_format=TicketClassification,
            ))
    
    def evaluate(self, llm_client: Any, template: PromptTemplate) -> list[EvalResult]:
        """
        执行评估
        
        Args:
            llm_client: LLM 客户端（需要有 call 方法）
            template: Prompt 模板
        
        Returns:
            评估结果列表
        """
        self.results = []
        
        for test_case in self.test_cases:
            try:
                # 渲染 Prompt
                prompt = template.render(test_case.input_text)
                
                # 调用 LLM（这里简化处理，实际应使用真实客户端）
                # response = llm_client.call(prompt)
                # output = json.loads(response)
                
                # 模拟输出（实际应替换为真实调用）
                output = {"category": test_case.expected_category, "confidence": 0.9}
                
                # 验证格式
                try:
                    validated = test_case.expected_format(**output)
                    format_valid = True
                except Exception:
                    format_valid = False
                
                # 检查正确性
                is_correct = output.get("category") == test_case.expected_category
                
                test_case.actual_output = output
                self.results.append(EvalResult(
                    test_case=test_case,
                    is_correct=is_correct,
                    format_valid=format_valid,
                ))
                
            except Exception as e:
                self.results.append(EvalResult(
                    test_case=test_case,
                    is_correct=False,
                    format_valid=False,
                    error_message=str(e),
                ))
        
        return self.results
    
    def calculate_metrics(self) -> dict[str, float]:
        """计算评估指标"""
        if not self.results:
            return {"accuracy": 0.0, "format_compliance": 0.0}
        
        correct = sum(1 for r in self.results if r.is_correct)
        valid_format = sum(1 for r in self.results if r.format_valid)
        total = len(self.results)
        
        return {
            "accuracy": correct / total,
            "format_compliance": valid_format / total,
            "total_tests": total,
        }
    
    def generate_report(self, version: str = "v1") -> str:
        """生成 Markdown 评估报告"""
        metrics = self.calculate_metrics()
        
        report = f"""# Prompt 评估报告

## 版本: {version}
## 日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 总体指标

| 指标 | 值 |
|------|-----|
| 准确率 | {metrics['accuracy']:.2%} |
| 格式合规率 | {metrics['format_compliance']:.2%} |
| 测试样本数 | {metrics['total_tests']} |

## 详细结果

"""
        for i, result in enumerate(self.results, 1):
            status = "✅" if result.is_correct else "❌"
            format_status = "✅" if result.format_valid else "❌"
            report += f"""### 测试 {i}
- 输入: {result.test_case.input_text[:50]}...
- 期望: {result.test_case.expected_category}
- 状态: {status} 正确性 | {format_status} 格式
"""
            if result.error_message:
                report += f"- 错误: {result.error_message}\n"
        
        return report


# ============================================================================
# Part 5: 完整工单分类系统
# ============================================================================

class TicketClassificationSystem:
    """
    完整的工单分类系统
    
    整合：
    - PromptTemplate
    - FewShotManager
    - PromptEvaluator
    """
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.templates: dict[str, PromptTemplate] = {}
        self.few_shot_manager = FewShotManager()
        self.evaluator = PromptEvaluator()
        
        self._load_configs()
    
    def _load_configs(self) -> None:
        """加载配置文件"""
        templates_dir = self.config_dir / "templates"
        examples_file = self.config_dir / "examples" / "few_shot.yaml"
        
        # 加载模板
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.yaml"):
                name = template_file.stem
                self.templates[name] = PromptTemplate.from_yaml(template_file)
        
        # 加载 Few-shot 示例
        if examples_file.exists():
            self.few_shot_manager.load_from_yaml(examples_file)
    
    def classify(
        self,
        ticket_text: str,
        template_name: str = "classify",
        use_few_shot: bool = True,
        few_shot_count: int = 3,
    ) -> TicketClassification:
        """
        对工单进行分类
        
        Args:
            ticket_text: 工单文本
            template_name: 使用的模板名称
            use_few_shot: 是否使用 Few-shot
            few_shot_count: Few-shot 示例数量
        
        Returns:
            分类结果
        """
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"模板 '{template_name}' 不存在")
        
        # 添加 Few-shot 示例
        if use_few_shot:
            examples = self.few_shot_manager.select_examples(count=few_shot_count)
            for ex in examples:
                template.add_example(ex.input_text, ex.output_text)
        
        # 渲染 Prompt
        prompt = template.render(ticket_text)
        
        # 调用 LLM（简化版，实际应使用真实客户端）
        # response = self.llm_client.call(prompt)
        # return TicketClassification(**json.loads(response))
        
        # 模拟返回
        return TicketClassification(
            category="技术支持",
            confidence=0.95,
            reasoning="工单提到无法登录，属于技术支持类别",
        )
    
    def run_evaluation(
        self,
        test_set_path: Path,
        output_report_path: Optional[Path] = None,
    ) -> dict[str, float]:
        """
        运行评估
        
        Args:
            test_set_path: 测试集文件路径
            output_report_path: 报告输出路径（可选）
        
        Returns:
            评估指标
        """
        self.evaluator.load_test_set(test_set_path)
        
        # 使用默认分类模板
        template = self.templates.get("classify")
        if not template:
            raise ValueError("分类模板不存在")
        
        # 执行评估（这里需要真实的 LLM 客户端）
        # results = self.evaluator.evaluate(self.llm_client, template)
        
        # 计算指标
        metrics = self.evaluator.calculate_metrics()
        
        # 生成报告
        if output_report_path:
            report = self.evaluator.generate_report()
            with open(output_report_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return metrics


# ============================================================================
# Main: 演示用法
# ============================================================================

def main():
    """演示系统用法"""
    print("=" * 60)
    print("Week 02 Prompt Engineering 实战 - 参考解决方案")
    print("=" * 60)
    
    # 1. 创建 Prompt 模板
    print("\n【1】创建 PromptTemplate")
    template = PromptTemplate(
        role="你是一个专业的客服工单分类专家，有5年客服经验",
        task="请对以下客服工单进行分类",
        constraints=[
            "只输出分类结果，不要添加解释",
            "分类必须是：技术支持/账户问题/投诉建议/其他 之一",
            "输出必须是 JSON 格式",
        ],
        output_format='{"category": "分类名称", "confidence": 0.95}',
    )
    print(f"角色: {template.role}")
    print(f"任务: {template.task}")
    print(f"约束: {len(template.constraints)} 条")
    
    # 2. 添加 Few-shot 示例
    print("\n【2】添加 Few-shot 示例")
    template.add_example(
        input_text="我忘记密码了，怎么重置？",
        output_text='{"category": "账户问题", "confidence": 0.98}',
    )
    template.add_example(
        input_text="软件打开就闪退，根本用不了",
        output_text='{"category": "技术支持", "confidence": 0.95}',
    )
    print(f"已添加 {len(template.examples)} 个示例")
    
    # 3. 渲染完整 Prompt
    print("\n【3】渲染 Prompt")
    test_input = "登录的时候一直提示验证码错误，但我明明输入对了"
    prompt = template.render(test_input)
    print("生成的 Prompt:")
    print("-" * 40)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("-" * 40)
    
    # 4. Few-shot 管理器
    print("\n【4】Few-shot 管理器")
    manager = FewShotManager()
    manager.examples = [
        FewShotExample("忘记密码", '{"category": "账户问题"}', "账户问题"),
        FewShotExample("软件崩溃", '{"category": "技术支持"}', "技术支持"),
        FewShotExample("投诉物流慢", '{"category": "投诉建议"}', "投诉建议"),
        FewShotExample("无法登录", '{"category": "技术支持"}', "技术支持"),
    ]
    selected = manager.select_examples(count=2, strategy="balanced")
    print(f"选中 {len(selected)} 个示例（平衡策略）:")
    for ex in selected:
        print(f"  - {ex.input_text} -> {ex.output_text}")
    
    # 5. 评估框架
    print("\n【5】评估框架")
    test_cases = [
        TestCase("忘记密码怎么办", "账户问题", TicketClassification),
        TestCase("软件打不开", "技术支持", TicketClassification),
        TestCase("投诉服务态度", "投诉建议", TicketClassification),
    ]
    evaluator = PromptEvaluator(test_cases)
    print(f"加载了 {len(evaluator.test_cases)} 个测试用例")
    metrics = evaluator.calculate_metrics()
    print(f"当前指标（模拟）: 准确率={metrics['accuracy']:.0%}, 格式合规率={metrics['format_compliance']:.0%}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
