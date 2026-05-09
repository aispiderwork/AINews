# AI资讯平台爬虫完整方案文档

> 基于 Phase 1 实践经验，涵盖所有「最简单」和「简单」难度平台，以及完整的监控部署方案。

---

## 一、平台难度分级与技术方案总览

### 1.1 难度分类

| 难度 | 平台 | 数据源类型 | 封面状态 | 时间格式 | 标签来源 |
|------|------|-----------|---------|---------|---------|
|  最简单 | Hacker News | Firebase API (JSON) | 无封面 (API不提供) | API timestamp | AI关键词过滤 |
| ⭐ 最简单 | TechCrunch | RSS Feed + og:image | 有封面 (二次抓取) | RSS published | RSS tags |
| ⭐⭐ 简单 | 量子位 (qbitai.com) | WordPress HTML | 有封面 (列表页) | 相对时间 (43分钟前) | 文章tag链接 |
| ⭐⭐ 简单 | 新智元 (aiera.com.cn) | WordPress HTML | 部分有封面 | 中文时间 (发布于2026年5月8日) | 分类链接 |
| ⭐⭐ 简单 | RadarAI (radarai.top) | 静态HTML摘要 | 无封面 (纯文字) | 标准时间 (2026-05-06 08:00) | 分类标签 |
| ⭐⭐ 简单 | Google AI Blog | 静态HTML | 有封面 (列表页) | 详情页时间 | 区块分类 |

### 1.2 各平台字段映射总结

| 字段 | Hacker News | TechCrunch | 量子位 | 新智元 | RadarAI | Google AI |
|------|------------|-----------|--------|--------|---------|-----------|
| **标题** | `item.title` | `entry.title` | `<h4>` 内 `<a>` 文本 | `<h2>` 内 `<a>` 文本 | `<h3>` 标签文本 | `<h3>` 标签文本 |
| **链接** | `item.url` | `entry.link` | `<h4>` 内 `<a href>` | `<h2>` 内 `<a href>` | 标题下方 `<a href>` | 标题下方 `<a href>` |
| **封面** | 无 | og:image (二次抓取) | 列表页 `<img src>` | 列表页/详情页 `<img src>` | 无 | 列表页 `<img src>` |
| **封面URL** | — | `aka.doubaocdn.com` | `i.qbitai.com/wp-content/uploads/` | `aka.doubaocdn.com` / `wp-content/uploads/` | — | `aka.doubaocdn.com` |
| **时间** | `item.time` (UNIX) | `entry.published` | 相对时间需转换 | `发布于XXXX年XX月XX日` | `2026-05-06 08:00` | 需进详情页 |
| **标签** | AI关键词匹配 | `entry.tags[].term` | `.tag` 链接文本 | `.category` 链接文本 | 文章上方标签行 | 区块分类标题 |
| **摘要** | 无 | `entry.summary` | 需进详情页 | 需进详情页 | 列表页直接有 | 列表页直接有 |
| **作者** | `item.by` | 无 | 作者链接锚文本 | 无 | RadarAI 官方 | 无 |
| **评论数** | `item.descendants` | 无 | 需进详情页 | 需进详情页 | 无 | 需进详情页 |
| **得分** | `item.score` | 无 | 无 | 无 | 无 | 无 |
| **热度分** | 自动计算 | 自动计算 | 自动计算 | 自动计算 | 自动计算 | 自动计算 |
| **7天筛选** | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **平台Top10** | 按HN热度 | 按发布时间 | 按发布时间 | 按发布时间 | 按发布时间 | 按发布时间 |

### 1.2a 热度计算字段说明

| 字段名 | 类型 | 说明 | 计算来源 |
|--------|------|------|---------|
| `hot_score` | float | 综合热度分 (0-1) | 平台权重×30% + 时间因子×40% + HN热度分×30% |
| `time_factor` | float | 时间衰减因子 (0.1-1.0) | 24h内=1.0, 每过1天-0.1, 10天后=0.1 |
| `platform_weight` | float | 平台权重 | HN(1.0) > TC(0.9) > GoogleAI(0.85) > 量子位(0.8) > 新智元(0.75) > RadarAI(0.7) |
| `hn_hot_score` | float | HN原始热度分 | score×0.7 + descendants×0.3 (仅HN有) |
| `score` | int | HN投票得分 | Hacker News API 提供 |
| `comments_count` | int | HN评论数 | Hacker News API 提供 |

