# AI热点资讯监控系统 - 技术架构

## 一、整体架构设计

### 1.1 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                        展示层 (Frontend)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  响应式网页  │  │ 数据可视化   │  │  监控看板    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据处理层 (Processing)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 关键词过滤   │  │ 数据去重     │  │ 监控统计     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据采集层 (Crawling)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌──────────┐    │
│  │ 微博爬虫│ │ B站爬虫│ │小红书  │ │ X   │ │ Facebook │    │
│  │ (热搜榜)│ │(热门榜)│ │(热榜)  │ │(趋势)│ │(Trending)│    │
│  └────────┘ └────────┘ └────────┘ └─────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层 (Storage)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SQLite DB   │  │  JSON文件    │  │ GitHub Pages│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      部署调度层 (Deployment)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ GitHub Actions│ │ 定时任务     │  │ 自动推送     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 二、技术栈选型

| 层次 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | Python 3.x + Flask/FastAPI | 轻量级Web框架 |
| 爬虫库 | Requests + BeautifulSoup4 | 静态页面爬取 |
| 动态爬虫 | Selenium/Playwright | 处理JavaScript渲染 |
| 数据存储 | SQLite | 本地关系型数据库 |
| 前端 | HTML5 + CSS3 + JavaScript | 原生前端技术 |
| 图表库 | ECharts/Chart.js | 数据可视化图表 |
| 部署 | GitHub Actions + GitHub Pages | 免费CI/CD和托管 |
| 任务调度 | cron (GitHub Actions) | 定时触发 |

## 三、模块详细设计

### 3.1 数据采集模块

#### 平台热榜爬取策略

| 平台 | 主要数据源 | 优先级 | 爬取方式 | 热度指标 |
|------|----------|--------|---------|---------|
| **微博** | 热搜榜、实时热搜 | ⭐⭐⭐⭐⭐ | API/爬虫 | 搜索热度、讨论数 |
| **哔哩哔哩** | 全站热门榜、全站热搜 | ⭐⭐⭐⭐⭐ | API + 爬虫 | 播放量、点赞数、弹幕数 |
| **小红书** | 热搜榜、热门笔记 | ⭐⭐⭐⭐ | Selenium | 点赞数、收藏数、评论数 |
| **X (Twitter)** | Trends趋势榜、热门推文 | ⭐⭐⭐ | 爬虫/API | 转发数、点赞数、引用数 |
| **Facebook** | Trending话题、热门帖子 | ⭐⭐ | 爬虫/API | 分享数、点赞数、评论数 |

#### 各平台热榜详细说明

**微博**
- 主要入口：https://s.weibo.com/top/summary
- 备选：https://s.weibo.com/top/summary?cate=realtimehot（实时热搜）
- 关键词搜索："GPT", "大模型", "AI", "Agent", "Claude", "Llama"等
- 数据字段：排名、热搜词、搜索热度、讨论数、热度标识
- 封面获取：热搜话题配图、相关新闻图片

**哔哩哔哩**
- 主要入口：https://www.bilibili.com/v/popular/rank/all
- 备选：https://s.bilibili.com/hot（全站热搜）
- 搜索关键词：科技区筛选 + AI相关关键词
- 数据字段：视频标题、UP主、播放量、点赞数、弹幕数、收藏数、热度值
- 封面获取：视频封面图（16:9比例）

**小红书**
- 主要入口：首页热榜、搜索热榜
- 关键词标签：#AI #大模型 #GPT #Agent #Claude #ChatGPT
- 数据字段：标题、作者、点赞数、收藏数、评论数、互动总量
- 封面获取：笔记首图（正方形比例）

**X (Twitter)**
- 主要入口：https://twitter.com/i/trends
- 话题搜索：#AI #LLM #GPT #Agent #Claude
- 数据字段：推文内容、作者、转发数、点赞数、引用数、回复数
- 封面获取：推文中的图片、视频缩略图

**Facebook**
- 主要入口：Trending Topics
- 相关页面：AI领域官方账号、科技媒体账号
- 数据字段：帖子标题、作者、分享数、点赞数、评论数
- 封面获取：帖子配图、缩略图

#### 封面处理策略

