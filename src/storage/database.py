import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import DB_PATH, DATA_DIR


def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            source TEXT DEFAULT 'hotlist',
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            cover_url TEXT,
            cover_local TEXT,
            content TEXT,
            hot_value INTEGER DEFAULT 0,
            hot_rank INTEGER,
            publish_time TEXT,
            author TEXT,
            tags TEXT,
            crawl_time TEXT,
            metrics TEXT,
            UNIQUE(url)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            avg_latency REAL,
            error_message TEXT,
            items_collected INTEGER DEFAULT 0,
            hotlist_items INTEGER DEFAULT 0,
            covers_collected INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_platform ON news(platform)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_publish_time ON news(publish_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_time ON crawl_metrics(start_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON news(source)')
    
    conn.commit()
    conn.close()


def save_news_items(items: List[Dict]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for item in items:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO news 
                (id, platform, source, title, url, cover_url, cover_local, content, 
                 hot_value, hot_rank, publish_time, author, tags, crawl_time, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('id'),
                item.get('platform'),
                item.get('source', 'hotlist'),
                item.get('title'),
                item.get('url'),
                item.get('cover_url'),
                item.get('cover_local'),
                item.get('content'),
                item.get('hot_value', 0),
                item.get('hot_rank'),
                item.get('publish_time'),
                item.get('author'),
                json.dumps(item.get('tags', []), ensure_ascii=False) if item.get('tags') else None,
                item.get('crawl_time'),
                json.dumps(item.get('metrics', {}), ensure_ascii=False) if item.get('metrics') else None
            ))
        except Exception as e:
            print(f"Error saving news item: {e}")
    
    conn.commit()
    conn.close()


def save_crawl_metric(metric: Dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO crawl_metrics 
        (platform, start_time, end_time, success_count, fail_count, 
         avg_latency, error_message, items_collected, hotlist_items, covers_collected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        metric.get('platform'),
        metric.get('start_time'),
        metric.get('end_time'),
        metric.get('success_count', 0),
        metric.get('fail_count', 0),
        metric.get('avg_latency'),
        metric.get('error_message'),
        metric.get('items_collected', 0),
        metric.get('hotlist_items', 0),
        metric.get('covers_collected', 0)
    ))
    
    conn.commit()
    conn.close()


def get_news_by_platform(platform: str, limit: int = 100) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if platform == 'all':
        cursor.execute('SELECT * FROM news ORDER BY crawl_time DESC LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT * FROM news WHERE platform = ? ORDER BY crawl_time DESC LIMIT ?', (platform, limit))
    
    rows = cursor.fetchall()
    result = []
    for row in rows:
        item = dict(row)
        if item.get('tags'):
            item['tags'] = json.loads(item['tags'])
        if item.get('metrics'):
            item['metrics'] = json.loads(item['metrics'])
        result.append(item)
    
    conn.close()
    return result


def get_recent_crawl_metrics(limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM crawl_metrics ORDER BY start_time DESC LIMIT ?', (limit,))
    
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result


if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
