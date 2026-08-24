# 🤖 Codex 理论分析 SOP

本 SOP 用于把深度对话或已发布案例提炼为理论层内容。它适用于 `/theory-new`、`/theory-extract`、`/theory-update {id}`，以及“总结一下”“写成知识文章”等自然语言请求。

## 1. 对话收集

对话不设轮次上限。Codex 围绕核心观点、支撑证据、适用场景、不适用场景、前提条件和反例追问；每三轮或出现关键结论时，先给出当前理解摘要，避免把推测当作用户立场。

退出条件是用户要求记录、提炼或写成文章，或输入 `/theory-extract`。进入发布前，用户必须确认核心观点、证据和适用边界可以公开。

## 2. 观点结构

每篇文章至少包含：

1. 一句话核心观点；
2. 事实、案例或来源支撑；
3. 推理过程；
4. 适用与不适用场景；
5. 前提、反例和不确定性；
6. 与案例、Demo、工具或外部资源的关联。

文章必须显式区分“事实”“推断”“观点”。多个相互独立的观点拆成独立文章；未确认的信息写 `[待补充]`。

## 3. 路由规则

| 内容性质 | 目标仓库 |
|---|---|
| 学习顺序、能力模型、练习路径 | `goldentellus-roadmap` |
| 原理、方法论、角色工作法 | `goldentellus-knowledge` |
| 已核实的外部工具、框架、文章、课程或社区 | `awesome-fde` |
| 多来源支撑的行业判断、简报或复盘 | `goldentellus-reports` |

知识文章按现有角色目录写入；全员通识进入 `00-pipeline-fundamentals`，跨角色方法进入 `99-general`。发布前先查重，重复时优先更新原文而不是建立平行条目。

## 4. 发布与关联

发布前，Codex 展示目标文件、内容分类、关联案例和外部来源。确认后直接提交到 `main`，例如 `feat(knowledge): add K-data-003 RAG 分块策略`。

若文章引用案例，在文章 `related_cases` 中记录案例 ID，并在案例的 `related_knowledge` 中补充文章 ID。推送前先运行知识文章 frontmatter 校验，再对两个工作副本运行 `scripts/validate_content_links.py --cases <cases-path> --knowledge <knowledge-path>`。只有两边都校验通过时才报告关联完成。发布后创建不含敏感信息的“内容排期”Project 卡片并设为“已发布”。
