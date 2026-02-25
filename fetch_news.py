#!/usr/bin/env python3
"""
科技资讯抓取与推送脚本 - PushPlus 版本
"""

import os
import requests
import feedparser
from deep_translator import GoogleTranslator
from datetime import datetime, timedelta, timezone


# ==================== 配置区域 ====================

RSS_FEEDS = {
    # ==================== 科技类资讯 ====================
    "Hacker News 热门": "https://hnrss.org/frontpage?points=100",
    "Hacker News 最佳": "https://hnrss.org/best",
    "少数派": "https://sspai.com/feed",

    # 国外科技媒体
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired 连线": "https://www.wired.com/feed/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "CNET 科技": "https://www.cnet.com/rss/news/",

    # ==================== 设计类资讯 ====================
    "Smashing Magazine": "https://www.smashingmagazine.com/feed/",
    "Designboom": "https://www.designboom.com/feed/",
    "CSS-Tricks": "https://css-tricks.com/feed/",

    # ==================== 家居/生活/装修类资讯 ====================
    "Home Designing": "https://www.home-designing.com/feed",
    "Decoist 家居": "https://www.decoist.com/feed/",
    "Homedit 装修": "https://www.homedit.com/feed/",

    # ==================== 产品/创业/营销 ====================
    "Product Hunt": "https://www.producthunt.com/feed",
    "HubSpot 营销": "https://feeds.feedburner.com/HubSpotMarketing",

    # ==================== 生活方式/个人成长 ====================
    "Lifehacker 生活技巧": "https://lifehacker.com/feed/rss",
    "Art of Manliness": "https://feeds.feedburner.com/TheArtOfManliness",
    "Mark Manson": "https://markmanson.net/feed",
    "99% Invisible 设计": "https://99percentinvisible.org/feed/",
}


# ==================== RSS 解析 ====================

def parse_feed(url, hours=24):
    try:
        feed = feedparser.parse(url)

        # 检查是否解析成功
        if not feed or not hasattr(feed, 'entries') or len(feed.entries) == 0:
            print(f"  警告: 无内容或解析失败")
            if hasattr(feed, 'feed'):
                print(f"  Feed 信息: {feed.feed.get('title', 'N/A')}")
            return []

        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        for entry in feed.entries[:20]:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            if published is None or published > cutoff_time:
                summary = entry.get('summary') or entry.get('description', '')[:300]
                articles.append({
                    'title': entry.get('title', '无标题'),
                    'link': entry.get('link', ''),
                    'summary': summary,
                    'published': published.strftime('%m-%d %H:%M') if published else '未知时间'
                })
        return articles
    except Exception as e:
        print(f"  错误: {e}")
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


# ==================== 翻译功能 ====================

SOURCE_NAMES = {
    "TechCrunch": "科技Crunch",
    "The Verge": "The Verge",
    "Wired 连线": "连线",
    "Ars Technica": "Ars Technica",
    "CNET 科技": "CNET 科技",
    "Smashing Magazine": "Smashing Magazine",
    "Designboom": "Designboom",
    "CSS-Tricks": "CSS技巧",
    "Home Designing": "家居设计",
    "Decoist 家居": "Decoist",
    "Homedit 装修": "Homedit",
    "Product Hunt": "产品狩猎",
    "HubSpot 营销": "HubSpot",
    "Lifehacker 生活技巧": "生活黑客",
    "Art of Manliness": "男性气概",
    "Mark Manson": "马克·曼森",
    "99% Invisible 设计": "99%不可见",
    "Hacker News 热门": "Hacker News",
    "Hacker News 最佳": "Hacker News",
}


def translate_text(text):
    try:
        translated = GoogleTranslator(source='auto', target='zh-CN').translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"  翻译失败: {e}")
        return text


def translate_source_name(name):
    if name in SOURCE_NAMES:
        return SOURCE_NAMES[name]
    return name


# ==================== 格式化 ====================

def format_markdown(news_data):
    if not news_data:
        return "今日暂无新资讯"

    lines = []
    for source, articles in news_data.items():
        lines.append(f"## {translate_source_name(source)}")
        lines.append("")
        for i, article in enumerate(articles[:10], 1):
            title = translate_text(article['title']).replace('[', '【').replace(']', '】')
            lines.append(f"### {i}. {title}")
            if article.get('summary'):
                summary = translate_text(article['summary']).replace('[', '【').replace(']', '】')
                lines.append(f"> {summary[:200]}...")
            lines.append(f"   - [阅读原文]({article['link']})")
            lines.append(f"   - {article['published']}")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


# ==================== PushPlus 推送 ====================

def push_via_pushplus(title, content, token):
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": f"# {title}\n\n{content}",
        "template": "markdown",
        "channel": "wechat"
    }
    print(f"推送内容长度: {len(content)} 字符")
    print(f"推送目标: {url}")
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"响应状态码: {response.status_code}")
        result = response.json()
        print(f"响应内容: {result}")
        if result.get('code') == 200:
            print("推送成功!")
            return True
        else:
            print(f"推送失败: {result.get('msg')}")
            return False
    except Exception as e:
        print(f"推送出错: {e}")
        return False


# ==================== 主程序 ====================

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
