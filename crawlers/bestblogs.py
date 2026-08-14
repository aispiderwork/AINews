#!/usr/bin/env python3
"""BestBlogs 爬虫 - 调用官方 OpenAPI v2

抓取：
1. 每日公开简报（/briefs/latest）→ 标记为「早报」
2. 近 7 天热门精选（/resources/trending?period=week）→ 标记为「精选」

环境变量：
    BESTBLOGS_API_KEY: BestBlogs OpenAPI Key（前缀 bb_）
"""

import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

API_BASE = 'https://api.bestblogs.dev/openapi/v2'

# BestBlogs 接口中的字符串日期/时间为北京时间
CHINA_TZ = ZoneInfo('Asia/Shanghai')

# 429 / 限流时最多重试次数与退避参数
# 注意：BestBlogs 日配额（Free 仅 50 次/天，业务码 160003）耗尽时不可重试，
# 仅对秒级限流 / 服务端错误做有限退避重试，避免把剩余额度一次烧光。
MAX_RETRIES = 2
BASE_BACKOFF = 5.0  # 秒
# 连续请求间默认间隔，降低并发触发的限流概率
REQUEST_DELAY = 3.0  # 秒

# BestBlogs 业务码：日配额耗尽，不可重试
QUOTA_EXCEEDED_CODES = {160003}


class DailyQuotaExceeded(Exception):
    """BestBlogs 日调用配额已耗尽，不可重试"""
    pass


def _safe_json(response) -> Optional[Dict[str, Any]]:
    try:
        return response.json()
    except Exception:
        return None


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
        """调用 BestBlogs API 并返回 data 字段。

        限流策略：
        - 业务码 160003（日配额耗尽）→ 抛 DailyQuotaExceeded，不重试
        - 其他 429 / 5xx → 指数退避重试（最多 MAX_RETRIES 次）
        - 4xx 客户端错误（401/403/404 等）→ 直接抛出，不重试
        """
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.get(url, headers=self.get_headers(), timeout=self.timeout)
                # 优先识别日配额耗尽：429 body 内业务码 160003
                if response.status_code == 429:
                    payload = _safe_json(response)
                    code = (payload or {}).get('code')
                    if code in QUOTA_EXCEEDED_CODES:
                        raise DailyQuotaExceeded((payload or {}).get('message') or 'BestBlogs 日配额已耗尽')
                    response.raise_for_status()
                else:
                    response.raise_for_status()
                payload = response.json()
                if not payload.get('success'):
                    raise Exception(payload.get('message') or 'BestBlogs API request failed')
                return payload.get('data')
            except DailyQuotaExceeded:
                raise
            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code
                # 仅对限流 / 服务端错误重试；4xx 客户端错误直接抛出
                if status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                    wait = BASE_BACKOFF * (2 ** attempt)
                    print(f'[{self.name}] API {status_code}，{wait:.1f}s 后重试 ({attempt + 1}/{MAX_RETRIES})...')
                    await asyncio.sleep(wait)
                    continue
                raise
            except Exception:
                raise
        raise last_error or Exception('BestBlogs API request failed after retries')

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
        """从多种可能字段解析发布时间（统一转为 UTC ISO 格式）"""
        # Unix 时间戳为 UTC
        ts = item.get('publishTimeStamp')
        if isinstance(ts, (int, float)) and ts > 0:
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()

        # 字符串日期/时间按北京时间解析后转 UTC
        dt_str = item.get('publishDateTimeStr')
        if dt_str:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
                try:
                    dt = datetime.strptime(dt_str, fmt).replace(tzinfo=CHINA_TZ)
                    return dt.astimezone(timezone.utc).isoformat()
                except ValueError:
                    continue

        date_str = item.get('publishDateStr')
        if date_str == '今天':
            return datetime.now(CHINA_TZ).astimezone(timezone.utc).isoformat()
        if date_str:
            for fmt in ('%Y-%m-%d',):
                try:
                    dt = datetime.strptime(date_str, fmt).replace(tzinfo=CHINA_TZ)
                    return dt.astimezone(timezone.utc).isoformat()
                except ValueError:
                    continue

        return None

    @staticmethod
    def _extract_resource_id(url: str) -> Optional[str]:
        """从 BestBlogs 站内链接中提取资源 ID"""
        if not url:
            return None
        url = url.rstrip('/')
        for prefix in ('https://www.bestblogs.dev/read/', 'https://bestblogs.dev/read/',
                       'https://www.bestblogs.dev/article/', 'https://bestblogs.dev/article/'):
            if url.startswith(prefix):
                return url[len(prefix):]
        return None

    def _article_from_resource(self, item: Dict[str, Any], tag: str) -> Optional[Dict[str, Any]]:
        """将 BestBlogs 资源对象转换为统一文章格式"""
        title = item.get('title') or item.get('originalTitle')
        if not title:
            return None

        original_url = item.get('url') or ''
        read_url = item.get('readUrl') or ''
        # 尝试多种字段名获取资源 ID，兼容简报(resourceId)与热门(id)等不同接口
        resource_id = (
            item.get('id')
            or item.get('resourceId')
            or self._extract_resource_id(read_url)
            or self._extract_resource_id(original_url)
        )

        # platform_url 必须指向 BestBlogs 站内页面（阅读页 / 讨论页），优先使用接口返回的 readUrl
        if read_url:
            platform_url = read_url
        elif original_url and self._extract_resource_id(original_url):
            platform_url = original_url
        elif resource_id:
            platform_url = f'https://www.bestblogs.dev/article/{resource_id}'
        else:
            platform_url = ''

        # url 用于 merge 去重：优先保留原文链接；没有原文链接时回退到 BestBlogs 站内链接
        url = original_url or platform_url
        if not platform_url and url:
            platform_url = url

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
        """抓取每日公开简报（/briefs/latest 自动取最新一期，规避当日未发布/周日无版的空窗）"""
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

            # 简报接口已包含 url / readUrl / cover / score 等字段，无需额外调用详情接口
            article = self._article_from_resource(item, '早报')
            if article:
                articles.append(article)

        return articles

    async def crawl_trending(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """抓取近 7 天热门精选（period=week 比 period=today 稳定，避免早晨「今日热门」尚未积累的空结果）"""
        print(f'[{self.name}] 获取热门精选...')
        data = await self.fetch_json(client, f'{API_BASE}/resources/trending?period=week&limit=10')
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
            # 分别捕获异常，避免一个接口失败导致整个平台无数据
            briefs = []
            quota_exhausted = False
            try:
                briefs = await self.crawl_briefs(client)
            except DailyQuotaExceeded as e:
                print(f'[{self.name}] 日配额耗尽，跳过本平台后续调用: {str(e)}')
                quota_exhausted = True
            except Exception as e:
                print(f'[{self.name}] 简报抓取失败: {str(e)}')

            if not quota_exhausted and briefs:
                await asyncio.sleep(REQUEST_DELAY)

            trending = []
            # 简报已命中日配额则跳过热门，省下最后一次调用额度
            if not quota_exhausted:
                try:
                    trending = await self.crawl_trending(client)
                except DailyQuotaExceeded as e:
                    print(f'[{self.name}] 日配额耗尽，跳过热门: {str(e)}')
                except Exception as e:
                    print(f'[{self.name}] 热门精选抓取失败: {str(e)}')

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
