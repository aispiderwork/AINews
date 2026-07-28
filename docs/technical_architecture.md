# AI热点资讯监控系统 - 技术架构

> ⚠️ **变更说明（2026-07-28）**：
> 1. **Google AI Blog 平台已下线**（`crawlers/googleai.py` 已删除），本文架构图与示例中的 Google AI 部分仅为历史记录。
> 2. **`hot_score` 热度计算已移除**（除 HN 外无真实互动数据，旧分数为主观合成值）。当前排序统一为**按发布时间倒序**，平台内取近 7 天 Top10；数据处理层的「热度计算」模块已删除，HN 的 `score` / `comments_count` 真实字段保留。
> 3. 前端已改为报纸风格设计，见 `docs/newspaper-style-redesign-plan.md`；HuggingFace 已接入（`crawlers/huggingface.py`），真实热度字段（`upvotes` / `likes` / `downloads` / `trendingScore`）已输出。

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
│  │ 关键词过滤   │  │ 数据去重     │  │ 时间排序     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据采集层 (Crawling)                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌──────────┐    │
│  │ Hacker │ │ Tech   │ │ 量子位 │ │ 新  │ │ RadarAI  │    │
│  │ News   │ │ Crunch │ │        │ │ 智元│ │          │    │
│  └────────┘ └────────┘ └────────┘ └─────┘ └──────────┘    │
│                    ┌─────────────┐                          │
│                    │ HuggingFace │                          │
│                    └─────────────┘                          │
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
| **HuggingFace** | 官方公开 API | ⭐⭐⭐⭐ | API | upvotes(论文), likes/downloads/trendingScore(模型) |

> Google AI Blog 已下线；HuggingFace 已接入。前端按「全部 / 论文 / 模型」子标签展示；`merge.py` 对 HuggingFace 保留最多 20 条，其中 Trending 模型代表当前热度，不受 7 天创建时间限制。

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
    
    # Hacker News特有字段（真实互动数据）
    score: Optional[int]       # HN投票得分
    comments_count: Optional[int]  # HN评论数
    discussion_url: Optional[str]  # HN讨论页URL
```

### 3.2 排序模块（2026-07-28 修订）

> 原热度计算模块（`crawlers/utils/hot_score.py`）已删除。旧公式 `hot_score = 平台权重×30% + 时间因子×40% + HN热度×30%` 中，平台权重是主观设定、时间因子只反映新旧，除 HN 外不构成真实热度，故废弃。

当前排序规则：

```python
def _parse_time(article):
    """解析 publish_time，失败返回最小时间（排最后）"""
    dt = datetime.fromisoformat(article['publish_time'].replace('Z', '+00:00'))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

# 全局 sorted_all 与平台内 Top10：均按发布时间倒序
sorted_articles = sorted(articles, key=_parse_time, reverse=True)
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
        "discussion_url": "https://news.ycombinator.com/item?id=12345"
      }
    ],
    "techcrunch": [...],
    "qbitai": [...],
    "aiera": [...],
    "radarai": [...]
  },
  "sorted_all": [...],  // 全部文章按发布时间倒序
  "monitor": {
    "summary": {
      "total_success_rate": 98.5,
      "total_fail_rate": 1.5,
      "avg_response_time": 2.3,
      "cover_success_rate": 87.2
    },
    "platforms": [...],
    "recent_executions": [...]
  }
}
```

### 3.5 前端展示模块（2026-07-28 报纸风格改版后）

#### 页面结构

```
index.html
├── 报头（Masthead）
│   ├── 报眉（日期 · 期号 · 更新时间）
│   ├── 报名
│   ├── 页面切换（资讯看板/运行监控）
│   └── 操作按钮（刷新/导出）
├── 资讯看板页面
│   ├── 平台栏目 Tab（头版=全部 / 分平台）
│   ├── 搜索栏
│   └── 文章列表（左封面 + 右文字，无封面则文字通栏）
│       └── 文章条目
│           ├── 封面图片（有 cover_url 才渲染）
│           ├── 标题（最多两行截断）
│           └── 元信息（mono 排名 / 来源 / 时间 / HN 真实互动数据）
└── 运行监控页面
    ├── 统计栏（成功率/失败率/响应时间/封面获取率）
    ├── 平台状态列表
    └── 最近采集记录
```

#### 排序模式

| 模式 | 说明 | 数据来源 |
|------|------|---------|
| 🕐 时间排序 | 按 publish_time 降序（唯一排序方式） | sorted_all 字段 |
| 📰 平台分组 | 按 platform 分组 | news 字段 |

> 原「热度排序」模式与 Top3 金银铜样式已随 hot_score 一并移除；热度排名改为元信息行内的 mono 编号。

### 3.6 监控统计模块

#### 监控指标定义

```python
class MonitorMetrics:
    # 汇总指标
    total_success_rate: float      # 总体成功率
    total_fail_rate: float         # 总体失败率
    avg_response_time: float       # 平均响应时间
    cover_success_rate: float      # 封面获取成功率
    
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
│   ├── huggingface.py          # HuggingFace爬虫
│   └── utils/
│       ├── __init__.py
│       ├── filter.py           # 关键词过滤（死代码，未被引用）
│       └── merge.py            # 数据合并去重（含已下线平台过滤）
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
| 数据排序 | 自动按发布时间倒序 |
| 监控统计 | 自动采集运行指标 |
| 数据导出 | 自动生成JSON文件 |
| Git提交推送 | 自动commit和push |
| GitHub Pages部署 | 自动部署前端 |

### 5.2 ⚙️ 需要人工配合的部分

| 维护项 | 频率 | 说明 |
|--------|------|------|
| 爬虫修复 | 按需 | 平台页面结构变化时修复 |
| 关键词调整 | 按需 | 根据热点变化调整过滤关键词 |
| 监控查看 | 日常 | 检查运行状态和数据质量 |

## 六、部署步骤指南

### 步骤1：准备工作
1. [ ] Fork或创建GitHub仓库
2. [ ] 本地克隆仓库
3. [ ] 安装Python 3.11+

### 步骤2：代码开发
1. [ ] 实现各平台爬虫
2. [ ] 实现数据处理逻辑（合并去重、时间排序）
3. [ ] 开发前端页面
4. [ ] 本地测试完整流程

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

## 八、扩展方向

- [x] 多平台数据采集
- [x] 按发布时间排序（2026-07 替代原热度排序）
- [x] 运行监控看板
- [ ] 更多平台接入（知乎、Medium等）
- [ ] 热度趋势分析
- [ ] AI内容摘要
- [ ] 邮件/IM推送通知