### 1.3 封面展示策略

| 平台 | 封面策略 | 前端展示 | 实现方式 |
|------|---------|---------|---------|
| Hacker News | **不展示封面区域** | 纯文本卡片，无封面占位 | API 本身不提供，正常现象 |
| TechCrunch | **展示封面** | 左图右文布局 | RSS 无封面 → 并发请求文章页提取 og:image |
| 量子位 | **展示封面** | 左图右文布局 | 列表页直接有 `<img>` 标签，直接提取 |
| 新智元 | **有则展示，无则隐藏封面区域** | 动态布局 | 部分文章有封面，部分无 |
| RadarAI | **不展示封面区域** | 纯文本卡片，无封面占位 | 纯文字摘要，无图片 |
| Google AI Blog | **展示封面** | 左图右文布局 | 列表页直接有 `<img>` 标签 |

### 1.4 技术选型总结

| 层级 | 技术 | 用途 | 适配性 |
|------|------|------|--------|
| 采集层 | httpx (异步) | HTTP请求 | ⭐⭐⭐⭐⭐ |
| 采集层 | urllib + feedparser | RSS抓取（SSL兼容） | ⭐⭐⭐⭐⭐ |
| 解析层 | BeautifulSoup4 + lxml | HTML解析 | ⭐⭐⭐⭐⭐ |
| 解析层 | httpx.json() | JSON API解析 | ⭐⭐⭐⭐⭐ |
| 封面提取 | BeautifulSoup4 提取 og:image | 封面获取 | ⭐⭐⭐⭐ |
| 数据存储 | JSON 文件 | 本地+GitHub Pages | ⭐⭐⭐⭐⭐ |
| 调度 | GitHub Actions cron | 定时执行 | ⭐⭐⭐⭐⭐ |

### 1.3 GitHub Actions 约束确认

| 约束 | 值 | 影响 |
|------|-----|------|
| Job 执行时间 | 6小时 | 充分 |
| 内存 | 7-16GB | 充分 |
| 磁盘 | 14GB | 充分 |
| 免费分钟 | 2000/月 | 每日3次约900分钟，安全 |
| 禁止项 | Playwright/Selenium | 不使用浏览器自动化 |
| 数据存储 | JSON (无SQLite) | 兼容 GitHub Pages |

---

## 二、各平台爬虫详细方案

### 2.1 数据抓取策略

| 平台 | 抓取方式 | 抓取范围 | 筛选条件 | 更新频率 |
|------|---------|---------|---------|---------|
| **Hacker News** | Firebase API | Top 100 | 近7天 + AI相关 + 热度Top10 | 每2小时 |
| **TechCrunch** | RSS Feed | 全部文章 | 近7天 + 最新Top10 | 每2小时 |
| **量子位** | 静态HTML | 首页文章 | 近7天 + 最新Top10 | 每2小时 |
| **新智元** | 静态HTML | 首页文章 | 近7天 + 最新Top10 | 每2小时 |
| **RadarAI** | 静态HTML | Updates页 | 近7天 + 最新Top10 | 每2小时 |
| **Google AI** | RSS Feed | 全部文章 | 近7天 + 最新Top10 | 每2小时 |

**抓取策略说明**：
- **近7天筛选**：所有平台只保留7天内发布的文章（基于当前时间往前推7天）
- **各平台Top10**：每个平台独立筛选，取该平台近7天内最热门的10篇文章
- **Hacker News热度**：基于投票分(score)和评论数(descendants)计算
- **其他平台热度**：基于发布时间排序（越新越热）
- **总计文章数**：最多 6平台 × 10篇 = 60篇文章

---

### 2.2 Hacker News — 官方 Firebase API

**数据源**：`https://hacker-news.firebaseio.com/v0/`

**技术方案**：
```
GET /v0/topstories.json     → 返回热门ID列表 (int[])
GET /v0/item/{id}.json      → 返回单篇文章详情
```

**实现细节**：
- 获取 top 100 热门ID（扩大范围以支持近7天+AI筛选）
- 并发请求每个 item 的详情
- 用 AI 关键词列表过滤标题
- 筛选近7天内发布的文章
- 按热度分排序取Top10
- 保留 `discussion_url` = `news.ycombinator.com/item?id={id}`

