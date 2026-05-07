from datetime import datetime
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.crawlers.base_crawler import BaseCrawler


class XiaohongshuCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('xiaohongshu')
    
    def fetch_hotlist(self) -> List[Dict]:
        items = []
        sample_titles = [
            "AI绘画工具推荐 | 新手也能画出大片",
            "ChatGPT实用技巧分享",
            "2026必用的AI生产力工具",
            "用AI做视频太简单了！"
        ]
        
        for idx, title in enumerate(sample_titles, 1):
            item = {
                'id': self.generate_id(f"xiaohongshu_{idx}"),
                'platform': 'xiaohongshu',
                'source': 'hotlist',
                'title': title,
                'url': f'https://www.xiaohongshu.com/explore/{idx}',
                'cover_url': None,
                'content': '',
                'hot_value': (100 - idx) * 100,
                'hot_rank': idx,
                'publish_time': datetime.now().isoformat(),
                'author': f'博主{idx}',
                'tags': ['AI', '教程'],
                'crawl_time': datetime.now().isoformat(),
                'metrics': {
                    'like_count': f"{random.randint(1000, 10000)}",
                    'collect_count': f"{random.randint(500, 5000)}"
                }
            }
            items.append(item)
            self.hotlist_items += 1
        
        return items


class XCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('x')
    
    def fetch_hotlist(self) -> List[Dict]:
        items = []
        sample_titles = [
            "Claude 3 最新更新来了",
            "OpenAI CEO最新访谈",
            "AI Agent技术突破"
        ]
        
        for idx, title in enumerate(sample_titles, 1):
            item = {
                'id': self.generate_id(f"x_{idx}"),
                'platform': 'x',
                'source': 'hotlist',
                'title': title,
                'url': f'https://twitter.com/status/{idx}',
                'cover_url': None,
                'content': '',
                'hot_value': (100 - idx) * 100,
                'hot_rank': idx,
                'publish_time': datetime.now().isoformat(),
                'author': f'@tech{idx}',
                'tags': ['AI', '科技'],
                'crawl_time': datetime.now().isoformat(),
                'metrics': {
                    'retweet_count': f"{random.randint(1000, 10000)}",
                    'like_count': f"{random.randint(5000, 50000)}"
                }
            }
            items.append(item)
            self.hotlist_items += 1
        
        return items


class FacebookCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('facebook')
    
    def fetch_hotlist(self) -> List[Dict]:
        items = []
        sample_titles = [
            "Meta AI 最新开源项目",
            "AI技术前沿动态"
        ]
        
        for idx, title in enumerate(sample_titles, 1):
            item = {
                'id': self.generate_id(f"facebook_{idx}"),
                'platform': 'facebook',
                'source': 'hotlist',
                'title': title,
                'url': f'https://facebook.com/post/{idx}',
                'cover_url': None,
                'content': '',
                'hot_value': (100 - idx) * 100,
                'hot_rank': idx,
                'publish_time': datetime.now().isoformat(),
                'author': f'Tech Page {idx}',
                'tags': ['AI', '科技'],
                'crawl_time': datetime.now().isoformat(),
                'metrics': {
                    'share_count': f"{random.randint(500, 5000)}",
                    'like_count': f"{random.randint(2000, 20000)}"
                }
            }
            items.append(item)
            self.hotlist_items += 1
        
        return items


import random
