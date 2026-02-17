---
name: draft-chapter
description: 生成本周正文：规划（含 Bloom/回顾桥/超级线/角色）→ 场景驱动写正文 → 深度润色 → 四维 QA → 修订回路 → 落盘 QA_REPORT。
argument-hint: "<week_id e.g. week_01>"
allowed-tools: Read, Write, Edit, Grep, Glob
disable-model-invocation: true
---

# /draft-chapter

## 用法

```
/draft-chapter week_XX
```

## 目标

- `CHAPTER.md`：叙事流畅、有贯穿案例 + TextAgent 超级线、循环角色出场、回顾桥达标、读起来像真人教材（不是模板填空）
- `QA_REPORT.md`：写入 StudentQA 的四维评分 + 阻塞项/建议项

## 核心原则

**写作质量是第一优先级。** 通过验证是必要条件，但不是充分条件。一篇通过了所有检查但读起来像模板的文章，仍然是失败的交付。

## 步骤（按顺序）

### 第 0 步：日期校准（立即执行）

生成 `shared/current_date.txt`，供后续所有 agent 读取当前日期：

```bash
date '+%Y-%m-%d' > shared/current_date.txt
```

这确保时代脉搏、AI 小专栏、参考链接中的日期使用当前年份，不会因模型训练数据截止日期而过时。

### 第 1 步：规划结构 + 贯穿案例 + 认知负荷 + 超级线 + 角色

调用 subagent `syllabus-planner`：

- 产出章节结构（小节标题 + 每节学习目标 + Bloom 层次）
- **必须设计本章的贯穿案例**：一个渐进式小项目，每节推进一步，章末可运行
- **必须规划 2 个 AI 小专栏的位置和主题**（第 1 个在前段，第 2 个在中段；含建议搜索词）
- **必须做认知负荷检查**：新概念数在预算内，回顾桥设计达标
- **必须规划 TextAgent 超级线推进**
- **必须规划循环角色出场位置**
- **必须规划章首导入**：选择一句与本章主题相关的引言格言，并草拟时代脉搏段落的方向
- 写入 `chapters/week_XX/CHAPTER.md`
- **所有规划元数据必须用 `<!-- ... -->` HTML 注释包裹**（Bloom 标注、概念预算表、AI 专栏规划、角色出场规划、章节结构骨架等）

### 第 1.5 步：Context7 技术查证

在写正文之前，使用 **Context7 MCP** 查证本章涉及的统计/数据分析相关库的最佳实践（pandas、scipy、statsmodels、scikit-learn 等）：

1. 从第 1 步的规划中提取本章涉及的库与关键 API
2. 调用 `resolve-library-id` 定位相关库（如 `pandas`、`scikit-learn` 等）
3. 调用 `query-docs` 查询具体的最佳实践和 API 用法
4. 将查证结果传递给第 2 步的 chapter-writer，确保代码示例符合当前最佳实践（尤其是避免数据泄漏、保证可复现）

**搜索工具分工**：
- **Context7**：查证官方文档 API 用法（标准答案）
- **Exa Code Context**：搜索真实项目代码示例（社区实践）
- 两者互补，确保代码既正确又实用

### 第 2 步：场景驱动写正文

调用 subagent `chapter-writer`：

- **必须先读 `shared/writing_exemplars.md` + `shared/characters.yml`**
- **必须写章首导入**：在章标题之后、学习目标之前写入引言格言 + 时代脉搏段落（200-300 字，场景化引入 AI/技术趋势与本章关联）。详见 `shared/style_guide.md` 的"章首导入"章节
- **必须基于第 1.5 步的 Context7 查证结果**确保代码示例使用当前最佳实践
- 以贯穿案例为主线，用"场景 → 困惑 → 解法 → 深化"的叙事弧线写每一节
- 使用循环角色（小北/阿码/老潘）增强代入感，每章至少 2 次出场
- 写回顾桥：在新场景中自然引用前几周概念
- 写 TextAgent 进度小节
- 严禁所有节使用相同的子标题模式
- 严禁用 bullet list 堆砌做小结
- **所有写作元数据（每节的 Bloom/叙事入口/建议示例等）必须用 `<!-- ... -->` 注释包裹**

### 第 2.5 步：联网研究收集（Lead agent 亲自执行）

**由你（Lead agent）直接执行**，不委派给 subagent。为第 3 步的 prose-polisher 准备搜索数据。

