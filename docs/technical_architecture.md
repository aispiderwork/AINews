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
│  │ 关键词过滤   │  │ 数据去重     │  │ 热度计算     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据采集层 (Crawling)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌──────────┐    │
│  │ Hacker │ │ Tech   │ │ 量子位 │ │ 新  │ │ RadarAI  │    │
│  │ News   │ │ Crunch │ │        │ │ 智元│ │          │    │
│  └────────┘ └────────┘ └────────┘ └─────┘ └──────────┘    │
│  ┌────────┐                                                 │
│  │ Google │                                                 │
│  │ AI Blog│                                                 │
│  └────────┘                                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层 (Storage)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  JSON文件    │  │ GitHub Pages │  │ 历史记录     │      │
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
| 后端框架 | Python 3.x | 异步爬虫框架 |
| 爬虫库 | httpx + BeautifulSoup4 | 异步HTTP + HTML解析 |
| RSS解析 | feedparser | RSS/Atom订阅解析 |
| 数据存储 | JSON文件 | 轻量级数据存储 |
| 前端 | HTML5 + CSS3 + JavaScript | 原生前端技术 |
| 部署 | GitHub Actions + GitHub Pages | 免费CI/CD和托管 |
| 任务调度 | cron (GitHub Actions) | 定时触发 |

## 三、模块详细设计

### 3.1 数据采集模块

#### 平台爬取策略

| 平台 | 主要数据源 | 优先级 | 爬取方式 | 热度指标 |
|------|----------|--------|---------|---------|
| **Hacker News** | Top Stories API | ⭐⭐⭐⭐⭐ | API | score(投票), descendants(评论) |
| **TechCrunch** | RSS Feed | ⭐⭐⭐⭐ | RSS | 无（按时间） |
| **量子位** | 网站首页 | ⭐⭐⭐⭐ | 爬虫 | 无（按时间） |
| **新智元** | 网站首页 | ⭐⭐⭐ | 爬虫 | 无（按时间） |
| **RadarAI** | 网站首页 | ⭐⭐⭐ | 爬虫 | 无（按时间） |
| **Google AI Blog** | RSS Feed | ⭐⭐⭐⭐ | RSS | 无（按时间） |

#### 数据结构设计

```python
class NewsItem:
    # 基础字段
    id: str                    # 唯一标识 (MD5 of URL)
    platform: str              # 平台名称
    title: str                 # 标题
    url: str                   # 原始链接
    cover_url: Optional[str]   # 封面图片链接
    publish_time: str          # 发布时间 (ISO格式)
    
    # Hacker News特有字段
    score: Optional[int]       # HN投票得分
    comments_count: Optional[int]  # HN评论数
    discussion_url: Optional[str]  # HN讨论页URL
    
    # 热度计算字段
    hot_score: float           # 综合热度分
    time_factor: float         # 时间衰减因子
    platform_weight: float     # 平台权重
    hn_hot_score: Optional[float]  # HN热度分
```

### 3.2 热度计算模块

#### 热度计算公式

```
hot_score = platform_weight × 30% + time_factor × 40% + hn_hot_score_normalized × 30%
```

#### 平台权重配置

```python
PLATFORM_WEIGHTS = {
    'hackernews': 1.0,      # 国际技术社区，权重最高
    'techcrunch': 0.9,      # 国际科技媒体
    'googleai': 0.85,       # 官方博客
    'qbitai': 0.8,          # 国内头部AI媒体
    'aiera': 0.75,          # 国内AI媒体
    'radarai': 0.7,         # 新兴AI平台
}
```

#### 时间衰减因子

```python
def calc_time_factor(publish_time: str) -> float:
    """
    时间衰减因子计算
    
    规则：
    - 24小时内 = 1.0
    - 每过一天衰减 0.1
    - 10天后降至最低 0.1
    """
    hours_ago = (now - publish_time).total_seconds() / 3600
    factor = 1.0 - (hours_ago / 240)  # 240小时 = 10天
    return max(0.1, min(1.0, factor))
```

#### Hacker News热度分

```python
def calc_hn_hot_score(score: int, descendants: int) -> float:
    """
    HN热度分 = 投票分 × 0.7 + 评论数 × 0.3
    """
    return score * 0.7 + descendants * 0.3

# 归一化到0-1范围（假设最高500分）
hn_hot_score_normalized = min(1.0, hn_raw_score / 500)
```

### 3.3 数据处理模块

#### 关键词过滤策略

