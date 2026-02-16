#!/usr/bin/env python3
"""Initialize a week_XX chapter-package directory with templates.

Usage:
    python3 scripts/new_week.py --week 01 --title "从数据到问题：你的第一份数据卡"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _common import normalize_week, repo_root, week_number


# ---------------------------------------------------------------------------
# File writing helpers
# ---------------------------------------------------------------------------

def _write_file(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _update_current_week(root: Path, week: str) -> None:
    (root / "chapters" / "current_week.txt").write_text(week + "\n", encoding="utf-8")


def _update_toc(root: Path, week: str, title: str) -> None:
    toc_path = root / "chapters" / "TOC.md"
    if not toc_path.exists():
        return

    n = week_number(week)
    lines = toc_path.read_text(encoding="utf-8").splitlines()
    # Old list format match
    old_re = re.compile(rf"^\s*-\s*\[{re.escape(week)}\]\(")
    # New table format match: "| 01 | [标题](week_01/CHAPTER.md) | ... |"
    table_re = re.compile(rf"^\|\s*{n:02d}\s*\|.*{re.escape(week)}/CHAPTER\.md")

    out: list[str] = []
    replaced = False
    for line in lines:
        if old_re.match(line):
            out.append(f"- [{week}]({week}/CHAPTER.md) {title}")
            replaced = True
        elif table_re.match(line):
            # Preserve description column (after the link column)
            parts = line.split("|")
            desc = parts[3].strip() if len(parts) > 3 else ""
            out.append(f"| {n:02d} | [{title}]({week}/CHAPTER.md) | {desc} |")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"- [{week}]({week}/CHAPTER.md) {title}")

    toc_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _update_syllabus_title(root: Path, week: str, title: str) -> None:
    syllabus_path = root / "chapters" / "SYLLABUS.md"
    if not syllabus_path.exists():
        return

    n = week_number(week)
    # Old format: "1. Week 01：标题"
    old_pat = re.compile(rf"^(\s*\d+\.\s*Week\s+{n:02d}\s*[:：])\s*(.+?)\s*$")
    # New heading format: "### Week 01：标题"
    new_pat = re.compile(rf"^(#{2,4}\s*Week\s+{n:02d}\s*[:：])\s*(.+?)\s*$")
    lines = syllabus_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    changed = False
    for line in lines:
        m = old_pat.match(line)
        if m:
            out.append(f"{m.group(1)} {title}")
            changed = True
        else:
            m = new_pat.match(line)
            if m:
                out.append(f"{m.group(1)} {title}")
                changed = True
            else:
                out.append(line)

    if changed:
        syllabus_path.write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Git/PR section generators
# ---------------------------------------------------------------------------

def _git_pr_sections(week: str) -> tuple[str, str]:
    n = week_number(week)

    pr_policy = (
        "- （可选/预告）了解 Gitea 的 Pull Request (PR) 流程：push 分支 -> 开 PR -> review -> merge。"
        if n <= 5
        else "- （必做）使用 Gitea 的 Pull Request (PR) 流程：分支 -> 多次提交 -> push -> 开 PR -> review -> merge。"
    )

    pr_checklist = (
        "\n".join(
            [
                "PR 清单（Week 06+ 必做；Week 01-05 可选）：",
                f"- 分支命名：`{week}/<topic>`（示例：`{week}/intro`）",
                "- 至少 2 次提交：draft + verify（便于复盘与回滚）",
                "- PR 描述引用本周 DoD，并粘贴验证命令输出（pytest/validate 通过）",
                "- review 后再 merge 到 `main`（或 `master`）",
            ]
        )
        if n >= 6
        else "\n".join(
            [
                "PR 预告（可选）：",
                "- 先学会 commit/diff/restore；如果你愿意，也可以提前练习：开分支 -> push -> 开 PR -> merge",
                "- Gitea PR 语义等价 GitHub PR（只是 UI 不同）",
            ]
        )
    )

    chapter_section = f"""## Git 本周要点

本周必会命令：
- `git status`
- `git diff`
- `git add -A`
- `git commit -m "draft: ..."`
- `git log --oneline -n 10`

Pull Request (PR)：
{pr_policy}
参考：`shared/gitea_workflow.md`

{pr_checklist}

"""

    assignment_section = f"""## Git/PR 提交流程（本周要求）

{pr_policy}

