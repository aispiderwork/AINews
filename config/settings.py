import os
from typing import Dict, List

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'news.db')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'public')

# 各平台配置
PLATFORMS = {
    'weibo': {
        'name': '微博',
        'url': 'https://s.weibo.com/top/summary',
        'priority': 1,
        'cookie': os.environ.get('WEIBO_COOKIE', '')
    },
    'bilibili': {
        'name': '哔哩哔哩',
        'url': 'https://www.bilibili.com/v/popular/rank/all',
        'priority': 2,
        'cookie': ''
    },
    'xiaohongshu': {
        'name': '小红书',
        'url': '',
        'priority': 3,
        'cookie': os.environ.get('XIAOHONGSHU_COOKIE', '')
    },
    'x': {
        'name': 'X (Twitter)',
        'url': 'https://twitter.com/i/trends',
        'priority': 4,
        'cookie': ''
    },
    'facebook': {
        'name': 'Facebook',
        'url': '',
        'priority': 5,
        'cookie': ''
    }
}

# 关键词过滤
KEYWORDS = {
    'llm': ['GPT', 'Claude', 'Llama', '大模型', '语言模型', 'Gemini', 'DeepSeek', '文心一言', '通义千问', '星火'],
    'ai_application': ['AI应用', 'AI工具', 'ChatGPT', 'Copilot', 'Midjourney', 'Sora', 'Stable Diffusion', 'AI绘画'],
    'agent': ['Agent', 'AutoGPT', '智能体', '多Agent', 'LangChain', 'AI助手'],
    'generative': ['Sora', 'Midjourney', '生成式AI', 'AIGC', '文生图', '文生视频', '图生图'],
    'trending': ['AI', '人工智能', 'OpenAI', 'Anthropic', 'Google AI', 'Meta AI', '百度', '阿里', '腾讯']
}

# 封面尺寸规范
COVER_SPECS = {
    'weibo': (400, 225),
    'bilibili': (400, 225),
    'xiaohongshu': (400, 400),
    'x': (400, 225),
    'facebook': (400, 225)
}