```python
AI_KEYWORDS = [
    'ai', 'llm', 'gpt', 'claude', 'openai', 'anthropic', 'google ai', 'deepmind',
    'machine learning', '机器学习', 'deep learning', '深度学习', 'neural network',
    'transformer', 'bert', 'llama', 'mistral', 'agent', '智能体', 'copilot',
    '大模型', 'foundation model', 'agi', 'artificial general intelligence',
    'computer vision', 'nlp', 'natural language processing', 'rag',
    'retrieval augmented generation', 'fine-tuning', 'prompt', '多模态',
    'multimodal', 'gemini', 'palm', 'bard', 'midjourney', 'stable diffusion',
    'dall-e', 'ai safety', 'ai regulation', 'llm', 'chatbot', 'generative ai',
]
```

#### 去重算法

```python
def generate_id(url: str) -> str:
    """基于URL生成唯一ID"""
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:16]

# 去重策略：基于URL的MD5值
```

#### 数据合并流程

```python
def merge_and_deduplicate(all_news: dict) -> dict:
    """
    合并各平台数据并去重
    
    Args:
        all_news: {platform: [articles]}
        
    Returns:
        去重后的数据
    """
    seen_urls = set()
    merged = {}
    
    for platform, articles in all_news.items():
        merged[platform] = []
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                merged[platform].append(article)
    
    return merged
```

### 3.4 数据存储模块

#### JSON文件输出格式

```json
{
  "update_time": "2026-05-09T12:00:00+00:00",
  "news": {
    "hackernews": [
      {
        "id": "abc123",
        "title": "OpenAI发布GPT-5最新进展",
        "url": "https://example.com/article",
        "platform": "hackernews",
        "publish_time": "2026-05-09T10:00:00+00:00",
        "cover_url": "https://example.com/cover.jpg",
        "score": 256,
        "comments_count": 89,
        "discussion_url": "https://news.ycombinator.com/item?id=12345",
        "hot_score": 0.8234,
        "time_factor": 0.9167,
        "platform_weight": 1.0,
        "hn_hot_score": 205.9
      }
    ],
    "techcrunch": [...],
    "qbitai": [...],
    "aiera": [...],
    "radarai": [...],
    "googleai": [...]
  },
  "sorted_all": [...],  // 全部文章按热度排序
  "monitor": {
    "summary": {
      "total_success_rate": 98.5,
      "total_fail_rate": 1.5,
      "avg_response_time": 2.3,
      "cover_success_rate": 87.2,
      "hot_sort_enabled": true,
      "platform_hot_stats": {
        "hackernews": {
          "count": 15,
          "avg_hot_score": 0.7523,
          "max_hot_score": 0.9123,
          "min_hot_score": 0.5234
        }
      }
    },
    "platforms": [...],
    "recent_executions": [...]
  }
}
```

### 3.5 前端展示模块

#### 页面结构

```
index.html
├── 头部导航
│   ├── Logo
│   ├── 页面切换（资讯看板/运行监控）
│   ├── 最后更新时间
│   └── 操作按钮（刷新/导出）
├── 资讯看板页面
│   ├── 搜索栏
│   ├── 排序切换（热度/时间/平台）
│   ├── 平台Tab栏
│   └── 资讯列表区
│       └── 资讯卡片
│           ├── 热度排名（Top3特殊样式）
│           ├── 封面图片（可选）
│           ├── 平台标签
│           ├── 标题
│           ├── 元信息（时间/热度分/HN数据）
│           └── 操作链接
└── 运行监控页面
    ├── KPI指标卡片
    ├── 平台状态网格
    └── 最近采集记录
```

#### 排序模式

| 模式 | 说明 | 数据来源 |
|------|------|---------|
| 🔥 热度排序 | 按hot_score降序 | sorted_all字段 |
| 🕐 时间排序 | 按publish_time降序 | sorted_all字段 |
| 📰 平台分组 | 按platform分组 | news字段 |

#### 热度排名样式

- Top 1: 金色背景 🔥
- Top 2: 银色背景
- Top 3: 铜色背景
- 其他: 默认样式

### 3.6 监控统计模块

#### 监控指标定义

```python
class MonitorMetrics:
    # 汇总指标
    total_success_rate: float      # 总体成功率
    total_fail_rate: float         # 总体失败率
    avg_response_time: float       # 平均响应时间
    cover_success_rate: float      # 封面获取成功率
    hot_sort_enabled: bool         # 是否启用热度排序
    platform_hot_stats: dict       # 各平台热度统计
    
    # 平台状态
    platforms: List[{
        "platform": str,
        "name": str,
        "status": "online" | "error",
        "item_count": int,
        "last_crawl": str
    }]
    
    # 最近执行记录
    recent_executions: List[{
        "timestamp": str,
        "platform": str,
        "status": "success" | "error",
        "items_collected": int,
        "latency": float,
        "error_message": Optional[str]
    }]
```

