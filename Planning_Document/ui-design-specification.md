# AI 热点资讯监控系统 - UI 设计规范

## 📋 概览

**项目名称：** AI Hot News Monitor  
**设计风格：** Dark Mode (OLED) + 科技风 + 轻微未来感  
**主色调：** 深邃黑 + 霓虹蓝/绿渐变  
**交互方式：** 响应式 Web，支持桌面/平板/移动

---

## 🎨 设计系统

### 1. 色彩系统

#### 基础色板
| 角色 | HEX | CSS 变量 | 用途 |
|------|-----|----------|------|
| **背景** | `#09090F` | `--color-bg` | 页面最底层背景 |
| **表面** | `#12121A` | `--color-surface` | 卡片背景 |
| **边框** | `#1F1F2B` | `--color-border` | 分割线、边框 |
| **高亮** | `#262633` | `--color-highlight` | 悬停背景 |

#### 功能色
| 角色 | HEX | CSS 变量 | 用途 |
|------|-----|----------|------|
| **主色（霓虹蓝）** | `#60A5FA` | `--color-primary` | 主按钮、激活态、链接 |
| **主色亮** | `#93C5FD` | `--color-primary-light` | 渐变、高光 |
| **主色暗** | `#3B82F6` | `--color-primary-dark` | 按下状态 |
| **成功（霓虹绿）** | `#22C55E` | `--color-success` | 成功提示、在线状态 |
| **警告** | `#F59E0B` | `--color-warning` | 警告、中等风险 |
| **错误** | `#EF4444` | `--color-error` | 错误、危险操作 |

#### 文本色
| 角色 | HEX | CSS 变量 | 用途 |
|------|-----|----------|------|
| **主文本** | `#F9FAFB` | `--color-text-primary` | 标题、正文 |
| **次文本** | `#9CA3AF` | `--color-text-secondary` | 辅助信息、元数据 |
| **禁用文本** | `#4B5563` | `--color-text-muted` | 禁用、占位 |

#### 霓虹效果色（用于 accent 和装饰）
| 角色 | HEX | CSS 变量 | 用途 |
|------|-----|----------|------|
| **霓虹蓝** | `#38BDF8` | `--color-neon-blue` | 科技感强调 |
| **霓虹紫** | `#A78BFA` | `--color-neon-purple` | 渐变配色 |
| **霓虹青** | `#34D399` | `--color-neon-cyan` | 数据可视化 |

#### 语义色规则
```css
/* 永远不要直接使用原始 hex 颜色！ */
/* ✅ 推荐 */
background-color: var(--color-surface);
color: var(--color-text-primary);
border-color: var(--color-border);

/* ❌ 避免 */
background-color: #12121A;
color: #F9FAFB;
```

### 2. 排版系统

