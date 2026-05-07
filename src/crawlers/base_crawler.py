import time
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import PLATFORMS


class BaseCrawler(ABC):
    def __init__(self, platform: str):
        self.platform = platform
        self.config = PLATFORMS.get(platform, {})
        self.name = self.config.get('name', platform)
        self.start_time = None
        self.end_time = None
        self.success_count = 0
        self.fail_count = 0
        self.items_collected = 0
        self.hotlist_items = 0
        self.covers_collected = 0
        self.error_message = None
    
    @abstractmethod
    def fetch_hotlist(self) -> List[Dict]:
        pass
    
    def generate_id(self, url: str) -> str:
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def get_crawl_metric(self) -> Dict:
        latency = None
        if self.start_time and self.end_time:
            latency = (self.end_time - self.start_time).total_seconds()
        
        return {
            'platform': self.platform,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'avg_latency': latency / self.items_collected if self.items_collected > 0 else None,
            'error_message': self.error_message,
            'items_collected': self.items_collected,
            'hotlist_items': self.hotlist_items,
            'covers_collected': self.covers_collected
        }
    
    def run(self) -> List[Dict]:
        self.start_time = datetime.now()
        items = []
        
        try:
            print(f"[{self.name}] Starting crawl...")
            items = self.fetch_hotlist()
            self.items_collected = len(items)
            self.success_count = 1 if items else 0
            print(f"[{self.name}] Successfully fetched {len(items)} items")
        except Exception as e:
            self.fail_count = 1
            self.error_message = str(e)
            print(f"[{self.name}] Error: {e}")
        
        self.end_time = datetime.now()
        return items
