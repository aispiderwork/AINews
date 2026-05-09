# AI Hot News Crawler

AI 热点资讯爬虫系统，自动采集多个平台的 AI 相关新闻。

## 功能特性

- 多平台新闻采集（量子位、Hacker News、TechCrunch、RadarAI、Google AI、新智元）
- 定时自动爬取（每6小时）
- 数据去重与合并
- 前端可视化展示
- 运行监控面板

## 项目结构

```
AINewsCrawler/
├── .github/workflows/    # GitHub Actions 配置
├── crawlers/             # 爬虫模块
├── data/                 # 数据文件
├── docs/                 # 项目文档
├── index.html            # 前端页面
├── main.py               # 主入口
└── requirements.txt      # 依赖配置
```

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行爬虫
python main.py

# 启动本地服务器（查看前端）
python -m http.server 8082
```

### GitHub Actions 部署

1. 推送代码到 GitHub 仓库
2. 配置 GitHub Pages（选择 main 分支）
3. Actions 会自动定时爬取数据

## 数据来源

- 量子位 (QbitAI)
- Hacker News
- TechCrunch
- RadarAI
- Google AI Blog
- 新智元

## License

MIT