#### 字体选择
| 用途 | 字体 | Google Fonts |
|------|------|--------------|
| **标题/Logo** | Orbitron | [Orbitron](https://fonts.google.com/specimen/Orbitron) |
| **正文** | Exo 2 | [Exo 2](https://fonts.google.com/specimen/Exo+2) |
| **代码/数据** | JetBrains Mono | [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) |

```css
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-heading: 'Orbitron', system-ui, sans-serif;
  --font-body: 'Exo 2', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

#### 字体层级
| 层级 | 尺寸 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| Display | 2.5rem (40px) | 700 | 1.2 | 首页大标题 |
| H1 | 1.75rem (28px) | 700 | 1.3 | 页面标题 |
| H2 | 1.5rem (24px) | 600 | 1.3 | 区块标题 |
| H3 | 1.25rem (20px) | 600 | 1.4 | 卡片标题 |
| Body-lg | 1.125rem (18px) | 400 | 1.6 | 重点正文 |
| Body | 1rem (16px) | 400 | 1.6 | 正文 |
| Body-sm | 0.875rem (14px) | 400 | 1.5 | 辅助文本 |
| Caption | 0.75rem (12px) | 500 | 1.4 | 标签、元数据 |

### 3. 间距系统

使用 4px 的倍数作为基础单位：

| Token | 像素 | 用途 |
|-------|------|------|
| xs | 4px | 微调、图标内边距 |
| sm | 8px | 组件内间距 |
| md | 16px | 卡片内边距、组件间距 |
| lg | 24px | 区块间距、卡片间距 |
| xl | 32px | 页面边距、大区块间距 |
| 2xl | 48px | 大节段间距 |

```css
:root {
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;
}
```

### 4. 圆角系统

| Token | 像素 | 用途 |
|-------|------|------|
| none | 0px | 直角（极少使用） |
| sm | 4px | 标签、小按钮 |
| md | 8px | 按钮、输入框 |
| lg | 12px | 卡片、面板 |
| xl | 16px | 大卡片、容器 |
| full | 9999px | 圆形按钮、胶囊 |

### 5. 阴影与效果

#### 阴影层级
```css
:root {
  /* 微阴影 - 微妙区分 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  
  /* 标准阴影 - 卡片 */
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  
  /* 大阴影 - 悬浮面板 */
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
  
  /* 霓虹发光 - 激活元素 */
  --glow-primary: 0 0 20px rgba(96, 165, 250, 0.4),
                  0 0 40px rgba(96, 165, 250, 0.2);
}
```

#### 霓虹发光效果
```css
/* 霓虹文字 */
.text-neon {
  text-shadow: 0 0 8px var(--color-primary-light),
               0 0 16px var(--color-primary);
}

/* 霓虹边框 */
.border-neon {
  box-shadow: 0 0 8px var(--color-primary),
              inset 0 0 8px rgba(96, 165, 250, 0.1);
}
```

---

## 🧩 组件规范

### 1. 按钮 Button

#### 类型
| 类型 | 样式 | 用途 |
|------|------|------|
| Primary | 霓虹蓝填充 + 发光边框 | 主要操作 |
| Secondary | 透明 + 霓虹边框 | 次要操作 |
| Ghost | 纯文本 + 悬停背景 | 三级操作 |
| Danger | 红色填充 | 危险操作 |

#### 尺寸
| 尺寸 | 高度 | 内边距 | 字号 |
|------|------|--------|------|
| sm | 32px | 8px 12px | 12px |
| md | 40px | 12px 20px | 14px |
| lg | 48px | 16px 28px | 16px |

#### 交互状态
```css
/* 基础 */
.btn {
  transition: all 0.15s ease-out;
  cursor: pointer;
}

/* 悬停 */
.btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--glow-primary);
}

/* 按下 */
.btn:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}

/* 禁用 */
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}
```

### 2. 标签页 Tab

#### 样式
```css
.tab {
  padding: 12px 20px;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
  cursor: pointer;
}

.tab:hover {
  color: var(--color-text-primary);
  background: var(--color-highlight);
}

.tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  text-shadow: 0 0 8px rgba(96, 165, 250, 0.5);
}
```

#### 行为
- 默认选中第一个 Tab
- 点击切换 Tab，对应内容区域切换
- URL 同步更新（可选）
- 键盘导航：← → 切换，Enter 激活

### 3. 资讯卡片 News Card

#### 结构
```
┌─────────────────────────────────────┐
│  ┌──────────────┐                   │
│  │   封面图     │  [标题]          │
│  │  (140x90)    │  [摘要]          │
│  │              │  [元数据]        │
│  └──────────────┘  [标签]          │
└─────────────────────────────────────┘
```

#### 尺寸与间距
- 卡片内边距：16px
- 封面尺寸：140px × 90px (16:9)
- 封面与内容间距：16px
- 元数据区域间距：8px

#### 样式
```css
.news-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  transition: all 0.2s ease;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}

.news-card:hover {
  background: var(--color-highlight);
  border-color: var(--color-primary);
  box-shadow: var(--glow-primary);
  transform: translateY(-2px);
}

