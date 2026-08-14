#!/usr/bin/env python3
"""AI News Crawler - 主入口程序"""

import json
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from crawlers.hackernews import crawl_hackernews
from crawlers.qbitai import crawl_qbitai
from crawlers.radarai import crawl_radarai
from crawlers.huggingface import crawl_huggingface
from crawlers.bestblogs import crawl_bestblogs
from crawlers.utils.merge import merge_and_deduplicate
from crawlers.utils.cluster import cluster_articles

PLATFORMS = {
    'hackernews': {'name': 'Hacker News', 'func': crawl_hackernews, 'priority': 1},
    'qbitai': {'name': '量子位', 'func': crawl_qbitai, 'priority': 2},
    'radarai': {'name': 'RadarAI', 'func': crawl_radarai, 'priority': 3},
    'bestblogs': {'name': 'BestBlogs', 'func': crawl_bestblogs, 'priority': 4},
    'huggingface': {'name': 'HuggingFace', 'func': crawl_huggingface, 'priority': 5},
}

OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'news.json'
HISTORY_FILE = OUTPUT_DIR / 'history.json'
MAX_HISTORY = 100


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


def load_existing_bestblogs() -> Optional[list]:
    """晚报模式：从现有 news.json 读回早班已抓取的 BestBlogs，避免被晚报覆盖清空"""
    try:
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            bb = (data.get('news') or {}).get('bestblogs')
            if isinstance(bb, list):
                return bb
    except Exception:
        pass
    return None


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

    # 晚报模式跳过 BestBlogs：简报每天仅一篇，晚班不更新且会浪费日配额；
    # 但需保留早班已抓取的 BestBlogs 数据，避免晚报覆盖清空（见下方回填）。
    run_mode = sys.argv[3] if len(sys.argv) > 3 else 'morning'
    skip_bestblogs_evening = (run_mode == 'evening' and 'bestblogs' in platforms_to_crawl)
    if skip_bestblogs_evening:
        platforms_to_crawl = {k: v for k, v in platforms_to_crawl.items() if k != 'bestblogs'}

    all_news = {}
    failed_platforms = set()  # 本次抓取整体失败的来源，不沿用旧数据、标记为暂不可用
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
            failed_platforms.add(platform_key)
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

    # 晚报模式：回填早班已抓取的 BestBlogs（不重新消耗 API 配额）
    if skip_bestblogs_evening:
        existing_bb = load_existing_bestblogs()
        if existing_bb is not None:
            all_news['bestblogs'] = existing_bb
            monitor_data['platforms'].append({
                'platform': 'bestblogs',
                'name': PLATFORMS['bestblogs']['name'],
                'status': 'online',
                'item_count': len(existing_bb),
                'last_crawl': datetime.now(timezone.utc).isoformat(),
            })
            monitor_data['recent_executions'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': 'bestblogs',
                'status': 'success',
                'items_collected': len(existing_bb),
                'latency': 0,
            })
            print(f"\n  [晚报] 保留早班 BestBlogs {len(existing_bb)} 条（不重复抓取）")

    merged_news = merge_and_deduplicate(all_news, exclude_old_platforms=failed_platforms)

    total_items = sum(len(v) for v in merged_news.values())
    success_platforms = sum(1 for p in monitor_data['platforms'] if p['status'] == 'online')
    total_platforms = len(monitor_data['platforms'])

    all_articles_list = []
    for articles in merged_news.values():
        all_articles_list.extend(articles)
    total_articles = len(all_articles_list)
    articles_with_cover = sum(1 for a in all_articles_list if a.get('cover_url'))
    cover_rate = round(articles_with_cover / total_articles * 100, 1) if total_articles > 0 else 0

    # 跨平台事件聚类：把不同来源报道的同一事件归并为一个条目
    print(f"\n  [聚类] 跨源事件归并（{total_articles} 篇 -> ", end='')
    clustered_articles = cluster_articles(all_articles_list)
    print(f"{len(clustered_articles)} 条）")

    # 排序：被 N 个来源报道（source_count 降序）优先；同档按发布时间倒序。
    # 说明：除 HN/HF 外无真实互动数据，合成 hot_score 已移除；
    # 「跨源报道数」是事件重要性的真实代理信号，比纯时间序更贴近用户价值。
    def _parse_time(article):
        try:
            t = (article.get('publish_time') or '').replace('Z', '+00:00')
            dt = datetime.fromisoformat(t)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    sorted_articles = sorted(
        clustered_articles,
        key=lambda a: (a.get('source_count', 1), _parse_time(a)),
        reverse=True,
    )

    output_data = {
        'update_time': datetime.now(timezone.utc).isoformat(),
        'platform_unavailable': sorted(failed_platforms),  # 本次抓取失败的来源，前端/邮件据此标注「暂不可用」
        'news': merged_news,            # 各平台保持时间序（平台分栏用原始数据）
        'sorted_all': sorted_articles,  # 头版：聚类后按跨源报道数 + 时间排序
        'monitor': {
            'summary': {
                'total_success_rate': round(success_platforms / total_platforms * 100, 1) if total_platforms > 0 else 0,
                'total_fail_rate': round((total_platforms - success_platforms) / total_platforms * 100, 1) if total_platforms > 0 else 0,
                'avg_response_time': round(sum(
                    e['latency'] for e in monitor_data['recent_executions'] if e['status'] == 'success'
                ) / max(len([e for e in monitor_data['recent_executions'] if e['status'] == 'success']), 1), 1),
                'cover_success_rate': cover_rate,
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
        'total_items': total_items,
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
    print(f"共获取 {total_items} 条新闻")
    print(f"封面获取率: {cover_rate}%")
    print(f"数据已保存到: {OUTPUT_FILE}")
    print(f"历史记录已保存到: {HISTORY_FILE}")
    print(f"{'='*60}")

    return output_data


if __name__ == '__main__':
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(platform))
