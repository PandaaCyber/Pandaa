#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每天抓取 RSS → 调用 ChatGPT 摘要 → 生成 docs/daily/YYYY-MM-DD.md
"""
import os, datetime, feedparser, markdownify, openai, pathlib, textwrap

### ===== 配置区 =====
RSS_URLS = [
    "https://nitter.net/elonmusk/rss",            # ← 换成你想看的推特账号或列表 RSS
    # "https://nitter.net/ai_alignment/rss",
]
ITEMS_PER_FEED = 30                               # 每个源最多读取多少条
MODEL         = "gpt-3.5-turbo"                   # 免费额度足够；想升级可改 gpt-4o
PROMPT_TMPL   = textwrap.dedent("""
    你是一位中文编辑，请用不超过 200 字总结下面这条推文内容，并给出 3 个 #标签：
    === 原文开始 ===
    {tweet}
    === 原文结束 ===
""")
### ==================

def today_outfile() -> pathlib.Path:
    day = datetime.date.today().isoformat()
    odir = pathlib.Path("docs") / "daily"
    odir.mkdir(parents=True, exist_ok=True)
    return odir / f"{day}.md"

def summarize(text: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY", "DUMMY_KEY")
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT_TMPL.format(tweet=text)}],
        temperature=0.4,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()

def main():
    outfile = today_outfile()
    with outfile.open("w", encoding="utf-8") as f:
        f.write(f"# {datetime.date.today()} AI / Tech 推文摘要\n\n")
        for url in RSS_URLS:
            feed = feedparser.parse(url)
            for entry in feed.entries[:ITEMS_PER_FEED]:
                raw = markdownify.markdownify(entry.summary)
                digest = summarize(raw)
                f.write(f"## {entry.title}\n\n{digest}\n\n[原推文链接]({entry.link})\n\n---\n")
    print(f"生成完毕 → {outfile}")

if __name__ == "__main__":
    main()
