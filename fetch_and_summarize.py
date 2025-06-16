#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
免 API 抓推文版：使用 snscrape 直接爬 X.com。
生成 docs/daily/YYYY-MM-DD.md（含 Jekyll 头），配合 GitHub Pages。
"""

import os, datetime, pathlib, textwrap, subprocess, json, html
import markdownify, openai

# ── 配置 ────────────────────────────────────────
TWITTER_USERS = [
    "lansao13",
    "435hz",
    "jefflijun",
    "sama",
    "NewsCaixin",
]
TWEETS_PER_USER = 10                # 每人取多少条
MODEL = "gpt-3.5-turbo"
PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
OUT_DIR = pathlib.Path("docs") / "daily"
# ───────────────────────────────────────────────


def scrape_user(username: str, limit: int = 10):
    """调用 snscrape CLI，返回 tweet 列表（最新 → 旧）"""
    cmd = ["snscrape", "--jsonl", f"--max-results={limit}", f"twitter-user:{username}"]
    print(" ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[warn] snscrape {username} failed: {proc.stderr[:200]}")
        return []
    tweets = [json.loads(line) for line in proc.stdout.splitlines()]
    return tweets


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
    outfile.unlink(missing_ok=True)          # 覆盖

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
            tweets = scrape_user(user, TWEETS_PER_USER)
            print(f"{user} -> {len(tweets)} tweets")
            if not tweets:
                continue

            for tw in tweets:
                raw_text = html.unescape(tw["content"])
                digest = summarize(raw_text)

                f.write('<div class="card">\n')
                f.write(f"### @{user} · {tw['date'][:10]}\n\n")
                f.write(f"{digest}\n\n")
                f.write(f"[原推文链接](https://x.com/{user}/status/{tw['id']})\n")
                f.write("\n</div>\n\n")

    print(f"[done] 写入 {outfile}")


if __name__ == "__main__":
    main()


