---
name: team-week
description: 完整执行一周章包的 6 阶段流水线：规划 → 写作 → 润色 → 并行产出 → QA → 收敛发布。
argument-hint: "<week_id e.g. week_01>"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task
---

# /team-week

## 用法

```
/team-week week_XX
```

## 目标

**直接执行完整的 6 阶段流水线**，把 week_XX 从零产出为完整章包，并通过 release 校验：

```bash
python3 scripts/validate_week.py --week week_XX --mode release
```

## 全局约束（贯穿所有阶段）

- 交付遵循 `CLAUDE.md` + `shared/style_guide.md`
- **所有写正文的 subagent 必须先读 `shared/writing_exemplars.md` + `shared/characters.yml`**
- **ANCHORS.yml 由阶段 6（收敛阶段）统一管理**：其他阶段如有 anchor 建议，在输出中标注即可，不直接写 ANCHORS.yml
- **一致性处理由 consistency-editor 执行**：阶段 5 的术语同步、格式检查、角色一致性问题由 consistency-editor 完成

### 写作质量红线（四维评分体系）

- student-qa 四维评分总分必须 >= 18/20
  - 叙事流畅度 >= 3 / 趣味性 >= 3 / 知识覆盖 >= 3 / 认知负荷 >= 3
- 任一维度 <= 2 = 阻塞项
- 禁止每节都用相同的子标题模式
- 每章必须有贯穿案例（渐进式分析任务）+ TextAgent 超级线推进
- 循环角色（小北/阿码/老潘）每章至少出场 2 次
- 新概念数不超预算，回顾桥数量达标
- 禁止连续 6+ 条 bullet list；小结不能全部用 bullet list
- **AI 小专栏必须 2 个，分别在前段和中段**（禁止全堆章末）；Lead agent 在 Stage 2.5 预先搜索素材写入 `.research_cache.md`，prose-polisher 优先读取缓存，不足时用自身的 **WebSearch** 补充搜索。**绝对禁止编造参考链接**——搜索失败时写 `<!-- TODO -->` 占位
- **章首导入必须包含引言格言 + 时代脉搏段落**（详见 `shared/style_guide.md`）
- **所有写作元数据必须用 HTML 注释包裹**，不能出现在渲染正文中
- **写作前必须使用 Context7 MCP 查证本章技术点的当前最佳实践**

---

## 流水线阶段（严格按顺序执行）

```
阶段 0（日期校准） → 阶段 1（规划） → 阶段 2（写作） → 阶段 2.5（联网研究）
  → 阶段 3（润色） → 阶段 4（并行产出） → 阶段 5（QA） → 阶段 6（收敛）
```

### 阶段 0：日期校准（流水线启动时立即执行）

生成 `shared/current_date.txt`，供后续所有 agent 读取当前日期：

```bash
date '+%Y-%m-%d' > shared/current_date.txt
echo "当前日期已写入 shared/current_date.txt: $(cat shared/current_date.txt)"
```

**为什么需要这一步**：时代脉搏、AI 小专栏、参考链接的访问日期都需要使用当前年份。如果不显式注入日期，agent 可能使用训练数据中的旧年份。

**校验**：确认 `shared/current_date.txt` 存在且内容为当天日期。

---

### 阶段 1：规划（前置：阶段 0 完成）

调用 subagent `syllabus-planner`：

- 产出章节结构（小节标题 + 每节学习目标 + Bloom 层次）
- 设计本章贯穿案例（渐进式小项目）
- 规划 2 个 AI 小专栏的位置和主题（第 1 个在前段，第 2 个在中段；含建议搜索词）
- 做认知负荷检查：新概念数在预算内，回顾桥设计达标
- 规划 TextAgent 超级线推进
- 规划循环角色出场位置
- **规划章首导入**：选择引言格言、草拟时代脉搏段落方向
- 产出写入 `chapters/week_XX/CHAPTER.md`（大纲阶段）
- **所有规划元数据必须用 `<!-- ... -->` HTML 注释包裹**（Bloom 标注、概念预算表、AI 专栏规划、角色出场规划、章节结构骨架等，不能渲染为正文）