建议动作（不作为硬性闸门，但强烈建议遵守）：
- draft 阶段：先提交一次（`draft: ...`）
- verify 阶段：跑通测试后再提交一次（`test:` / `fix:` / `docs:`）
- 发布/合并前自检：
  - `git status --porcelain` 输出为空
  - `git log -n 5 --oneline` 能看到本周提交

{pr_checklist}

"""

    return chapter_section, assignment_section


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize chapters/week_XX scaffold.")
    parser.add_argument("--week", required=True, help="Week number (e.g. 06 or week_06)")
    parser.add_argument("--title", required=True, help="Week title (Chinese recommended)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing week files")
    args = parser.parse_args()

    root = repo_root()
    week = normalize_week(args.week)
    title = args.title.strip()
    if not title:
        print("error: --title cannot be empty", file=sys.stderr)
        return 2

    week_dir = root / "chapters" / week
    week_dir.mkdir(parents=True, exist_ok=True)
    (week_dir / "examples").mkdir(parents=True, exist_ok=True)
    (week_dir / "starter_code").mkdir(parents=True, exist_ok=True)
    (week_dir / "tests").mkdir(parents=True, exist_ok=True)

    chapter_git, assignment_git = _git_pr_sections(week)

    # Read SYLLABUS.md to find previous week info for "前情提要"
    n = week_number(week)
    prev_week_hint = ""
    if n > 1:
        prev_week = f"week_{n-1:02d}"
        prev_week_hint = f"""## 前情提要

上一周（{prev_week}）我们学习了……（请参考 `chapters/{prev_week}/CHAPTER.md` 的"本周小结"段落补充具体内容）。本周在此基础上继续。

"""

    agentic_md = f"""## 本周 Agentic 训练（必做）

你每周都要重复同一个交付循环，把"写代码"变成"可验证交付"：

1. Plan：用 1 句话写清本周目标 + DoD
2. Implement：小步实现（建议至少 2 次提交：draft + verify）
3. Verify：运行校验与测试（见下方命令）
4. Reflect：在 `QA_REPORT.md` 写 3 行复盘（卡点/定位方式/下次改进）

建议验证命令：

```bash
python3 scripts/validate_week.py --week {week} --mode release
python3 -m pytest chapters/{week}/tests -q
```

"""

    chapter_md = f"""# {week}：{title}

{prev_week_hint}## 学习目标

<!-- 写 3-5 条可验证、可考核的学习目标。示例：
- 能为一个数据集写出最小数据卡（来源/字段/缺失概览）
- 能用 pandas 计算并解释至少 2 个描述性统计量
- 能生成一个可复现的 `report.md` 片段，并说明结论边界
-->

## 先修要求

{"- 已具备基础 Python 能力（本课程不讲 Python 入门）" if n == 1 else f"- 已完成 week_{n-1:02d} 的学习目标"}
- 能运行 `pytest`（本书用它做自动验证）

## 本周 DoD（Definition of Done）

发布前必须满足 `CLAUDE.md` 的 DoD 条目，并通过：

```bash
python3 scripts/validate_week.py --week {week} --mode release
```

{agentic_md}

{chapter_git}

<!-- === 正文从这里开始 === -->

## TextAgent 进度

<!-- 本周对 TextAgent（全书贯穿项目：Agentic 文本分析系统）的改进。
     参考 shared/book_project.md 了解本周推进点。
     建议在 examples/ 里提供本周可运行的脚本/笔记，并能生成 report.md（或 report.md 的一部分）。
     必须在上周基础上增量修改。 -->

## 小结

<!-- 本周核心要点的 3-5 句话总结。同时供下一周的"前情提要"引用。 -->

## 本周小结（供下周参考）

<!-- 用 2-3 句话概括本周教了哪些核心概念和技能，供下一周的 chapter-writer 读取作为上下文。 -->

"""

    assignment_md = f"""# {week}：作业

## 提交物

- 修改 `starter_code/solution.py`
- 确保 `pytest` 通过：
  ```bash
  python3 -m pytest chapters/{week}/tests -q
  ```

## 验证（必做）

```bash
python3 scripts/validate_week.py --week {week} --mode release
python3 -m pytest chapters/{week}/tests -q
```

{assignment_git}

## 任务

### 基础

<!-- 1-2 个基础练习，对应本周核心知识点 -->

### 进阶

<!-- 1-2 个进阶练习，需要组合本周多个知识点 -->

### 挑战