```python
# 封面获取流程
def fetch_cover(item: NewsItem, platform: str) -> str:
    """获取并处理封面图片"""
    # 1. 尝试从源平台获取封面
    cover_url = extract_cover_from_page(item.url, platform)
    
    if not cover_url:
        # 2. 无封面时使用平台默认占位图
        return get_default_cover(platform)
    
    # 3. 下载并压缩封面（如需本地存储）
    if NEED_LOCAL_STORAGE:
        local_path = download_and_resize_cover(cover_url, item.id)
        item.cover_local = local_path
    
    item.cover_url = cover_url
    return cover_url

# 封面尺寸规范
COVER_SPECS = {
    'weibo': (400, 225),   # 16:9
    'bilibili': (400, 225),
    'xiaohongshu': (400, 400),  # 1:1
    'x': (400, 225),
    'facebook': (400, 225)
}
```

#### 爬虫执行策略

```python
# 爬虫优先级
CRAWL_PRIORITY = {
    'weibo': 1,      # 最高优先级：微博热搜实时性最强
    'bilibili': 2,   # B站热门视频更新频繁
    'xiaohongshu': 3,
    'x': 4,
    'facebook': 5
}

# 爬取流程
def crawl_pipeline():
    # 1. 优先爬取各平台热榜
    hot_items = []
    for platform in sorted_by_priority(PLATFORMS):
        items = crawl_hot_list(platform)
        hot_items.extend(items)
    
    # 2. 从热榜中筛选AI相关内容
    ai_related_items = filter_by_keywords(hot_items, KEYWORDS)
    
    # 3. 如果热榜中AI内容不足，补充搜索结果
    if len(ai_related_items) < MIN_ITEMS:
        search_items = search_ai_keywords(PLATFORMS)
        ai_related_items.extend(search_items)
    
    # 4. 去重、排序、存储
    return process_and_save(ai_related_items)
```

**数据结构设计：**

```python
class NewsItem:
    id: str                    # 唯一标识
    platform: str              # 平台名称
    source: str                # 数据来源（热榜/搜索）
    title: str                 # 标题
    url: str                   # 原始链接
    cover_url: str             # 封面图片链接
    cover_local: str           # 本地封面路径（如适用）
    content: str               # 摘要内容
    hot_value: int             # 热度值（各平台原生指标）
    hot_rank: int              # 热榜排名（如有）
    publish_time: datetime     # 发布时间
    author: str                # 作者/发布者
    tags: List[str]            # 标签
    crawl_time: datetime       # 爬取时间
    metrics: dict              # 详细指标（播放、点赞等）
```

### 3.2 数据处理模块

**关键词过滤策略：**

```python
KEYWORDS = {
    'llm': ['GPT', 'Claude', 'Llama', '大模型', '语言模型', 'Gemini', 'DeepSeek'],
    'ai_application': ['AI应用', 'AI工具', 'ChatGPT', 'Copilot', 'Midjourney', 'Sora'],
    'agent': ['Agent', 'AutoGPT', '智能体', '多Agent', 'LangChain'],
    'generative': ['Sora', 'Midjourney', '生成式AI', 'AIGC', '文生图', '文生视频'],
    'trending': ['AI', '人工智能', 'OpenAI', 'Anthropic', 'Google AI', 'Meta AI']
}
```

**热榜内容评分策略：**

```python
def calculate_score(item: NewsItem) -> float:
    base_score = 0
    
    # 1. 热榜排名加分（排名越靠前分数越高）
    if item.hot_rank:
        base_score += (100 - item.hot_rank) * 10
    
    # 2. 热度指标加分
    hot_factor = min(item.hot_value / 10000, 50)  # 封顶50分
    base_score += hot_factor
    
    # 3. 关键词匹配加分
    keyword_matches = count_keywords(item.title + item.content)
    base_score += keyword_matches * 20
    
    # 4. 时效性加分（最近发布的内容）
    time_factor = calculate_time_factor(item.publish_time)
    base_score *= time_factor
    
    return base_score
```

**去重算法：**
- 基于URL去重（优先）
- 基于标题相似度去重（使用Levenshtein距离）
- 基于内容指纹去重

**热度排序：**
- 按热榜排名优先
- 其次按各平台原生热度指标降序
- 支持跨平台热度归一化（可选）

### 3.3 数据存储模块

