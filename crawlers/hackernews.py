#!/usr/bin/env python3
"""Hacker News 爬虫 - 使用官方 Firebase API

策略：获取足够多的文章，筛选近7天的AI相关文章，按HN热度(score+comments)取前10
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from crawlers.base import BaseCrawler

AI_KEYWORDS = [
    'ai', 'llm', 'gpt', 'claude', 'openai', 'anthropic', 'google ai', 'deepmind',
    'machine learning', '机器学习', 'deep learning', '深度学习', 'neural network',
    'transformer', 'bert', 'llama', 'mistral', 'agent', '智能体', 'copilot',
    '大模型', 'foundation model', 'agi', 'artificial general intelligence',
    'computer vision', 'nlp', 'natural language processing', 'rag',
    'retrieval augmented generation', 'fine-tuning', 'prompt', '多模态',
    'multimodal', 'gemini', 'palm', 'bard', 'midjourney', 'stable diffusion',
    'dall-e', 'ai safety', 'ai regulation', 'llm', 'chatbot', 'generative ai',
]

# 7天前的时间戳
def get_7days_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=7)


class HackerNewsCrawler(BaseCrawler):
    """Hacker News 爬虫"""
    
    def __init__(self):
        super().__init__(name='hackernews', timeout=30)
        self.api_base = 'https://hacker-news.firebaseio.com/v0'
    
    @staticmethod
    def is_ai_related(title: str, summary: str = '') -> bool:
        """判断是否为AI相关新闻"""
        text = (title + ' ' + summary).lower()
        return any(keyword.lower() in text for keyword in AI_KEYWORDS)
    
    async def get_story(self, story_id: int) -> Dict[str, Any]:
        """获取单篇文章详情"""
        url = f'{self.api_base}/item/{story_id}.json'
        return await self.fetch_json(url)
    
    async def get_top_stories(self, limit: int = 100) -> List[int]:
        """获取热门文章ID列表（获取更多以确保有足够近7天的数据）"""
        url = f'{self.api_base}/topstories.json'
        story_ids = await self.fetch_json(url)
        return story_ids[:limit]
    
    def is_within_7days(self, timestamp: int) -> bool:
        """判断时间是否在7天内"""
        if not timestamp:
            return False
        publish_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return publish_dt >= get_7days_ago()
    
    def calc_hn_hot_score(self, score: int, descendants: int) -> float:
        """计算HN热度分 = 投票分*0.7 + 评论数*0.3"""
        return score * 0.7 + descendants * 0.3
    
    async def crawl(self, top_n: int = 10, filter_ai: bool = True) -> List[Dict[str, Any]]:
        """
        执行爬虫 - 获取近7天内热度最高的AI相关文章
        
        Args:
            top_n: 取热度前N篇文章（默认10）
            filter_ai: 是否过滤AI相关文章
            
        Returns:
            文章列表（按HN热度降序）
        """
        print(f"[{self.name}] 开始获取热门文章（筛选近7天）...")
        
        # 获取更多文章以确保有足够近7天的数据
        story_ids = await self.get_top_stories(limit=100)
        print(f"[{self.name}] 获取到 {len(story_ids)} 篇热门文章ID")
        
        articles = []
        for i, story_id in enumerate(story_ids):
            try:
                story = await self.get_story(story_id)
                
                if not story or 'title' not in story:
                    continue
                
                title = story.get('title', '')
                source_url = story.get('url', '')
                hn_url = f'https://news.ycombinator.com/item?id={story_id}'
                score = story.get('score', 0)
                descendants = story.get('descendants', 0)
                timestamp = story.get('time', 0)
                
                # 筛选近7天的文章
                if not self.is_within_7days(timestamp):
                    continue
                
                publish_time = None
                if timestamp:
                    publish_time = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                
                article = {
                    'title': title,
                    'url': source_url if source_url else hn_url,
                    'discussion_url': hn_url,
                    'score': score,
                    'comments_count': descendants,
                    'publish_time': publish_time,
                    'platform': self.name,
                    'hn_hot_score': self.calc_hn_hot_score(score, descendants),
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"[{self.name}] 获取文章 {story_id} 失败: {str(e)}")
                continue
        
        print(f"[{self.name}] 近7天文章: {len(articles)} 篇")
        
        # AI关键词过滤
        if filter_ai:
            original_count = len(articles)
            articles = [a for a in articles if self.is_ai_related(a['title'])]
            print(f"[{self.name}] AI过滤: {original_count} -> {len(articles)} 篇")
        
        # 按HN热度分降序排序，取前N
        articles.sort(key=lambda x: x.get('hn_hot_score', 0), reverse=True)
        articles = articles[:top_n]
        
        print(f"[{self.name}] 最终获取热度Top{top_n}: {len(articles)} 篇")
        return articles


async def crawl_hackernews(top_n: int = 10, filter_ai: bool = True) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = HackerNewsCrawler()
    return await crawler.crawl(top_n=top_n, filter_ai=filter_ai)


if __name__ == '__main__':
    articles = asyncio.run(crawl_hackernews(limit=20))
    print(f"\n获取到 {len(articles)} 篇AI相关文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']} (score: {article['score']})")