<!-- 1 个挑战题，需要独立思考或查阅文档 -->

"""

    rubric_md = f"""# {week}：评分细则 (Rubric)

> 评分项必须可验证（tests 或 anchors 支撑）。

## 基础

<!-- 基础任务的评分标准 -->

## 进阶

<!-- 进阶任务的评分标准 -->

## 挑战

<!-- 挑战任务的评分标准 -->

"""

    qa_report_md = f"""# {week}：QA Report

## 阻塞项 (Blocking)

<!-- 空列表表示无阻塞。QA 审查后在此添加 checkbox 条目。
     格式：  - [ ] 问题描述    （解决后改为 - [x]） -->

## 建议项 (Suggestions)

<!-- 空列表表示无建议。 -->

## 状态

- [x] 初始化完成

"""

    anchors_yml = """# Evidence anchors for this week.
#
# Each item must contain:
# - id (unique within week)
# - claim
# - evidence
# - verification
#
# Example:
# - id: W06-A01
#   claim: ...
#   evidence: "CHAPTER.md#某小节"
#   verification: "pytest:tests/test_smoke.py::test_solution_import_and_solve_returns_str"
[]
"""

    terms_yml = f"""# New terms introduced in {week}.
#
# Each item must contain:
# - term_zh
# - term_en (optional)
# - definition_zh
# - first_seen (must be {week})
[]
"""

    solution_py = f'''"""
Starter code for {week}: {title}

Contract:
- Implement solve(text: str) -> str
- Treat ``text`` as the raw input (e.g., CSV/TSV text, or a short JSON string).
- Return a string that can be written to stdout (often a Markdown snippet/report).
- tests assert against this file only
"""
from __future__ import annotations


def solve(text: str) -> str:
    """Transform input text and return output text (often Markdown)."""

    # Default: identity transform (keeps smoke test passing).
    return text


def main() -> None:
    import sys

    data = sys.stdin.read()
    sys.stdout.write(solve(data))


if __name__ == "__main__":
    main()
'''

    example_placeholder_py = f'''"""
示例占位文件 — {week}: {title}

运行方式：python3 chapters/{week}/examples/00_placeholder.py
预期输出：Placeholder example for {week}.

请将此文件替换为本周的真实示例（由 ExampleEngineer 产出）。
"""
print("Placeholder example for {week}. Replace this file with real examples.")
'''

    test_smoke_py = f'''from __future__ import annotations

import importlib.util
from pathlib import Path


def test_solution_import_and_solve_returns_str() -> None:
    root = Path(__file__).resolve().parents[3]
    p = root / "chapters" / "{week}" / "starter_code" / "solution.py"
    assert p.exists(), f"missing solution.py: {{p}}"

    spec = importlib.util.spec_from_file_location("week_solution", p)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # type: ignore[union-attr]

    assert hasattr(m, "solve")
    out = m.solve("hello")  # type: ignore[attr-defined]
    assert isinstance(out, str)
'''

    written: list[Path] = []
    skipped: list[Path] = []
    try:
        for p, content in [
            (week_dir / "CHAPTER.md", chapter_md),
            (week_dir / "ASSIGNMENT.md", assignment_md),
            (week_dir / "RUBRIC.md", rubric_md),
            (week_dir / "QA_REPORT.md", qa_report_md),
            (week_dir / "ANCHORS.yml", anchors_yml),
            (week_dir / "TERMS.yml", terms_yml),
            (week_dir / "starter_code" / "solution.py", solution_py),
            (week_dir / "examples" / "00_placeholder.py", example_placeholder_py),
            (week_dir / "tests" / "test_smoke.py", test_smoke_py),
        ]:
            if _write_file(p, content, force=args.force):
                written.append(p)
            else:
                skipped.append(p)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    _update_current_week(root, week)
    _update_toc(root, week, title)
    _update_syllabus_title(root, week, title)

    print(f"[new-week] created/updated: chapters/{week}/")
    if written:
        print("[new-week] wrote files:")
        for p in written:
            print(f"- {p.relative_to(root)}")
    if skipped:
        print("[new-week] kept existing files:")
        for p in skipped:
            print(f"- {p.relative_to(root)}")
    print()
    print("Suggested agent team conventions:")
    print(f"- All task subjects MUST start with '[{week}]' (hooks rely on it).")
    print(f"- Example task subject: '[{week}] Write CHAPTER.md section 1'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
