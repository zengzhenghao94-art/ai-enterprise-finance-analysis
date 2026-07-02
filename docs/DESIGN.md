# DESIGN.md — AI 赋能财务·经营分析平台

> 基于 [Steep](https://styles.refero.design/style/75fdb89f-ca64-41b3-af36-7a78bd09448e)（Soft dawn on a marble dashboard）+ [Column](https://styles.refero.design/style/a76ec6ba-20b3-495c-9d89-1e58281e79e7)（Swiss ledger）融合设计。
> 供 AI coding agent 和人类开发者参考。

---

## 一、设计哲学

**底层叙事：** "这是一份可以递进董事会的财务报告——冷静、权威、数据即主角。"

三条铁律：
1. **骨架纯灰度** —— UI 框架（导航/卡片/边框）只用黑白灰，不抢数据的戏
2. **数据只有两个颜色** —— Steel Blue（暖调）做主线，Cyan（冷调）做辅线。红色仅用于异常标记
3. **瓷片触感** —— 大圆角（24px）+ 纯白底 + 细灰网格线，卡片像瓷片而不是窗口

---

## 二、色彩系统

### 2.1 灰度骨架（chrome）

| Token | 色值 | Tailwind | 用途 |
|-------|------|----------|------|
| Obsidian | `#000000` | `black` | 锐利细线、发丝边框 |
| Ink | `#17191c` | `gray-900` | 主文本、深色填充按钮 |
| Ash | `#4c4c4c` | `gray-600` | 次级正文 |
| Graphite | `#777b86` | `gray-500` | 三级文本、图标 |
| Slate | `#8b8c8d` | `gray-400` | 低强调图标/链接边框 |
| Dove | `#a3a6af` | `gray-300` | 发丝边框、placeholder |
| Fog | `#f7f7f8` | `gray-100` | 次级背景、侧边栏 |
| Pure White | `#ffffff` | `white` | 页面底色、卡片表面 |

### 2.2 数据色彩（chromatic）

| Token | 色值 | Tailwind | 用途 |
|-------|------|----------|------|
| Steel Blue | `#1e40af` | `blue-800` | 主线（折线/柱/标题强调） |
| Cyan | `#0891b2` | `cyan-600` | 辅线（对比序列第二条） |
| Blue Wash | `#dbeafe` | `blue-100` | 暖调数据卡片背景 |
| Sky Wash | `#d3e3fc` | `blue-50` | 冷调数据卡片/对话区背景 |
| Crimson | `#dc2626` | `red-600` | **仅用于异常标记** |

### 2.3 使用规则

- ✅ 图表中始终 Steel Blue 为主线、Cyan 为辅线，不引入第三色
- ✅ 异常散点可用 Crimson，但必须是最小面积
- ❌ 禁止为区分数据集而使用彩虹色
- ❌ 禁止在 UI chrome 中使用任何 chromatic 色

---

## 三、字体系统

### 3.1 字体栈

| 层级 | 英文字体 | 中文字体 | 用途 |
|------|---------|---------|------|
| Display | `'Noto Serif', 'Noto Serif CJK SC', 'SimSun', serif` | 思源宋体 | 报告大标题（44-90px） |
| Body | `'Inter', 'Noto Sans SC', 'PingFang SC', sans-serif` | 思源黑体 | 正文/UI（14-18px） |
| Mono | `'JetBrains Mono', 'Fira Code', 'Consolas', monospace` | — | SQL/数字/表格等宽 |

### 3.2 字阶（Minor Third 1.2 基准 16px）

| Token | 大小 | 字重 | 行高 | 用途 |
|-------|------|------|------|------|
| display | 90px | 400 | 1.1 | Hero 标题（简报封面） |
| heading-lg | 64px | 400 | 1.1 | 章节标题 |
| heading | 44px | 400 | 1.1 | 卡片标题 |
| heading-sm | 26px | 450 | 1.18 | 小标题 |
| subheading | 22px | 400 | 1.5 | 段落小标题 |
| body-lg | 18px | 430 | 1.4 | 导语/摘要 |
| body | 16px | 400 | 1.5 | 正文 |
| caption | 14px | 400 | 1.4 | 图表标签/注释 |
| mono | 13px | 400 | 1.5 | SQL/数据表格 |

---

## 四、形状 & 间距

### 4.1 圆角

| 元素 | 圆角值 | Tailwind |
|------|--------|----------|
| 卡片 | `24px` | `rounded-3xl` |
| 图片/图表容器 | `12px` | `rounded-xl` |
| 输入框 | `16px` | `rounded-2xl` |
| CTA 按钮 | `9999px` | `rounded-full` |
| 标签/徽章 | `8px` | `rounded-lg` |

### 4.2 间距

| Token | 值 | 用途 |
|-------|-----|------|
| 基础单位 | `4px` | 最小步长 |
| 元素间距 | `8px` | 密切关联元素 |
| 卡片内边距 | `20-24px` | 卡片内容 |
| 段间距 | `80px` | 报告段落 |
| 最大宽度 | `1200px` | 报告内容区 |

---

## 五、图表规范（matplotlib 渲染）

### 5.1 通用规则
- 背景：Pure White `#ffffff`，无 chart box 边框
- 网格：仅水平方向，Dove `#a3a6af`，alpha 0.3
- 坐标轴线：单条细线，Slate `#8b8c8d`
- 刻度标签：caption 14px，Graphite `#777b86`
- 去上边框 + 右边框（Tufte 原则）
- 保存：200 DPI，`bbox_inches='tight'`，`facecolor='white'`

### 5.2 折线图
- 线宽 2.5px，数据点标记 `o` / `s` / `^`
- 主线 Steel Blue，辅线 Cyan，第三条用 Graphite（仅当必要）
- 图例：`frameon=True, fancybox=True, framealpha=0.9`

### 5.3 柱状图
- 分组柱或堆叠柱
- Steel Blue 主色，Cyan 辅色
- 标签在柱顶，字号 10px (caption)

### 5.4 散点图（异常）
- 正常点：Graphite `#777b86`，size 60
- 异常点：Crimson `#dc2626`，size 120，edgecolors darkred
- 标注异常点名称，字号 9px

### 5.5 雷达图
- 多边形填充 alpha 0.1，边框 alpha 0.7
- 网格线 Dove alpha 0.3
- 维度标签 caption

---

## 六、组件速查（前端 Tailwind）

```css
/* 卡片 */
.card { @apply bg-white rounded-3xl p-5 shadow-sm; }

/* 主按钮 */
.btn-primary { @apply bg-[#17191c] text-white rounded-full px-6 py-3 font-medium; }

/* 次级按钮 */
.btn-secondary { @apply text-[#17191c] bg-[#f7f7f8] rounded-full px-6 py-3; }

/* 输入框 */
.input { @apply rounded-2xl border border-[#a3a6af] px-4 py-3 text-[#17191c]; }

/* KPI 数值 */
.kpi-value { @apply text-[44px] font-normal leading-[1.1] text-[#17191c]; }

/* 异常徽章 */
.badge-high { @apply bg-[#dc2626] text-white rounded-lg px-2 py-0.5 text-xs; }
.badge-medium { @apply bg-orange-500 text-white rounded-lg px-2 py-0.5 text-xs; }
```

---

## 七、AI Agent 指令

当 AI coding agent 生成 UI/样式代码时，以本文档为最高优先级：

1. 不确定的颜色 → 查色板表，找不到就用灰度
2. 不确定的圆角 → 24px（卡片）/ 9999px（按钮）
3. 不确定的字体 → Inter + Noto Sans SC
4. 加新图表 → 只用 Steel Blue + Cyan，不引入新色
5. 打印/导出场景 → 纯白底，不加阴影，不加渐变背景
