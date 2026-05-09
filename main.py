#!/usr/bin/env python3
"""AI News Crawler - 主入口程序"""

import json
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from crawlers.hackernews import crawl_hackernews
from crawlers.techcrunch import crawl_techcrunch
from crawlers.qbitai import crawl_qbitai
from crawlers.aiera import crawl_aiera
from crawlers.radarai import crawl_radarai
from crawlers.googleai import crawl_googleai
from crawlers.utils.merge import merge_and_deduplicate
from crawlers.utils.hot_score import sort_by_hot_score, get_platform_hot_stats, calculate_hot_score

PLATFORMS = {
    'hackernews': {'name': 'Hacker News', 'func': crawl_hackernews, 'priority': 1},
    'techcrunch': {'name': 'TechCrunch', 'func': crawl_techcrunch, 'priority': 2},
    'qbitai': {'name': '量子位', 'func': crawl_qbitai, 'priority': 3},
    'aiera': {'name': '新智元', 'func': crawl_aiera, 'priority': 4},
    'radarai': {'name': 'RadarAI', 'func': crawl_radarai, 'priority': 5},
    'googleai': {'name': 'Google AI Blog', 'func': crawl_googleai, 'priority': 6},
}

OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'news.json'
HISTORY_FILE = OUTPUT_DIR / 'history.json'
MAX_HISTORY = 100
DAYS_WINDOW = 7  # 保留7天内的数据
TOP_N_PER_PLATFORM = 10  # 每平台保留热度Top10


def load_existing_data() -> dict:
    """加载现有数据（用于累积）"""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  [警告] 读取现有数据失败: {e}")
    return {'sorted_all': []}


def is_within_days(publish_time: str, days: int = DAYS_WINDOW) -> bool:
    """检查文章是否在指定天数内"""
    if not publish_time:
        return False
    try:
        pub_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        return pub_time >= cutoff_time
    except Exception:
        return False


def merge_with_existing(new_articles: list, existing_articles: list) -> list:
    """合并新旧数据并去重（基于URL）"""
    # 使用URL作为唯一标识
    seen_urls = set()
    merged = []
    
    # 先添加新数据（优先级更高，可以覆盖旧数据）
    for article in new_articles:
        url = article.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            merged.append(article)
    
    # 再添加旧数据中不存在的
    for article in existing_articles:
        url = article.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            merged.append(article)
    
    return merged


def filter_and_limit_by_platform(articles: list, days: int = DAYS_WINDOW, top_n: int = TOP_N_PER_PLATFORM) -> list:
    """按平台分组，过滤7天内数据，取每平台热度TopN"""
    # 按平台分组
    by_platform = {}
    for article in articles:
        platform = article.get('platform', 'unknown')
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(article)
    
    result = []
    for platform, platform_articles in by_platform.items():
        # 过滤7天内
        recent_articles = [a for a in platform_articles if is_within_days(a.get('publish_time'), days)]
        
        # 重新计算热度分（因为时间因子会变化）
        for article in recent_articles:
            article['hot_score'] = calculate_hot_score(article)
        
        # 按热度排序，取TopN
        recent_articles.sort(key=lambda x: x.get('hot_score', 0), reverse=True)
        top_articles = recent_articles[:top_n]
        
        result.extend(top_articles)
        print(f"  [{platform}] 保留 {len(top_articles)}/{len(recent_articles)} 篇 (7天内热度Top{top_n})")
    
    return result