**校验**：无需校验（规划阶段，ASSIGNMENT 等文件不存在是正常的）

### 阶段 1.5：Context7 技术查证（前置：阶段 1 完成）

在写正文之前，使用 **Context7 MCP** 查证本章涉及的 Python 官方文档和 API 最佳实践：

1. 从阶段 1 的规划中提取本章涉及的 Python 特性、标准库模块、第三方库
2. 调用 `resolve-library-id` 定位相关库（如 `python`、`pytest`、`argparse` 等）
3. 调用 `query-docs` 查询具体的最佳实践和 API 用法
4. 将查证结果作为上下文传递给阶段 2 的 chapter-writer

**搜索工具分工说明**：
- **Context7**：仅用于查证 Python/库的官方文档 API 用法和最佳实践
- **Exa Code Context** (`mcp__exa__get_code_context_exa`)：用于搜索真实项目中的代码示例和社区实践
- 两者互补：Context7 提供官方标准，Exa 提供社区真实用法

**校验**：无需校验

### 阶段 2：写作（前置：阶段 1.5 完成）

调用 subagent `chapter-writer`：

- **必须先读 `shared/writing_exemplars.md` + `shared/characters.yml`**
- **必须写章首导入**：在章标题之后、学习目标之前，写入引言格言 + 时代脉搏段落（200-300 字）。详见 `shared/style_guide.md` 的"章首导入"章节
- **必须基于阶段 1.5 的 Context7 查证结果**确保代码示例使用当前 Python 最佳实践
- 以贯穿案例为主线，用"场景 → 困惑 → 解法 → 深化"的叙事弧线写每一节
- 使用循环角色增强代入感，每章至少 2 次出场
- 写回顾桥：在新场景中自然引用前几周概念
- 写 TextAgent 进度小节
- 严禁所有节使用相同子标题模式；严禁 bullet list 堆砌做小结
- **所有写作元数据必须用 `<!-- ... -->` 注释包裹**，不能出现在渲染正文中

**校验**：

```bash
python3 scripts/validate_week.py --week week_XX --mode drafting
```

### 阶段 2.5：联网研究收集（前置：阶段 2 完成，Lead agent 亲自执行）

**由 Lead agent 直接执行**（不委派给 subagent），因为 Lead 拥有全部搜索工具。

目的：为阶段 3 的 prose-polisher 提供真实的搜索数据和参考链接，避免 AI 小专栏使用 TODO 占位。

1. **读取阶段 1 的 AI 小专栏规划**：从 CHAPTER.md 的 HTML 注释中提取 2 个侧栏的主题和建议搜索词
2. **读取 `shared/current_date.txt`** 获取当前日期，搜索关键词中包含当前年份
3. **执行搜索**（每个侧栏 2-3 次搜索）：

   ```
   # 优先级 1: 内置 WebSearch（最可靠，无外部依赖）
   WebSearch("GitHub Copilot adoption statistics 2026")
   WebSearch("Python popularity TIOBE index 2026")

   # 优先级 2: Exa MCP（AI 增强搜索，适合深度研究）
   mcp__exa__web_search_exa({
     "query": "GitHub Copilot adoption statistics 2026",
     "numResults": 5,
     "type": "auto"
   })
   mcp__exa__company_research_exa({
     "companyName": "OpenAI",
     "numResults": 3
   })

   # 优先级 3: perplexity MCP（如可用）
   mcp__perplexity__perplexity_search({
     "query": "vibe coding trend AI programming 2026",
     "recency": "year",
     "response_format": "json"
   })
   ```

4. **收集时代脉搏素材**：搜索与本章主题相关的最新 AI/技术事件
5. **将搜索结果写入缓存文件** `chapters/week_XX/.research_cache.md`：

   ```markdown
   # Week XX 研究缓存
   生成日期：YYYY-MM-DD

   ## 时代脉搏素材
   ### 搜索词: "..."
   - 事实: ... (来源: https://真实URL)

   ## AI 小专栏 #1: {主题}
   ### 搜索词: "..."
   - 数据点: ... (来源: https://真实URL)
   - 引用: "..." (来源: https://真实URL)

   ## AI 小专栏 #2: {主题}
   ### 搜索词: "..."
   - 数据点: ... (来源: https://真实URL)
   ```

