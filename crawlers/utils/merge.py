#!/usr/bin/env python3
"""数据合并与去重"""

import hashlib
from typing import Dict, List


def generate_id(platform: str, title: str, url: str) -> str:
    """生成唯一ID"""
    content = f"{platform}:{title}:{url}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def merge_and_deduplicate(all_news: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """合并各平台新闻并去重"""
    merged = {}
    seen_urls = set()
    
    for platform, articles in all_news.items():
        merged[platform] = []
        for article in articles:
            article['id'] = generate_id(
                platform,
                article.get('title', ''),
                article.get('url', '')
            )
            
            url_key = article.get('url', '')
            if url_key and url_key in seen_urls:
                continue
            
            seen_urls.add(url_key)
            merged[platform].append(article)
    
    return merged