def load_history() -> dict:
    """加载历史记录"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'executions': []}


def save_history(history: dict):
    """保存历史记录"""
    if len(history['executions']) > MAX_HISTORY:
        history['executions'] = history['executions'][-MAX_HISTORY:]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def append_history_record(record: dict):
    """追加单次执行记录"""
    history = load_history()
    history['executions'].append(record)
    save_history(history)


async def main(target_platform=None):
    """主爬虫流程"""
    start_time = datetime.now(timezone.utc)
    trigger = sys.argv[2] if len(sys.argv) > 2 else 'manual'

    if target_platform and target_platform in PLATFORMS:
        platforms_to_crawl = {target_platform: PLATFORMS[target_platform]}
    else:
        platforms_to_crawl = PLATFORMS

    all_news = {}
    monitor_data = {
        'platforms': [],
        'failure_reasons': {},
        'recent_executions': []
    }

    for platform_key in sorted(platforms_to_crawl.keys(), key=lambda k: platforms_to_crawl[k]['priority']):
        config = platforms_to_crawl[platform_key]
        print(f"\n{'='*60}")
        print(f"开始抓取: {config['name']}")
        print(f"{'='*60}")
        exec_start = datetime.now(timezone.utc)

        try:
            articles = await config['func']()
            all_news[platform_key] = articles

            monitor_data['platforms'].append({
                'platform': platform_key,
                'name': config['name'],
                'status': 'online',
                'item_count': len(articles),
                'last_crawl': datetime.now(timezone.utc).isoformat()
            })

            monitor_data['recent_executions'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': platform_key,
                'status': 'success',
                'items_collected': len(articles),
                'latency': (datetime.now(timezone.utc) - exec_start).total_seconds()
            })

            print(f"\n  [完成] 获取 {len(articles)} 条")

        except Exception as e:
            print(f"\n  [失败] {str(e)}")
            monitor_data['platforms'].append({
                'platform': platform_key,
                'name': config['name'],
                'status': 'error',
                'item_count': 0,
                'last_crawl': datetime.now(timezone.utc).isoformat()
            })
            monitor_data['recent_executions'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': platform_key,
                'status': 'error',
                'error_message': str(e),
                'latency': (datetime.now(timezone.utc) - exec_start).total_seconds()
            })

    # 合并本次抓取的数据
    merged_news = merge_and_deduplicate(all_news)
    
    # 提取本次抓取的所有文章
    new_articles_list = []
    for articles in merged_news.values():
        new_articles_list.extend(articles)
    
    print(f"\n  [本次抓取] 共 {len(new_articles_list)} 条新数据")
    
    # 加载现有数据并合并（累积模式）
    print(f"  [数据累积] 加载历史数据...")
    existing_data = load_existing_data()
    existing_articles = existing_data.get('sorted_all', [])
    print(f"  [历史数据] 现有 {len(existing_articles)} 条")
    
    # 合并新旧数据（去重）
    all_articles_list = merge_with_existing(new_articles_list, existing_articles)
    print(f"  [合并后] 共 {len(all_articles_list)} 条（去重后）")
    
    # 按平台过滤7天内数据并取TopN
    print(f"\n  [筛选] 保留{DAYS_WINDOW}天内各平台热度Top{TOP_N_PER_PLATFORM}...")
    filtered_articles = filter_and_limit_by_platform(all_articles_list, DAYS_WINDOW, TOP_N_PER_PLATFORM)
    print(f"  [筛选后] 最终保留 {len(filtered_articles)} 条")
    
    # 按热度排序
    sorted_articles = sort_by_hot_score(filtered_articles)

    success_platforms = sum(1 for p in monitor_data['platforms'] if p['status'] == 'online')
    total_platforms = len(monitor_data['platforms'])
    articles_with_cover = sum(1 for a in sorted_articles if a.get('cover_url'))
    cover_rate = round(articles_with_cover / len(sorted_articles) * 100, 1) if sorted_articles else 0

    # 生成按热度排序的平台数据
    sorted_news = {}
    for article in sorted_articles:
        platform = article.get('platform', 'unknown')
        if platform not in sorted_news:
            sorted_news[platform] = []
        sorted_news[platform].append(article)

    # 获取热度统计
    hot_stats = get_platform_hot_stats(sorted_articles)
    print(f"\n  [热度] 各平台平均热度分:")
    for platform, stats in hot_stats.items():
        print(f"         - {platform}: {stats['avg_hot_score']:.4f}")

    output_data = {
        'update_time': datetime.now(timezone.utc).isoformat(),
        'news': sorted_news,
        'sorted_all': sorted_articles,  # 全部文章按热度排序
        'monitor': {
            'summary': {
                'total_success_rate': round(success_platforms / total_platforms * 100, 1) if total_platforms > 0 else 0,
                'total_fail_rate': round((total_platforms - success_platforms) / total_platforms * 100, 1) if total_platforms > 0 else 0,
                'avg_response_time': round(sum(
                    e['latency'] for e in monitor_data['recent_executions'] if e['status'] == 'success'
                ) / max(len([e for e in monitor_data['recent_executions'] if e['status'] == 'success']), 1), 1),
                'cover_success_rate': cover_rate,
                'hot_sort_enabled': True,
                'platform_hot_stats': hot_stats,
            },
            'platforms': monitor_data['platforms'],
            'failure_reasons': monitor_data['failure_reasons'],
            'recent_executions': monitor_data['recent_executions'][-10:]
        }
    }

    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    history_record = {
        'run_id': start_time.strftime('%Y%m%d-%H%M%S'),
        'timestamp': start_time.isoformat(),
        'trigger': trigger,
        'total_items': len(sorted_articles),
        'new_items': len(new_articles_list),
        'platforms': {
            p['platform']: {
                'status': p['status'],
                'items': p['item_count'],
                'latency': next(
                    (e['latency'] for e in monitor_data['recent_executions']
                     if e['platform'] == p['platform'] and e['status'] == 'success'),
                    0
                )
            }
            for p in monitor_data['platforms']
        },
        'duration_seconds': round(elapsed, 1)
    }
    append_history_record(history_record)

    print(f"\n{'='*60}")
    print(f"全部完成! 总耗时: {elapsed:.1f}秒")
    print(f"本次新增: {len(new_articles_list)} 条")
    print(f"累积保留: {len(sorted_articles)} 条")
    print(f"封面获取率: {cover_rate}%")
    print(f"数据已保存到: {OUTPUT_FILE}")
    print(f"历史记录已保存到: {HISTORY_FILE}")
    print(f"{'='*60}")

    return output_data


if __name__ == '__main__':
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(platform))
