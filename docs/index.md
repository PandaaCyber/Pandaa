---
layout: default     # 使用主题默认布局
title: 首页
---

# 每日推文摘要

{% assign posts = site.daily | sort: 'date' | reverse %}
{% for p in posts %}
<div class="card">
  <h3><a href="{{ p.url }}">{{ p.date | date: '%Y-%m-%d' }}</a></h3>
  <p>{{ p.excerpt | strip_html | truncate: 120 }}</p>
</div>
{% endfor %}