1. 从 CHAPTER.md 的 HTML 注释中提取 2 个 AI 小专栏的主题和建议搜索词
2. 读取 `shared/current_date.txt` 获取当前日期
3. 使用搜索工具收集数据（每个侧栏 2-3 次搜索）：

   **优先级 1: WebSearch**（内置搜索，最可靠）
   ```
   WebSearch("GitHub Copilot adoption statistics 2026")
   ```

   **优先级 2: Exa MCP**（AI 增强搜索，适合深度研究）
   ```
   mcp__exa__web_search_exa({
     "query": "GitHub Copilot adoption statistics 2026",
     "numResults": 5,
     "type": "auto"
   })
   mcp__exa__company_research_exa({
     "companyName": "OpenAI",
     "numResults": 3
   })
   ```

   **优先级 3: perplexity MCP**（如可用）
   ```
   mcp__perplexity__perplexity_search({
     "query": "vibe coding trend AI programming 2026",
     "recency": "year",
     "response_format": "json"
   })
   ```

   - 搜索关键词中必须包含当前年份
   - 同时搜索时代脉搏段落需要的素材

4. 将所有搜索结果写入 `chapters/week_XX/.research_cache.md`（含事实、URL、访问日期）

### 第 3 步：深度润色 + AI 小专栏

调用 subagent `prose-polisher`：

- **必须先读 `shared/writing_exemplars.md` + `shared/characters.yml`**
- 执行诊断清单 + 趣味性诊断清单，判断需要哪个级别的改写
- 检查角色一致性（对照 `shared/characters.yml`）
- 可做结构性重组（不仅仅是换词）
- **必须插入 2 个 AI 时代小专栏**：
  - 按 `syllabus-planner` 规划的位置和主题插入
  - **优先读取 `chapters/week_XX/.research_cache.md`** 中的预搜索数据和真实 URL
  - 如果缓存数据不足，**可以补充搜索**（WebSearch/Exa MCP），并将新结果**追加写入缓存文件**
  - **绝对禁止编造参考链接**：所有 URL 必须来自搜索工具或研究缓存。搜索失败时写 `<!-- TODO -->` 占位，不得伪造
  - 位置硬约束：一个在前段、一个在中段，禁止全堆章末

### 第 3.5 步：图片与公式补充（根据诊断执行）

如果 student-qa 诊断指出需要图片或公式：

**图片生成** → 调用 `/stat-viz` skill：
```
skill: "stat-viz"
args: "week_XX"
```

**关键要求**：
- ✅ 代码**必须**保存到 `examples/NN_chart_xxx.py`（可复现）
- ✅ 图片输出到 `images/xxx.png`（嵌入正文）
- ✅ 使用正确的中文字体配置
- ✅ 避免常见错误（截断 Y 轴、3D 效果等）

**公式补充** → 直接编辑 CHAPTER.md：
- 使用 LaTeX 格式：`$$公式$$`（块级）或 `$公式$`（行内）
- 块级公式用引用块包裹：`> $$...$$`
- 每个符号都要解释含义

### 第 4 步：学生视角四维审读

调用 subagent `student-qa`：

- 只读审读，输出四维评分 + 问题清单
- 四维评分：叙事流畅度 / 趣味性 / 知识覆盖 / 认知负荷（各 1-5 分）
- 总分 >= 18/20 才能通过

### 第 5 步：修订回路（简化版：2 档处理，有硬性迭代上限）

**修订回路规则**：

| 总分范围 | 处理方式 | 回传给谁 |
|---------|---------|---------|
| >= 18 | 根据 QA 反馈进行轻量修订后通过 | `prose-polisher`（轻量修复，处理建议项） |
| < 18 | 结构性重写（需大幅改进） | `chapter-writer` |

**迭代计数规则（防止无限循环）：**

1. 维护一个变量 `revision_round`，初始值为 0。
2. 每次进入修订回路（回传给 polisher/writer/planner），`revision_round += 1`。
3. **`revision_round` 达到 3 时，强制停止修订回路**：
   - 不再回传修订，直接进入第 6 步落盘。
   - 在 QA_REPORT.md 中标注：`<!-- 修订回路已达上限（3 轮），以下问题需人工介入 -->`
   - 未解决的阻塞项保留为 `- [ ]` 但添加注释说明已尝试 3 轮修订。
4. 如果第 1 轮修订后总分 >= 18 且无阻塞项，跳过后续轮次，直接进入第 6 步。

### 第 6 步：落盘 QA_REPORT

把最终的 StudentQA 输出落盘到 `chapters/week_XX/QA_REPORT.md`：

- 四维评分写在顶部（标注是第几轮评分）
- 阻塞项放到"## 阻塞项"下（checkbox）
- 建议项放到"## 建议项"下（checkbox）
- 如果经过修订回路，记录每轮评分变化（例如 `第 1 轮：14/20 → 第 2 轮：17/20`）
