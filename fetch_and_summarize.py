#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取指定 X 账号 → ChatGPT 中文 200 字摘要 → docs/daily/YYYY-MM-DD.md
使用 snscrape **Python API**（非 CLI）并全局关闭 SSL 校验，避免证书报错。
"""

import ssl, os, datetime, pathlib, textwrap, html, itertools
import snscrape.modules.twitter as sntwitter
import markdownify, openai

# ────────────── 配置 ──────────────
TWITTER_USERS = [
    "lansao13",
    "435hz",
    "jefflijun",
    "sama",
    "NewsCaixin",
]
TWEETS_PER_USER = 10
MODEL = "gpt-3.5-turbo"
OUT_DIR = pathlib.Path("docs") / "daily"

PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
# ────────────────────────────────


def disable_ssl_verify():
    """全局关闭 SSL 校验（requests / urllib3 / snscrape都会受影响）"""
    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ["PYTHONHTTPSVERIFY"] = "0"
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""


def summarize(text: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT_TMPL.format(tweet=text)}],
        temperature=0.4,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def fetch_tweets(username: str, limit: int):
    """返回最近 limit 条推文（含转推、回复）"""
    scraper = sntwitter.TwitterUserScraper(username)
    return itertools.islice(scraper.get_items(), limit)


def main():
    disable_ssl_verify()

    today = datetime.date.today()
    outfile = OUT_DIR / f"{today}.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.unlink(missing_ok=True)  # 覆盖旧文件

    with outfile.open("w", encoding="utf-8") as f:
        # — Jekyll 头 —
        f.write("---\n")
        f.write(f"title: {today} 推文摘要\n")
        f.write(f"date: {today}\n")
        f.write("layout: post\n")
        f.write("excerpt: 今日热门推文速览\n")
        f.write("---\n\n")
        f.write(f"# {today} AI / Tech 推文摘要\n\n")

        for user in TWITTER_USERS:
            tweets = list(fetch_tweets(user, TWEETS_PER_USER))
            print(f"{user} -> {len(tweets)} tweets")
            if not tweets:
                continue

            for tw in tweets:
                raw = html.unescape(tw.content)
                digest = summarize(markdownify.markdownify(raw))

                f.write('<div class="card">\n')
                f.write(f"### @{user} · {tw.date.date()}\n\n")
                f.write(f"{digest}\n\n")
                f.write(f"[原推文链接](https://x.com/{user}/status/{tw.id})\n")
                f.write("\n</div>\n\n")

    print(f"[done] 写入 {outfile}")


if __name__ == "__main__":
    main()





