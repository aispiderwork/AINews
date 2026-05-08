# AI资讯平台爬虫方案 (GitHub Actions 部署版)

## 一、GitHub Actions 限制分析

### 关键限制
| 限制项 | 数值 | 影响 |
|--------|------|------|
| Job 执行时间 | 6小时 | 单次爬虫任务不能超过6小时 |
| 内存 (Linux) | 16GB (公开) / 7GB (私有) | 浏览器自动化需谨慎 |
| 磁盘空间 | 14GB | 缓存和数据存储限制 |
| 缓存限制 | 10GB/repository | 依赖缓存策略 |
| 免费分钟数 | 2000分钟/月 | 需控制执行频率 |
| 网络出口 | 共享IP池 | 可能触发目标站反爬 |

### 约束结论
1. **不能使用 Playwright**：安装浏览器耗时太长(约5分钟)，且内存占用大
2. **不能使用 SQLite**：GitHub Pages 不支持 SQLite 文件读取
3. **数据存储用 JSON**：适合静态站点展示
4. **定时任务频率**：每天2-4次，每月约60-120次运行

---

## 二、调整后的技术栈

### 推荐框架 (适配 GitHub Actions)

| 框架 | 说明 | 适配性 |
|------|------|--------|
| **httpx** | 异步HTTP客户端，内置超时控制 | ⭐⭐⭐⭐⭐ |
| **scrapling** | 轻量级解析，无浏览器依赖 | ⭐⭐⭐⭐⭐ |
| **BeautifulSoup4** | 经典HTML解析 | ⭐⭐⭐⭐ |
| **trafilatura** | 新闻内容提取 | ⭐⭐⭐⭐ |
| **feedparser** | RSS Feed解析 | ⭐⭐⭐⭐⭐ |

### 调整后的技术选型

```
采集层：httpx (异步) + requests (同步备选)
解析层：scrapling / BeautifulSoup4
内容提取：trafilatura (可选)
数据存储：JSON (GitHub Pages兼容)
调度系统：GitHub Actions 定时触发
```

---

## 三、平台爬虫方案 (GitHub Actions 适配)

### 1. 量子位 (qbitai.com) - 优先级最高

#### 适配策略
```python
# 纯静态页面，使用 httpx + scrapling
import httpx
from scrapling import Scrapling

async def crawl_qbitai():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get('https://www.qbitai.com/')
        page = Scrapling(response.text)
        
        articles = []
        for item in page.css('article'):
            articles.append({
                'title': item.css_first('h2 a').text(),
                'url': item.css_first('h2 a').attrs.get('href'),
                'cover': item.css_first('.wp-block-image img').attrs.get('src'),
                'author': item.css_first('.author-name').text(),
                'time': item.css_first('.post-time').text(),
                'tags': [a.text() for a in item.css('.tag-link')]
            })
        return articles
```

#### GitHub Actions 优化
- 请求间隔：1-2秒
- 超时设置：30秒
- 预计耗时：2-3分钟

---

### 2. 36氪 (36kr.com) - 高优先级

#### 调整策略 (无 Playwright)
```python
# 方案A: 分析API接口 (优先)
# 观察浏览器Network面板，找到内部API
async def crawl_36kr_api():
    async with httpx.AsyncClient(timeout=30) as client:
        # 需要人工抓包确认实际API
        response = await client.get(
            'https://www.36kr.com/api/news/list',
            params={'channel': 'technology', 'page': 1}
        )
        return response.json()

# 方案B: 使用RSS (备选)
import feedparser

def crawl_36kr_rss():
    feed = feedparser.parse('https://www.36kr.com/rss')
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'url': entry.link,
            'published': entry.published,
            'summary': entry.summary
        })
    return articles
```

#### 需要人工配合
| 项目 | 说明 |
|------|------|
| API抓包 | 需使用浏览器开发者工具分析36氪内部API |
| RSS确认 | 验证36是否有公开RSS |

#### GitHub Actions 优化
- 如果使用API：预计耗时 1-2分钟
- 如果使用RSS：预计耗时 <1分钟

---

### 3. 机器之心 (jiqizhixin.com)

