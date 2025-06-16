#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取 Nitter RSS (多节点轮询) → ChatGPT 摘要
输出 docs/daily/YYYY-MM-DD.md（含 Jekyll 头），供 GitHub Pages 渲染
"""

import os, datetime, pathlib, textwrap, html, random
import feedparser, markdownify, openai

# ────────────────── 配置 ──────────────────
TWITTER_USERS = [
    "lansao13",
    "435hz",
    "jefflijun",
    "sama",
    "NewsCaixin",
]
ITEMS_PER_USER = 10
MODEL = "gpt-3.5-turbo"

# 可用 Nitter 节点池（http 优先，避免 SSL）——可随时增删
NITTER_NODES = [
    "http://nitter.net",
    "http://nitter.hu",
    "http://nitter.cz",
    "http://nitter.pufe.org",
    "http://nitter.nohost.me",
    "http://nitter.poast.org",
    "http://nitter.hostux.net",
    "http://nitter.moomer.party",
    "http://nitter.it",
    "http://nitter.weiler.rocks",
    "http://nitter.mha.fi",
    "http://nitter.esmailelbob.xyz",
    "http://nitter.lacontrevoie.fr",
    "http://nitter.kavin.rocks",
    "http://nitter.unixfox.eu",
]
random.shuffle(NITTER_NODES)  # 每次随机顺序尝试
OUT_DIR = pathlib.Path("docs") / "daily"

PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
# ────────────────────────────────────────


def fetch_feed(username: str):
    """轮询节点，返回首个成功解析且有 entry 的 feedparser Feed，或 None"""
    for base in NITTER_NODES:
        rss_url = f"{base.rstrip('/')}/{username}/rss"
        feed = feedparser.parse(rss_url, agent="Mozilla/5.0")
        if feed.bozo:
            continue  # 网络错误 / 解析失败
        if feed.entries:
            print(f"[node] {rss_url} -> {len(feed.entries)} entries ✔")
            return feed
        else:
            print(f"[node] {rss_url} -> 0 entries")
    return None


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
    outfile.unlink(missing_ok=True)

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
            feed = fetch_feed(user)
            if not feed:
                print(f"[warn] {user} 全部节点失败")
                continue

            for entry in feed.entries[:ITEMS_PER_USER]:
                raw = markdownify.markdownify(html.unescape(entry.summary))
                digest = summarize(raw)

                f.write('<div class="card">\n')
                f.write(f"### @{user} · {entry.published[:16]}\n\n")
                f.write(f"{digest}\n\n")
                f.write(f"[原推文链接]({entry.link})\n")
                f.write("\n</div>\n\n")

    print(f"[done] 写入 {outfile}")


if __name__ == "__main__":
    main()




