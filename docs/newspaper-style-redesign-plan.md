# AI Hot News · 报纸风格网页重设计方案

> 基于 `index.html` 现状（暗色赛博朋克监控台风格）的改版设计方案。
> 设计依据：Kimi Design Skill —— `principles.md`（决策层）+ `tokens.json`（取值层）+ `web-best-practices.md` / `components-web.md` / `animation.md`（组件与页面层）。

---

## 1. 设计概念

**从「监控大屏」到「每日 AI 早报」。**

当前页面是深色霓虹风格的运维监控台：发光渐变、玻璃卡片、Orbitron 科幻字体。这与产品的真实用途——**每天定时抓取六个平台的 AI 资讯供人阅读**——并不匹配。用户的核心任务是"扫读今天 AI 圈发生了什么"，这正是报纸几百年优化出来的信息形态。

改版概念：**把网站做成一份每天自动出版的数字报纸**。

- 页面即报纸：报头（Masthead）、日期与期号、头版头条、分栏版面
- 六个平台即六个「版面/栏目」：全部 = 头版，各平台 = 子栏目
- 热度排序即编辑排序：Top1 是头条（大标题 + 摘要），Top2-3 是要闻，其余是列表简讯
- 运行监控页即「印刷房日志」：克制的状态表格，而非发光仪表盘

风格基调遵循 **Quiet Utility** 原则：报纸感靠**排版秩序**（字重、分栏、细线、留白）表达，而不是靠纹理、做旧、阴影等装饰。这是一份"干净的现代报纸"，对标 The New York Times 数字版 / 财新网的信息气质，而非复古做旧风。

---

## 2. 现状诊断（改版动因）

| 现状 | 冲突的原则 | 处理 |
|---|---|---|
| 深色霓虹背景 + radial-gradient 光斑 | Quiet Utility / Surface Usage：避免装饰性渐变 | 改为纸面浅色（`background.primary` / `groupedBackground.primary`） |
| Logo 渐变色 + text-shadow 发光 | 颜色应表达层级而非装饰 | 报头用 `labels.primary` 单色 |
| 按钮/卡片 hover 发光（glow）+ translateX 位移 | Purposeful Motion：动效应解释状态而非装饰 | hover 仅改背景填充 |
| 平台徽章六个彩色渐变（橙/绿/蓝/紫…） | Semantic Hierarchy：一个区域内多个竞争强调点 | 统一为墨色文字徽章，仅保留一个强调色（聚焦蓝）用于可交互元素 |
| Top1/2/3 金银铜渐变奖牌 | 装饰性、与"阅读"无关 | 改为大号排名数字（编辑排版手法，如 "01"） |
| Orbitron / Exo 2 科幻字体 | Typography 原则：字体服务于阅读秩序 | 回归 `PingFang SC` 体系（见 §4 Token Gap 记录） |
| 全宽 1400px 卡片流 | Main Content Width：核心任务应聚焦 | 报纸栏宽容器（见 §5） |

---

## 3. 色彩方案（Token 映射）

整体采用**浅色"纸面"主题**为主版本；暗色模式作为可选二期（报纸没有暗色版，优先把浅色做好）。

| 角色 | 报纸语义 | Token 路径 | 取值（light） |
|---|---|---|---|
| 纸面底色 | 纸张 | `color.background.primary` | `#ffffff` |
| 版面分区底色 | 栏间衬底 | `color.groupedBackground.primary` | `#f5f5f5` |
| 墨色正文 | 油墨 | `color.labels.primary` | `rgba(0,0,0,0.9)` |
| 副文/摘要 | 淡墨 | `color.labels.secondary` | `rgba(0,0,0,0.6)` |
| 元信息（日期/来源） | 报眉小字 | `color.labels.tertiary` | `rgba(0,0,0,0.45)` |
| 弱化/禁用 | — | `color.labels.quaternary` | `rgba(0,0,0,0.3)` |
| 报线/分隔线 | 栏线 | `color.separator.s1` | `rgba(0,0,0,0.13)` |
| 选中/hover 填充 | — | `color.fills.f1` / `color.fills.f2` | `rgba(0,0,0,0.03)` / `0.05` |
| 唯一强调色 | 可交互/链接/聚焦 | `color.status.kimiBlue` | `#1783ff` |
| 采编状态：正常 | 监控页 | `color.status.positiveGreen` | `#16c456` |
| 采编状态：异常/失败 | 监控页 | `color.status.danger` | `#ff3849` |

