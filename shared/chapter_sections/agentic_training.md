<!-- 每周 CHAPTER.md 中可引用此段。Agent 展开时直接复制并替换 {week} 占位符。 -->

## 本周 Agentic 训练（必做）

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
