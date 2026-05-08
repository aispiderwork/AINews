#!/usr/bin/env python3
"""TechCrunch 爬虫 - 使用 RSS Feed"""

import asyncio
import feedparser
import ssl
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler


class TechCrunchCrawler(BaseCrawler):
    """TechCrunch AI 分类爬虫"""
    
    def __init__(self):
        super().__init__(name='techcrunch', timeout=30)
        self.rss_url = 'https://techcrunch.com/category/artificial-intelligence/feed/'
    
    def _fetch_rss(self, url: str):
        """获取RSS数据，处理SSL验证问题"""
        import urllib.request
        
        ctx = ssl.create_default_context()
        
        try:
            import certifi
            ctx.load_verify_locations(certifi.where())
        except Exception:
            pass
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, context=ctx, timeout=self.timeout) as response:
            xml_data = response.read()
        
        return feedparser.parse(xml_data)
    
    async def extract_cover_from_page(self, url: str) -> Optional[str]:
        """从文章页面提取 Open Graph 封面图片"""
        try:
            html = await self.fetch(url)
            soup = BeautifulSoup(html, 'lxml')
            
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                return twitter_image['content']
            
            return None
        except Exception as e:
            print(f"[{self.name}] 提取封面失败 ({url}): {str(e)[:50]}")
            return None
    
    async def crawl(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        执行爬虫
        
        Args:
            limit: 获取文章数量上限
            
        Returns:
            文章列表
        """
        print(f"[{self.name}] 开始获取 RSS Feed: {self.rss_url}")
        
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, self._fetch_rss, self.rss_url)
        
        if feed.bozo:
            print(f"[{self.name}] RSS解析警告: {feed.bozo_exception}")
        
        print(f"[{self.name}] RSS Feed 包含 {len(feed.entries)} 篇文章")
        
        articles = []
        for entry in feed.entries[:limit]:
            try:
                title = entry.get('title', '')
                link = entry.get('link', '')
                published = entry.get('published', '')
                summary = entry.get('summary', '')
                
                publish_time = None
                if published:
                    try:
                        dt = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                        publish_time = dt.isoformat()
                    except ValueError:
                        try:
                            dt = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S +0000')
                            publish_time = dt.replace(tzinfo=timezone.utc).isoformat()
                        except ValueError:
                            publish_time = published
                
                cover_url = None
                if hasattr(entry, 'media_content') and entry.media_content:
                    for media in entry.media_content:
                        if media.get('medium') == 'image':
                            cover_url = media.get('url')
                            break
                
                if not cover_url and hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                    cover_url = entry.media_thumbnail[0].get('url')
                
                tags = []
                if hasattr(entry, 'tags'):
                    tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
                
                article = {
                    'title': title,
                    'url': link,
                    'cover_url': cover_url,
                    'publish_time': publish_time,
                    'tags': tags[:5],
                    'summary': summary[:500] if summary else '',
                    'platform': self.name,
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"[{self.name}] 解析文章失败: {str(e)}")
                continue
        
        covers_to_fetch = [a for a in articles if not a.get('cover_url')]
        if covers_to_fetch:
            print(f"[{self.name}] 正在从 {len(covers_to_fetch)} 个文章页面提取封面...")
            tasks = [
                self._set_cover(article, self.extract_cover_from_page(article['url']))
                for article in covers_to_fetch
            ]
            await asyncio.gather(*tasks)
            fetched_count = sum(1 for a in covers_to_fetch if a.get('cover_url'))
            print(f"[{self.name}] 成功提取 {fetched_count}/{len(covers_to_fetch)} 个封面")
        
        print(f"[{self.name}] 成功解析 {len(articles)} 篇文章")
        return articles
    
    async def _set_cover(self, article: Dict, cover_task):
        """辅助方法：异步设置封面"""
        cover_url = await cover_task
        if cover_url:
            article['cover_url'] = cover_url


async def crawl_techcrunch(limit: int = 20) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = TechCrunchCrawler()
    return await crawler.crawl(limit=limit)


if __name__ == '__main__':
    articles = asyncio.run(crawl_techcrunch(limit=10))
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        if article.get('cover_url'):
            print(f"   封面: {article['cover_url']}")
        print(f"   链接: {article['url']}")
