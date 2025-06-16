#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取 TwitRSS.me → ChatGPT 摘要 → docs/daily/YYYY-MM-DD.md
供 GitHub Pages 渲染，无需任何 Twitter API / snscrape。
"""

import os, datetime, pathlib, textwrap, html
import feedparser, markdownify, openai

# ────────────── 配置 ──────────────
TWITTER_USERS = [
    "lansao13",
    "435hz",
    "jefflijun",
    "sama",
    "NewsCaixin",
]
ITEMS_PER_USER = 10               # 每人抓多少条
MODEL = "gpt-3.5-turbo"
OUT_DIR = pathlib.Path("docs") / "daily"

PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
# ────────────────────────────────


def build_rss_url(username: str) -> str:
    """TwitRSS URL"""
    return f"https://twitrss.me/twitter_user_to_rss/?user={username}"


def summarize(text: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT_TMPL.format(tweet=text)}],
        temperature=0.4,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def main():
    today = datetime.date.today()
    outfile = OUT_DIR / f"{today}.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.unlink(missing_ok=True)   # 覆盖旧文件

    with outfile.open("w", encoding="utf-8") as f:
        # Jekyll 头
        f.write("---\n")
        f.write(f"title: {today} 推文摘要\n")
        f.write(f"date: {today}\n")
        f.write("layout: post\n")
        f.write("excerpt: 今日热门推文速览\n")
        f.write("---\n\n")
        f.write(f"# {today} AI / Tech 推文摘要\n\n")

        for user in TWITTER_USERS:
            url = build_rss_url(user)
            feed = feedparser.parse(url)
            print(f"{user} -> {len(feed.entries)} entries")

            if not feed.entries:
                continue

            for entry in feed.entries[:ITEMS_PER_USER]:
                # TwitRSS 把正文放在 description
                raw = markdownify.markdownify(html.unescape(entry.description))
                digest = summarize(raw)

                f.write('<div class="card">\n')
                f.write(f"### @{user} · {entry.published[:16]}\n\n")
                f.write(f"{digest}\n\n")
                f.write(f"[原推文链接]({entry.link})\n")
                f.write("\n</div>\n\n")

    print(f"[done] 写入 {outfile}")


if __name__ == "__main__":
    main()