**校验**：确认 `.research_cache.md` 存在且至少包含 2 个侧栏的搜索数据。

---

### 阶段 3：润色（前置：阶段 2.5 完成）

调用 subagent `prose-polisher`：

- **必须先读 `shared/writing_exemplars.md` + `shared/characters.yml`**
- 执行诊断清单 + 趣味性诊断清单，判断改写级别
- 检查角色一致性（对照 `shared/characters.yml`）
- 可做结构性重组
- **必须插入 2 个 AI 时代小专栏**（按阶段 1 规划的位置和主题）：
  - **优先读取 `chapters/week_XX/.research_cache.md`** 中的搜索数据和参考链接
  - 如果缓存数据不足，**可以补充搜索**（WebSearch/Exa MCP），并将新结果**追加写入缓存文件**
  - 用 **WebFetch** 验证关键 URL 是否可访问
  - **绝对禁止编造 URL**——搜索失败时才写 `<!-- TODO -->` 占位

**校验**：

```bash
python3 scripts/validate_week.py --week week_XX --mode drafting
```

### 阶段 4：并行产出（前置：阶段 3 完成，以下四个可并行）

同时调用以下 4 个 subagent（**可以并行**）：

1. **`example-engineer`**：产出 `examples/` + TextAgent 示例代码 + 讲解段落
2. **`test-designer`**：产出 `tests/` pytest 用例矩阵
3. **`exercise-factory`**：产出 `ASSIGNMENT.md` + `RUBRIC.md` + AI 协作练习
4. **图片生成**（如 student-qa 诊断需要）：调用 `/stat-viz` skill 生成图表

**图片生成判断**（根据 student-qa 阶段 5 的诊断结果）：
- 如果本章涉及分布/比较/关系/评估类主题，需要图片
- 调用方式：`Skill("stat-viz", "week_XX")`
- 代码保存到 `examples/NN_chart_xxx.py`，图片输出到 `images/`

**校验**（四个全部完成后执行）：

```bash
python3 scripts/validate_week.py --week week_XX --mode idle
```

### 阶段 5：QA（前置：阶段 4 全部完成）

执行完整的三维度 QA 审读（与 `/qa-week` 共享相同流程）。

#### 5a. 并行审读（一致性 + 技术正确性）

同时启动以下两个 agent（可并行）：

1. **`consistency-editor`**：
   - 修复格式/术语/角色一致性
   - 同步 `TERMS.yml` -> `shared/glossary.yml`
   - 检查循环角色使用（对照 `shared/characters.yml`）
   - 修复 `ANCHORS.yml` 问题（依赖 `validate_week.py` 报错定位）
   - **可直接修改文件**

2. **`technical-reviewer`**：
   - 审读概念/公式/代码/答案正确性
   - 检查教学法对齐（目标/递进/示例-练习）
   - 检查练习题质量（可评分/难度梯度）
   - **只读，输出问题清单（含 S1-S4 Severity 分级）**

#### 5b. 收集结果

- 等待 5a 的两个 agent 完成
- 收集 `technical-reviewer` 的问题清单（含 S1/S2 致命问题）

#### 5c. 学生视角审读

调用 **`student-qa`**：

- **传入 technical-reviewer 发现的 S1/S2 问题摘要**
- 基于修复后的文件进行审读
- 输出四维评分（叙事流畅度/趣味性/知识覆盖/认知负荷）
- 如有 S1 错误，在"知识覆盖"维度标注扣分原因
- **只读，通过 tool result 返回评分和清单**

**重要**：student-qa 是只读角色（tools: [Read, Grep, Glob]，无 Write 权限），**不要让它写 QA_REPORT.md**。

**校验**：无（QA 是只读角色）

