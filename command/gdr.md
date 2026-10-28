---
description: 按 是什么: / 能干什么: / 解决: / 何时选: 四段标签格式批量重写 GitHub 用户名下所有仓库的 description（owner 缺省为当前认证账号，单行 ≤150 字符）。流程：API 拉数据 → 宿主 LLM 生成新描述 → dry-run → 批量 PATCH。
---

使用 github-desc-rewriter skill，按其 SKILL.md 的流程执行：

1. 调 `scripts/list_repos.py --owner <owner>` 拉仓库清单到 `/tmp/<owner>_repos.json`（owner 缺省为当前认证账号：`$GITHUB_USER`，否则 `gh api user`）。
2. **宿主 LLM 介入**：逐个仓库按 `templates/format.md`（= SKILL.md 阶段 2）的格式生成新描述，格式为 `是什么: X | 能干什么: Y | 解决: Z | 何时选: W`，**四个标签齐全**、**不加语言前缀**、**总长 ≤ 150 字符**（硬上限 350），写入 `/tmp/<owner>_new_descs.json`。**不读 README**，只根据仓库名 + 当前 description + language + topics 推断。同类仓库复用同一模板。
3. **dry-run**：调 `scripts/apply_descs.py ... --dry-run` 打印前 10 条改动 + 格式校验结果，宿主 LLM 自检（四段标签齐全、总长 ≤150、无换行/emoji），不合格的**先修好再继续**。
4. **真执行**：去掉 `--dry-run`，跑 `scripts/apply_descs.py` 完成批量 PATCH（≤150 目标 / 350 硬截断、旧描述自动备份、API 422/5xx 自动重试、单批 25 个 sleep 0.3s）。
5. 报告：成功 N / 失败 M / 跳过 K + 备份文件路径。

Owner 参数：`$ARGUMENTS`（空格分隔，最后一个 token 若是合法 GitHub username 就用，否则缺省为当前认证账号）。
