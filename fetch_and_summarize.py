#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每天抓取指定 RSS → 调用 ChatGPT 摘要 → 生成 docs/daily/YYYY-MM-DD.md
文件自带 Jekyll 头信息，GitHub Pages 会自动渲染成博客文章。
"""

import os
import datetime
import pathlib
import textwrap

import feedparser          # 在 requirements.txt 中已列出
import markdownify
import openai

# ─────────────── 配置区 ───────────────
RSS_URLS = [
    "https://nitter.net/elonmusk/rss",     # 换成你自己的 Nitter / rsshub 源
    # "https://rsshub.app/twitter/user/ai_alignment",
]
ITEMS_PER_FEED = 30                        # 每个源最多抓 N 条推文
MODEL = "gpt-3.5-turbo"                    # 免费额度够用，需要更好效果可改 gpt-4o
PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
OUTPUT_DIR = pathlib.Path("docs") / "daily"  # Jekyll collection 目录
# ──────────────────────────────────────


def get_outfile() -> pathlib.Path:
    """返回今天的输出文件路径，确保目录存在"""
    today_str = datetime.date.today().isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"{today_str}.md"


def summarize(text: str) -> str:
    """调用 OpenAI 生成中文摘要"""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT_TMPL.format(tweet=text)}],
        temperature=0.4,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def main() -> None:
    outfile = get_outfile()
    today = datetime.date.today()

    with outfile.open("w", encoding="utf-8") as f:
        # ── Jekyll 前置头信息 ──
        f.write("---\n")
        f.write(f"title: {today} 推文摘要\n")
        f.write(f"date: {today}\n")
        f.write("layout: post\n")
        f.write("excerpt: 今日热门推文速览\n")
        f.write("---\n\n")

        f.write(f"# {today} AI / Tech 推文摘要\n\n")

        # 遍历 RSS 源
        for url in RSS_URLS:
            feed = feedparser.parse(url)
            for entry in feed.entries[:ITEMS_PER_FEED]:
                raw = markdownify.markdownify(entry.summary)
                digest = summarize(raw)

                # 卡片包装，配合自定义 CSS
                f.write('<div class="card">\n')
                f.write(f"### {entry.title}\n\n")
                f.write(f"{digest}\n\n")
                f.write(f"[原推文链接]({entry.link})\n")
                f.write("\n</div>\n\n")

    print(f"已生成：{outfile.relative_to(pathlib.Path.cwd())}")


if __name__ == "__main__":
    main()