**SQLite数据库 schema：**

```sql
CREATE TABLE news (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    source TEXT DEFAULT 'hotlist',  -- 数据来源：hotlist/search
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    cover_url TEXT,                -- 封面图片链接
    cover_local TEXT,              -- 本地封面路径
    content TEXT,
    hot_value INTEGER DEFAULT 0,
    hot_rank INTEGER,              -- 热榜排名
    publish_time TEXT,
    author TEXT,
    tags TEXT,                    -- JSON格式
    crawl_time TEXT,
    metrics TEXT,                 -- JSON格式，详细指标
    UNIQUE(url)
);

CREATE TABLE crawl_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    avg_latency REAL,             -- 平均响应时间（秒）
    error_message TEXT,
    items_collected INTEGER DEFAULT 0,
    hotlist_items INTEGER DEFAULT 0,  -- 从热榜获取的条目数
    covers_collected INTEGER DEFAULT 0  -- 成功获取封面数
);

CREATE INDEX idx_platform ON news(platform);
CREATE INDEX idx_publish_time ON news(publish_time);
CREATE INDEX idx_crawl_time ON crawl_metrics(start_time);
CREATE INDEX idx_source ON news(source);
```

**JSON文件输出格式：**
```json
{
  "news": {
    "weibo": [
      {
        "title": "OpenAI发布GPT-5最新进展",
        "url": "https://...",
        "cover_url": "https://.../cover.jpg",
        "source": "hotlist",
        "hot_rank": 3,
        "hot_value": 1250000,
        "metrics": {
          "search_count": "125万",
          "discussion_count": "5.2万"
        }
      }
    ],
    "bilibili": [...],
    "xiaohongshu": [...],
    "x": [...],
    "facebook": [...]
  },
  "monitor": {
    "summary": {
      "total_success_rate": 0.968,
      "total_fail_rate": 0.032,
      "avg_latency": 1.2,
      "total_items": 2847,
      "hotlist_ratio": 0.85,
      "cover_success_rate": 0.92
    },
    "platforms": [
      {"platform": "weibo", "status": "online", "success_rate": 0.98},
      {"platform": "bilibili", "status": "online", "success_rate": 0.95},
      {"platform": "x", "status": "offline", "success_rate": 0.2}
    ],
    "failure_reasons": {
      "network_timeout": 12,
      "cookie_expired": 8,
      "page_changed": 4,
      "other": 3
    },
    "recent_executions": [
      {
        "id": "abc123",
        "timestamp": "2026-05-07T14:30:00Z",
        "platform": "weibo",
        "status": "success",
        "items_collected": 45,
        "latency": 2.1
      },
      {
        "id": "def456",
        "timestamp": "2026-05-07T14:30:02Z",
        "platform": "x",
        "status": "error",
        "error_message": "网络超时",
        "failure_reason": "network_timeout"
      }
    ]
  }
}
```

### 3.4 前端展示模块

**页面结构：**
```
index.html
├── 头部导航（资讯看板/运行监控切换）
├── 资讯看板页面
│   ├── 平台Tab栏
│   └── 资讯列表区
│       └── 资讯卡片
│           ├── 标题（热榜排名标识）
│           ├── 元信息（热度指标）
│           └── 标签
└── 运行监控页面
    ├── 时间范围选择
    ├── KPI指标卡片
    │   ├── 成功率
    │   ├── 失败率
    │   ├── 平均响应
    │   └── 封面获取率
    ├── 平台状态列表
    ├── 失败原因统计（横向柱状图）
    │   ├── 网络超时
    │   ├── Cookie过期
    │   ├── 页面结构变化
    │   └── 其他原因
    └── 最近采集记录
        ├── 状态标识（成功/失败）
        ├── 平台名称
        ├── 执行时间
        ├── 采集数量/耗时
        └── 失败原因（如有）
```

**交互功能：**
- 页面切换（资讯/监控）
- Tab切换平台
- 时间范围筛选
- 卡片点击跳转
- 响应式布局（移动端适配）

### 3.5 监控统计模块

**监控指标定义：**