### 阶段 6：收敛（前置：阶段 5 完成，序列执行）

#### 6a. 修订回路

**优先处理 S1/S2 技术审读问题**：

| 问题级别 | 处理方式 | 回传给谁 |
|---------|---------|---------|
| S1 致命 | 必须修复，否则不能 release | `chapter-writer` 或 `example-engineer`（视问题类型） |
| S2 重要 | 强烈建议修复 | `prose-polisher` |

**四维评分处理**：

| 总分范围 | 处理方式 | 回传给谁 |
|---------|---------|---------|
| >= 18 | 根据 QA 反馈进行轻量修订后通过 | `prose-polisher`（轻量修复，处理建议项） |
| < 18 | 结构性重写（需大幅改进） | `chapter-writer` |

**修订规则说明**：
- **S1 问题必须先于四维评分处理**：即使总分 >= 18，有 S1 问题也不能进入 release
- 无论评分高低，每轮 QA 后都需根据反馈进行一轮修订（即使是 >= 18 分的建议项也要处理）
- 修订后如无阻塞项且质量达标，即可进入 release
- **硬性上限：最多迭代 3 轮。** 如果 3 轮后总分仍 < 18 或仍有 S1 问题：
1. 在 QA_REPORT.md 记录当前评分和未解决问题
2. 标注 `<!-- 需人工介入 -->`
3. 继续推进到 6b（不再回传修订）

#### 6b. 落盘 QA_REPORT + Release 校验

**一致性处理已在阶段 5a 由 consistency-editor 完成**，此处无需重复。

**落盘 QA_REPORT（由 Lead agent 直接写入）**：

- 汇总阶段 5 的所有审读结果，写入 `chapters/week_XX/QA_REPORT.md`
- 格式如下：

```markdown
# QA Report: week_XX

## 四维评分

| 维度 | 分数 | 说明 |
|------|------|------|
| 叙事流畅度 | X/5 | ... |
| 趣味性 | X/5 | ... |
| 知识覆盖 | X/5 | ... |
| 认知负荷 | X/5 | ... |
| **总分** | **XX/20** | |

## 技术审读问题

### S1 致命（必须修复）
- [ ] {问题描述} — `CHAPTER.md#xxx`

### S2 重要（强烈建议修复）
- [ ] {问题描述} — `CHAPTER.md#xxx`

## 阻塞项

- [ ] {问题描述} — {位置}

## 建议项

- [ ] {问题描述} — {位置}

## 教学法建议
{technical-reviewer 的教学法建议}

## 审读记录
- consistency-editor: 已修复 X 处一致性问题
- technical-reviewer: 发现 X 个问题（S1: X, S2: X, S3: X, S4: X）
- student-qa: 四维评分 XX/20
```

**如有 S1/S2 问题**：
- 标注需回传 `chapter-writer` 或 `prose-polisher` 修复
- 修复后需重新运行阶段 5 的审读

- 调用 subagent `error-fixer`（如果校验有报错）：逐条修复再验证

- 最终 release 校验：

```bash
python3 scripts/validate_week.py --week week_XX --mode release
```

---

## 校验模式速查（简化后：3 种模式）

| 阶段 | 校验模式 | 说明 |
|------|---------|------|
| 阶段 1（规划） | 无 | ASSIGNMENT 等文件不存在是正常的 |
| 阶段 2-3（写作/润色） | `--mode drafting` | 只检查 CHAPTER.md + TERMS.yml（如果存在）|
| 阶段 4-5（产出/QA） | `--mode idle` | 所有文件 + QA 阻塞项检查，无 pytest |
| 阶段 6（收敛） | `--mode release` | 完整发布级校验（含 pytest + pedagogical 检查）|

## 收敛规则

- QA_REPORT 的"阻塞项"必须清零（不允许 `- [ ]`）才能 release
- **S1 致命问题必须清零**才能 release
- 四维评分总分必须 >= 18/20 才能 release（或 3 轮修订后人工豁免）
- 不要为了"写完"牺牲可运行/可验证：tests/anchors/terms 要能对上
