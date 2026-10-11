---
description: 按 * / * / 解决：* / 何时选：* 格式批量重写 GitHub 用户名下所有仓库的 description（owner 缺省 mcgrapeng）。流程：API 拉数据 → 宿主 LLM 生成新描述 → dry-run → 批量 PATCH。
---

使用 github-desc-rewriter skill，按其 SKILL.md 的流程执行：

1. 调 `scripts/list_repos.py --owner <owner>` 拉仓库清单到 `/tmp/<owner>_repos.json`（owner 缺省 `mcgrapeng`）。
2. **宿主 LLM 介入**：逐个仓库按 `templates/format.md`（= SKILL.md 阶段 2）的格式生成新描述，格式为 `是什么 / 能干什么 / 解决什么问题 — 用户痛点 / 何时选它 — 决策建议`，**不加语言前缀**、**总长目标 300 字左右**（硬上限 350），写入 `/tmp/<owner>_new_descs.json`。**不读 README**，只根据仓库名 + 当前 description + language + topics 推断。同类仓库复用同一模板。
3. **dry-run**：调 `scripts/apply_descs.py ... --dry-run` 打印前 10 条改动，让宿主 LLM 自检（不要让用户审核）。
4. **真执行**：去掉 `--dry-run`，跑 `scripts/apply_descs.py` 完成批量 PATCH（≤ 350 字符硬截断、API 422/5xx 自动重试、单批 25 个 sleep 0.3s）。
5. 报告：成功 N / 失败 M / 跳过 K。

Owner 参数：`$ARGUMENTS`（空格分隔，最后一个 token 若是合法 GitHub username 就用，否则缺省 mcgrapeng）。
