#!/usr/bin/env python3
"""BestBlogs 爬虫 - 调用官方 OpenAPI v2

抓取：
1. 每日公开简报（/briefs/latest）→ 标记为「早报」
2. 今日热门精选（/resources/trending?period=today）→ 标记为「精选」

环境变量：
    BESTBLOGS_API_KEY: BestBlogs OpenAPI Key（前缀 bb_）
"""

import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

API_BASE = 'https://api.bestblogs.dev/openapi/v2'


class BestBlogsCrawler:
    """BestBlogs OpenAPI 爬虫"""

    def __init__(self):
        self.name = 'bestblogs'
        self.api_key = os.environ.get('BESTBLOGS_API_KEY', '')
        self.timeout = 30

    def get_headers(self) -> Dict[str, str]:
        return {
            'X-API-KEY': self.api_key,
            'Accept': 'application/json',
            'User-Agent': 'AINews-Crawler/1.0',
        }

    async def fetch_json(self, client: httpx.AsyncClient, url: str) -> Any:
        """调用 BestBlogs API 并返回 data 字段"""
        response = await client.get(url, headers=self.get_headers(), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not payload.get('success'):
            raise Exception(payload.get('message') or 'BestBlogs API request failed')
        return payload.get('data')

    async def fetch_resource_detail(
        self, client: httpx.AsyncClient, resource_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取单条资源详情，用于补全简报中缺失的 url/cover/score"""
        try:
            data = await self.fetch_json(client, f'{API_BASE}/resources/{resource_id}')
            if isinstance(data, dict) and 'metaData' in data:
                return data['metaData']
            return data
        except Exception as e:
            print(f'[{self.name}] 获取资源详情失败 {resource_id}: {str(e)}')
            return None

    def _parse_publish_time(self, item: Dict[str, Any]) -> Optional[str]:
        """从多种可能字段解析发布时间"""
        ts = item.get('publishTimeStamp')
        if isinstance(ts, (int, float)) and ts > 0:
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()

        dt_str = item.get('publishDateTimeStr')
        if dt_str:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
                try:
                    dt = datetime.strptime(dt_str, fmt)
                    return dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    continue

        date_str = item.get('publishDateStr')
        if date_str == '今天':
            return datetime.now(timezone.utc).isoformat()
        if date_str:
            for fmt in ('%Y-%m-%d',):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    continue

        return None

    def _article_from_resource(self, item: Dict[str, Any], tag: str) -> Optional[Dict[str, Any]]:
        """将 BestBlogs 资源对象转换为统一文章格式"""
        resource_id = item.get('id') or item.get('resourceId')
        title = item.get('title') or item.get('originalTitle')
        if not title:
            return None

        original_url = item.get('url') or item.get('readUrl') or ''
        platform_url = f'https://www.bestblogs.dev/article/{resource_id}' if resource_id else ''
        # url 保持为原始文章地址，用于 merge 去重；前端展示优先使用 platform_url
        url = original_url or platform_url
        if not platform_url and original_url:
            platform_url = original_url

        publish_time = self._parse_publish_time(item)
        if not publish_time:
            publish_time = datetime.now(timezone.utc).isoformat()

        score = item.get('score') or item.get('totalScore') or item.get('weightedScore')

        tags = [tag]
        for t in (item.get('tags') or [])[:3]:
            if t and t not in tags:
                tags.append(t)

        summary = item.get('oneSentenceSummary') or ''
        if not summary and item.get('summary'):
            summary = item['summary'][:500]

        return {
            'title': title,
            'url': url,
            'platform_url': platform_url,
            'original_url': original_url,
            'resource_id': resource_id,
            'cover_url': item.get('cover') or None,
            'publish_time': publish_time,
            'tags': tags,
            'summary': summary,
            'platform': self.name,
            'score': score if score is not None else None,
            'source_name': item.get('sourceName') or '',
        }

    async def crawl_briefs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """抓取最新每日简报"""
        print(f'[{self.name}] 获取每日简报...')
        data = await self.fetch_json(client, f'{API_BASE}/briefs/latest')
        items = data.get('contentItems', []) if isinstance(data, dict) else []
        print(f'[{self.name}] 简报条目: {len(items)} 篇')

        articles = []
        seen_ids = set()
        for item in items:
            resource_id = item.get('resourceId')
            if not resource_id or resource_id in seen_ids:
                continue
            seen_ids.add(resource_id)

            # 简报条目缺少 url/cover，调用详情接口补全
            detail = await self.fetch_resource_detail(client, resource_id)
            if detail and isinstance(detail, dict):
                merged = {**item, **detail}
            else:
                merged = item

            article = self._article_from_resource(merged, '早报')
            if article:
                articles.append(article)

        return articles

    async def crawl_trending(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """抓取今日热门精选"""
        print(f'[{self.name}] 获取热门精选...')
        data = await self.fetch_json(client, f'{API_BASE}/resources/trending?period=today&limit=10')
        items = data if isinstance(data, list) else data.get('dataList', [])
        print(f'[{self.name}] 热门条目: {len(items)} 篇')

        articles = []
        for item in items:
            article = self._article_from_resource(item, '精选')
            if article:
                articles.append(article)

        return articles

    async def crawl(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """执行爬虫：简报 + 热门精选，按 URL 去重后返回"""
        if not self.api_key:
            raise Exception('BESTBLOGS_API_KEY environment variable is not set')

        async with httpx.AsyncClient() as client:
            briefs, trending = await asyncio.gather(
                self.crawl_briefs(client),
                self.crawl_trending(client),
            )

        # 按 URL 去重：简报优先；如果 URL 重复保留先出现的（简报在前）
        seen_urls = {}
        for article in briefs + trending:
            url = article.get('url')
            if url and url not in seen_urls:
                seen_urls[url] = article

        articles = list(seen_urls.values())

        # 排序：先按 score 降序，再按发布时间降序
        def sort_key(a):
            return (a.get('score') or 0, a.get('publish_time') or '')

        articles.sort(key=sort_key, reverse=True)

        # 两个来源合并后，总量放宽到 2 * top_n
        limit = top_n * 2
        print(f'[{self.name}] 去重后共 {len(articles)} 篇，保留 Top {limit}')
        return articles[:limit]


async def crawl_bestblogs(top_n: int = 10) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = BestBlogsCrawler()
    return await crawler.crawl(top_n=top_n)


if __name__ == '__main__':
    articles = asyncio.run(crawl_bestblogs(top_n=10))
    print(f'\n获取到 {len(articles)} 篇文章:')
    for i, article in enumerate(articles, 1):
        print(f"{i}. [{article.get('tags')[0] if article.get('tags') else '?'}] {article['title']}")
        print(f"   链接: {article.get('platform_url') or article['url']}")
        if article.get('cover_url'):
            print(f"   封面: {article['cover_url']}")
