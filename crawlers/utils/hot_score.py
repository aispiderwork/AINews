#!/usr/bin/env python3
"""热度计算工具模块 - 提供多维度热度分计算"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

# 平台权重配置（基于平台影响力）
PLATFORM_WEIGHTS = {
    'hackernews': 1.0,      # 国际技术社区，权重最高
    'techcrunch': 0.9,      # 国际科技媒体
    'googleai': 0.85,       # 官方博客
    'qbitai': 0.8,          # 国内头部AI媒体
    'aiera': 0.75,          # 国内AI媒体
    'radarai': 0.7,         # 新兴AI平台
}

# Hacker News热度分权重
HN_SCORE_WEIGHT = 0.7
HN_COMMENTS_WEIGHT = 0.3

# 时间衰减配置
TIME_DECAY_HOURS = 240    # 10天后降至最低
TIME_DECAY_MIN = 0.1      # 最低时间因子


def calc_hn_hot_score(score: int, descendants: int) -> float:
    """
    计算Hacker News热度分
    
    Args:
        score: HN投票得分
        descendants: HN评论数
        
    Returns:
        HN热度分
    """
    return score * HN_SCORE_WEIGHT + descendants * HN_COMMENTS_WEIGHT


def calc_time_factor(publish_time: str) -> float:
    """
    计算时间衰减因子
    
    规则：
    - 24小时内 = 1.0
    - 每过一天衰减0.1
    - 10天后降至0.1
    
    Args:
        publish_time: ISO格式时间字符串
        
    Returns:
        时间因子 (0.1 - 1.0)
    """
    try:
        if not publish_time:
            return TIME_DECAY_MIN
            
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
            
        now = datetime.now(timezone.utc)
        hours_ago = (now - dt).total_seconds() / 3600
        
        # 计算时间因子
        factor = 1.0 - (hours_ago / TIME_DECAY_HOURS)
        return max(TIME_DECAY_MIN, min(1.0, factor))
        
    except Exception as e:
        print(f"[HotScore] 时间因子计算失败: {e}")
        return TIME_DECAY_MIN


def calc_hot_score(article: Dict[str, Any]) -> float:
    """
    计算文章综合热度分
    
    公式：
    hot_score = (
        platform_weight * 0.3 +           # 平台权重 30%
        time_factor * 0.4 +               # 时间因子 40%
        hn_hot_score_normalized * 0.3     # HN热度分 30%（仅HN有）
    )
    
    Args:
        article: 文章数据字典
        
    Returns:
        综合热度分
    """
    platform = article.get('platform', '')
    
    # 获取平台权重
    platform_weight = PLATFORM_WEIGHTS.get(platform, 0.5)
    
    # 计算时间因子
    publish_time = article.get('publish_time', '')
    time_factor = calc_time_factor(publish_time)
    
    # HN热度分（仅Hacker News有）
    hn_hot_score_normalized = 0
    if platform == 'hackernews':
        score = article.get('score', 0) or 0
        descendants = article.get('comments_count', 0) or 0
        hn_raw_score = calc_hn_hot_score(score, descendants)
        # 归一化：假设最高500分
        hn_hot_score_normalized = min(1.0, hn_raw_score / 500)
    
    # 计算综合热度分
    hot_score = (
        platform_weight * 0.3 +
        time_factor * 0.4 +
        hn_hot_score_normalized * 0.3
    )
    
    return round(hot_score, 4)


def add_hot_score_to_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    为文章添加热度相关字段
    
    Args:
        article: 原始文章数据
        
    Returns:
        添加热度字段后的文章数据
    """
    platform = article.get('platform', '')
    publish_time = article.get('publish_time', '')
    
    # 计算并添加热度字段
    article['hot_score'] = calc_hot_score(article)
    article['time_factor'] = calc_time_factor(publish_time)
    article['platform_weight'] = PLATFORM_WEIGHTS.get(platform, 0.5)
    
    # Hacker News特有字段
    if platform == 'hackernews':
        score = article.get('score', 0) or 0
        descendants = article.get('comments_count', 0) or 0
        article['hn_hot_score'] = calc_hn_hot_score(score, descendants)
    else:
        article['hn_hot_score'] = None
    
    return article


def sort_by_hot_score(articles: list) -> list:
    """
    按热度分排序文章列表
    
    Args:
        articles: 文章列表
        
    Returns:
        按热度分降序排列的文章列表
    """
    # 为每篇文章计算热度分
    scored_articles = [add_hot_score_to_article(article) for article in articles]
    
    # 按热度分降序排序
    sorted_articles = sorted(
        scored_articles,
        key=lambda x: (x.get('hot_score', 0), x.get('publish_time', '')),
        reverse=True
    )
    
    return sorted_articles


def get_platform_hot_stats(articles: list) -> Dict[str, Any]:
    """
    获取各平台热度统计
    
    Args:
        articles: 文章列表
        
    Returns:
        各平台热度统计信息
    """
    stats = {}
    
    for platform in PLATFORM_WEIGHTS.keys():
        platform_articles = [a for a in articles if a.get('platform') == platform]
        if platform_articles:
            hot_scores = [a.get('hot_score', 0) for a in platform_articles]
            stats[platform] = {
                'count': len(platform_articles),
                'avg_hot_score': round(sum(hot_scores) / len(hot_scores), 4),
                'max_hot_score': round(max(hot_scores), 4),
                'min_hot_score': round(min(hot_scores), 4),
            }
    
    return stats