**封面处理**：HN API 无封面信息，不提供封面

**注意事项**：
- 官方 API 无速率限制，稳定可靠
- 返回的 `url` 是原文链接（如 anthropic.com），不是 HN 页面
- 需用 AI 关键词过滤非AI内容
- 无封面字段是正常现象

---

### 2.3 TechCrunch — RSS Feed + og:image 二次抓取

**数据源**：`https://techcrunch.com/category/artificial-intelligence/feed/`

**技术方案**：
```
Step 1: feedparser.parse(RSS_URL)   → 获取标题、链接、时间、标签
Step 2: 对缺少封面的文章，并发请求文章页面提取 og:image
```

**实现细节**：
- RSS Feed 不包含 `media_content`/`media_thumbnail`，封面为 null
- 使用 urllib.request + ssl 上下文处理 SSL 验证（macOS 兼容性）
- 提取封面时解析 `<meta property="og:image">` 标签
- 并发执行封面提取，20篇文章约5秒完成

**注意事项**：
- macOS 的 Python SSL 证书链不完整，需用 certifi 的 CA bundle
- feedparser 的 `bozo` 标志表示解析警告（非致命）
- 日期格式需多重 try-except 兼容（`%z` / `+0000` / 原始字符串）

---

### 2.4 量子位 (qbitai.com) — WordPress 静态HTML

**数据源**：`https://www.qbitai.com/`

**技术方案**：
```
httpx.AsyncClient.get(url)  → 获取HTML
BeautifulSoup(html, 'lxml')  → 解析DOM
CSS选择器定位文章卡片、标题、封面、标签
```

**实际页面结构分析**：
- WordPress 主题，文章列表结构为：封面图 + 标题链接 + 作者 + 时间 + 标签
- 封面图格式：`.webp` 格式，存储在 `i.qbitai.com/wp-content/uploads/` 路径
- 标题格式：`<h4>` 标签 + `<a>` 链接
- 时间格式：相对时间如 "43分钟前"、"2小时前"、"昨天 15:14"、"2026-05-04"
- 标签：每个标签有独立链接，如 `[Deepseek]`、`[OpenAI]`、`[Claude]`

**字段映射**：
- 标题：`<h4>` 标签内 `<a>` 的文本内容
- 链接：`<h4>` 内 `<a>` 的 href 属性
- 封面：`.post-thumbnail img` 或 `.wp-post-image` 的 src 属性
- 时间：`.post-meta` 内的相对时间文本
- 标签：`.tag` 或 `.category` 容器内的链接文本
- 作者：`/?author=xxx` 链接的锚文本

**注意事项**：
- WordPress 主题更新可能改变 CSS 选择器
- 需设置随机 User-Agent
- 翻页逻辑：观察 URL 模式如 `/page/2/`
- 请求间隔 1-2 秒
- CDN 图片可能需要添加 referer
- 时间需要转换为标准时间格式

---

### 2.5 新智元 (aiera.com.cn) — WordPress 静态HTML

**数据源**：`https://www.aiera.com.cn/`

**技术方案**：与量子位类似，WordPress 静态 HTML 解析

**实际页面结构分析**：
- WordPress 主题，文章列表结构为：标题链接 + 发布时间 + 封面图（部分文章有）
- 标题格式：`<h2>` 标签 + `<a>` 链接（URL包含URL编码的中文字符）
- 时间格式：`发布于2026年5月8日`
- 封面图：部分文章有 `![]()` 格式的图片链接，来自 `aka.doubaocdn.com` CDN
- 结构：标题 → 时间 → 查看链接 → 封面图（如有）

**字段映射**：
- 标题：`<h2>` 标签内 `<a>` 的文本内容
- 链接：`<h2>` 内 `<a>` 的 href 属性
- 封面：`.post-thumbnail img` 或 `.entry-content img` 的 src 属性，来自 `aka.doubaocdn.com`
- 时间：`.entry-meta` 内的 `发布于XXXX年XX月XX日` 格式文本
- 标签：`.tag` 或 `.category` 容器内的链接文本

