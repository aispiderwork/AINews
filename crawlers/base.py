#!/usr/bin/env python3
"""基础爬虫类 - 提供通用HTTP请求功能"""

import httpx
import random
import time
from typing import Dict, Any, Optional

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
]


class BaseCrawler:
    """基础爬虫类，封装HTTP请求逻辑"""
    
    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout
        self.headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头（每次调用可能使用不同UA）"""
        headers = self.headers.copy()
        headers['User-Agent'] = random.choice(USER_AGENTS)
        return headers
    
    async def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """获取页面内容"""
        req_headers = headers or self.get_headers()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=req_headers,
            follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    
    async def fetch_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """获取JSON数据"""
        req_headers = headers or self.get_headers()
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=req_headers
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def delay(min_sec: float = 1.0, max_sec: float = 2.0):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