## 四、GitHub部署方案

### 4.1 项目目录结构

```
AINewsCrawl/
├── .github/
│   └── workflows/
│       └── crawl-news.yml      # GitHub Actions工作流
├── crawlers/
│   ├── __init__.py
│   ├── base.py                 # 基础爬虫类
│   ├── hackernews.py           # Hacker News爬虫
│   ├── techcrunch.py           # TechCrunch爬虫
│   ├── qbitai.py               # 量子位爬虫
│   ├── aiera.py                # 新智元爬虫
│   ├── radarai.py              # RadarAI爬虫
│   ├── googleai.py             # Google AI Blog爬虫
│   └── utils/
│       ├── __init__.py
│       ├── filter.py           # 关键词过滤
│       ├── merge.py            # 数据合并去重
│       └── hot_score.py        # 热度计算
├── data/                       # 数据目录（git忽略）
│   ├── news.json               # 主数据文件
│   └── history.json            # 执行历史
├── docs/                       # 文档目录
│   ├── product_plan.html       # 产品方案
│   ├── technical_architecture.md  # 技术架构
│   ├── CRAWLER_FULL_SPEC.md    # 爬虫规范
│   └── ui-design-specification.md  # UI设计规范
├── index.html                  # 前端主页面
├── main.py                     # 主程序入口
├── requirements.txt            # Python依赖
└── README.md                   # 项目说明
```

### 4.2 GitHub Actions工作流配置

```yaml
name: Crawl AI News

on:
  schedule:
    # 北京时间 9:00 和 20:00 (UTC 01:00 和 12:00)
    - cron: '0 1,12 * * *'
  workflow_dispatch:
    inputs:
      platform:
        description: '指定平台 (留空=全部)'
        required: false
        type: string

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run crawler
        run: |
          python main.py ${{ inputs.platform || '' }}
      
      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/
          git diff --staged --quiet || git commit -m "Update news data [$(date +%Y-%m-%d\ %H:%M)]"
          git push
```

### 4.3 requirements.txt

```
httpx>=0.27.0
beautifulsoup4>=4.12.0
feedparser>=6.0.0
```

## 五、自动化 vs 人工配合

### 5.1 ✅ 可完全自动化的部分

| 模块 | 说明 |
|------|------|
| 定时任务调度 | GitHub Actions cron自动触发 |
| 数据采集执行 | 各平台爬虫自动执行 |
| 关键词筛选 | AI关键词自动过滤 |
| 热度计算 | 自动计算hot_score |
| 数据排序 | 自动按热度/时间排序 |
| 监控统计 | 自动采集运行指标 |
| 数据导出 | 自动生成JSON文件 |
| Git提交推送 | 自动commit和push |
| GitHub Pages部署 | 自动部署前端 |

### 5.2 ⚙️ 需要人工配合的部分

| 维护项 | 频率 | 说明 |
|--------|------|------|
| 爬虫修复 | 按需 | 平台页面结构变化时修复 |
| 关键词调整 | 按需 | 根据热点变化调整过滤关键词 |
| 热度算法调优 | 按需 | 根据效果调整权重参数 |
| 监控查看 | 日常 | 检查运行状态和数据质量 |

## 六、部署步骤指南

### 步骤1：准备工作
1. [ ] Fork或创建GitHub仓库
2. [ ] 本地克隆仓库
3. [ ] 安装Python 3.11+

### 步骤2：代码开发
1. [ ] 实现各平台爬虫
2. [ ] 实现热度计算模块
3. [ ] 实现数据处理逻辑
4. [ ] 开发前端页面
5. [ ] 本地测试完整流程

### 步骤3：GitHub配置
1. [ ] 开启GitHub Pages
2. [ ] 配置Actions工作流

### 步骤4：启动自动化
1. [ ] Push代码到GitHub
2. [ ] 手动触发一次workflow测试
3. [ ] 验证Pages部署成功
4. [ ] 确认定时任务正常执行

## 七、风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|---------|
| 页面改版 | 爬虫失效 | 监控告警、及时修复 |
| 平台反爬 | 无法获取数据 | 使用RSS/API替代 |
| 数据量过大 | 存储压力 | 只保留最近数据 |
| 热度算法不准 | 排序效果差 | 持续调优权重参数 |

## 八、扩展方向

- [x] 多平台数据采集
- [x] 热度排序算法
- [x] 运行监控看板
- [ ] 更多平台接入（知乎、Medium等）
- [ ] 热度趋势分析
- [ ] AI内容摘要
- [ ] 邮件/IM推送通知