#### 适配策略
```python
async def crawl_jiqizhixin():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get('https://www.jiqizhixin.com/articles/')
        page = Scrapling(response.text)
        
        articles = []
        for item in page.css('.article-card'):
            articles.append({
                'title': item.css_first('h3').text(),
                'url': item.css_first('a').attrs.get('href'),
                'date': item.css_first('.date').text(),
                'tags': item.css_first('.tags').text().split(',')
            })
        return articles
```

#### GitHub Actions 优化
- 预计耗时：2-3分钟

---

### 4. TechCrunch (techcrunch.com)

#### 最佳策略：RSS Feed
```python
import feedparser

def crawl_techcrunch():
    feed = feedparser.parse('https://techcrunch.com/category/artificial-intelligence/feed/')
    articles = []
    for entry in feed.entries[:10]:  # 取最新10条
        article = {
            'title': entry.title,
            'url': entry.link,
            'published': entry.published,
            'summary': entry.get('summary', ''),
            'tags': [tag.term for tag in entry.get('tags', [])]
        }
        # 尝试获取封面图
        if entry.get('media_content'):
            article['cover'] = entry.media_content[0].get('url')
        articles.append(article)
    return articles
```

#### GitHub Actions 优化
- 预计耗时：<1分钟
- 最稳定的方案

---

### 5. Hacker News (news.ycombinator.com)

#### 最佳策略：官方API
```python
import httpx

async def crawl_hackernews():
    async with httpx.AsyncClient(timeout=30) as client:
        # 获取热门文章ID
        top_stories = await client.get(
            'https://hacker-news.firebaseio.com/v0/topstories.json'
        )
        story_ids = top_stories.json()[:20]  # 取前20条
        
        articles = []
        for story_id in story_ids:
            story = await client.get(
                f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
            )
            data = story.json()
            # 过滤AI相关文章
            if is_ai_related(data.get('title', '')):
                articles.append({
                    'title': data['title'],
                    'url': data.get('url', f'https://news.ycombinator.com/item?id={story_id}'),
                    'score': data.get('score', 0),
                    'descendants': data.get('descendants', 0)
                })
        return articles

def is_ai_related(title):
    ai_keywords = ['AI', 'LLM', 'GPT', 'Claude', 'OpenAI', 'Machine Learning', 
                   'Deep Learning', 'Neural', 'AI', '人工智能']
    return any(keyword.lower() in title.lower() for keyword in ai_keywords)
```

#### GitHub Actions 优化
- 预计耗时：1-2分钟
- 官方API，最稳定

---

### 6. OpenAI Blog (openai.com/blog)

#### 适配策略
```python
async def crawl_openai():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get('https://openai.com/blog/')
        page = Scrapling(response.text)
        
        articles = []
        for item in page.css('a[href^="/index/"]'):
            articles.append({
                'title': item.text(),
                'url': 'https://openai.com' + item.attrs.get('href'),
                'date': item.css_first('.date').text() if item.css_first('.date') else None
            })
        return articles
```

#### 注意事项
- OpenAI 可能有 Cloudflare 防护
- 如被拦截需添加更真实的 User-Agent

#### GitHub Actions 优化
- 预计耗时：1-2分钟

---

### 7. Google AI Blog (blog.google/technology/ai/)

#### 适配策略
```python
async def crawl_googleai():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get('https://blog.google/technology/ai/')
        page = Scrapling(response.text)
        
        articles = []
        for item in page.css('.article-card'):
            articles.append({
                'title': item.css_first('h3').text(),
                'url': item.css_first('a').attrs.get('href'),
                'date': item.css_first('.date').text()
            })
        return articles
```

#### GitHub Actions 优化
- 预计耗时：1-2分钟

---

### 8-9. 新智元 / RadarAI - 待确认

#### 需要人工完成
| 项目 | 说明 |
|------|------|
| 新智元域名 | 需确认实际访问地址 (可能是 aibox.com 或其他) |
| RadarAI | 需访问分析页面结构和内容来源 |

---

## 四、GitHub Actions 工作流设计

