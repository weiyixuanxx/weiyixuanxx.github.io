#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
POSTS = CONTENT / "posts"
ASSETS = ROOT / "assets"
PUBLIC = ROOT / "public"


@dataclass
class Page:
    title: str
    body: str
    source: Path


@dataclass
class Post:
    title: str
    date: str
    description: str
    tags: list[str]
    slug: str
    body: str
    source: Path


def load_config() -> dict:
    return json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip().splitlines()
    meta: dict[str, str] = {}
    for line in raw:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5 :].strip()


def slugify(path: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", path.stem).strip("-").lower()


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', escaped)
    escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img src="{html.escape(m.group(2), quote=True)}" alt="{m.group(1)}" loading="lazy">', escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                out.append(f'<pre><code class="language-{html.escape(code_lang)}">{html.escape(chr(10).join(code_lines))}</code></pre>')
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                flush_paragraph()
                close_list()
                in_code = True
                code_lang = line[3:].strip()
            continue

        if in_code:
            code_lines.append(raw)
            continue

        if not line.strip():
            flush_paragraph()
            close_list()
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue

        item = re.match(r"^-\s+(.+)$", line)
        if item:
            flush_paragraph()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_markdown(item.group(1))}</li>")
            continue

        paragraph.append(line)

    flush_paragraph()
    close_list()
    if in_code:
        out.append(f'<pre><code class="language-{html.escape(code_lang)}">{html.escape(chr(10).join(code_lines))}</code></pre>')
    return "\n".join(out)


def read_page(path: Path) -> Page:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return Page(
        title=meta.get("title", path.stem.replace("-", " ").title()),
        body=markdown_to_html(body),
        source=path,
    )