**注意事项**：
- 域名可能变更（原 xinzhiyuan.com → aiera.com.cn）
- 需人工确认当前可用地址
- 封面可能在 `wp-content/uploads/` 或 `aka.doubaocdn.com` 等 CDN 路径下
- CDN 图片可能需要添加 referer
- 时间格式为中文，需转换为标准时间格式
- URL 包含 URL 编码的中文，需正确处理

---

### 2.6 RadarAI (radarai.top) — 静态HTML

**数据源**：`https://radarai.top/updates/`

**技术方案**：静态 HTML 解析

**实际页面结构分析**：
- 页面为文章列表，按时间倒序排列
- 每篇内容为摘要形式，包含标题、时间、简介
- 更新频率约为每日3-6条AI速报
- 文章结构为 `<h3>` 标题 + 链接 + 时间信息 + 摘要内容
- 标签信息：`RadarAI 官方`、`AI速报`、`官方AI动态`、`开源` 等
- 无封面图片，纯文字摘要

**字段映射**：
- 标题：`<h3>` 标签或 `.brief-title` 内的文本
- 链接：`<a href="...">` 标签的 href 属性
- 时间：紧跟在标题后的日期时间信息，格式如 `2026-05-06 08:00`
- 简介：文章详情页内容摘要
- 标签：分类信息如 AI速报、官方AI动态等
- 封面：无（RadarAI 无封面图）

**注意事项**：
- 更新频率固定（每日多次更新）
- 内容为结构化摘要而非完整文章
- 页面结构相对稳定
- 无封面图片，仅文字内容
- 适合快速获取AI行业动态
- 时间格式为标准格式，无需转换

---

### 2.7 Google AI Blog — 静态 HTML

**数据源**：`https://blog.google/technology/ai/`

**技术方案**：httpx + BeautifulSoup 解析

**实际页面结构分析**：
- Google 博客页面结构相对稳定
- 文章分为不同区块：Gemini App、Research、Developers 等分类
- 每篇文章包含：标题 `<h3>`、链接、摘要文本、封面图
- 封面图来自 `aka.doubaocdn.com` CDN
- 时间信息通常在文章详情页，列表页不直接显示

**字段映射**：
- 标题：`<h3>` 标签内的文本
- 链接：`<a href="...">` 标签的 href 属性
- 封面：`.article-image img` 或 `.wp-post-image` 的 src 属性，来自 `aka.doubaocdn.com`
- 时间：文章详情页内的时间信息，列表页不显示
- 标签：分类信息如 Gemini App、Research、Developers 等
- 摘要：标题下方的描述文本

**注意事项**：
- 可能有 Cloudflare 防护（概率较低）
- 更新频率低，建议抓取间隔拉长
- 文章链接可能是 `https://blog.google/technology/ai/{slug}/` 格式
- 时间信息需要访问文章详情页获取
- CDN 图片可能需要添加 referer

---

## 三、爬虫技术指标监控方案

### 3.1 监控指标定义

所有指标在 `main.py` 中采集，写入 `data/news.json` 的 `monitor` 字段。

| 指标类别 | 指标名 | 类型 | 说明 |
|---------|--------|------|------|
| **全局** | `total_success_rate` | float | 成功平台 / 总平台数 (%) |
| **全局** | `total_fail_rate` | float | 失败平台占比 (%) |
| **全局** | `avg_response_time` | float | 成功请求平均耗时 (秒) |
| **全局** | `cover_success_rate` | float | 有封面的文章 / 总文章数 (%) |
| **全局** | `hot_sort_enabled` | bool | 是否启用热度排序 |
| **全局** | `platform_hot_stats` | dict | 各平台热度统计 |
| **平台级** | `status` | string | online / error |
| **平台级** | `item_count` | int | 本次抓取文章数 |
| **平台级** | `last_crawl` | datetime | 上次成功抓取时间 |
| **执行历史** | `timestamp` | datetime | 执行时间 |
| **执行历史** | `platform` | string | 平台标识 |
| **执行历史** | `status` | string | success / error |
| **执行历史** | `items_collected` | int | 本次收集文章数 |
| **执行历史** | `latency` | float | 本次请求耗时 (秒) |
| **错误统计** | `failure_reasons` | dict | 按错误类型计数 |

### 3.1a 热度排序监控

