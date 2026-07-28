#!/usr/bin/env python3
"""HuggingFace 爬虫 — 官方公开 API（免 key）

策略：
1. 每日论文榜 /api/daily_papers：按 upvotes 取 Top N（真实热度）
2. Trending 模型榜 /api/models?sort=trendingScore：限定 text-generation（LLM 方向）取 Top N

热度字段均为 HF 官方真实数据：
- 论文：score = upvotes，comments_count = numComments
- 模型：score = likes，附 downloads / trendingScore
"""

import asyncio
from typing import List, Dict, Any
from crawlers.base import BaseCrawler


class HuggingFaceCrawler(BaseCrawler):
    """HuggingFace 爬虫（每日论文 + Trending 模型）"""

    def __init__(self):
        super().__init__(name='huggingface', timeout=30)
        self.papers_url = 'https://huggingface.co/api/daily_papers'
        self.models_url = (
            'https://huggingface.co/api/models'
            '?sort=trendingScore&pipeline_tag=text-generation&limit=10&full=false'
        )

    async def crawl_papers(self, top_n: int) -> List[Dict[str, Any]]:
        """每日论文榜：按 upvotes 降序取 Top N"""
        data = await self.fetch_json(self.papers_url)
        if not isinstance(data, list):
            return []

        def get_upvotes(entry: Dict[str, Any]) -> int:
            return entry.get('upvotes') or (entry.get('paper') or {}).get('upvotes') or 0

        data.sort(key=get_upvotes, reverse=True)

        articles = []
        for entry in data[:top_n]:
            try:
                paper = entry.get('paper') or {}
                paper_id = paper.get('id', '')
                title = entry.get('title') or paper.get('title', '')
                if not paper_id or not title:
                    continue

                articles.append({
                    'title': title,
                    'url': f'https://huggingface.co/papers/{paper_id}',
                    'cover_url': entry.get('thumbnail') or None,
                    'publish_time': entry.get('publishedAt'),
                    'tags': ['论文'] + [t for t in (paper.get('keywords') or [])][:3],
                    'summary': (entry.get('summary') or paper.get('summary') or '')[:500],
                    'platform': self.name,
                    # HF 官方真实互动数据
                    'score': get_upvotes(entry),
                    'comments_count': entry.get('numComments') or 0,
                })
            except Exception as e:
                print(f"[{self.name}] 解析论文失败: {str(e)}")
                continue
        return articles

    async def crawl_models(self, top_n: int) -> List[Dict[str, Any]]:
        """Trending 模型榜（text-generation）：按 trendingScore 取 Top N"""
        data = await self.fetch_json(self.models_url)
        if not isinstance(data, list):
            return []

        articles = []
        for model in data[:top_n]:
            try:
                model_id = model.get('id') or model.get('modelId', '')
                if not model_id:
                    continue

                likes = model.get('likes') or 0
                downloads = model.get('downloads') or 0
                trending = model.get('trendingScore')
                summary = f"TrendingScore {trending} · 下载 {downloads:,}" if trending is not None \
                    else f"下载 {downloads:,}"

                articles.append({
                    'title': f"[模型] {model_id}",
                    'url': f'https://huggingface.co/{model_id}',
                    'cover_url': None,
                    'publish_time': model.get('createdAt'),
                    'tags': ['模型', model.get('pipeline_tag') or 'text-generation'],
                    'summary': summary,
                    'platform': self.name,
                    # HF 官方真实互动数据
                    'score': likes,
                    'trending_score': trending,
                    'downloads': downloads,
                })
            except Exception as e:
                print(f"[{self.name}] 解析模型失败: {str(e)}")
                continue
        return articles

    async def crawl(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        执行爬虫：论文榜 + 模型榜各取 Top N，合并返回

        Args:
            top_n: 每个榜单取前N篇（默认10；merge 阶段会再按时间截断到平台 Top10）

        Returns:
            文章列表
        """
        print(f"[{self.name}] 开始抓取: 每日论文榜 + Trending 模型榜")

        papers, models = await asyncio.gather(
            self.crawl_papers(top_n),
            self.crawl_models(top_n),
        )

        print(f"[{self.name}] 论文 {len(papers)} 篇 · 模型 {len(models)} 篇")
        return papers + models


async def crawl_huggingface(top_n: int = 10) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = HuggingFaceCrawler()
    return await crawler.crawl(top_n=top_n)


if __name__ == '__main__':
    articles = asyncio.run(crawl_huggingface(top_n=10))
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   链接: {article['url']} | score: {article.get('score')}")
