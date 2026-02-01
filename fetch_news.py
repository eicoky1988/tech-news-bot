#!/usr/bin/env python3
"""
科技资讯抓取与推送脚本 - PushPlus 版本
"""

import os
import requests
import feedparser
from datetime import datetime, timedelta, timezone


RSS_FEEDS = {
    "Hacker News 热门": "https://hnrss.org/frontpage?points=100",
    "Hacker News 最佳": "https://hnrss.org/best",
    "GitHub Trending": "https://rsshub.app/github/trending/daily/all",
    "V2EX 热门": "https://rsshub.app/v2ex/topics/hot",
    "少数派": "https://sspai.com/feed",
    "36氪快讯": "https://rsshub.app/36kr/newsflashes",
}


def parse_feed(url, hours=24):
    try:
        feed = feedparser.parse(url)
        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        for entry in feed.entries[:20]:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            if published is None or published > cutoff_time:
                articles.append({
                    'title': entry.get('title', '无标题'),
                    'link': entry.get('link', ''),
                    'published': published.strftime('%m-%d %H:%M') if published else '未知时间'
                })
        return articles
    except Exception as e:
        print(f"解析RSS出错 {url}: {e}")
        return []


def fetch_all_news():
    all_news = {}
    for name, url in RSS_FEEDS.items():
        print(f"正在抓取: {name}")
        articles = parse_feed(url)
        if articles:
            all_news[name] = articles
            print(f"  获取 {len(articles)} 条")
    return all_news


def format_markdown(news_data):
    if not news_data:
        return "今日暂无新资讯"

    lines = []
    for source, articles in news_data.items():
        lines.append(f"## {source}")
        lines.append("")
        for i, article in enumerate(articles[:10], 1):
            title = article['title'].replace('[', '【').replace(']', '】')
            lines.append(f"{i}. [{title}]({article['link']})")
            lines.append(f"   _{article['published']}_")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def push_via_pushplus(title, content, token):
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": f"# {title}\n\n{content}",
        "template": "markdown"
    }
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()
        if result.get('code') == 200:
            print("推送成功!")
            return True
        else:
            print(f"推送失败: {result.get('msg')}")
            return False
    except Exception as e:
        print(f"推送出错: {e}")
        return False


def main():
    pushplus_token = os.environ.get('PUSHPLUS_TOKEN')

    if not pushplus_token:
        print("错误: 请设置 PUSHPLUS_TOKEN")
        exit(1)

    print("=" * 50)
    print(f"开始抓取科技资讯 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    news_data = fetch_all_news()
    total_count = sum(len(articles) for articles in news_data.values())
    print(f"\n共抓取 {total_count} 条资讯")

    if total_count == 0:
        print("无新资讯，跳过推送")
        return

    today = datetime.now().strftime('%m月%d日')
    title = f"{today}科技资讯速递"
    content = format_markdown(news_data)

    print("\n正在推送到微信...")
    push_via_pushplus(title, content, pushplus_token)


if __name__ == "__main__":
    main()
