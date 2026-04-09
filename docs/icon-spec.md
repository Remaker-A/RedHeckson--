# TabBar 图标设计规范

> 深夜施工队 · My Little Camp
> 版本：v1.0 · 2026-04-09

---

## 一、设计总则

### 风格方向
- **线条手绘风**，与产品"帐篷里的存在"温暖调性一致
- 不要 Material / SF Symbols 的工业感
- 线条粗细约 **2px**（@1x），圆角柔和
- 整体感觉：像用铅笔/细马克笔随手画的，有人味

### 尺寸规范

| 规格 | 尺寸 | 用途 |
|------|------|------|
| @1x | 24×24 px | 基准设计稿 |
| @2x | 48×48 px | 标准屏幕 |
| @3x | 72×72 px | 高清屏幕 |

### 文件格式
- **SVG**（首选）— 矢量可缩放，前端直接使用
- PNG 备用（需提供 @2x 和 @3x）
- 背景透明

### 状态要求

每个图标需提供 **4 个状态版本**：

| 状态 | 说明 |
|------|------|
| 白天 · 未选中 | 线条描边，无填充，低饱和度 |
| 白天 · 选中 | 线条描边 + 局部暖色填充，饱和度提升 |
| 夜晚 · 未选中 | 线条描边，无填充，浅色线条 |
| 夜晚 · 选中 | 线条描边 + 局部暖光填充，微发光感 |

---

## 二、配色方案

### 白天模式

| 元素 | 色值 | 说明 |
|------|------|------|
| 未选中线条 | `rgba(100, 90, 80, 0.4)` | 暖灰，低对比 |
| 选中线条 | `#6B5B4E` | 暖褐色 |
| 选中填充 | `#E8A04C` | 帐篷暖光橙（产品主色） |
| 选中填充辅助 | `#F2E8D5` | 泛黄纸张色（纸条专用） |

### 夜晚模式

| 元素 | 色值 | 说明 |
|------|------|------|
| 未选中线条 | `rgba(200, 190, 175, 0.35)` | 浅暖白，低对比 |
| 选中线条 | `#D4C4A8` | 暖白 |
| 选中填充 | `#E8A04C` | 帐篷暖光橙（保持一致） |
| 选中发光 | `#E8A04C` at 20% opacity | 微光晕效果 |

---

## 三、四个图标详细描述

### 图标 1：帐篷 / 我的家（Home）

**Tab名称**：帐篷

**设计描述**：
- 一个简笔帐篷的正面轮廓，三角形帐篷体 + 入口帘子微掀开
- 帐篷顶部有一面小旗帜（可选，增加辨识度）
- 帐篷入口处透出一点光（选中状态）

**状态细节**：

| 状态 | 视觉表现 |
|------|---------|
| 白天 · 未选中 | 帐篷轮廓线条，入口闭合，无光 |
| 白天 · 选中 | 帐篷轮廓 + 入口微开，透出暖橙色光，旗帜微上扬 |
| 夜晚 · 未选中 | 浅色帐篷轮廓，入口闭合 |
| 夜晚 · 选中 | 帐篷轮廓 + 入口透出暖黄光晕，像深夜帐篷里亮着灯 |

**参考意象**：露营帐篷、温暖的家、一个有人住的小角落

---

### 图标 2：纸条（Notes）

**Tab名称**：纸条

**设计描述**：
- 一张略微卷角的小纸条/便签
- 纸面上有 2-3 条横线（暗示手写文字）
- 整体微微倾斜 5-10°（像随意贴上去的）

**状态细节**：

| 状态 | 视觉表现 |
|------|---------|
| 白天 · 未选中 | 纸条轮廓线条，无填充 |
| 白天 · 选中 | 纸条轮廓 + 泛黄纸张底色填充（#F2E8D5），横线加深 |
| 夜晚 · 未选中 | 浅色纸条轮廓 |
| 夜晚 · 选中 | 纸条轮廓 + 淡暖色填充，纸面微发光 |

**参考意象**：贴在冰箱上的便利贴、帐篷内壁上的纸条

