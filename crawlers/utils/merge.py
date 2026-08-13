#!/usr/bin/env python3
"""数据合并与去重 - 支持新旧数据合并、7天筛选、保留Top10"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List

OUTPUT_FILE = Path('data/news.json')
DAYS_LIMIT = 7  # 只保留7天内的文章
TOP_N = 10  # 每个平台保留Top10
# 部分平台聚合多个数据源，允许保留更多条数
PLATFORM_TOP_N = {
    'huggingface': 20,  # 每日论文 10 + Trending 模型 10
    'bestblogs': 20,    # 早报 + 精选两个来源合并后保留最多 20
}
REMOVED_PLATFORMS = {'googleai', 'techcrunch', 'aiera'}  # 已下线的平台，旧数据不再合并


def _parse_time(article: Dict) -> datetime:
    """解析文章发布时间，失败时返回最小时间"""
    try:
        t = (article.get('publish_time') or '').replace('Z', '+00:00')
        dt = datetime.fromisoformat(t)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


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


def _is_hf_model(article: Dict) -> bool:
    """判断是否为 HuggingFace Trending 模型（不受 7 天时间窗限制）"""
    tags = article.get('tags') or []
    return '模型' in tags


def _is_bb_featured(article: Dict) -> bool:
    """判断是否为 BestBlogs 精选内容（按热度/质量推荐，不受 7 天时间窗限制）"""
    tags = article.get('tags') or []
    return '精选' in tags


def filter_by_time_and_topn(articles: List[Dict], top_n: int = TOP_N, platform: str = '') -> List[Dict]:
    """
    筛选7天内的文章，并按发布时间保留Top N
    
    HuggingFace Trending 模型按 trendingScore 排序，代表当前热度，不受 7 天创建时间限制。
    
    Args:
        articles: 文章列表
        top_n: 保留条数（默认 TOP_N）
        platform: 平台标识（用于特殊规则）
        
    Returns:
        筛选后的文章列表
    """
    # 筛选7天内的文章；HuggingFace 模型 / BestBlogs 精选跳过时间窗
    recent_articles = [
        article for article in articles
        if (platform == 'huggingface' and _is_hf_model(article))
        or (platform == 'bestblogs' and _is_bb_featured(article))
        or is_within_days(article.get('publish_time', ''))
    ]
    
    # 按发布时间倒序并取 Top N（热度分已移除，见 main.py 说明）
    sorted_articles = sorted(recent_articles, key=_parse_time, reverse=True)
    return sorted_articles[:top_n]


def merge_and_deduplicate(all_news: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    合并新旧数据并去重，保留7天内最新 Top10

    流程：
    1. 加载旧数据（跳过已下线平台）
    2. 新旧数据合并
    3. 按URL去重（新数据覆盖旧数据）
    4. 筛选7天内文章
    5. 按时间保留最新Top10
    
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
    seen_resource_ids = {}

    def _add_index(platform: str, index: int, article: Dict):
        """维护 url 与 resource_id 的索引映射"""
        url_key = article.get('url', '')
        if url_key:
            seen_urls[url_key] = (platform, index)
        rid = article.get('resource_id')
        if rid:
            seen_resource_ids[(platform, rid)] = (platform, index)

    def _replace_article(old_platform: str, old_index: int, new_platform: str, article: Dict):
        """用新文章替换旧文章，并更新索引"""
        if old_platform == new_platform:
            merged[new_platform][old_index] = article
            _add_index(new_platform, old_index, article)
        else:
            merged[old_platform][old_index] = {}
            merged[new_platform].append(article)
            _add_index(new_platform, len(merged[new_platform]) - 1, article)

    # 先处理旧数据（跳过已下线平台）
    for platform, articles in existing_news.items():
        if platform in REMOVED_PLATFORMS:
            print(f"[Merge] 跳过已下线平台: {platform}（{len(articles)} 条旧数据）")
            continue
        merged[platform] = []
        for article in articles:
            article['id'] = generate_id(
                platform,
                article.get('title', ''),
                article.get('url', '')
            )
            _add_index(platform, len(merged[platform]), article)
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
            rid = article.get('resource_id')
            rid_key = (platform, rid) if rid else None

            if rid_key and rid_key in seen_resource_ids:
                # 同一平台同一 resource_id 优先去重（适用于 BestBlogs 等 url 不稳定的场景）
                old_platform, old_index = seen_resource_ids[rid_key]
                _replace_article(old_platform, old_index, platform, article)
            elif url_key and url_key in seen_urls:
                # 按 URL 去重
                old_platform, old_index = seen_urls[url_key]
                _replace_article(old_platform, old_index, platform, article)
            elif url_key or rid:
                # 新数据：至少要有 url 或 resource_id 才保留
                merged[platform].append(article)
                _add_index(platform, len(merged[platform]) - 1, article)
    
    # 过滤被标记删除的空条目
    for platform in merged:
        merged[platform] = [a for a in merged[platform] if a]
    
    total_before_filter = sum(len(v) for v in merged.values())
    print(f"[Merge] 合并后共 {total_before_filter} 条（去重后）")
    
    # 筛选7天内热度Top N（按平台规则）
    filtered = {}
    for platform, articles in merged.items():
        platform_top_n = PLATFORM_TOP_N.get(platform, TOP_N)
        filtered[platform] = filter_by_time_and_topn(articles, top_n=platform_top_n, platform=platform)
        print(f"[Merge] {platform}: {len(articles)} -> {len(filtered[platform])} 条")
    
    total_after_filter = sum(len(v) for v in filtered.values())
    print(f"[Merge] 筛选后共 {total_after_filter} 条（7天内Top{TOP_N}）")
    
    return filtered