.news-cover {
  width: 140px;
  height: 90px;
  border-radius: var(--radius-md);
  object-fit: cover;
  background: linear-gradient(135deg, #1e293b, #0f172a);
}
```

#### 响应式
- **桌面 (≥1024px)**：2-3列网格
- **平板 (768-1023px)**：2列，封面可选
- **移动 (≤767px)**：单列，封面垂直排列在顶部

### 4. 平台标签 Platform Badge

#### 配色
| 平台 | 背景 | 文字 |
|------|------|------|
| 微博 | `#E6162D` 渐变 | 白色 |
| B站 | `#FB7299` 渐变 | 白色 |
| 小红书 | `#FE2C55` 渐变 | 白色 |
| X | `#000000` → `#1A1A1A` | 白色 |
| Facebook | `#1877F2` → `#0D47A1` | 白色 |

```css
.platform-weibo {
  background: linear-gradient(135deg, #E6162D, #C41230);
}
.platform-bilibili {
  background: linear-gradient(135deg, #FB7299, #F45489);
}
.platform-xiaohongshu {
  background: linear-gradient(135deg, #FE2C55, #E31B47);
}
.platform-x {
  background: linear-gradient(135deg, #000000, #1A1A1A);
}
.platform-facebook {
  background: linear-gradient(135deg, #1877F2, #0D47A1);
}
```

### 5. 数据指标 Metric Card

#### 样式
```css
.metric-card {
  background: linear-gradient(135deg, var(--color-surface), var(--color-bg));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  position: relative;
  overflow: hidden;
}

/* 装饰性发光角 */
.metric-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(96, 165, 250, 0.1), transparent);
  pointer-events: none;
}

.metric-value {
  font-family: var(--font-mono);
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-primary);
  text-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
}

.metric-value.success {
  color: var(--color-success);
  text-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
}

.metric-value.warning {
  color: var(--color-warning);
  text-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
}

.metric-value.danger {
  color: var(--color-error);
  text-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
}

.metric-label {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-top: var(--space-xs);
}
```

### 6. 页面切换按钮 Page Switcher

#### 样式
```css
.page-switcher {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.page-btn {
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-highlight);
}

.page-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  text-shadow: 0 0 8px rgba(96, 165, 250, 0.5);
}
```

### 7. 状态圆点 Status Dot

#### 样式
```css
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-right: var(--space-xs);
}

.status-dot.online {
  background: var(--color-success);
  box-shadow: 0 0 10px var(--color-success);
}

.status-dot.offline {
  background: var(--color-error);
  box-shadow: 0 0 10px var(--color-error);
}
```

### 8. 平台状态项 Platform Status Item

#### 样式
```css
.platform-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.platform-item {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  text-align: center;
  transition: all 0.2s ease;
}

.platform-item.online {
  border-color: var(--color-success);
}

.platform-item.offline {
  border-color: var(--color-error);
}

.platform-item:hover {
  background: var(--color-highlight);
}
```

### 9. 失败原因统计 Failure Reason Stats

#### 结构
```
┌─────────────────────────────────────────┐
│  📊 失败原因统计                         │
├─────────────────────────────────────────┤
│  ● 网络超时        ██████ 45%  12     │
│  ● Cookie过期      ████ 30%    8     │
│  ● 页面结构变化    ██ 15%      4     │
│  ● 其他原因        █ 10%       3     │
└─────────────────────────────────────────┘
```

#### 样式
```css
.monitor-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.monitor-section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.failure-reasons {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.failure-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.failure-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.failure-label {
  flex: 1;
  min-width: 100px;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.failure-bar {
  flex: 1;
  height: 8px;
  background: var(--color-highlight);
  border-radius: 9999px;
  overflow: hidden;
}

.failure-bar-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.3s ease;
}

.failure-count {
  min-width: 30px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* 失败原因颜色映射 */
.failure-item[data-reason="network_timeout"] .failure-dot,
.failure-item[data-reason="network_timeout"] .failure-bar-fill {
  background: var(--color-error);
}

.failure-item[data-reason="cookie_expired"] .failure-dot,
.failure-item[data-reason="cookie_expired"] .failure-bar-fill {
  background: var(--color-warning);
}

.failure-item[data-reason="page_changed"] .failure-dot,
.failure-item[data-reason="page_changed"] .failure-bar-fill {
  background: var(--color-neon-purple);
}

.failure-item[data-reason="auth_failed"] .failure-dot,
.failure-item[data-reason="auth_failed"] .failure-bar-fill {
  background: var(--color-neon-blue);
}

.failure-item[data-reason="rate_limited"] .failure-dot,
.failure-item[data-reason="rate_limited"] .failure-bar-fill {
  background: var(--color-neon-cyan);
}

.failure-item[data-reason="other"] .failure-dot,
.failure-item[data-reason="other"] .failure-bar-fill {
  background: var(--color-text-secondary);
}
```

### 10. 最近采集记录 Recent Execution Log

#### 结构
```
┌─────────────────────────────────────────┐
│  📝 最近采集记录                        │
├─────────────────────────────────────────┤
│  ┌─────┐                                │
│  │  ✓  │  微博热榜采集                  │
│  └─────┘  2026-05-07 14:30:00           │
│           获取 45 条 · 耗时 2.1s         │
│  ┌─────┐                                │
│  │  ✕  │  X (Twitter) 趋势采集          │
│  └─────┘  2026-05-07 14:30:04           │
│           失败: 网络超时                 │
└─────────────────────────────────────────┘
```

#### 样式
```css
.record-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.record-item {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-highlight);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  border-left-width: 3px;
  transition: all 0.2s ease;
}

.record-item:hover {
  border-color: var(--color-border);
  border-left-width: 3px;
}

.record-item.success {
  border-left-color: var(--color-success);
}

.record-item.error {
  border-left-color: var(--color-error);
}

.record-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.record-item.success .record-icon {
  background: rgba(34, 197, 94, 0.15);
  color: var(--color-success);
}

.record-item.error .record-icon {
  background: rgba(239, 68, 68, 0.15);
  color: var(--color-error);
}

.record-content {
  flex: 1;
  min-width: 0;
}

.record-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.record-meta {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.record-time {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.record-detail {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.record-detail.error-detail {
  color: var(--color-error);
}
```

### 11. 监控网格 Monitor Grid

#### 布局
```css
.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--space-lg);
  margin-top: var(--space-lg);
}

@media (max-width: 768px) {
  .monitor-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 📱 响应式断点

| 断点 | 宽度范围 | 布局 |
|------|----------|------|
| sm | < 640px | 移动单列 |
| md | 640-1023px | 平板双列 |
| lg | ≥ 1024px | 桌面多列 |

```css
/* Mobile-first CSS */
.container {
  width: 100%;
  padding: var(--space-md);
}

@media (min-width: 640px) {
  .container {
    padding: var(--space-lg);
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--space-xl);
  }
}
```

---

## ♿ 可访问性

### 1. 色彩对比度
- **正文文本**：≥ 4.5:1 (WCAG AA)
- **大文本 (≥18px)**：≥ 3:1
- **UI 组件**：≥ 3:1

### 2. 键盘导航
- 所有交互元素可通过 Tab 访问
- 焦点状态清晰可见（不要移除 outline）
- Tab 顺序遵循视觉顺序

### 3. 屏幕阅读器
- 所有图片有描述性 alt 文本
- 按钮/链接有明确目的
- 使用语义化 HTML (nav, main, article, aside)

### 4. 减少动画
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 🎯 设计检查清单

### 交付前检查

#### 通用检查
- [ ] 所有图标使用 SVG (Lucide/Heroicons)，不使用 emoji
- [ ] 所有可点击元素有 `cursor: pointer`
- [ ] 所有交互有悬停/按下/禁用状态
- [ ] 文本对比度符合 WCAG AA (4.5:1)
- [ ] 焦点状态清晰可见
- [ ] 动画时长 150-300ms，有 `prefers-reduced-motion` 支持
- [ ] 响应式测试：375px, 768px, 1024px, 1440px
- [ ] 使用语义化设计 token，无硬编码 hex
- [ ] 触摸目标 ≥ 44px
- [ ] 安全区域适配（移动端）

#### 资讯看板检查
- [ ] 平台 Tab 切换功能正常
- [ ] 资讯卡片有封面展示
- [ ] 卡片点击跳转功能正常
- [ ] 响应式布局适配移动/平板/桌面

#### 运行监控看板检查
- [ ] 页面切换（资讯/监控）功能正常
- [ ] KPI 指标卡片正确展示（成功率、失败率、响应时间、封面获取率）
- [ ] 平台状态列表在线/离线标识正确
- [ ] 失败原因统计横向柱状图展示正常
- [ ] 失败原因颜色映射正确（网络超时=红，Cookie过期=黄，页面结构变化=紫）
- [ ] 最近采集记录列表展示正常
- [ ] 执行记录成功/失败状态标识正确
- [ ] 失败记录错误信息高亮显示红色
- [ ] 时间戳使用等宽字体展示
- [ ] 监控网格响应式布局正常

---

## 📄 附录：参考资源

### 图标库
- [Lucide Icons](https://lucide.dev/) - 现代简约 SVG 图标
- [Heroicons](https://heroicons.com/) - Tailwind 官方图标

### 字体
- [Orbitron](https://fonts.google.com/specimen/Orbitron) - 科技感标题字体
- [Exo 2](https://fonts.google.com/specimen/Exo+2) - 现代正文字体

### 参考风格
- Cyberpunk UI - 霓虹未来感
- HUD / Sci-Fi FUI - 科幻数据界面
- Dark Mode (OLED) - 深色主题最佳实践
