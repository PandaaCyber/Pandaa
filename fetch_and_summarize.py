#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
免 API　抓推文：snscrape × ChatGPT
写入 docs/daily/YYYY-MM-DD.md（附 Jekyll 头），供 GitHub Pages 展示
"""

import os, datetime, pathlib, textwrap, subprocess, json, html, sys
import markdownify, openai

# ───────────── 配置区 ─────────────
TWITTER_USERS = [           # 需要抓取的 X 账号
    "lansao13",
    "435hz",
    "jefflijun",
    "sama",
    "NewsCaixin",
]
TWEETS_PER_USER = 10        # 每人抓多少条
MODEL = "gpt-3.5-turbo"     # 如要更佳效果可改 gpt-4o
OUT_DIR = pathlib.Path("docs") / "daily"

PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
# ────────────────────────────────


def scrape_user(username: str, limit: int = 10):
    """
    用 snscrape CLI 抓取推文，返回列表
    关闭 SSL 验证以规避 GitHub runner 证书链问题
    """
    cmd = [
        "snscrape",
        "--jsonl",
        "--max-results",
        str(limit),
        "twitter-user",
        username,
    ]
    print(" ".join(cmd))
    # 关键：PYTHONHTTPSVERIFY=0 可让 snscrape 内部 requests 忽略证书
    env = {**os.environ, "PYTHONHTTPSVERIFY": "0"}
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        first_line = proc.stderr.splitlines()[0] if proc.stderr else "unknown error"
        print(f"[warn] snscrape {username} failed: {first_line}", file=sys.stderr)
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
    outfile.unlink(missing_ok=True)   # 始终覆盖

    with outfile.open("w", encoding="utf-8") as f:
        # --- Jekyll 头 ---
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
                raw = html.unescape(tw["content"])
                digest = summarize(raw)

                f.write('<div class="card">\n')
                f.write(f"### @{user} · {tw['date'][:10]}\n\n")
                f.write(f"{digest}\n\n")
                f.write(f"[原推文链接](https://x.com/{user}/status/{tw['id']})\n")
                f.write("\n</div>\n\n")

    print(f"[done] 写入 {outfile}")


if __name__ == "__main__":
    main()




