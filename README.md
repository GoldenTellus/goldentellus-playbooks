# 📋 goldentellus-playbooks

流水线角色 SOP、阶段交接协议、项目模板和检查清单。

## 🗺️ 三句话导航

> 这是什么：让流水线可以重复协作的操作手册。
>
> 上一个：`goldentellus-knowledge` -> **当前** -> 下一个：`goldentellus-community`
>
> 我应该看：先读交接协议，再选择项目模板。

## 🗂️ 目录

- `role-playbooks/`
- `collaboration/`
- `document-templates/`
- `checklists/`
- `sops/`

## 🤖 Codex 内容生产

- [案例拆解 SOP](./sops/codex-case-pipeline.md)
- [理论分析 SOP](./sops/codex-theory-pipeline.md)
- [指令与提交速查](./sops/codex-command-reference.md)
- [理论文章模板](./document-templates/theory-article-template.md)
- [案例 Frontmatter 模板](./document-templates/case-frontmatter.yml)
- [知识文章 Frontmatter 模板](./document-templates/knowledge-frontmatter.yml)

案例正文、知识文章和 Demo 的实际模板分别以对应目标仓库为准。本仓库只维护跨仓库的流程、边界与写作规范。

## 🔎 发布前关联校验

当案例和知识文章有相互引用时，在推送前对两个本地工作副本运行：

```bash
python scripts/validate_content_links.py --cases ../goldentellus-cases --knowledge ../goldentellus-knowledge
```

该检查会验证案例和知识文章 ID 是否重复、`related_knowledge` 与 `related_cases` 是否双向一致，以及 Markdown 本地链接是否存在。组织级工作流会每 6 小时和手动触发时复核；它用于发现跨仓库不一致，不能替代推送前检查。