| 指标 | 类型 | 说明 |
|------|------|------|
| `hot_sort_enabled` | bool | 热度排序功能开关状态 |
| `platform_hot_stats.{platform}.count` | int | 该平台文章数量 |
| `platform_hot_stats.{platform}.avg_hot_score` | float | 该平台平均热度分 |
| `platform_hot_stats.{platform}.max_hot_score` | float | 该平台最高热度分 |
| `platform_hot_stats.{platform}.min_hot_score` | float | 该平台最低热度分 |

### 3.2 监控数据结构

```json
{
  "update_time": "2026-05-08T14:30:00+00:00",
  "news": { ... },
  "monitor": {
    "summary": {
      "total_success_rate": 100.0,
      "total_fail_rate": 0.0,
      "avg_response_time": 2.5,
      "cover_success_rate": 85.0
    },
    "platforms": [
      {
        "platform": "hackernews",
        "name": "Hacker News",
        "status": "online",
        "item_count": 11,
        "last_crawl": "2026-05-08T14:30:00+00:00"
      }
    ],
    "failure_reasons": {
      "network_timeout": 0,
      "page_structure_changed": 0
    },
    "recent_executions": [
      {
        "timestamp": "2026-05-08T14:30:00+00:00",
        "platform": "hackernews",
        "status": "success",
        "items_collected": 11,
        "latency": 3.2
      }
    ]
  }
}
```

### 3.3 历史监控持久化方案

由于 JSON 文件每次写入会覆盖，需要**追加历史记录**策略：

**方案：维护 history.json 独立文件**

```python
# main.py 中新增逻辑
HISTORY_FILE = OUTPUT_DIR / 'history.json'

def append_history(new_record: dict):
    """追加执行记录到历史文件"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    else:
        history = {'executions': []}
    
    history['executions'].append(new_record)
    # 保留最近 100 条记录
    if len(history['executions']) > 100:
        history['executions'] = history['executions'][-100:]
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
```

**历史文件结构**：
```json
{
  "executions": [
    {
      "run_id": "20260508-143000",
      "timestamp": "2026-05-08T14:30:00+00:00",
      "trigger": "schedule",
      "total_items": 31,
      "platforms": {
        "hackernews": {"status": "success", "items": 11, "latency": 3.2},
        "techcrunch": {"status": "success", "items": 20, "latency": 8.5}
      },
      "duration_seconds": 20.1
    }
  ]
}
```

### 3.3a 热度排序数据输出

**主数据文件 news.json 新增字段**：
```json
{
  "update_time": "2026-05-09T12:00:00+00:00",
  "news": {
    "hackernews": [
      {
        "title": "...",
        "url": "...",
        "platform": "hackernews",
        "hot_score": 0.8234,
        "time_factor": 0.9167,
        "platform_weight": 1.0,
        "hn_hot_score": 205.9,
        "score": 256,
        "comments_count": 89
      }
    ]
  },
  "sorted_all": [
    // 全部文章按 hot_score 降序排列
    {"title": "...", "hot_score": 0.9123, ...},
    {"title": "...", "hot_score": 0.8567, ...}
  ],
  "monitor": {
    "summary": {
      "hot_sort_enabled": true,
      "platform_hot_stats": {
        "hackernews": {
          "count": 15,
          "avg_hot_score": 0.7523,
          "max_hot_score": 0.9123,
          "min_hot_score": 0.5234
        },
        "techcrunch": {...}
      }
    }
  }
}
```

### 3.4 监控数据是否需要部署到 GitHub Actions？

**结论：需要。**

**原因**：
1. 监控数据来源于爬虫执行过程，只有 GitHub Actions 运行时才能产生真实数据
2. `news.json` 和 `history.json` 由爬虫写入，需要随数据一起 commit 并部署到 Pages
3. 验证页面（`verify-crawler.html`）需要读取这些监控数据来展示统计信息

**部署流程**：
```
GitHub Actions 触发 → 执行爬虫 → 生成 news.json + history.json 
    → git commit 数据文件 → git push 
    → Pages 自动部署更新后的 JSON
    → 验证页面加载最新数据和监控指标
```

---

## 四、GitHub Actions 工作流配置

### 4.1 目录结构

