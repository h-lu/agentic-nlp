---
name: polish-week
description: 对指定 week 的 CHAPTER.md 做深度改写——消灭模板感、补贯穿案例、重组结构，使其达到教材水准。
argument-hint: "<week_id e.g. week_01>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
disable-model-invocation: true
---

# /polish-week

## 用法

```
/polish-week week_XX
```

## 目标

- `chapters/week_XX/CHAPTER.md` 达到教材水准：叙事流畅、有贯穿案例、节奏多变、有温度
- 可做结构性改写（不仅仅是换词润色）
- 追加 1-2 个"AI 时代小专栏"（200-500 字/个），附**真实**参考链接 + 访问日期（**优先读取 `.research_cache.md` 研究缓存，不足时使用 WebSearch / Exa MCP / perplexity MCP 搜索获取真实 URL，绝对禁止编造**）
- 不改代码/测试/YAML，不引入新的 `validate_week.py` 失败

## 步骤

### 0. 日期校准（立即执行）

生成 `shared/current_date.txt`，供后续 agent 读取当前日期：

```bash
date '+%Y-%m-%d' > shared/current_date.txt
```

这确保 AI 小专栏中的数据和访问日期使用当前年份。

### 1. 诊断

调用 subagent `student-qa`（只读模式）：
- 必须先读 `shared/writing_exemplars.md`
- 输出叙事质量评分 + 阻塞项/建议项
- **新增：图片需求诊断** — 根据本章主题判断是否需要图片（分布/比较/关系/评估类主题通常需要）
- **新增：公式需求诊断** — 判断核心概念是否需要数学精确定义
- 如果评分 >= 4 且无阻塞项，可跳到步骤 3（轻润色即可）

### 2. 深度改写

调用 subagent `prose-polisher`：
- 必须先读 `shared/writing_exemplars.md`
- 根据 student-qa 的诊断结果，执行对应级别的改写
- 如果缺贯穿案例，补入一条
- 如果结构过于机械，重组

### 2.5 图片与公式补充（根据诊断执行）

如果 student-qa 诊断指出需要图片或公式：

#### 2.5A. 图片生成 → 调用 `/stat-viz` skill

使用 Skill 工具调用 `stat-viz`：
```
skill: "stat-viz"
args: "week_XX"
```

**关键要求**（确保 `/stat-viz` 遵守）：
- ✅ 代码**必须**保存到 `examples/NN_chart_xxx.py`（可复现）
- ✅ 图片输出到 `images/xxx.png`（嵌入正文）
- ✅ 使用正确的中文字体配置
- ✅ 避免常见错误（截断 Y 轴、3D 效果等）
- ✅ 在 CHAPTER.md 中插入图片引用：`![](images/xxx.png) *图注*`

#### 2.5B. 公式补充 → 直接编辑 CHAPTER.md

根据诊断结果，在合适位置补充数学公式：
- 使用 LaTeX 格式：`$$公式$$`（块级）或 `$公式$`（行内）
- 块级公式用引用块包裹：`> $$...$$`
- 每个符号都要解释含义

**执行要点**：
- 检查 `chapters/week_XX/images/` 是否存在
- 重新运行验证确保无破坏

### 3. 一致性检查（可选）

调用 subagent `consistency-editor`：做格式/术语/引用一致性检查（避免重写内容）

### 4. 验证

```bash
python3 scripts/validate_week.py --week week_XX --mode task
```

如果你准备发布（并且已清空 QA 阻塞项），再跑：

```bash
python3 scripts/validate_week.py --week week_XX --mode release
```
