# 个人博客

这是一个零前端依赖的 Markdown 静态博客。你只需要写 Markdown，运行一个 Python 脚本即可生成网页。

## 修改个人信息

编辑 `site.config.json`：

- `title`：博客名称
- `description`：首页简介
- `author`：你的名字
- `baseUrl`：部署后的完整地址
- `social.github`：你的 GitHub 链接
- `social.email`：你的邮箱

如果你的 GitHub Pages 地址是 `https://用户名.github.io/仓库名`，把 `baseUrl` 改成这个地址。

## 写新文章

在 `content/posts/` 新建 Markdown 文件，例如 `my-note.md`：

```markdown
---
title: 文章标题
date: 2026-05-13
description: 文章摘要
tags: 标签1, 标签2
---

正文内容写在这里。
```

## 本地生成

在仓库根目录运行：

```bash
python3 scripts/build.py
```

生成的网页在 `public/`。

## 上传和自动部署

推荐用 GitHub Pages：

1. 把整个仓库推送到 GitHub。
2. 打开 GitHub 仓库的 `Settings`。
3. 进入 `Pages`。
4. 在 `Build and deployment` 里选择 `GitHub Actions`。
5. 推送到 `main` 或 `master` 分支后，工作流会自动构建并发布博客。

之后更新博客只需要：

```bash
git add .
git commit -m "Update blog"
git push
```

如果你使用 Vercel，也可以导入这个仓库，并设置：

- Root Directory: `.`
- Build Command: `python3 scripts/build.py`
- Output Directory: `public`
