#!/usr/bin/env python3
"""量子位 (qbitai.com) 爬虫 — WordPress 静态HTML解析

策略：获取列表页文章，筛选近7天的文章，按发布时间取前10
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler

# 量子位页面时间为北京时间（东八区）
CHINA_TZ = ZoneInfo('Asia/Shanghai')

# 从可能包含标签等杂文的 meta 文本中提取时间片段
QBITAI_TIME_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2}|\d+\s*分钟前|\d+\s*小时前|昨天\s*\d{1,2}:\d{2}|前天\s*\d{1,2}:\d{2}|昨天|前天)',
    re.UNICODE
)

# 7天前的时间戳
def get_7days_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=7)


class QbitaiCrawler(BaseCrawler):
    """量子位爬虫"""
    
    def __init__(self):
        super().__init__(name='qbitai', timeout=30)
        self.base_url = 'https://www.qbitai.com'
    
    @staticmethod
    def parse_relative_time(time_str: str) -> Optional[datetime]:
        """将相对时间转换为datetime对象（按北京时间解析，返回 UTC）"""
        # 从 meta 文本中提取时间片段（可能夹杂标签等字符）
        match = QBITAI_TIME_RE.search(time_str.strip())
        if not match:
            return None
        time_str = match.group(1).strip()

        # 以北京时间为基准计算“现在”
        now = datetime.now(CHINA_TZ)

        try:
            if '分钟前' in time_str:
                minutes = int(time_str.replace('分钟前', '').strip())
                dt = now - timedelta(minutes=minutes)
                return dt.astimezone(timezone.utc)

            elif '小时前' in time_str:
                hours = int(time_str.replace('小时前', '').strip())
                dt = now - timedelta(hours=hours)
                return dt.astimezone(timezone.utc)

            elif '昨天' in time_str:
                parts = time_str.replace('昨天', '').strip().split()
                dt = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                if parts and ':' in parts[0]:
                    h, m = parts[0].split(':')
                    dt = dt.replace(hour=int(h), minute=int(m))
                return dt.astimezone(timezone.utc)

            elif '前天' in time_str:
                parts = time_str.replace('前天', '').strip().split()
                dt = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
                if parts and ':' in parts[0]:
                    h, m = parts[0].split(':')
                    dt = dt.replace(hour=int(h), minute=int(m))
                return dt.astimezone(timezone.utc)

            elif '-' in time_str:
                dt = datetime.strptime(time_str, '%Y-%m-%d')
                dt = dt.replace(tzinfo=CHINA_TZ)
                return dt.astimezone(timezone.utc)

            return None
        except Exception:
            return None

    @staticmethod
    def parse_exact_time(soup: BeautifulSoup) -> Optional[datetime]:
        """从文章详情页解析平台原始 date/time 字段（北京时间 -> UTC）"""
        date_el = soup.select_one('span.date')
        time_el = soup.select_one('span.time')
        if not date_el or not time_el:
            return None
        date_str = date_el.get_text(strip=True)
        time_str = time_el.get_text(strip=True)
        try:
            dt = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M:%S')
            dt = dt.replace(tzinfo=CHINA_TZ)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    async def fetch_article_time(self, url: str) -> Optional[datetime]:
        """进入文章详情页读取平台原始发布时间"""
        try:
            html = await self.fetch(url)
            soup = BeautifulSoup(html, 'lxml')
            return self.parse_exact_time(soup)
        except Exception:
            return None

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
        print(f"[{self.name}] 开始抓取: {self.base_url}")
        
        html = await self.fetch(self.base_url)
        soup = BeautifulSoup(html, 'lxml')
        
        articles = []
        seen_urls = set()
        
        # 获取足够多的文章再筛选
        for pt in soup.select('.picture_text'):
            try:
                title_link = pt.select_one('h4 a')
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
                if not title:
                    continue
                
                picture = pt.select_one('.picture img, img.attachment-744x136, img.size-744x136, img.wp-post-image, img[src*="wp-content/uploads"]')
                cover_url = None
                if picture:
                    cover_url = picture.get('src') or picture.get('data-src') or picture.get('data-lazy-src') or ''
                    if cover_url and cover_url.startswith('/'):
                        cover_url = 'https://i.qbitai.com' + cover_url
                
                # 量子位时间：优先进入详情页读取平台原始 date/time 字段
                publish_time = None
                dt = await self.fetch_article_time(url)
                if dt:
                    publish_time = dt.isoformat()
                else:
                    # 降级：从列表页 .time 文本解析相对时间
                    time_el = pt.select_one('.info .time, .time')
                    if time_el:
                        time_str = time_el.get_text(strip=True)
                        dt = self.parse_relative_time(time_str)
                        if dt:
                            publish_time = dt.isoformat()
                
                # 如果时间解析失败，使用当前时间（首页文章默认是新的）
                if not publish_time:
                    publish_time = datetime.now(timezone.utc).isoformat()
                    print(f"[{self.name}] 时间解析失败，使用当前时间: {title[:30]}...")
                
                # 筛选近7天的文章
                if not self.is_within_7days(publish_time):
                    continue
                
                tags = []
                for tag_link in pt.select('.text_info a, .post-tags a, .tag a, a[href*="/tag/"]'):
                    tag_name = tag_link.get_text(strip=True)
                    if tag_name and tag_name not in tags:
                        tags.append(tag_name)
                
                article = {
                    'title': title,
                    'url': url,
                    'platform_url': url,
                    'cover_url': cover_url or None,
                    'publish_time': publish_time,
                    'tags': tags[:5],
                    'platform': self.name,
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"[{self.name}] 解析文章失败: {str(e)}")
                continue
        
        # 备用方案：轮播图
        if not articles:
            for slide in soup.select('.swiper-slide'):
                try:
                    link = slide.select_one('a[href]')
                    if not link:
                        continue
                    
                    url = link.get('href', '')
                    if not url or url in seen_urls:
                        continue
                    
                    seen_urls.add(url)
                    
                    title = link.get_text(strip=True)
                    if not title:
                        continue
                    
                    img = slide.select_one('img')
                    cover_url = None
                    if img:
                        cover_url = img.get('src') or img.get('data-src') or ''
                    
                    article = {
                        'title': title,
                        'url': url,
                        'platform_url': url,
                        'cover_url': cover_url or None,
                        'publish_time': None,
                        'tags': [],
                        'platform': self.name,
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    print(f"[{self.name}] 解析轮播文章失败: {str(e)}")
                    continue
        
        print(f"[{self.name}] 近7天文章: {len(articles)} 篇")
        
        # 按发布时间降序排序，取前N（处理None值，None排到最后）
        articles.sort(key=lambda x: x.get('publish_time') or '1970-01-01T00:00:00+00:00', reverse=True)
        articles = articles[:top_n]
        
        print(f"[{self.name}] 最终获取最新Top{top_n}: {len(articles)} 篇")
        return articles


async def crawl_qbitai(top_n: int = 10) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = QbitaiCrawler()
    return await crawler.crawl(top_n=top_n)


if __name__ == '__main__':
    articles = asyncio.run(crawl_qbitai(top_n=10))
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        if article.get('cover_url'):
            print(f"   封面: {article['cover_url']}")
        print(f"   链接: {article['url']}")
        if article.get('tags'):
            print(f"   标签: {article['tags']}")