### 目录结构
```
.github/
└── workflows/
    └── crawl-news.yml        # 主工作流

crawlers/
├── __init__.py
├── base.py                   # 基础爬虫类
├── qbitai.py
├── kr36.py
├── jiqizhixin.py
├── techcrunch.py
├── hackernews.py
├── openai.py
├── googleai.py
└── utils/
    ├── headers.py            # UA池
    ├── filter.py             # AI关键词过滤
    └── merge.py              # 数据合并去重

data/
└── news.json                 # 输出数据

main.py                       # 主入口
requirements.txt
```

### 完整工作流配置

```yaml
# .github/workflows/crawl-news.yml
name: AI News Crawler

on:
  schedule:
    # 北京时间每天 8:00, 14:00, 20:00 执行 (UTC 0:00, 6:00, 12:00)
    - cron: '0 0,6,12 * * *'
  workflow_dispatch:          # 支持手动触发
    inputs:
      platform:
        description: '指定平台 (留空抓取全部)'
        required: false
        type: string

permissions:
  contents: write             # 需要写入权限更新数据
  pages: write                # Pages部署权限

jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 30       # 设置30分钟超时
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run AI News Crawler
        run: |
          python main.py ${{ inputs.platform }}
        env:
          # 可在此添加代理配置等环境变量
          HTTP_PROXY: ${{ secrets.HTTP_PROXY }}
          HTTPS_PROXY: ${{ secrets.HTTPS_PROXY }}
      
      - name: Commit and push if changed
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add data/news.json
          if ! git diff --staged --quiet; then
            git commit -m "Update news data - $(date '+%Y-%m-%d %H:%M:%S')"
            git push
          else
            echo "No changes to commit"
          fi
      
      - name: Upload artifact (可选)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: news-data
          path: data/news.json
          retention-days: 7

  deploy:
    needs: crawl
    runs-on: ubuntu-latest
    if: github.event_name != 'workflow_dispatch' || github.event.inputs.platform == ''
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## 五、数据模型设计

### 输出格式 (JSON)
```json
{
  "update_time": "2026-05-08T14:30:00+08:00",
  "news": {
    "qbitai": [
      {
        "id": "qbitai_413296",
        "title": "GPT-5 最新研究进展曝光",
        "url": "https://www.qbitai.com/2026/05/413296.html",
        "cover_url": "https://aka.doubaocdn.com/s/xyPE1wNjAL",
        "author": "邓思邈",
        "publish_time": "2026-05-08T13:30:00+08:00",
        "crawl_time": "2026-05-08T14:30:00+08:00",
        "tags": ["GPT-5", "AI研究", "多模态"],
        "summary": "文章摘要..."
      }
    ],
    "kr36": [...],
    "jiqizhixin": [...],
    "techcrunch": [...],
    "hackernews": [...],
    "openai": [...],
    "googleai": [...]
  },
  "monitor": {
    "summary": {
      "total_success_rate": 98.5,
      "total_fail_rate": 1.5,
      "avg_response_time": 2.1,
      "cover_success_rate": 92.0
    },
    "platforms": [
      {
        "platform": "qbitai",
        "name": "量子位",
        "status": "online",
        "item_count": 32,
        "last_crawl": "2026-05-08T14:30:00+08:00"
      }
    ],
    "failure_reasons": {
      "network_timeout": 2,
      "page_changed": 1
    },
    "recent_executions": [
      {
        "timestamp": "2026-05-08T14:30:00+08:00",
        "platform": "qbitai",
        "status": "success",
        "items_collected": 32,
        "latency": 2.1
      }
    ]
  }
}
```

---

## 六、核心代码实现

### 主入口 (main.py)
```python
#!/usr/bin/env python3
"""AI News Crawler - Main Entry Point"""

import json
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# 导入各平台爬虫
from crawlers.qbitai import crawl_qbitai
from crawlers.kr36 import crawl_36kr
from crawlers.jiqizhixin import crawl_jiqizhixin
from crawlers.techcrunch import crawl_techcrunch
from crawlers.hackernews import crawl_hackernews
from crawlers.openai import crawl_openai
from crawlers.googleai import crawl_googleai
from crawlers.utils.merge import merge_and_deduplicate
from crawlers.utils.filter import filter_ai_news

