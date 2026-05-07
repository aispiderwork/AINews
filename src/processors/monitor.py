from typing import List, Dict
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.storage.database import get_recent_crawl_metrics, get_news_by_platform


def calculate_monitor_summary(crawl_metrics: List[Dict]) -> Dict:
    if not crawl_metrics:
        return {
            'total_success_rate': 0,
            'total_fail_rate': 0,
            'avg_response_time': 0,
            'total_items': 0,
            'hotlist_ratio': 0,
            'cover_success_rate': 0
        }
    
    total_runs = len(crawl_metrics)
    success_count = sum(1 for m in crawl_metrics if m.get('success_count', 0) > 0)
    total_items = sum(m.get('items_collected', 0) for m in crawl_metrics)
    total_hotlist = sum(m.get('hotlist_items', 0) for m in crawl_metrics)
    total_covers = sum(m.get('covers_collected', 0) for m in crawl_metrics)
    
    latencies = [m.get('avg_latency', 0) for m in crawl_metrics if m.get('avg_latency')]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    return {
        'total_success_rate': round(success_count / total_runs * 100, 1) if total_runs > 0 else 0,
        'total_fail_rate': round((total_runs - success_count) / total_runs * 100, 1) if total_runs > 0 else 0,
        'avg_response_time': round(avg_latency, 2),
        'total_items': total_items,
        'hotlist_ratio': round(total_hotlist / total_items * 100, 1) if total_items > 0 else 0,
        'cover_success_rate': round(total_covers / total_items * 100, 1) if total_items > 0 else 0
    }


def get_platform_status(crawl_metrics: List[Dict]) -> List[Dict]:
    from config.settings import PLATFORMS
    
    platform_status = {}
    for platform in PLATFORMS.keys():
        platform_metrics = [m for m in crawl_metrics if m.get('platform') == platform]
        if platform_metrics:
            latest = platform_metrics[0]
            success = latest.get('success_count', 0) > 0
            item_count = latest.get('items_collected', 0)
        else:
            success = False
            item_count = 0
        
        platform_status[platform] = {
            'platform': platform,
            'name': PLATFORMS[platform]['name'],
            'status': 'online' if success else 'offline',
            'item_count': item_count
        }
    
    return list(platform_status.values())


def calculate_failure_reasons(crawl_metrics: List[Dict]) -> Dict:
    reasons = {
        'network_timeout': 0,
        'cookie_expired': 0,
        'page_changed': 0,
        'auth_failed': 0,
        'other': 0
    }
    
    for metric in crawl_metrics:
        error_msg = metric.get('error_message', '')
        if not error_msg:
            continue
        
        error_lower = error_msg.lower()
        if 'timeout' in error_lower or 'network' in error_lower:
            reasons['network_timeout'] += 1
        elif 'cookie' in error_lower or 'expired' in error_lower:
            reasons['cookie_expired'] += 1
        elif 'page' in error_lower or 'structure' in error_lower or 'parse' in error_lower:
            reasons['page_changed'] += 1
        elif 'auth' in error_lower or 'login' in error_lower:
            reasons['auth_failed'] += 1
        else:
            reasons['other'] += 1
    
    return reasons


def get_recent_executions(crawl_metrics: List[Dict], limit: int = 10) -> List[Dict]:
    executions = []
    for metric in crawl_metrics[:limit]:
        success = metric.get('success_count', 0) > 0
        execution = {
            'id': str(metric.get('id', '')),
            'timestamp': metric.get('start_time', ''),
            'platform': metric.get('platform', ''),
            'status': 'success' if success else 'error',
            'items_collected': metric.get('items_collected', 0),
            'latency': metric.get('avg_latency', 0),
            'error_message': metric.get('error_message', '')
        }
        executions.append(execution)
    return executions


def generate_monitor_data() -> Dict:
    crawl_metrics = get_recent_crawl_metrics(50)
    
    return {
        'summary': calculate_monitor_summary(crawl_metrics),
        'platforms': get_platform_status(crawl_metrics),
        'failure_reasons': calculate_failure_reasons(crawl_metrics),
        'recent_executions': get_recent_executions(crawl_metrics)
    }