```
.
├── .github/
│   ── workflows/
│       └── crawl-news.yml       # 定时爬虫工作流
── crawlers/
│   ├── __init__.py
│   ├── base.py                  # 基础爬虫类
│   ├── hackernews.py            # HN API 爬虫
│   ├── techcrunch.py            # TC RSS 爬虫
│   ├── qbitai.py                # 量子位爬虫
│   ├── aiera.py                 # 新智元爬虫
│   ├── radarai.py               # RadarAI 爬虫
│   ├── googleai.py              # Google AI Blog 爬虫
│   └── utils/
│       ├── __init__.py
│       ├── filter.py            # AI关键词过滤
│       ├── merge.py             # 数据合并去重
│       └── hot_score.py         # 热度计算模块
├── data/
│   ├── news.json                # 最新新闻数据
│   └── history.json             # 历史执行记录
├── docs/                        # 文档目录
│   ├── CRAWLER_FULL_SPEC.md     # 爬虫完整方案
│   ├── product_plan.html        # 产品方案
│   ├── technical_architecture.md # 技术架构
│   └── ui-design-specification.md # UI设计规范
├── verify-crawler.html          # 数据验证页面
├── index.html                   # 主页（可指向验证页面）
├── main.py                      # 主入口
└── requirements.txt             # 依赖清单
```

### 4.2 工作流 YAML

```yaml
name: AI News Crawler

on:
  schedule:
    - cron: '0 0,6,12 * * *'    # 每天 0:00, 6:00, 12:00 UTC (北京时间 8:00, 14:00, 20:00)
  workflow_dispatch:
    inputs:
      platform:
        description: '指定平台 (留空=全部)'
        required: false
        type: string

permissions:
  contents: write

jobs:
  crawl:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - run: python main.py ${{ inputs.platform }}
      
      - run: |
          git config user.name 'github-actions[bot]'
          git config user.email 'github-actions[bot]@users.noreply.github.com'
          git add data/news.json data/history.json
          if ! git diff --staged --quiet; then
            git commit -m "Update news data - $(date '+%Y-%m-%d %H:%M:%S')"
            git push
          fi
```

### 4.3 分钟数估算（全平台）

| 平台 | 单次耗时 | 每日3次 | 每月消耗 |
|------|---------|---------|---------|
| Hacker News | < 1分钟 | 3分钟 | 90分钟 |
| TechCrunch | 3分钟 | 9分钟 | 270分钟 |
| 量子位 | 2分钟 | 6分钟 | 180分钟 |
| 新智元 | 2分钟 | 6分钟 | 180分钟 |
| RadarAI | 1分钟 | 3分钟 | 90分钟 |
| Google AI | 1分钟 | 3分钟 | 90分钟 |
| **总计** | **10分钟** | **30分钟** | **900分钟** |

**结论**：900分钟/月 < 2000分钟免费额度，安全余量 55%。

---

## 五、注意事项汇总

### 5.1 通用注意事项

| 事项 | 说明 |
|------|------|
| User-Agent 轮换 | 每次请求随机选择，防基础反爬 |
| 请求间隔 | 1-2秒随机延迟，控制频率 |
| 超时设置 | 30秒超时，单个平台失败不影响整体 |
| 错误隔离 | 每个平台独立 try-except，失败不阻断 |
| 依赖缓存 | GitHub Actions 使用 actions/cache 加速 |
| 数据格式 | JSON，兼容 GitHub Pages 静态托管 |
| robots.txt | 遵守目标站 robots.txt 规则 |

### 5.2 平台特定注意事项

| 平台 | 特别注意 |
|------|---------|
| Hacker News | 无封面是正常现象；`url` 是原文链接不是 HN 页面 |
| TechCrunch | macOS SSL 证书问题需用 certifi；封面需二次抓取 |
| 量子位 | WordPress 主题更新可能破坏选择器 |
| 新智元 | 需先确认域名是否变更 |
| RadarAI | 更新频率低，抓取间隔可设长 |
| Google AI Blog | 时间格式可能为相对时间 |

### 5.3 维护建议

| 场景 | 建议 |
|------|------|
| 页面结构变化 | 在 `verify-crawler.html` 中观察抓取结果变化 |
| 平台失败 | 检查 `monitor.failure_reasons` 和 `monitor.platforms[].status` |
| 封面缺失 | 检查目标站是否改变了 og:image 标签结构 |
| 分钟数预警 | 监控 GitHub Actions 使用量，必要时减少频率 |

---

*文档版本: v2.0*
*基于 Phase 1 实践经验编写*
*最后更新: 2026-05-08*