```python
from enum import Enum

class FailureReason(Enum):
    NETWORK_TIMEOUT = "network_timeout"      # 网络超时
    COOKIE_EXPIRED = "cookie_expired"        # Cookie过期
    PAGE_STRUCTURE_CHANGED = "page_changed"  # 页面结构变化
    AUTHENTICATION_FAILED = "auth_failed"    # 认证失败
    RATE_LIMITED = "rate_limited"            # 限流
    NO_DATA = "no_data"                      # 无数据
    OTHER = "other"                          # 其他原因

class CrawlMetrics:
    platform: str
    success_count: int
    fail_count: int
    success_rate: float
    avg_latency: float
    items_collected: int
    hotlist_items: int          # 热榜获取的条目数
    hotlist_ratio: float        # 热榜内容占比
    covers_collected: int       # 成功获取封面数
    cover_success_rate: float   # 封面获取成功率
    failure_reasons: Dict[FailureReason, int]  # 失败原因统计

class ExecutionLog:
    id: str
    timestamp: datetime
    platform: str
    status: str  # "success" / "error"
    items_collected: int
    latency: float
    error_message: Optional[str]
    failure_reason: Optional[FailureReason]

class MonitorDashboard:
    total_success_rate: float
    total_fail_rate: float
    avg_response_time: float
    total_items: int
    hotlist_total_ratio: float  # 总体热榜内容占比
    cover_success_rate: float    # 总封面获取成功率
    platform_status: Dict[str, PlatformStatus]
    recent_executions: List[ExecutionLog]  # 最近采集记录（最近20条）
    failure_reason_stats: Dict[FailureReason, int]  # 失败原因统计（近7天）
```

**时间范围支持：**
- 实时数据（最新一次执行）
- 近1天
- 近3天
- 近7天

## 四、GitHub部署方案

### 4.1 项目目录结构

```
ai-hotspot-monitor/
├── .github/
│   └── workflows/
│       └── crawl.yml          # GitHub Actions工作流
├── src/
│   ├── crawlers/              # 爬虫模块
│   │   ├── base_crawler.py    # 基础爬虫类
│   │   ├── weibo_crawler.py   # 微博热搜爬虫
│   │   ├── bilibili_crawler.py # B站热榜爬虫
│   │   ├── xiaohongshu_crawler.py # 小红书热榜爬虫
│   │   ├── x_crawler.py       # X趋势爬虫
│   │   └── facebook_crawler.py # Facebook热榜爬虫
│   ├── processors/            # 数据处理模块
│   │   ├── filter.py          # 关键词过滤
│   │   ├── dedup.py           # 去重
│   │   └── monitor.py         # 监控统计模块
│   ├── storage/               # 存储模块
│   │   ├── database.py
│   │   └── json_exporter.py
│   └── main.py                # 主程序入口
├── data/                      # 数据目录（git忽略）
│   └── news.db
├── public/                    # 前端文件
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── config/                    # 配置文件
│   └── settings.py
├── requirements.txt           # Python依赖
└── README.md
```

### 4.2 GitHub Actions工作流配置

