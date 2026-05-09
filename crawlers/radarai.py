#!/usr/bin/env python3
"""RadarAI (radarai.top) 爬虫 — 静态HTML摘要解析

策略：获取列表页文章，筛选近7天的文章，按发布时间取前10
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler

# 7天前的时间戳
def get_7days_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=7)


class RadaraiCrawler(BaseCrawler):
    """RadarAI 爬虫"""
    
    def __init__(self):
        super().__init__(name='radarai', timeout=30)
        self.base_url = 'https://radarai.top'
        self.updates_url = 'https://radarai.top/updates/'
    
    def is_within_7days(self, publish_time: str) -> bool:
        """判断时间是否在7天内"""
        if not publish_time:
            return False
        try:
            dt = datetime.fromisoformat(publish_time)
            return dt >= get_7days_ago()
        except Exception:
            return False
    
    async def crawl(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        执行爬虫 - 获取近7天内最新的AI文章
        
        Args:
            top_n: 取前N篇文章（默认10）
            
        Returns:
            文章列表（按发布时间降序）
        """
        print(f"[{self.name}] 开始抓取: {self.updates_url}")
        
        html = await self.fetch(self.updates_url)
        soup = BeautifulSoup(html, 'lxml')
        
        articles = []
        seen_urls = set()
        
        # 获取足够多的文章再筛选
        for brief_item in soup.select('li.brief-item, .brief-card, article, .update-item'):
            try:
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
                if not title:
                    continue
                
                time_el = brief_item.select_one('.brief-time, .date, time, .meta .date')
                time_str = time_el.get_text(strip=True) if time_el else ''
                
                publish_time = None
                if time_str:
                    try:
                        if '-' in time_str and ':' in time_str:
                            parts = time_str.split()
                            if len(parts) >= 2:
                                dt = datetime.strptime(parts[0] + ' ' + parts[-1], '%Y-%m-%d %H:%M')
                                publish_time = dt.replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass
                
                # 筛选近7天的文章
                if not self.is_within_7days(publish_time):
                    continue
                
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
                
            except Exception as e:
                print(f"[{self.name}] 解析文章失败: {str(e)}")
                continue
        
        print(f"[{self.name}] 近7天文章: {len(articles)} 篇")
        
        # 按发布时间降序排序，取前N（处理None值，None排到最后）
        articles.sort(key=lambda x: x.get('publish_time') or '1970-01-01T00:00:00+00:00', reverse=True)
        articles = articles[:top_n]
        
        print(f"[{self.name}] 最终获取最新Top{top_n}: {len(articles)} 篇")
        return articles


async def crawl_radarai(top_n: int = 10) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = RadaraiCrawler()
    return await crawler.crawl(top_n=top_n)


if __name__ == '__main__':
    articles = asyncio.run(crawl_radarai(top_n=10))
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   链接: {article['url']}")
        if article.get('summary'):
            print(f"   摘要: {article['summary'][:80]}...")
