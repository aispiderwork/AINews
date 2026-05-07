import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import PUBLIC_DIR
from src.storage.database import get_news_by_platform
from src.processors.monitor import generate_monitor_data


def export_json():
    if not os.path.exists(PUBLIC_DIR):
        os.makedirs(PUBLIC_DIR)
    
    data_dir = os.path.join(PUBLIC_DIR, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    news_data = {
        'weibo': get_news_by_platform('weibo', 50),
        'bilibili': get_news_by_platform('bilibili', 50),
        'xiaohongshu': get_news_by_platform('xiaohongshu', 50),
        'x': get_news_by_platform('x', 50),
        'facebook': get_news_by_platform('facebook', 50)
    }
    
    monitor_data = generate_monitor_data()
    
    output = {
        'news': news_data,
        'monitor': monitor_data,
        'update_time': datetime.now().isoformat()
    }
    
    output_path = os.path.join(data_dir, 'data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Data exported to {output_path}")
    return output_path
