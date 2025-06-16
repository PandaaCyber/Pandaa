#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snscrape × ChatGPT  -> docs/daily/YYYY-MM-DD.md
抓取失败只写 0 tweets，脚本绝不崩溃。
"""

import os, ssl, datetime, pathlib, textwrap, html, itertools, logging
import requests, urllib3, snscrape.modules.twitter as sntwitter
import markdownify, openai

# ───── 用户配置 ─────
TWITTER_USERS      = ["lansao13", "435hz", "jefflijun", "sama", "NewsCaixin"]
TWEETS_PER_USER    = 10
MODEL              = "gpt-3.5-turbo"
OUT_DIR            = pathlib.Path("docs") / "daily"
PROMPT_TMPL        = textwrap.dedent("""
你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
=== 原文开始 ===
{tweet}
=== 原文结束 ===
""")
# ───────────────────

def _disable_ssl():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ.update({"PYTHONHTTPSVERIFY":"0",
                       "CURL_CA_BUNDLE":"",
                       "REQUESTS_CA_BUNDLE":""})
    # patch requests
    _orig = requests.sessions.Session.request
    def _patched(self,*a,**kw):
        kw["verify"]=False
        return _orig(self,*a,**kw)
    requests.sessions.Session.request = _patched

_disable_ssl()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

def _summarize(text:str)->str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    r = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role":"user","content":PROMPT_TMPL.format(tweet=text)}],
        temperature=0.4,
        max_tokens=300)
    return r.choices[0].message.content.strip()

def _safe_fetch(user:str, limit:int):
    """返回 list；任何异常 → []"""
    try:
        scr = sntwitter.TwitterUserScraper(user)
        gen = itertools.islice(scr.get_items(), limit)
        tweets = []
        for _ in range(limit):
            try:
                tw = next(gen)
                tweets.append(tw)
            except StopIteration:
                break
            except Exception as e:
                logging.warning("iterate %s tweet failed: %s", user, e)
                break
        return tweets
    except Exception as e:
        logging.warning("init scraper %s failed: %s", user, e)
        return []

def main():
    today = datetime.date.today()
    outfile = OUT_DIR / f"{today}.md"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.unlink(missing_ok=True)

    with outfile.open("w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f"title: {today} 推文摘要\n")
        f.write(f"date: {today}\nlayout: post\nexcerpt: 今日热门推文速览\n---\n\n")
        f.write(f"# {today} AI / Tech 推文摘要\n\n")

        for user in TWITTER_USERS:
            tweets = _safe_fetch(user, TWEETS_PER_USER)
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