---

### 图标 3：活动日志（Activity）

**Tab名称**：足迹

**设计描述**：
- 简笔时钟轮廓 + 一条弯曲向上的小路径/箭头（暗示时间线、活动轨迹）
- 或者：一组脚印（2-3个小脚印从左下到右上排列）
- **推荐方案**：一个简笔小营火 + 2-3 个小光点围绕（暗示"发生过的事"）

**备选方案**（供设计师选择）：

| 方案 | 图形 | 优点 |
|------|------|------|
| A. 营火 | 简笔火焰 + 木柴 | 契合露营主题，暖感 |
| B. 足迹 | 2-3个小脚印排列 | 直觉传达"活动记录" |
| C. 时光线 | 竖线 + 2-3个小圆点 | 对应时间轴概念 |

**状态细节**（以方案 A 营火为例）：

| 状态 | 视觉表现 |
|------|---------|
| 白天 · 未选中 | 营火轮廓线条，火焰无色 |
| 白天 · 选中 | 营火轮廓 + 火焰暖橙色填充，微有跳动感 |
| 夜晚 · 未选中 | 浅色营火轮廓 |
| 夜晚 · 选中 | 营火 + 暖橙火焰 + 光晕扩散（深夜篝火感） |

**参考意象**：篝火旁的故事、露营的痕迹、它在你不在时做过的事

---

### 图标 4：我的（Me / Profile）

**Tab名称**：我的

**设计描述**：
- 一个简笔小人轮廓（头 + 肩），手绘风格
- 不要标准的圆形头像框，要更随意的手绘感
- 头部微微偏斜（不要正中端坐的僵硬感）

**状态细节**：

| 状态 | 视觉表现 |
|------|---------|
| 白天 · 未选中 | 小人轮廓线条 |
| 白天 · 选中 | 小人轮廓加深 + 面部区域微暖色（有"在场"的感觉） |
| 夜晚 · 未选中 | 浅色小人轮廓 |
| 夜晚 · 选中 | 小人轮廓变亮 + 微暖光感 |

**参考意象**：帐篷外面的你、一个安静坐着的人

---

## 四、交付清单

### 文件命名规范

```
icon-{name}-{theme}-{state}.svg

name:   home / notes / activity / me
theme:  day / night
state:  default / active
```

### 完整文件列表（16个文件）

```
icons/
├── icon-home-day-default.svg
├── icon-home-day-active.svg
├── icon-home-night-default.svg
├── icon-home-night-active.svg
├── icon-notes-day-default.svg
├── icon-notes-day-active.svg
├── icon-notes-night-default.svg
├── icon-notes-night-active.svg
├── icon-activity-day-default.svg
├── icon-activity-day-active.svg
├── icon-activity-night-default.svg
├── icon-activity-night-active.svg
├── icon-me-day-default.svg
├── icon-me-day-active.svg
├── icon-me-night-default.svg
└── icon-me-night-active.svg
```

### 存放路径

```
companion-agent/frontend/public/assets/icons/tab/
```

---

## 五、前端实现参考

图标切换逻辑（TabBar.vue 中使用）：

```vue
<!-- 根据 isNight + isActive 动态选择图标 -->
<img :src="`/assets/icons/tab/icon-${tab.name}-${isNight ? 'night' : 'day'}-${isActive ? 'active' : 'default'}.svg`" />
```

或使用 SVG inline + CSS 变量控制颜色（推荐，更灵活）：

```css
.tab-icon svg {
  stroke: var(--icon-stroke);
  fill: var(--icon-fill, none);
  transition: all 0.3s ease;
}

.tab-item.active .tab-icon svg {
  stroke: var(--icon-stroke-active);
  fill: var(--icon-fill-active);
}
```

---

## 六、视觉参考词

给设计师/AI绘图的关键词：

> hand-drawn line icon, camping theme, warm minimal, pencil sketch style,
> soft rounded corners, cozy tent life, 2px stroke weight, 24x24 grid,
> warm orange accent (#E8A04C), transparent background

---

*深夜施工队 · 2026-04-09*
