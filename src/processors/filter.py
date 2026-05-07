from typing import List, Dict, Set
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import KEYWORDS


def get_all_keywords() -> List[str]:
    all_keywords = []
    for category, keywords in KEYWORDS.items():
        all_keywords.extend(keywords)
    return all_keywords


def filter_by_keywords(items: List[Dict]) -> List[Dict]:
    all_keywords = get_all_keywords()
    filtered_items = []
    
    for item in items:
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        text = title + ' ' + content
        
        matched_keywords = []
        for keyword in all_keywords:
            if keyword.lower() in text:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            item['matched_keywords'] = matched_keywords
            filtered_items.append(item)
    
    return filtered_items


def remove_duplicates(items: List[Dict]) -> List[Dict]:
    seen_urls: Set[str] = set()
    unique_items = []
    
    for item in items:
        url = item.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item)
    
    return unique_items


def calculate_score(item: Dict) -> float:
    base_score = 0
    
    if item.get('hot_rank'):
        base_score += (100 - item['hot_rank']) * 10
    
    hot_value = item.get('hot_value', 0)
    hot_factor = min(hot_value / 10000, 50)
    base_score += hot_factor
    
    matched_keywords = item.get('matched_keywords', [])
    base_score += len(matched_keywords) * 20
    
    return base_score


def sort_by_hotness(items: List[Dict]) -> List[Dict]:
    for item in items:
        item['score'] = calculate_score(item)
    
    return sorted(items, key=lambda x: x.get('score', 0), reverse=True)


def process_items(items: List[Dict]) -> List[Dict]:
    items = remove_duplicates(items)
    items = filter_by_keywords(items)
    items = sort_by_hotness(items)
    return items
