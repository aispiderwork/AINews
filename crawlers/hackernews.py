#!/usr/bin/env python3
"""Hacker News 爬虫 - 使用官方 Firebase API"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone
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
    
    async def get_top_stories(self, limit: int = 30) -> List[int]:
        """获取热门文章ID列表"""
        url = f'{self.api_base}/topstories.json'
        story_ids = await self.fetch_json(url)
        return story_ids[:limit]
    
    async def crawl(self, limit: int = 30, filter_ai: bool = True) -> List[Dict[str, Any]]:
        """
        执行爬虫
        
        Args:
            limit: 获取文章数量上限
            filter_ai: 是否过滤AI相关文章（默认True，只保留AI相关）
            
        Returns:
            文章列表
        """
        print(f"[{self.name}] 开始获取热门文章...")
        
        story_ids = await self.get_top_stories(limit=limit)
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
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"[{self.name}] 获取文章 {story_id} 失败: {str(e)}")
                continue
        
        if filter_ai:
            original_count = len(articles)
            articles = [a for a in articles if self.is_ai_related(a['title'])]
            print(f"[{self.name}] AI过滤: {original_count} -> {len(articles)} 篇")
        else:
            print(f"[{self.name}] 获取到 {len(articles)} 篇文章")
        
        return articles


async def crawl_hackernews(limit: int = 30, filter_ai: bool = True) -> List[Dict[str, Any]]:
    """模块入口函数"""
    crawler = HackerNewsCrawler()
    return await crawler.crawl(limit=limit, filter_ai=filter_ai)


if __name__ == '__main__':
    articles = asyncio.run(crawl_hackernews(limit=20))
    print(f"\n获取到 {len(articles)} 篇AI相关文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']} (score: {article['score']})")
