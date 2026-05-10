#!/usr/bin/env python3
"""数据合并与去重 - 支持新旧数据合并、7天筛选、保留Top10"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List

from .hot_score import sort_by_hot_score

OUTPUT_FILE = Path('data/news.json')
DAYS_LIMIT = 7  # 只保留7天内的文章
TOP_N = 10  # 每个平台保留Top10


def generate_id(platform: str, title: str, url: str) -> str:
    """生成唯一ID"""
    content = f"{platform}:{title}:{url}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def load_existing_data() -> Dict[str, List[Dict]]:
    """加载已存在的旧数据"""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('news', {})
        except Exception as e:
            print(f"[Merge] 加载旧数据失败: {e}")
    return {}


def is_within_days(publish_time: str, days: int = DAYS_LIMIT) -> bool:
    """检查文章是否在指定天数内发布"""
    if not publish_time:
        return False
    
    try:
        # 解析时间
        if isinstance(publish_time, str):
            if publish_time.endswith('Z'):
                publish_time = publish_time.replace('Z', '+00:00')
            dt = datetime.fromisoformat(publish_time)
        else:
            dt = publish_time
        
        # 确保有时区信息
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # 计算是否在最近days天内
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(days=days)
        return dt >= cutoff_time
        
    except Exception as e:
        print(f"[Merge] 时间解析失败: {e}")
        return False


def filter_by_time_and_topn(articles: List[Dict]) -> List[Dict]:
    """
    筛选7天内的文章，并按热度保留Top N
    
    Args:
        articles: 文章列表
        
    Returns:
        筛选后的文章列表
    """
    # 筛选7天内的文章
    recent_articles = [
        article for article in articles
        if is_within_days(article.get('publish_time', ''))
    ]
    
    # 按热度排序并取Top N
    sorted_articles = sort_by_hot_score(recent_articles)
    return sorted_articles[:TOP_N]


def merge_and_deduplicate(all_news: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    合并新旧数据并去重，保留7天内热度Top10
    
    流程：
    1. 加载旧数据
    2. 新旧数据合并
    3. 按URL去重（新数据覆盖旧数据）
    4. 筛选7天内文章
    5. 按热度保留Top10
    
    Args:
        all_news: 新抓取的平台数据 {platform: [articles]}
        
    Returns:
        合并去重筛选后的数据 {platform: [articles]}
    """
    # 加载旧数据
    existing_news = load_existing_data()
    print(f"[Merge] 加载旧数据: {sum(len(v) for v in existing_news.values())} 条")
    
    # 合并新旧数据（新数据覆盖旧数据）
    merged = {}
    seen_urls = {}
    
    # 先处理旧数据
    for platform, articles in existing_news.items():
        merged[platform] = []
        for article in articles:
            article['id'] = generate_id(
                platform,
                article.get('title', ''),
                article.get('url', '')
            )
            url_key = article.get('url', '')
            if url_key:
                seen_urls[url_key] = (platform, len(merged[platform]))
            merged[platform].append(article)
    
    # 再处理新数据（覆盖旧数据）
    for platform, articles in all_news.items():
        if platform not in merged:
            merged[platform] = []
        
        for article in articles:
            article['id'] = generate_id(
                platform,
                article.get('title', ''),
                article.get('url', '')
            )
            
            url_key = article.get('url', '')
            if not url_key:
                continue
            
            if url_key in seen_urls:
                # 已存在，替换旧数据
                old_platform, old_index = seen_urls[url_key]
                if old_platform == platform:
                    merged[platform][old_index] = article
                else:
                    # URL相同但平台不同，保留新数据
                    merged[old_platform].pop(old_index)
                    merged[platform].append(article)
                    seen_urls[url_key] = (platform, len(merged[platform]) - 1)
            else:
                # 新数据
                seen_urls[url_key] = (platform, len(merged[platform]))
                merged[platform].append(article)
    
    total_before_filter = sum(len(v) for v in merged.values())
    print(f"[Merge] 合并后共 {total_before_filter} 条（去重后）")
    
    # 筛选7天内热度Top10
    filtered = {}
    for platform, articles in merged.items():
        filtered[platform] = filter_by_time_and_topn(articles)
        print(f"[Merge] {platform}: {len(articles)} -> {len(filtered[platform])} 条")
    
    total_after_filter = sum(len(v) for v in filtered.values())
    print(f"[Merge] 筛选后共 {total_after_filter} 条（7天内Top{TOP_N}）")
    
    return filtered
