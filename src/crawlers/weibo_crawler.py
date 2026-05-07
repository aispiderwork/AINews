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


class WeiboCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('weibo')
    
    def fetch_hotlist(self) -> List[Dict]:
        items = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        if self.config.get('cookie'):
            headers['Cookie'] = self.config['cookie']
        
        try:
            url = self.config.get('url', 'https://s.weibo.com/top/summary')
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('.data tbody tr')
            
            for idx, row in enumerate(rows[1:], 1):
                try:
                    rank_elem = row.select_one('.td-01')
                    title_elem = row.select_one('.td-02 a')
                    hot_elem = row.select_one('.td-02 .hot')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    if href and not href.startswith('http'):
                        href = 'https://s.weibo.com' + href
                    
                    hot_value = 0
                    if hot_elem:
                        hot_text = hot_elem.get_text(strip=True)
                        try:
                            hot_value = int(''.join(filter(str.isdigit, hot_text)))
                        except:
                            pass
                    
                    rank = idx
                    if rank_elem:
                        try:
                            rank = int(rank_elem.get_text(strip=True))
                        except:
                            pass
                    
                    item = {
                        'id': self.generate_id(href),
                        'platform': 'weibo',
                        'source': 'hotlist',
                        'title': title,
                        'url': href,
                        'cover_url': None,
                        'content': '',
                        'hot_value': hot_value,
                        'hot_rank': rank,
                        'publish_time': datetime.now().isoformat(),
                        'author': '',
                        'tags': [],
                        'crawl_time': datetime.now().isoformat(),
                        'metrics': {
                            'search_count': f"{hot_value//10000}万" if hot_value > 10000 else str(hot_value)
                        }
                    }
                    items.append(item)
                    self.hotlist_items += 1
                    
                    time.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    print(f"[Weibo] Error parsing row: {e}")
                    continue
                    
        except Exception as e:
            raise Exception(f"Failed to fetch Weibo hotlist: {e}")
        
        return items


if __name__ == '__main__':
    crawler = WeiboCrawler()
    items = crawler.run()
    print(f"Fetched {len(items)} items")
    for item in items[:5]:
        print(f"- {item['title']}")
