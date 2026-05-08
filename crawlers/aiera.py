#!/usr/bin/env python3
"""新智元 (aiera.com.cn) 爬虫 — WordPress 静态HTML解析"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler


class AieraCrawler(BaseCrawler):
    """新智元爬虫"""
    
    def __init__(self):
        super().__init__(name='aiera', timeout=30)
        self.base_url = 'https://www.aiera.com.cn'
    
    @staticmethod
    def parse_chinese_time(time_str: str) -> Optional[str]:
        """将中文时间转换为标准ISO格式"""
        try:
            match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', time_str)
            if match:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                dt = datetime(year, month, day, tzinfo=timezone.utc)
                return dt.isoformat()
            return None
        except Exception:
            return None
    
    async def crawl(self, limit: int = 20) -> List[Dict[str, Any]]:
        """执行爬虫"""
        print(f"[{self.name}] 开始抓取: {self.base_url}")
        
        html = await self.fetch(self.base_url)
        soup = BeautifulSoup(html, 'lxml')
        
        articles = []
        seen_urls = set()
        
        for h2_el in soup.select('h2'):
            if len(articles) >= limit:
                break
            
            title_link = h2_el.select_one('a')
            if not title_link:
                continue
            
            url = title_link.get('href', '')
            if not url or url in seen_urls:
                continue
            
            if url.startswith('/'):
                url = self.base_url + url
            elif not url.startswith('http'):
                url = self.base_url + '/' + url
            
            seen_urls.add(url)
            
            title = title_link.get_text(strip=True)
            
            parent = h2_el.find_parent(['article', '.post', '.entry', '.card'])
            if not parent:
                parent = h2_el
            
            cover_img = parent.select_one('.post-thumbnail img, .entry-thumbnail img, .wp-post-image, img')
            cover_url = None
            if cover_img:
                cover_url = cover_img.get('src') or cover_img.get('data-src') or ''
                if cover_url and not cover_url.startswith('http'):
                    cover_url = self.base_url + '/' + cover_url.lstrip('/')
            
            time_el = parent.select_one('.entry-meta, .post-meta, .date, time')
            time_str = time_el.get_text(strip=True) if time_el else ''
            publish_time = self.parse_chinese_time(time_str) if time_str else None
            
            tags = []
            for tag_link in parent.select('.tag a, .category a, .entry-tags a'):
                tag_name = tag_link.get_text(strip=True)
                if tag_name:
                    tags.append(tag_name)
            
            article = {
                'title': title,
                'url': url,
                'cover_url': cover_url or None,
                'publish_time': publish_time,
                'tags': tags[:5],
                'platform': self.name,
            }
            
            articles.append(article)
            print(f"  [{len(articles)}] {title[:40]}...")
        
        print(f"[{self.name}] 成功解析 {len(articles)} 篇文章")
        return articles


async def crawl_aiera(limit: int = 20) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = AieraCrawler()
    return await crawler.crawl(limit=limit)


if __name__ == '__main__':
    articles = asyncio.run(crawl_aiera(limit=10))
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        if article.get('cover_url'):
            print(f"   封面: {article['cover_url']}")
        print(f"   链接: {article['url']}")
        if article.get('tags'):
            print(f"   标签: {article['tags']}")
