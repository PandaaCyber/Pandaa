#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snscrape(Python API) × ChatGPT
关闭所有 SSL 校验；即使取不到推文也不会 raise，保底输出 0 tweets。
结果写入 docs/daily/YYYY-MM-DD.md（含 Jekyll 头）
"""

import os, ssl, datetime, pathlib, textwrap, html, itertools, logging
import requests, urllib3, snscrape.modules.twitter as sntwitter
import markdownify, openai

# ────────────── 用户配置 ──────────────
TWITTER_USERS = ["lansao13", "435hz", "jefflijun", "sama", "NewsCaixin"]
TWEETS_PER_USER = 10
MODEL = "gpt-3.5-turbo"
OUT_DIR = pathlib.Path("docs") / "daily"
PROMPT_TMPL = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
# ────────────────────────────────────


def _disable_ssl():
    """关闭 requests / urllib3 / ssl 全链路验证"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ.update({"PYTHONHTTPSVERIFY": "0",
                       "CURL_CA_BUNDLE": "",
                       "REQUESTS_CA_BUNDLE": ""})
    # patch requests 全局 verify=False
    _orig_request = requests.sessions.Session.request

    def _patched(self, *args, **kw):
        kw.setdefault("verify", False)
        return _orig_request(self, *args, **kw)

    requests.sessions.Session.request = _patched


def _summarize(text: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT_TMPL.format(tweet=text)}],
        temperature=0.4,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def _fetch_tweets(user: str, limit: int):
    """返回 generator；抓取异常时返回空列表"""
    try:
        scraper = sntwitter.TwitterUserScraper(user)
        return itertools.islice(scraper.get_items(), limit)
    except Exception as e:
        logging.warning("fetch %s failed: %s", user, e)
        return []


def main():
    _disable_ssl()

    today = datetime.date.today()
    outfile = OUT_DIR / f"{today}.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.unlink(missing_ok=True)

    with outfile.open("w", encoding="utf-8") as f:
        # — Jekyll front‑matter —
        f.write("---\n")
        f.write(f"title: {today} 推文摘要\n")
        f.write(f"date: {today}\n")
        f.write("layout: post\n")
        f.write("excerpt: 今日热门推文速览\n")
        f.write("---\n\n# " + str(today) + " AI / Tech 推文摘要\n\n")

        for user in TWITTER_USERS:
            tweets = list(_fetch_tweets(user, TWEETS_PER_USER))
            print(f"{user} -> {len(tweets)} tweets")

            for tw in tweets:
                raw = markdownify.markdownify(html.unescape(tw.content))
                digest = _summarize(raw)

                f.write('<div class="card">\n')
                f.write(f"### @{user} · {tw.date.date()}\n\n{digest}\n\n")
                f.write(f"[原推文链接](https://x.com/{user}/status/{tw.id})\n\n</div>\n\n")

    print("[done] 写入", outfile)


if __name__ == "__main__":
    main()