**用色纪律**：
- 报纸的"红黑版式"传统在这里映射为「墨色 + 单一聚焦蓝」。**聚焦蓝只出现在可交互元素上**（tab 激活态、按钮、链接、focus-visible），正文阅读区不放彩色。
- 平台徽章不再使用六色彩虹；平台区分靠**文字标签本身**（来源本就是文字信息）。
- 分隔用 `separator.s1` 细线（1px，报纸栏线的数字等价物），不用重边框、不用卡片套卡片。卡片之间的区分优先用**间距 + 背景填充对比**（Surface Over Stroke）。

---

## 4. 字体排版

### 4.1 字阶映射（全部来自 token）

| 报纸元素 | Token 路径 | 规格 |
|---|---|---|
| 报头报名 | `typography.webUI.largeTitleEmphasized` | 20 / 30 / w600 |
| 头条标题 | `typography.markdown.h1Content` | 22 / 36 / w400 |
| 要闻标题（Top2-3） | `typography.markdown.h3Content` | 18 / 28 / w400 |
| 列表标题 | `typography.webUI.t2Emphasized` | 16 / 24 / w500 |
| 摘要/正文 | `typography.markdown.b2Content` | 15 / 24 / w400 |
| 栏目名/Tab/标签 | `typography.webUI.b2Regular` | 14 / 20 / w400 |
| 元信息（日期、来源、热度分） | `typography.webUI.c1Regular` | 12 / 18 / w400 |
| 时间戳/期号（等宽） | `typography.fontFamily.mono`（Geist Mono） | 配合 c1 字号 |

### 4.2 Token Gap 记录（需设计系统确认，不在 MVP 内自造）

1. **报纸标题字（serif 展示字体）**：传统报纸的权威感很大程度来自衬线标题字（如 NYT 的 Cheltenham、中文报宋）。当前 token 仅有 `PingFang SC`（sans）与 `Geist Mono`（mono），**无 serif 展示字体**。Principle 4 明确禁止自行引入新字体 → 本方案头条标题使用 `h1Content`（w400，以字级而非字体区分层级），并将「新增 serif display token」记录为待确认缺口。若后续获批，建议候选：思源宋体（Source Han Serif）仅用于报头与头条标题。
2. **超大头条字号**：h1Content 上限 22px，报纸头版头条通常需要 32px+ 的视觉冲击。方案通过**独占整栏 + 摘要 + 封面图**的版面特权表达头条地位，而非超大字号；如需更大标题字号，同样记录为缺口。

---

## 5. 版面布局

### 5.1 整体结构

```
┌─────────────────────────────────────────────────┐
│ 报眉条：日期 · 期号 · 更新时间（c1，tertiary）        │
│ 报头：AI 日报            [资讯看板] [运行监控]        │  ← Masthead，双细线框住（上 1px + 下 1px s1）
├─────────────────────────────────────────────────┤
│ 栏目条：头版(全部) · HN · TC · 量子位 · 新智元 …      │  ← 平台 Tab，下划线式
├─────────────────────────────────────────────────┤
│ 搜索框（油墨边框，focus 变蓝）                          │
├──────────────────────┬──────────────────────────┤
│ 头版头条（Top1）        │  要闻栏（Top2-3）           │  ← 头版 Grid
│ 大标题 + 摘要 + 封面     │  中标题 × 2                │
├──────────────────────┴──────────────────────────┤
│ 简讯列表（Top4+）：编号 · 标题 · 元信息 · 一行截断      │
└─────────────────────────────────────────────────┘
```

### 5.2 宽度与节奏

