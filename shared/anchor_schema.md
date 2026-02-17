# ANCHORS.yml 规范（证据锚点）

## 目的

把“教材里的主张”变成可验证的证据链，降低幻觉与不可复现结论。

## 文件位置

每周：`chapters/week_XX/ANCHORS.yml`

## 字段

每条锚点是一个 YAML mapping，必须包含：

- `id`：周内唯一（推荐格式 `W06-A01`）
- `claim`：一句话主张（教材里真正想让学生相信的结论）
- `evidence`：证据指向（文件路径/段落标题/测试名/命令输出等）
- `verification`：可执行验证方式

## verification 推荐格式

为便于脚本静态校验，建议使用以下之一：

- `pytest:tests/test_smoke.py::test_solution_import_and_solve_returns_str`
- `cmd:python3 -m pytest chapters/week_XX/tests -q`
- `cmd:python3 scripts/validate_week.py --week week_XX --mode release`

脚本会对 `pytest:` 的 nodeid 做“文件存在”检查（路径可相对 `week_XX/` 或项目根目录）。
