# X / HuggingFace Trending 爬虫可行性调研

> 调研时间：2026-07-28 ｜ 调研方式：官方文档/社区资料检索 + 接口实测
> 需求：为 AINews 增加 X、HuggingFace Trending 榜单中 AI / 大模型 / LLM 方向的头部热门内容，单渠道最多 10 条

---

## 结论先行

| 渠道 | 可行性 | 结论 |
|---|---|---|
| **HuggingFace** | ✅ 高 | **建议立即实施**。官方公开 API 免 key、合规、带真实热度指标（trendingScore / upvotes），实测可用 |
| **X (Twitter)** | ❌ 低 | **不建议自建爬虫**。官方无免费读接口、直接抓取违反 ToS 且技术脆弱、Nitter 已死。如需 X 内容只能走付费第三方 API |

一个附带收益：HuggingFace 的热度指标（trendingScore、likes、downloads、论文 upvotes）是**平台官方计算的真实数据**，接入后可以解决本次整改中"热度分不真实"的痛点——头版可以重新展示有依据的热度信息。

---

## 1. HuggingFace：可行，推荐实施

### 1.1 实测结果（2026-07-28 本机实测，无需 API key）

| 接口 | 状态 | 说明 |
|---|---|---|
| `GET /api/models?sort=trendingScore&pipeline_tag=text-generation&limit=10` | ✅ 200 | Trending 模型榜，返回真实 `trendingScore`、`likes`、`downloads` |
| `GET /api/datasets?sort=trendingScore&limit=10` | ✅ 200 | Trending 数据集榜，同上有真实 trendingScore |
| `GET /api/daily_papers` | ✅ 200 | 每日论文榜（当天 50 篇），含 `upvotes`、`numComments`、`publishedAt`、`summary`、`thumbnail`——**最贴近"热门文章"语义** |
| `GET /blog/feed.xml` | ✅ 200 | HF 官方博客 RSS |

实测样例（今日 Trending 模型 Top1）：`poolside/Laguna-S-2.1`，trendingScore 738，likes 768，downloads 63,605。

### 1.2 合规与稳定性

- 以上为 HuggingFace **官方公开 REST API**，匿名可访问，属官方支持的集成方式（huggingface_hub 库底层即这套 API），无 ToS 风险。
- 频率：GitHub Actions 每天 2 次、每次 2-3 个请求，远低于公共 API 的合理使用强度，如需更稳妥可申请免费 HF token 带 `Authorization: Bearer` 头。

### 1.3 与现有架构的契合

- 内容形态：论文 = "文章"（标题/摘要/时间/链接/upvotes 齐全，还有 thumbnail 可作封面）；模型/数据集 = "趋势条目"（name 作标题、模型卡链接、likes/downloads 作真实热度）。
- 限制 10 条：API 自带 `limit` 参数，天然满足。
- 字段映射到现有 article schema：

```
title        ← paper.title / model.id
url          ← huggingface.co/papers/{id} / huggingface.co/{modelId}
publish_time ← publishedAt / createdAt
summary      ← paper.summary（已有字段，前端可后续展示）
cover_url    ← paper.thumbnail
score        ← upvotes / likes   ← 真实热度！
platform     ← 'huggingface'
```

### 1.4 实施建议（约半天工作量）

1. 新增 `crawlers/huggingface.py`：抓 `daily_papers`（按 upvotes 取 Top10）+ `models?sort=trendingScore`（`pipeline_tag=text-generation` 过滤 LLM 方向，取 Top10）。
2. `main.py` 注册平台（priority 6）；前端 `platformNames` 与栏目 Tab 增加 `huggingface`。
3. 元信息行可直接展示 `↑ upvotes` / `❤ likes`——真实热度回归。

---

## 2. X (Twitter)：不建议自建爬虫

### 2.1 官方 API 现状（2026 年）

- **免费层已取消**（2026-02 起新开发者全面转为 pay-per-use 计费，需先购买 credit）。
- 读取约 $0.005/帖，月读取上限 200 万帖；**搜索仅限近 7 天**（全量归档搜索要 Pro $5,000/月，且已关闭新注册）。
- 对本项目"每 12 小时抓 10 条 AI 热门"的场景，官方 API 成本不高（每天几美分），但需要绑卡开户，且 X 的 Trending 是全站热点，**并非 AI 垂直榜单**，还需自行做关键词过滤与互动量排序。

### 2.2 非官方抓取路径均已失效或高风险

- **直接爬虫**：X 的 ToS 明确禁止，且有诉讼先例；技术上登录墙 + 反爬严格。
- **Guest-token GraphQL**（读 Web 端同款 JSON）：2026 年仍可工作但脆弱——每个 guest token 约 150 次请求即 429，数据中心 IP 10-20 次即被封，**必须配住宅代理池**，运维成本远超收益。
- **Nitter**：2024 年起已死，剩余实例不可用。

### 2.3 若仍想要 X 内容

唯一现实选项是**第三方统一数据 API**（SocialCrawl、SociaVault、Apify、Sorsa 等），credit 计费、多有免费试用额度，本质是为别人的抓取基础设施付费。对本项目属于"可选增强"，建议等有明确需要时再评估，不进入当前迭代。

---

## 3. 建议的迭代顺序

1. **本期**：接入 HuggingFace（daily_papers + trending models），顺带让真实热度指标回归头版。
2. **备选增强**：HuggingFace 博客 RSS（官方深度文章）、Reddit r/LocalLLaMA（公开 JSON，`/r/LocalLLaMA/hot.json` 免 key，真实 upvotes）——与 HF 同为"真实热度 + 零成本"的优质源。
3. **暂缓**：X 渠道，待有预算与明确需求后通过第三方 API 接入。