def read_posts() -> list[Post]:
    posts: list[Post] = []
    for path in sorted(POSTS.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        tags = [tag.strip() for tag in meta.get("tags", "").split(",") if tag.strip()]
        posts.append(
            Post(
                title=meta.get("title", path.stem.replace("-", " ").title()),
                date=meta.get("date", "1970-01-01"),
                description=meta.get("description", ""),
                tags=tags,
                slug=slugify(path),
                body=markdown_to_html(body),
                source=path,
            )
        )
    return sorted(posts, key=lambda post: post.date, reverse=True)


def href(path: str, config: dict) -> str:
    base = config.get("basePath", "").rstrip("/")
    if not base:
        return path
    return f"{base}{path}"


def layout(config: dict, title: str, content: str, description: str = "") -> str:
    full_title = config["title"] if title == config["title"] else f"{title} | {config['title']}"
    nav = "".join(
        f'<a href="{href(item["href"], config)}">{html.escape(item["label"])}</a>'
        for item in config.get("nav", [])
    )
    return f"""<!doctype html>
<html lang="{html.escape(config.get("language", "zh-CN"))}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(full_title)}</title>
  <meta name="description" content="{html.escape(description or config.get("description", ""))}">
  <link rel="stylesheet" href="{href("/assets/styles.css", config)}">
  <link rel="alternate" type="application/rss+xml" title="{html.escape(config["title"])}" href="{href("/feed.xml", config)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body>
  <header class="site-header">
    <div class="header-left">
      <a class="brand" href="{href("/", config)}">{html.escape(config["title"])}</a>
      <nav>{nav}</nav>
    </div>
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">🌙</button>
  </header>
  <main>{content}</main>
  <footer class="site-footer">
    <span>&copy; {datetime.now().year} {html.escape(config.get("author", ""))}</span>
    <a href="{href("/feed.xml", config)}">RSS</a>
  </footer>
  <script>
    (function() {{
      const t = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', t);
      updateIcon(t);
    }})();
    function toggleTheme() {{
      const cur = document.documentElement.getAttribute('data-theme') || 'light';
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      updateIcon(next);
    }}
    function updateIcon(t) {{
      const btn = document.querySelector('.theme-toggle');
      if (btn) btn.textContent = t === 'dark' ? '☀️' : '🌙';
    }}
  </script>
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def post_card(post: Post, config: dict) -> str:
    tags = "".join(f"<span>{html.escape(tag)}</span>" for tag in post.tags)
    return f"""
<article class="post-card">
  <time>{html.escape(post.date)}</time>
  <h2><a href="{href(f"/posts/{post.slug}/", config)}">{html.escape(post.title)}</a></h2>
  <p>{html.escape(post.description)}</p>
  <div class="tags">{tags}</div>
</article>
"""


def build_home(config: dict, posts: list[Post]) -> str:
    latest = "".join(post_card(post, config) for post in posts[:3])
    github = config.get("social", {}).get("github", "#")
    email = config.get("social", {}).get("email", "#")
    return f"""
<section class="hero">
  <div class="hero-copy">
    <p class="eyebrow">Personal Blog</p>
    <h1>{html.escape(config["title"])}</h1>
    <p>{html.escape(config.get("description", ""))}</p>
    <div class="actions">
      <a class="button primary" href="{href("/blog/", config)}">阅读文章</a>
      <a class="button" href="{html.escape(github, quote=True)}">GitHub</a>
      <a class="button" href="{html.escape(email, quote=True)}">联系我</a>
    </div>
  </div>
  <div class="hero-visual">
    <img src="{href("/assets/profile-card.svg", config)}" alt="个人博客封面">
  </div>
</section>
<section class="section">
  <div class="section-head">
    <h2>最新文章</h2>
    <a href="{href("/blog/", config)}">全部文章</a>
  </div>
  <div class="post-grid">{latest}</div>
</section>
"""


def build_blog_index(config: dict, posts: list[Post]) -> str:
    cards = "".join(post_card(post, config) for post in posts)
    return f"""
<section class="page-title">
  <h1>文章</h1>
  <p>按时间整理的学习笔记、项目记录和技术文章。</p>
</section>
<section class="post-grid">{cards}</section>
"""


def build_post(config: dict, post: Post) -> str:
    tags = "".join(f"<span>{html.escape(tag)}</span>" for tag in post.tags)
    return f"""
<article class="article">
  <a class="back-link" href="{href("/blog/", config)}">返回文章列表</a>
  <header>
    <time>{html.escape(post.date)}</time>
    <h1>{html.escape(post.title)}</h1>
    <p>{html.escape(post.description)}</p>
    <div class="tags">{tags}</div>
  </header>
  <div class="article-body">{post.body}</div>
</article>
"""


def build_feed(config: dict, posts: list[Post]) -> str:
    base = config.get("baseUrl", "").rstrip("/")
    items = []
    for post in posts[:20]:
        url = f"{base}/posts/{quote(post.slug)}/"
        items.append(
            f"""<item>
  <title>{html.escape(post.title)}</title>
  <link>{html.escape(url)}</link>
  <guid>{html.escape(url)}</guid>
  <description>{html.escape(post.description)}</description>
  <pubDate>{html.escape(post.date)}</pubDate>
</item>"""
        )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
<channel>
  <title>{html.escape(config["title"])}</title>
  <link>{html.escape(base)}</link>
  <description>{html.escape(config.get("description", ""))}</description>
  {"".join(items)}
</channel>
</rss>
"""


def build_sitemap(config: dict, posts: list[Post]) -> str:
    base = config.get("baseUrl", "").rstrip("/")
    urls = ["/", "/blog/", "/about/"] + [f"/posts/{post.slug}/" for post in posts]
    body = "".join(f"<url><loc>{html.escape(base + url)}</loc></url>" for url in urls)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>
"""


def main() -> None:
    config = load_config()
    posts = read_posts()
    about = read_page(CONTENT / "about.md")

    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ASSETS, PUBLIC / "assets", dirs_exist_ok=True)
    shutil.copy2(ROOT / "styles.css", PUBLIC / "assets" / "styles.css")

    write(PUBLIC / "index.html", layout(config, config["title"], build_home(config, posts), config.get("description", "")))
    write(PUBLIC / "blog" / "index.html", layout(config, "文章", build_blog_index(config, posts), config.get("description", "")))
    write(PUBLIC / "about" / "index.html", layout(config, about.title, f'<article class="article"><h1>{html.escape(about.title)}</h1><div class="article-body">{about.body}</div></article>'))
    for post in posts:
        write(PUBLIC / "posts" / post.slug / "index.html", layout(config, post.title, build_post(config, post), post.description))
    write(PUBLIC / "feed.xml", build_feed(config, posts))
    write(PUBLIC / "sitemap.xml", build_sitemap(config, posts))
    print(f"Built {len(posts)} posts into {PUBLIC}")


if __name__ == "__main__":
    main()
