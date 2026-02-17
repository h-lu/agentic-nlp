---
name: llm-viz
description: 创建高质量 LLM 应用可视化的指南。包含 Token 使用图、RAG 检索效果、Agent 流程图、评估指标图。
argument-hint: "<week_id> [chart_type]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, WebSearch
disable-model-invocation: true
---

# /llm-viz

## 用法

```
/llm-viz week_XX              # 显示本周应该生成的图表类型
/llm-viz week_XX token_usage  # 生成特定类型的图表
```

## 目标

为 `chapters/week_XX/` 创建高质量的 LLM 应用可视化：
- 图表代码保存在 `examples/NN_chart_xxx.py`（可复现）
- 图片输出到 `images/xxx.png`（嵌入正文）
- 确保中文字体正确显示
- 避免常见的可视化错误

---

## 第一部分：图表类型选择指南

### 什么时候用什么图

| 你想展示什么 | 推荐图表 | 说明 |
|-------------|---------|------|
| Token 使用分布 | 柱状图 | 展示不同任务的 Token 消耗 |
| 成本对比 | 条形图 | 不同模型/配置的成本比较 |
| RAG 检索效果 | 柱状图 + 折线 | Recall@K、MRR 等指标 |
| Agent 执行流程 | 流程图/时序图 | 用 Mermaid 或 Matplotlib |
| 评估指标对比 | 雷达图/条形图 | 多维度性能对比 |
| 延迟分布 | 箱线图/直方图 | 响应时间分析 |
| 混合检索效果 | 分组柱状图 | 向量检索 vs 关键词检索 |

### 不推荐的图表类型

| 避免 | 原因 | 替代方案 |
|------|------|---------|
| 3D 图表 | 透视 distort 数值感知 | 2D 图表 + 分面 |
| 过多颜色 | 认知过载 | 使用色调渐变或分组 |
| 复杂饼图 | 人眼难以比较角度 | 条形图 |

---

## 第二部分：常见错误与修复

### 错误 1：截断 Y 轴

```python
# ❌ 错误：截断 Y 轴夸大差异
plt.ylim(95, 100)  # 从 95 开始，5% 差距看起来很大

# ✅ 正确：从 0 开始（柱状图必须）
plt.ylim(0, None)  # 或不设置，让 matplotlib 自动选择
```

### 错误 2：信息过载

```python
# ❌ 错误：一张图展示所有东西
sns.scatterplot(data=df, x='a', y='b', hue='c', size='d', style='e')

# ✅ 正确：分面或分图
g = sns.relplot(data=df, x='a', y='b', hue='c', col='e')
```

---

## 第三部分：中文字体配置

```python
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def setup_chinese_font() -> str:
    """配置中文字体，返回使用的字体名称"""
    chinese_fonts = ['SimHei', 'Noto Sans CJK SC', 'Arial Unicode MS',
                     'PingFang SC', 'Microsoft YaHei']
    available = [f.name for f in fm.fontManager.ttflist]
    for font in chinese_fonts:
        if font in available:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return font
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    return 'DejaVu Sans'
```

---

## 第四部分：代码模板

### 模板：Token 使用对比图

```python
"""
示例：生成不同 LLM 任务的 Token 使用对比图。

运行方式：python3 chapters/week_XX/examples/01_token_chart.py
预期输出：生成 images/token_usage.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path


def setup_chinese_font() -> str:
    chinese_fonts = ['SimHei', 'Noto Sans CJK SC', 'Arial Unicode MS']
    available = [f.name for f in fm.fontManager.ttflist]
    for font in chinese_fonts:
        if font in available:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return font
    return 'DejaVu Sans'


def main() -> None:
    font = setup_chinese_font()

    tasks = ['分类', '摘要', '抽取', '问答']
    input_tokens = [150, 500, 200, 300]
    output_tokens = [20, 100, 50, 150]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(tasks))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], input_tokens, width,
                   label='输入 Token', color='steelblue')
    bars2 = ax.bar([i + width/2 for i in x], output_tokens, width,
                   label='输出 Token', color='coral')

    ax.set_xlabel('任务类型', fontsize=12)
    ax.set_ylabel('Token 数量', fontsize=12)
    ax.set_title('不同 LLM 任务的 Token 使用对比', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks)
    ax.legend()

    # 添加数值标签
    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    ha='center', va='bottom', fontsize=10)

    output_dir = Path(__file__).parent.parent / 'images'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'token_usage.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"图片已保存: {output_dir / 'token_usage.png'}")


if __name__ == '__main__':
    main()
```

---

## 第五部分：Week 各阶段推荐图表

| 阶段 | 周次 | 推荐图表 |
|------|------|---------|
| LLM 基础 | 01-02 | Token 使用图、成本对比图 |
| RAG 系统 | 03-04 | 检索效果对比、RAGAS 评估雷达图 |
| LLM Agents | 05-06 | Agent 流程图、工具调用时序图 |
| 企业应用 | 07-08 | 端到端性能图、评估仪表板 |

---

## 执行流程

当调用此 skill 时：

1. **读取本周主题**：从 `chapters/week_XX/CHAPTER.md` 确定需要什么图表
2. **检查现有图片**：查看 `images/` 目录
3. **生成缺失的图表**：
   - 代码保存到 `examples/NN_chart_xxx.py`
   - 图片保存到 `images/xxx.png`
   - 在 CHAPTER.md 中插入引用
4. **验证**：运行代码确认图片正确生成
5. **更新验证**：确保 `validate_week.py` 仍然通过