- **内容容器最大宽度：960px，居中**。比 Kimi 对话窗（768px）宽，因为报纸是 browse 型内容而非 task 型；又不沿用旧的 1400px 全宽——报纸栏宽过宽会毁掉行长（理想 45-75 字符）。
- 间距节奏遵循 `32 / 24 / 20 / 16 / 12 / 8 / 4`：
  - 版面大区块之间：`spacing.3xl`（32px）
  - 头版与简讯列表之间：`spacing.2xl`（24px）
  - 列表条目之间：`spacing.lg`（16px）+ `separator.s1` 细线
  - 条目内部标题→元信息：`spacing.sm`（8px）
  - 图标与文字：`spacing.xs`（4px）

### 5.3 头版 Grid（桌面）

- 左栏（头条）：占 7/12，含封面图（16:9，`radius.lg` 12px）、头条标题、两行摘要、元信息行。
- 右栏（要闻）：占 5/12，Top2-3 各一条：标题 + 元信息，之间用 `s1` 细线分隔。
- 两栏之间用 **1px 竖栏线**（`separator.s1`）分隔——这是报纸分栏的标志性语言，也是方案中唯一保留的结构性竖线。
- ≤768px：右栏折到左栏下方，竖栏线消失，退化为统一纵向列表。

### 5.4 简讯列表

- 每条 = `编号（mono，tertiary）+ 标题（t2Emphasized，单行截断）+ 元信息行`。
- 不再使用卡片边框与封面缩略图（封面特权只给头条）；列表条目之间用细线分隔，整列无框。
- 编号取代金银铜奖牌：大号 mono 数字 "01 02 03…"，延续热度排序信息但去除装饰。

---

## 6. 组件规范

> 有对应 Kimi 组件规范的遵循规范；无对应组件的（News Entry、Masthead）按 tokens + principles 推导，并记录。

### 6.1 报头 Masthead（推导组件）

- 上行：报名（largeTitleEmphasized）居左；右侧「资讯看板 / 运行监控」导航 + 刷新（primary Button 32）+ 导出（outline Button 32）。
- 下行报眉：左侧日期 + 「第 N 期」（由 `update_time` 推导，c1 + mono）；右侧「更新于 HH:MM」（mono，tertiary）。
- 上下各 1px `s1` 报线；sticky 时压缩为单行（报名缩小为 b1Emphasized），`z-index: 500`（`--z-header`）。

### 6.2 栏目 Tab（无现成组件 → 按 web-best-practices §11 推导）

- 文本式 Tab（下划线指示器），b2Regular，激活态文字转 `kimiBlue` 并以 2px 下划线标示；计数徽章用 `fills.f2` 填充 + c1Emphasized，**不再做成彩色胶囊**。
- hover：`fills.f1` 背景；focus-visible：`kimiBlue` 外描边。

### 6.3 新闻条目 News Entry（推导组件）

- 三段式：标题 → 元信息行（来源 · 时间 · 热度分）→ 标签（可选）。
- 热度分不再用 🔥 渐变徽章，改为元信息中的一项：`热度 0.873`（c1，tertiary）。
- HN 的 score/comments 同理并入元信息行，以 `·` 分隔。
- 状态：
  - default：白底；
  - hover：`fills.f1` 填充，标题转 `kimiBlue`（明确表示"可点击跳转"）；无位移、无发光；
  - active：`fills.f2`；
  - focus-visible：`kimiBlue` 描边（条目应可 Tab 键聚焦，见 §8）。
- 长标题：头条两行截断，列表单行截断，布局不抖动。

### 6.4 平台徽章 → 来源署名（重设计）

- 六色渐变徽章改为**纯文字署名**：`Hacker News · 14:32`（c1Regular，tertiary）。
- 报纸惯例是署名（byline）而非彩色贴纸；平台辨识度由文字承担。

### 6.5 运行监控页（「印刷房」）