# 平台配置
PLATFORMS = {
    'qbitai': {'name': '量子位', 'func': crawl_qbitai, 'priority': 1},
    'kr36': {'name': '36氪', 'func': crawl_36kr, 'priority': 2},
    'jiqizhixin': {'name': '机器之心', 'func': crawl_jiqizhixin, 'priority': 3},
    'techcrunch': {'name': 'TechCrunch', 'func': crawl_techcrunch, 'priority': 4},
    'hackernews': {'name': 'Hacker News', 'func': crawl_hackernews, 'priority': 5},
    'openai': {'name': 'OpenAI Blog', 'func': crawl_openai, 'priority': 6},
    'googleai': {'name': 'Google AI Blog', 'func': crawl_googleai, 'priority': 7},
}

OUTPUT_DIR = Path('data')
OUTPUT_FILE = OUTPUT_DIR / 'news.json'

async def main(target_platform=None):
    """主爬虫流程"""
    start_time = datetime.now(timezone.utc)
    
    # 确定要抓取的的平台
    if target_platform and target_platform in PLATFORMS:
        platforms_to_crawl = {target_platform: PLATFORMS[target_platform]}
    else:
        platforms_to_crawl = PLATFORMS
    
    # 并行抓取 (按优先级分组)
    all_news = {}
    monitor_data = {
        'platforms': [],
        'failure_reasons': {},
        'recent_executions': []
    }
    
    for platform_key, config in platforms_to_crawl.items():
        print(f"开始抓取: {config['name']}")
        exec_start = datetime.now(timezone.utc)
        
        try:
            articles = await config['func']()
            
            # 过滤AI相关新闻 (对Hacker News等综合平台)
            if platform_key == 'hackernews':
                articles = filter_ai_news(articles)
            
            all_news[platform_key] = articles
            
            monitor_data['platforms'].append({
                'platform': platform_key,
                'name': config['name'],
                'status': 'online',
                'item_count': len(articles),
                'last_crawl': datetime.now(timezone.utc).isoformat()
            })
            
            monitor_data['recent_executions'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': platform_key,
                'status': 'success',
                'items_collected': len(articles),
                'latency': (datetime.now(timezone.utc) - exec_start).total_seconds()
            })
            
            print(f"  完成: 获取 {len(articles)} 条")
            
        except Exception as e:
            print(f"  失败: {str(e)}")
            monitor_data['platforms'].append({
                'platform': platform_key,
                'name': config['name'],
                'status': 'error',
                'item_count': 0,
                'last_crawl': datetime.now(timezone.utc).isoformat()
            })
            monitor_data['recent_executions'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': platform_key,
                'status': 'error',
                'error_message': str(e),
                'latency': (datetime.now(timezone.utc) - exec_start).total_seconds()
            })
    
    # 合并去重
    merged_news = merge_and_deduplicate(all_news)
    
    # 计算统计数据
    total_items = sum(len(v) for v in merged_news.values())
    success_platforms = sum(1 for p in monitor_data['platforms'] if p['status'] == 'online')
    total_platforms = len(monitor_data['platforms'])
    
    # 构建输出数据
    output_data = {
        'update_time': datetime.now(timezone.utc).isoformat(),
        'news': merged_news,
        'monitor': {
            'summary': {
                'total_success_rate': round(success_platforms / total_platforms * 100, 1) if total_platforms > 0 else 0,
                'total_fail_rate': round((total_platforms - success_platforms) / total_platforms * 100, 1) if total_platforms > 0 else 0,
                'avg_response_time': round(sum(
                    e['latency'] for e in monitor_data['recent_executions'] if e['status'] == 'success'
                ) / max(len([e for e in monitor_data['recent_executions'] if e['status'] == 'success']), 1), 1),
                'cover_success_rate': 85.0  # 可根据实际封面获取情况计算
            },
            'platforms': monitor_data['platforms'],
            'failure_reasons': monitor_data['failure_reasons'],
            'recent_executions': monitor_data['recent_executions'][-10:]  # 保留最近10条记录
        }
    }
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 写入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    print(f"\n全部完成! 总耗时: {elapsed:.1f}秒")
    print(f"共获取 {total_items} 条新闻")
    
    return output_data

