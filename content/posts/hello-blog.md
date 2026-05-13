---
title: 我的第一篇博客
date: 2026-05-13
description: 这是个人博客的第一篇文章，用来测试 Markdown 写作和页面生成。
tags: 博客, Markdown
---

这是我的第一篇博客文章。

以后可以把学习笔记、项目复盘、实验记录都放在 `blog/content/posts/` 目录里。每篇文章都是一个 Markdown 文件，顶部用 `---` 写标题、日期、摘要和标签。

## 可以写什么

- 学习笔记
- 项目记录
- 论文阅读
- 实验结果
- 常用工具整理

## 代码也可以展示

```python
def hello():
    print("Hello, blog!")
```

写完文章后运行：

```bash
python3 blog/scripts/build.py
```

生成结果会放到 `blog/public/`。