- 四个指标卡 → 一行**统计栏**：数值（h2Content 20/32，mono 可选）+ 标签（b2，secondary），之间细线分隔，无卡片边框、无 hover 上浮。
- 成功/失败率仅数字着色（`positiveGreen` / `danger`），不带光晕。
- 平台状态：表格化列表（状态点 + 名称 + 条数），状态点去 glow、去脉冲动画，改静态圆点（`positiveGreen` / `danger`）。
- 采集记录：左侧 3px 状态色条改为圆形状态点，行间距 `spacing.lg`，行间细线；hover 用 `fills.f1`。

### 6.6 按钮与输入

- Button 遵循 `components-web/button.md`：刷新 = primary（size 32），导出 = outline（size 32）。
- 搜索输入框：白底、1px `s1` 边框、`radius.md`（10px）、focus 时 `kimiBlue` 边框；内部 t2Regular（16/24）。
- 空态 / 加载态 / 加载失败态：居中 `b1Regular` + tertiary 色，加载失败附「重试」outline 按钮——沿用现有逻辑，只换视觉。

---

## 7. 动效规范（遵循 animation.md）

这是高频浏览工具，动效全面收敛：

| 交互 | 规范 |
|---|---|
| Tab 切换 / hover 变色 | **不做位移动画**；颜色过渡 ≤150ms `ease`；页面切换 fade 取消，直接切换（报纸翻版不需要淡入） |
| 按钮按压 | `:active` `transform: scale(0.97)`，100–160ms |
| 条目 hover | 仅背景填充变化，`transition: background-color 150ms ease` |
| 数据刷新 | 刷新按钮 loading 态（spinner 叠加，复用默认态尺寸）；列表内容就地替换，不做 stagger——每天看一次的页面，stagger 只会拖慢扫读 |
| 状态点脉冲动画 | **移除**（高频干扰，无信息价值） |
| 全局 | 保留 `prefers-reduced-motion` 媒体查询；transition 指定具体属性，禁用 `transition: all` |

---

## 8. 可访问性与细节

- 新闻条目从 `div onclick` 改为 `<a href target="_blank">`：获得键盘聚焦、右键菜单、屏幕阅读器语义，同时修复"新标签打开"的行为一致性。
- focus-visible 统一 `kimiBlue` 描边。
- 正文对比度：`labels.primary`（0.9 黑）on `#fff` ≈ 15:1；`labels.secondary`（0.6 黑）≈ 7:1，均过 WCAG AA。
- 报纸的灵魂是真实内容：上线前用真实 `news.json` 数据验证——最长中文标题、无封面条目、零数据空态、单平台只有 1 条时头版 Grid 的退化形态（此时右栏收起，头条通栏）。
- 移除 emoji 图标依赖（🤖📰📊），图标如需保留，按 `icon-system.md` 使用单色 `currentColor` 图标。

---

## 9. 实施建议（分三步）

1. **第一步 · 换肤（纯 CSS）**：替换 `:root` 变量与字体引入，删除 glow/渐变/位移类规则。改动集中在 `<style>` 区块，JS 与数据结构零改动，风险最低，可先上线看效果。
2. **第二步 · 改版式**：新增头版 Grid 与简讯列表结构，调整 `renderNewsList()` 的 HTML 生成（Top1/Top2-3/其余分三档渲染），平台徽章改文字署名，条目改 `<a>` 标签。
3. **第三步 · 监控页收敛 + 收尾**：监控页表格化，移除脉冲动画，空态/焦点态/键盘导航补齐。

---

## 10. Token Gap 汇总（待设计系统确认）

| 缺口 | 本方案的临时映射 | 说明 |
|---|---|---|
| serif 展示字体（报纸标题字） | `h1Content`（PingFang SC 22/36） | 候选：思源宋体，仅用于报头/头条 |
| 超大头条字号（32px+） | 用版面特权（独占栏 + 摘要 + 封面）替代 | 如需真大字需新增 markdown display 字阶 |
| 竖栏线（1px 结构性分隔） | `color.separator.s1` | 与「Surface Over Stroke」冲突处：此处竖线是报纸分栏的语义边界而非装饰，保留并记录 |
