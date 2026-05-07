import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.storage.database import init_db, save_news_items, save_crawl_metric
from src.crawlers.weibo_crawler import WeiboCrawler
from src.crawlers.bilibili_crawler import BilibiliCrawler
from src.crawlers.other_crawlers import XiaohongshuCrawler, XCrawler, FacebookCrawler
from src.processors.filter import process_items
from src.storage.json_exporter import export_json
from config.settings import PLATFORMS


def main():
    print("=" * 50)
    print("AI Hot News Monitor - Starting Crawl")
    print("=" * 50)
    
    init_db()
    
    crawlers = {
        'weibo': WeiboCrawler(),
        'bilibili': BilibiliCrawler(),
        'xiaohongshu': XiaohongshuCrawler(),
        'x': XCrawler(),
        'facebook': FacebookCrawler()
    }
    
    all_items = []
    sorted_platforms = sorted(PLATFORMS.keys(), key=lambda p: PLATFORMS[p]['priority'])
    
    for platform in sorted_platforms:
        if platform not in crawlers:
            continue
        
        print(f"\nProcessing {PLATFORMS[platform]['name']}...")
        crawler = crawlers[platform]
        items = crawler.run()
        
        if items:
            processed = process_items(items)
            all_items.extend(processed)
            save_news_items(processed)
        
        metric = crawler.get_crawl_metric()
        save_crawl_metric(metric)
    
    print(f"\nTotal processed items: {len(all_items)}")
    
    export_json()
    
    print("\n" + "=" * 50)
    print("Crawl completed successfully!")
    print("=" * 50)


if __name__ == '__main__':
    main()
