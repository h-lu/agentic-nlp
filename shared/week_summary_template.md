# 周间上下文传递约定

## 目的

让编写下一周内容的 Agent（尤其是 chapter-writer）能快速了解"上一周教了什么"，
避免内容重复或跳跃。

## 约定

每周 `CHAPTER.md` 末尾应包含以下段落：

```markdown
## 本周小结（供下周参考）

<!-- 用 2-3 句话概括本周教了哪些核心概念和技能。
     下一周的 chapter-writer 会读取此段作为写作上下文。 -->
```

## 使用方式

- **chapter-writer** 在开始写 week_XX 时，先读 `chapters/week_{XX-1}/CHAPTER.md` 的
  "本周小结（供下周参考）" 段落。
- 如果上一周该段落不存在或为空，则读取 `chapters/SYLLABUS.md` 中对应周的描述作为
  替代上下文。
- **prose-polisher** 在润色时应保留该段落（不要删除或大幅改写）。
