import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import random
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.crawlers.base_crawler import BaseCrawler


class BilibiliCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('bilibili')
    
    def fetch_hotlist(self) -> List[Dict]:
        items = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }
        
        try:
            url = self.config.get('url', 'https://www.bilibili.com/v/popular/rank/all')
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            video_cards = soup.select('.rank-list .rank-item')
            
            for idx, card in enumerate(video_cards, 1):
                try:
                    title_elem = card.select_one('.info a.title')
                    cover_elem = card.select_one('.img img')
                    play_elem = card.select_one('.data-box span:first-child')
                    danmaku_elem = card.select_one('.data-box span:nth-child(2)')
                    up_elem = card.select_one('.detail a.up-name')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    if href and not href.startswith('http'):
                        href = 'https://www.bilibili.com' + href
                    
                    cover_url = None
                    if cover_elem:
                        cover_url = cover_elem.get('src') or cover_elem.get('data-src')
                        if cover_url and not cover_url.startswith('http'):
                            cover_url = 'https:' + cover_url
                    
                    play_count = ''
                    if play_elem:
                        play_count = play_elem.get_text(strip=True)
                    
                    danmaku_count = ''
                    if danmaku_elem:
                        danmaku_count = danmaku_elem.get_text(strip=True)
                    
                    author = ''
                    if up_elem:
                        author = up_elem.get_text(strip=True)
                    
                    item = {
                        'id': self.generate_id(href),
                        'platform': 'bilibili',
                        'source': 'hotlist',
                        'title': title,
                        'url': href,
                        'cover_url': cover_url,
                        'content': '',
                        'hot_value': idx * 1000,
                        'hot_rank': idx,
                        'publish_time': datetime.now().isoformat(),
                        'author': author,
                        'tags': [],
                        'crawl_time': datetime.now().isoformat(),
                        'metrics': {
                            'play_count': play_count,
                            'danmaku_count': danmaku_count
                        }
                    }
                    items.append(item)
                    self.hotlist_items += 1
                    if cover_url:
                        self.covers_collected += 1
                    
                    time.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    print(f"[Bilibili] Error parsing card: {e}")
                    continue
                    
        except Exception as e:
            raise Exception(f"Failed to fetch Bilibili hotlist: {e}")
        
        return items


if __name__ == '__main__':
    crawler = BilibiliCrawler()
    items = crawler.run()
    print(f"Fetched {len(items)} items")
    for item in items[:5]:
        print(f"- {item['title']}")
