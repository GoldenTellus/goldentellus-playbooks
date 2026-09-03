# Codex 内容生产指令速查

本页定义 GoldenTellus 仓库管理 Agent 的聊天入口。它不是独立 CLI；同义的自然语言请求按相同流程处理。

## 指令

| 指令 | 用途 | 完成条件 |
|---|---|---|
| `/case-new` | 开始案例拆解 | 素材、脱敏和发布范围满足案例 SOP |
| `/case-update {id}` | 更新既有案例 | 只追加或更新已确认内容，不删除既有内容 |
| `/case-status` | 查看当前案例进度 | 展示已收集信息、待补充项和预定路由 |
| `/theory-new` | 开始理论或案例学习讨论 | 已形成可讨论的核心观点或岗位学习问题 |
| `/theory-extract` | 从当前对话或案例提炼知识 | 观点、论据与边界经用户确认；案例学习须关联已授权案例 |
| `/theory-update {id}` | 更新既有知识文章 | 优先处理查重后的既有条目 |
| `/theory-status` | 查看当前知识提炼进度 | 展示观点、证据、边界、内容类型和目标目录 |
| `/link {case-id} {knowledge-id}` | 建立案例与知识文章关联 | 两侧 frontmatter 和链接均校验通过 |
| `/skip` | 跳过当前建议 | 不影响已发布内容 |
| `/pipeline-status` | 查看内容资产总览 | 汇总各仓库公开内容与待补充项 |

## 发布前确认清单

1. 展示本次目标仓库、文件路径、分类、关联关系和 `[待补充]` 项。
2. 案例必须确认授权、脱敏和公开范围；理论与案例学习必须确认观点、证据和边界可公开。
3. 执行目标仓库已有的 frontmatter、链接、构建或格式检查。
4. 获得本次发布确认后，分别直接提交到各仓库的 `main`；不创建 Pull Request。

## 提交信息

| 仓库 | 格式 |
|---|---|
| `goldentellus-cases` | `feat(cases): add CASE-<编号> <标题>` |
| `goldentellus-labs` | `feat(labs): add <资产名>` |
| `goldentellus-playbooks` | `feat(playbooks): add <主题>` |
| `goldentellus-knowledge` | `feat(knowledge): add K-<角色>-<编号> <标题>` |
| `awesome-fde` | `feat(awesome-fde): add <名称>` |
| `goldentellus-reports` | `feat(reports): add insight <标题>` |

GitHub Labels 只能附着在 Issue 或 Pull Request，不能附着在提交上。内容分类以 frontmatter 和索引为准。
