#!/usr/bin/env python3
"""RadarAI (radarai.top) 爬虫 — 静态HTML摘要解析"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler


class RadaraiCrawler(BaseCrawler):
    """RadarAI 爬虫"""
    
    def __init__(self):
        super().__init__(name='radarai', timeout=30)
        self.base_url = 'https://radarai.top'
        self.updates_url = 'https://radarai.top/updates/'
    
    async def crawl(self, limit: int = 20) -> List[Dict[str, Any]]:
        """执行爬虫"""
        print(f"[{self.name}] 开始抓取: {self.updates_url}")
        
        html = await self.fetch(self.updates_url)
        soup = BeautifulSoup(html, 'lxml')
        
        articles = []
        seen_urls = set()
        
        for brief_item in soup.select('li.brief-item, .brief-card, article, .update-item')[:limit * 2]:
            if len(articles) >= limit:
                break
            
            title_el = brief_item.select_one('h3 a, h2 a, .brief-title a, .title a')
            if not title_el:
                continue
            
            url = title_el.get('href', '')
            if not url or url in seen_urls:
                continue
            
            if url.startswith('/'):
                url = self.base_url + url
            elif not url.startswith('http'):
                url = self.base_url + '/' + url
            
            seen_urls.add(url)
            
            title = title_el.get_text(strip=True)
            
            time_el = brief_item.select_one('.brief-time, .date, time, .meta .date')
            time_str = time_el.get_text(strip=True) if time_el else ''
            
            publish_time = None
            if time_str:
                try:
                    if '-' in time_str and ':' in time_str:
                        dt = datetime.strptime(time_str.split()[0] + ' ' + time_str.split()[-1], '%Y-%m-%d %H:%M')
                        publish_time = dt.replace(tzinfo=timezone.utc).isoformat()
                except Exception:
                    pass
            
            summary_el = brief_item.select_one('.brief-summary, .summary, .excerpt, .content')
            summary = summary_el.get_text(strip=True)[:500] if summary_el else ''
            
            tags = []
            for tag_el in brief_item.select('.brief-tags a, .tag a, .category a, .label a'):
                tag_name = tag_el.get_text(strip=True)
                if tag_name:
                    tags.append(tag_name)
            
            article = {
                'title': title,
                'url': url,
                'cover_url': None,
                'publish_time': publish_time,
                'tags': tags[:5],
                'summary': summary,
                'platform': self.name,
            }
            
            articles.append(article)
            print(f"  [{len(articles)}] {title[:40]}...")
        
        print(f"[{self.name}] 成功解析 {len(articles)} 篇文章")
        return articles


async def crawl_radarai(limit: int = 20) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = RadaraiCrawler()
    return await crawler.crawl(limit=limit)


if __name__ == '__main__':
    articles = asyncio.run(crawl_radarai(limit=10))
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   链接: {article['url']}")
        if article.get('summary'):
            print(f"   摘要: {article['summary'][:80]}...")