if __name__ == '__main__':
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(platform))
```

### 基础爬虫类 (crawlers/base.py)
```python
"""基础爬虫类"""

import httpx
from typing import List, Dict, Any
import random
import time

# UA池
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

class BaseCrawler:
    """基础爬虫类"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    async def fetch(self, url: str) -> str:
        """获取页面内容"""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    
    async def fetch_json(self, url: str) -> Dict[str, Any]:
        """获取JSON数据"""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    def delay(self, min_sec: float = 1.0, max_sec: float = 2.0):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
```

### 数据合并去重 (crawlers/utils/merge.py)
```python
"""数据合并与去重"""

import hashlib
from typing import Dict, List

def generate_id(platform: str, title: str, url: str) -> str:
    """生成唯一ID"""
    content = f"{platform}:{title}:{url}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def merge_and_deduplicate(all_news: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """合并各平台新闻并去重"""
    merged = {}
    seen_urls = set()
    
    for platform, articles in all_news.items():
        merged[platform] = []
        for article in articles:
            # 生成ID
            article['id'] = generate_id(
                platform,
                article.get('title', ''),
                article.get('url', '')
            )
            
            # 去重检查
            url_key = article.get('url', '')
            if url_key and url_key in seen_urls:
                continue
            
            seen_urls.add(url_key)
            merged[platform].append(article)
    
    return merged
```

### AI关键词过滤 (crawlers/utils/filter.py)
```python
"""AI相关新闻过滤"""

AI_KEYWORDS = [
    'AI', '人工智能', 'LLM', 'GPT', 'Claude', 'OpenAI', 'Anthropic',
    'Google AI', 'DeepMind', 'Machine Learning', '机器学习',
    'Deep Learning', '深度学习', 'Neural Network', '神经网络',
    'Transformer', 'BERT', 'LLaMA', 'Mistral',
    'Agent', '智能体', 'Copilot', 'Coding',
    '大模型', 'Foundation Model', '基础模型',
    'AGI', 'Artificial General Intelligence',
    'Computer Vision', '计算机视觉', 'CV',
    'NLP', 'Natural Language Processing', '自然语言处理',
    'RAG', 'Retrieval Augmented Generation',
    'Fine-tuning', '微调', 'Prompt', '提示词',
    '多模态', 'Multimodal', '具身智能', 'Embodied AI',
    'Robotics', '机器人', '自动驾驶', 'Autonomous',
    'Gemini', 'PaLM', 'Bard', 'Copilot',
    'Midjourney', 'Stable Diffusion', 'DALL-E',
    'AI安全', 'AI Safety', 'AI监管', 'AI Regulation',
]

def is_ai_related(title: str, summary: str = '') -> bool:
    """判断是否为AI相关新闻"""
    text = (title + ' ' + summary).lower()
    return any(keyword.lower() in text for keyword in AI_KEYWORDS)

def filter_ai_news(articles: List[Dict]) -> List[Dict]:
    """过滤出AI相关新闻"""
    return [
        article for article in articles
        if is_ai_related(
            article.get('title', ''),
            article.get('summary', '')
        )
    ]
```

---

## 七、依赖包清单 (requirements.txt)

```txt
# HTTP客户端
httpx>=0.27.0
requests>=2.31.0

# HTML解析
scrapling>=0.1.0
beautifulsoup4>=4.12.0
lxml>=5.1.0

# RSS解析
feedparser>=6.0.0

# 内容提取 (可选)
trafilatura>=1.8.0

# 工具
python-dateutil>=2.9.0

# 注意: 不使用以下包 (GitHub Actions不兼容)
# - playwright (安装太慢，内存占用大)
# - selenium (需要浏览器驱动)
# - apscheduler (GitHub Actions自身调度)
```

---

## 八、GitHub Actions 使用指南

### 1. 分钟数估算

| 平台 | 预计耗时 | 每日3次 | 每月消耗 |
|------|----------|---------|----------|
| 量子位 | 2分钟 | 6分钟 | 180分钟 |
| 36氪 | 2分钟 | 6分钟 | 180分钟 |
| 机器之心 | 2分钟 | 6分钟 | 180分钟 |
| TechCrunch | 1分钟 | 3分钟 | 90分钟 |
| Hacker News | 1分钟 | 3分钟 | 90分钟 |
| OpenAI | 1分钟 | 3分钟 | 90分钟 |
| Google AI | 1分钟 | 3分钟 | 90分钟 |
| **总计** | **10分钟** | **30分钟** | **900分钟** |

**结论**：在免费额度 2000分钟/月内，可以支持每日3次全平台抓取

### 2. 优化建议

1. **减少频率**：如分钟数不够，可改为每日2次
2. **分批抓取**：将平台分组，不同时间执行
3. **缓存依赖**：使用 actions/cache 缓存 pip 包
4. **按需触发**：使用 workflow_dispatch 手动触发特定平台

### 3. 环境变量配置

在 GitHub 仓库 Settings -> Secrets and variables -> Actions 中配置：

| 变量名 | 说明 |
|--------|------|
| HTTP_PROXY | HTTP代理地址 (可选) |
| HTTPS_PROXY | HTTPS代理地址 (可选) |

### 4. Pages 配置

在仓库 Settings -> Pages 中：
- Source: GitHub Actions
- 工作流会自动部署 data/ 目录下的内容

---

## 九、人工配合清单

### 必须完成 (P0)
| # | 任务 | 说明 | 预计耗时 |
|---|------|------|----------|
| 1 | 36氪API抓包 | 使用浏览器开发者工具分析36氪内部API | 30分钟 |
| 2 | 新智元域名确认 | 确认实际访问地址 | 10分钟 |
| 3 | RadarAI网站分析 | 分析页面结构 | 20分钟 |
| 4 | OpenAI选择器验证 | 确认博客列表页CSS选择器 | 15分钟 |

### 建议完成 (P1)
| # | 任务 | 说明 |
|---|------|------|
| 1 | AI关键词词典完善 | 根据实际抓取结果调整关键词列表 |
| 2 | 封面图获取策略 | 优化各平台封面图提取 |
| 3 | 时间格式统一 | 将各平台时间格式统一为ISO 8601 |

---

## 十、实施路线图

### Phase 1: 基础框架 (1天)
- [ ] 创建项目结构和基础爬虫类
- [ ] 实现量子位爬虫 (最简单)
- [ ] 实现 Hacker News 爬虫 (官方API)
- [ ] 配置 GitHub Actions 基础工作流

### Phase 2: 核心平台 (1-2天)
- [ ] 实现 36氪爬虫 (需API分析)
- [ ] 实现机器之心爬虫
- [ ] 实现 TechCrunch 爬虫 (RSS)
- [ ] 实现数据合并去重逻辑

### Phase 3: 补充平台 (1天)
- [ ] 实现 OpenAI/Google AI Blog 爬虫
- [ ] 实现新智元/RadarAI 爬虫 (待确认)
- [ ] 完善 AI 关键词过滤

### Phase 4: 优化部署 (0.5天)
- [ ] 配置 GitHub Actions 定时任务
- [ ] 添加依赖缓存
- [ ] 完善错误处理和监控数据
- [ ] 测试完整流程

---

## 十一、风险与应对

| 风险 | 概率 | 影响 | GitHub Actions 特殊应对 |
|------|------|------|------------------------|
| 页面结构变化 | 高 | 中 | 添加选择器验证，失败时记录日志 |
| IP被封 | 中 | 高 | GitHub IP池动态轮换，但仍需控制频率 |
| 超时失败 | 中 | 中 | 设置合理超时(30s)，单个平台失败不影响整体 |
| 分钟数超限 | 低 | 高 | 监控使用量，必要时减少频率 |
| 依赖安装失败 | 低 | 中 | 使用 actions/cache 缓存依赖 |
| 法律风险 | 低 | 高 | 遵守robots.txt，控制频率 |

---

*文档生成时间: 2026-05-08*
*最后更新: 2026-05-08*
*部署目标: GitHub Actions + GitHub Pages*