```yaml
name: AI Hotspot Monitor
on:
  schedule:
    - cron: '0 */2 * * *'  # 每2小时执行一次（热榜更新快，提高频率）
  workflow_dispatch:       # 手动触发

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run crawler (hotlist priority)
        env:
          # 需要人工配置的Secrets
          WEIBO_COOKIE: ${{ secrets.WEIBO_COOKIE }}
          XIAOHONGSHU_COOKIE: ${{ secrets.XIAOHONGSHU_COOKIE }}
        run: |
          python src/main.py
      
      - name: Commit and push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add public/data/
          git commit -m "Update news data (hotlist priority) $(date)" || echo "No changes"
          git push

  deploy-pages:
    needs: crawl
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Pages
        uses: actions/configure-pages@v4
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public
      
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 4.3 requirements.txt

```
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
```

## 五、自动化 vs 人工配合

### 5.1 ✅ 可完全自动化的部分（GitHub执行）

| 模块 | 说明 |
|------|------|
| 定时任务调度 | GitHub Actions cron自动触发（每2小时） |
| 热榜爬取执行 | 优先爬取各平台热榜内容 |
| 关键词筛选 | 自动从热榜中筛选AI相关内容 |
| 数据处理 | 关键词过滤、去重、排序全自动化 |
| 监控统计 | 自动采集运行指标、计算KPI |
| 数据导出 | 自动生成JSON文件 |
| Git提交推送 | 自动commit和push |
| GitHub Pages部署 | 自动构建和部署前端 |

### 5.2 ⚙️ 需要人工配置/配合的部分

#### 5.2.1 一次性配置

| 配置项 | 说明 | 操作步骤 |
|--------|------|---------|
| GitHub仓库创建 | 创建public/private仓库 | 手动在GitHub创建 |
| Secrets配置 | 存储敏感信息（Cookies等） | Settings → Secrets and variables → Actions → New repository secret |
| GitHub Pages开启 | 启用Pages服务 | Settings → Pages → Source选择GitHub Actions |
| 依赖安装 | 本地开发环境配置 | pip install -r requirements.txt |

#### 5.2.2 周期性维护

| 维护项 | 频率 | 说明 |
|--------|------|------|
| Cookie更新 | 按需 | 反爬严格的平台需要定期更新Cookie |
| 关键词调整 | 按需 | 根据热点变化调整过滤关键词 |
| 爬虫修复 | 按需 | 平台热榜页面结构变化时修复爬虫 |
| 依赖更新 | 每月 | 更新Python包以修复安全问题 |
| 监控看板查看 | 按需 | 检查运行状态、热榜内容占比 |

#### 5.2.3 需要登录的平台处理

| 平台 | 是否需要登录 | Cookie处理方式 | 热榜入口 |
|------|------------|--------------|---------|
| 微博 | 推荐 | 提取Cookie存入Secrets | https://s.weibo.com/top/summary |
| B站 | 可选 | 公开内容无需登录 | https://www.bilibili.com/v/popular/rank/all |
| 小红书 | 需要 | 必须配置Cookie | 首页热榜 |
| X | 困难 | 建议使用第三方API替代 | https://twitter.com/i/trends |
| Facebook | 困难 | 建议使用公开RSS或页面 | Trending Topics |

**Cookie获取方法：**
1. 浏览器登录对应平台
2. F12打开开发者工具
3. Network标签页刷新页面
4. 复制Request Headers中的Cookie
5. 存入GitHub Secrets

## 六、部署步骤指南

### 步骤1：准备工作
1. [ ] Fork或创建GitHub仓库
2. [ ] 本地克隆仓库
3. [ ] 安装Python 3.11+

### 步骤2：代码开发
1. [ ] 实现各平台热榜爬虫（优先）
2. [ ] 实现数据处理逻辑
3. [ ] 实现监控统计模块
4. [ ] 开发前端页面（含监控看板）
5. [ ] 本地测试完整流程

### 步骤3：GitHub配置
1. [ ] 配置仓库Secrets
2. [ ] 开启GitHub Pages
3. [ ] 配置Actions工作流（每2小时执行）

### 步骤4：启动自动化
1. [ ] Push代码到GitHub
2. [ ] 手动触发一次workflow测试
3. [ ] 验证Pages部署成功
4. [ ] 确认定时任务正常执行
5. [ ] 检查监控看板数据和热榜内容占比

## 七、风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|---------|
| 热榜页面改版 | 爬虫失效 | 定期检查页面结构，及时修复爬虫 |
| 平台反爬加强 | 无法获取热榜 | 使用代理池、增加间隔、模拟真实用户 |
| Cookie过期 | 部分平台无法爬取 | 监控告警、及时更新Cookie |
| 热榜中AI内容少 | 数据不足 | 启用关键词搜索作为补充源 |
| GitHub限流 | Actions无法执行 | 合理设置执行频率、错开高峰期 |
| 数据量过大 | 存储压力 | 定期清理旧数据、只保留最近7天 |
| 监控数据缺失 | 无法查看运行状态 | 数据冗余存储、本地备份 |

## 八、扩展方向

- [x] 优先从热榜爬取内容
- [x] 增加运行监控看板
- [ ] 增加更多平台热榜（知乎热榜、抖音热榜等）
- [ ] 热榜数据历史趋势分析
- [ ] 添加AI摘要功能（使用LLM总结内容）
- [ ] 实现邮件/IM推送通知（异常告警）
- [ ] 添加用户自定义关键词配置
- [ ] 实现更丰富的数据可视化图表
- [ ] 支持多语言内容
