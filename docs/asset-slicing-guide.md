# 素材切图规范与分层指南

> 深夜施工队 · H5移动端视觉实现
> 风格：3D粘土/Clay Render 等距立体场景

---

## 一、分层架构总览

从后到前，共 7 层：

```
┌────────────────────────────────────────────────────┐
│ ⑥ UI层      气泡 / 导航栏 / 标题                   │  ← HTML/CSS
│ ⑤ 角色层    角色不同状态                             │  ← PNG切图，JS切换
│ ④ 物件层    书/咖啡/纸条/毯子等                      │  ← PNG切图，按状态显隐
│ ③ 帐篷层    帐篷壳体+营灯（一张图）+ CSS光效叠加     │  ← 1张PNG + CSS
│ ② 平台层    木平台 + 周边装饰（草坪/雪地等）          │  ← 按主题切换的PNG
│ ① 背景层    纯色/渐变 + 虚化光斑                     │  ← 纯CSS
└────────────────────────────────────────────────────┘
```

**核心原则：切图按"物理结构"分，光效用CSS叠加到对应图层上，不单独成层。**

- 帐篷+营灯 = 一张图（营灯是帐篷结构的一部分）
- 灯光光晕 = CSS叠在帐篷层上
- 篝火底座 = 物件层切图，火焰 = CSS/Lottie叠在物件层上
- 角色阴影 = CSS叠在角色层下方

在页面中的对应关系：

```html
<div class="scene">
  <div class="layer-bg"></div>              <!-- ① CSS背景 -->

  <img class="layer-platform" />            <!-- ② 平台+周边 -->

  <div class="layer-tent">                  <!-- ③ 帐篷 -->
    <img class="tent-img" />                <!--    帐篷+营灯一张图 -->
    <div class="lantern-glow"></div>        <!--    CSS灯光光晕 -->
    <div class="tent-inner-shadow"></div>   <!--    CSS帐篷内部暖光 -->
  </div>

  <div class="layer-props">                 <!-- ④ 物件 -->
    <img class="prop" />
    <div class="campfire-wrap">             <!--    篝火=底座图+CSS火焰 -->
      <img class="prop-firewood" />
      <div class="fire-effect"></div>
    </div>
  </div>

  <div class="layer-character">             <!-- ⑤ 角色 -->
    <div class="char-shadow"></div>         <!--    CSS角色阴影 -->
    <img class="char-img" />               <!--    角色切图 -->
  </div>

  <div class="layer-ui">                   <!-- ⑥ UI -->
    <div class="speech-bubble"></div>
  </div>
</div>
```

---

## 二、逐层切图规范

### ① 背景层 — 不需要切图

完全用 CSS 实现。不需要提供任何图片素材。

```css
/* 白天 */
.layer-bg[data-time="day"] {
  background: radial-gradient(ellipse at 50% 40%,
    #f5e6d0 0%,     /* 中心暖白 */
    #e8dcc8 50%,     /* 边缘略深 */
    #d4c4a8 100%     /* 最外圈 */
  );
}

/* 夜晚 */
.layer-bg[data-time="night"] {
  background: radial-gradient(ellipse at 50% 40%,
    #2a3a5a 0%,
    #1a2540 60%,
    #0f1520 100%
  );
}

/* 虚化光斑用伪元素模拟 */
.layer-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(255,220,150,0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 60%, rgba(255,200,120,0.1) 0%, transparent 40%),
    radial-gradient(circle at 50% 80%, rgba(255,180,100,0.08) 0%, transparent 60%);
  filter: blur(30px);
  animation: bokeh-drift 8s ease-in-out infinite alternate;
}
```

如果想要更接近参考图那种森林虚化效果，也可以用一张**极度模糊的环境照片**做背景底（ blur(40px) ），但优先级低，CSS渐变已经足够。

---

### ② 平台层 — 按环境主题切换

**这是最重要的切图层之一。** 木平台 + 周边装饰（草、石头、花、雪等）作为一个整体切出来。

#### 切图要求

```
文件命名：platform-{主题名}.png
输出格式：PNG，透明背景
画布尺寸：750 x 500（@2x）
内容范围：平台居中，周边装饰不超出画布

注意：帐篷不包含在这一层！只有平台和平台周边的东西。
```

#### 需要的主题变体

| 文件名 | 主题 | 描述 |
|--------|------|------|
| `platform-grass.png` | 草坪（默认） | 木平台 + 周围青草、小花、石子、串灯 |
| `platform-snow.png` | 雪地（冬季） | 木平台 + 积雪、冰晶、松枝 |
| `platform-sand.png` | 沙漠/海滩 | 木平台 + 沙地、贝壳、小仙人掌 |
| `platform-autumn.png` | 秋叶 | 木平台 + 落叶、蘑菇、橡果 |

#### 切图示意

```
         ┌───────────────────────────┐
         │                           │
         │        (透明区域)          │  ← 帐篷会叠在这上面
         │                           │
         │   🌿 ┌─────────────┐ 🌿   │
         │  🪨  │  木  平  台  │  🌸  │  ← 平台本体
         │   🌱 └─────────────┘ 🪴   │
         │  🕯️   🌿   🪨   🌱   💡   │  ← 周边装饰
         │                           │
         └───────────────────────────┘
                 750 x 500 @2x
```

#### AI生成提示词

```
3D clay render, top-down slightly angled view of a round wooden platform
base with grass, small rocks, tiny flowers, and string lights around
the edge. No tent, no character, just the wooden deck platform and
surrounding nature decorations. Transparent background. Soft warm
lighting. Miniature diorama style. Isometric perspective.
--ar 3:2
```

雪地版：把 `grass, small rocks, tiny flowers` 改为 `snow, ice crystals, pine branches`

---

### ③ 帐篷层 — 壳体+营灯一张图，光效CSS叠加

帐篷和营灯是一个物理结构，**切成一张图**。灯光效果、帐篷内部暖光、阴影全部用CSS叠在这张图上。

#### 切图要求

```
文件名：tent-shell.png
输出格式：PNG，透明背景
画布尺寸：750 x 700（@2x）
内容：帐篷布/骨架/绳子/帐篷帘子 + 营灯（含灯体本身的发光质感）
不包含：角色、可变物件、平台

关键：
  · 营灯在渲染图里就带着它自身的发光感（灯体是亮的），这是素材的一部分
  · 帐篷内部留空（透明），角色和物件从后面露出
  · 帐篷壁上如果有固定的光影（灯照出来的布面明暗），保留在图里
```

#### 切图示意

```
         ┌───────────────────────────┐
         │         🔺帐篷顶          │
         │        ╱    ╲             │
         │       ╱  🏮  ╲           │  ← 营灯是帐篷的一部分，一起切
         │      ╱  灯本身  ╲         │     灯体自带发光质感（素材自带）
         │     ╱  带光感的  ╲        │
         │    ╱   (透明)    ╲       │  ← 内部留空
         │   ┃    (透明)     ┃      │  ← 角色和物件从这里露出
         │   ┃  帐篷帘子边缘  ┃      │
         │                           │
         └───────────────────────────┘
```

实操建议：从完整渲染图中抠出帐篷，**用蒙版擦掉内部区域**，只保留帐篷布、柱子、绳子、营灯。营灯本身的发光部分（灯罩里的亮光）保留，这是素材的一部分。

#### CSS光效叠加（叠在帐篷层上）

以下效果不需要切图，用CSS叠在帐篷图之上：

**A. 营灯光晕扩散（呼吸动效）**

营灯素材自带灯体发光，但向外扩散的光晕用CSS做，可以呼吸脉动：

```css
.lantern-glow {
  position: absolute;
  /* 定位到帐篷图中营灯的位置 */
  top: 22%;
  left: 48%;
  width: 180px;
  height: 180px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle,
    rgba(255, 180, 60, 0.45) 0%,
    rgba(255, 150, 30, 0.2) 35%,
    rgba(255, 120, 20, 0.05) 60%,
    transparent 80%
  );
  border-radius: 50%;
  mix-blend-mode: screen;
  pointer-events: none;
  animation: glow-breathe 3.5s ease-in-out infinite;
}

@keyframes glow-breathe {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.12); }
}

/* 深夜态：光晕更暖更集中 */
[data-status="night"] .lantern-glow {
  background: radial-gradient(circle,
    rgba(255, 160, 40, 0.6) 0%,
    rgba(255, 120, 20, 0.3) 30%,
    transparent 65%
  );
}

/* 打盹态：光晕很弱 */
[data-status="sleep"] .lantern-glow {
  opacity: 0.25;
  animation: glow-breathe 5s ease-in-out infinite;
}

/* 落灰态：几乎没有光 */
[data-status="away"] .lantern-glow {
  opacity: 0.08;
  animation: none;
}
```

**B. 帐篷内部暖光（渲染帐篷布面的光照感）**

给帐篷内部区域叠一层暖色半透明渐变，模拟灯光照亮帐篷布的效果：

```css
.tent-inner-glow {
  position: absolute;
  top: 15%;
  left: 20%;
  width: 60%;
  height: 50%;
  background: radial-gradient(ellipse at 50% 30%,
    rgba(255, 200, 100, 0.15) 0%,
    transparent 70%
  );
  mix-blend-mode: soft-light;
  pointer-events: none;
  transition: opacity 1.5s ease;
}

/* 不同状态调整内部光强度 */
[data-status="day"] .tent-inner-glow   { opacity: 0.6; }
[data-status="night"] .tent-inner-glow { opacity: 1; }
[data-status="sleep"] .tent-inner-glow { opacity: 0.2; }
[data-status="away"] .tent-inner-glow  { opacity: 0.05; }
```

**C. 角色投射阴影（CSS叠在角色层下方）**

```css
.char-shadow {
  position: absolute;
  bottom: -5%;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  height: 15px;
  background: radial-gradient(ellipse,
    rgba(60, 40, 20, 0.25) 0%,
    transparent 70%
  );
  border-radius: 50%;
  pointer-events: none;
}
```

**D. 物件投射阴影（通用）**

所有物件统一加一个轻微的底部阴影：

```css
.prop {
  filter: drop-shadow(0 4px 6px rgba(60, 40, 20, 0.2));
}
```

#### 帐篷帘子（可选，P1）

如果想做"掀帘子"的进入动画，可以额外切两片帐篷帘子：

```
tent-curtain-left.png   左帘
tent-curtain-right.png  右帘

进入动画：两片帘子从中间向两侧 translateX 展开
```

---

### ④ 物件层 — 每个单独切

每个物件是独立的小PNG，按状态组合显隐。

#### 切图要求

```
输出格式：PNG，透明背景
画布尺寸：每个物件紧凑裁切，保留少量padding（约10px）
命名规则：prop-{物件名}.png

关键：所有物件要在同一个渲染环境下生成，保持一致的光照方向和粘土质感。
不要从不同风格的图里抠——会穿帮。
```

#### 物件清单

**P0 — 必须有**

| 文件名 | 尺寸(约) | 描述 | 定位区域 |
|--------|---------|------|---------|
| `prop-books.png` | 140x100 | 2-3本叠放的小书 | 角色左侧 |
| `prop-coffee.png` | 80x90 | 咖啡杯/马克杯 | 角色右前方 |
| `prop-note-wall.png` | 120x100 | 帐篷壁上的纸条/照片 | 帐篷内壁右侧 |
| `prop-blanket.png` | 160x80 | 格子毯/被子 | 角色身上（打盹态） |
| `prop-backpack.png` | 100x110 | 小背包 | 帐篷右外侧 |

**P1 — 有了更好**

| 文件名 | 尺寸(约) | 描述 | 定位区域 |
|--------|---------|------|---------|
| `prop-plant.png` | 70x90 | 小盆栽 | 帐篷左侧 |
| `prop-camera.png` | 80x60 | 小相机 | 角色旁边 |
| `prop-notebook.png` | 100x80 | 打开的速写本 | 地面 |
| `prop-scarf.png` | 90x40 | 围巾/毛毯卷 | 平台边缘 |
| `prop-firewood.png` | 100x50 | 柴火堆（篝火底座） | 平台前方 |
| `prop-string-lights.png` | 200x30 | 串灯 | 帐篷口上方 |

#### AI批量生成物件的提示词模板

```
3D clay render of a single {物件描述}, miniature scale, soft warm
lighting from upper left, isometric perspective, transparent background,
cute and cozy style matching a camping tent diorama. High detail
clay/felt texture.
--ar 1:1
```

例如：
```
3D clay render of a single small stack of three colorful books,
miniature scale, soft warm lighting from upper left, isometric
perspective, transparent background, cute and cozy style matching
a camping tent diorama. High detail clay/felt texture.
```

---

### ⑤ 角色层 — 多状态，统一锚点

#### 切图要求

```
输出格式：PNG，透明背景
画布尺寸：统一 300 x 300（@2x）— 所有状态用同样大小的画布
角色定位：在画布中统一居中偏下（底部对齐）
命名规则：char-{状态名}.png

关键中的关键：
  所有状态的角色位置必须一致！
  画布大小一致，角色底部对齐。
  这样代码里只需要切换src，不用调位置。
```

#### 角色状态清单

| 文件名 | 状态 | 描述 | 优先级 |
|--------|------|------|--------|
| `char-idle.png` | 默认/陪伴 | 坐着，睁眼，微笑，手里可以拿东西 | P0 |
| `char-reading.png` | 看书 | 坐着，低头看书 | P0 |
| `char-sleeping.png` | 打盹 | 闭眼，头微倾，配合blanket使用 | P0 |
| `char-looking.png` | 看你 | 抬头面朝摄像机，眼睛亮 | P0 |
| `char-waiting.png` | 等你回来 | 面朝帐篷口方向（面朝画面前方），略低头 | P1 |
| `char-happy.png` | 高兴 | 手举起/微微蹦跳姿态 | P1 |

#### AI生成角色提示词

先确定角色设计后，用这个模板批量生成状态：

```
3D clay render of a cute small {角色描述} character, {状态动作},
sitting inside a camping tent, miniature scale, soft warm amber
lighting, isometric perspective, transparent background.
The character should be centered in frame, same size and position
across all renders.
--ar 1:1
```

---

### CSS光效速查（不需要切图，叠加到对应图层上）

光效不再是独立的层，而是叠加在对应的素材图层上：

| 效果 | 叠在哪一层上 | 实现方式 | 是否需要素材 |
|------|------------|---------|------------|
| 营灯光晕扩散 | ③帐篷层 | CSS `radial-gradient` + `mix-blend-mode: screen` | 不需要 |
| 帐篷内部暖光 | ③帐篷层 | CSS `radial-gradient` + `mix-blend-mode: soft-light` | 不需要 |
| 角色阴影 | ⑤角色层下方 | CSS `radial-gradient` 椭圆 | 不需要 |
| 物件阴影 | ④物件层 | CSS `filter: drop-shadow()` | 不需要 |
| 篝火火焰 | ④物件层（柴火图上方） | Lottie JSON 或 CSS animation | Lottie需要1个JSON |
| 咖啡热气 | ④物件层（咖啡杯上方） | CSS伪元素 + animation | 不需要 |
| 串灯闪烁 | ③帐篷层或②平台层 | CSS `box-shadow` + animation | 不需要 |
| 月亮+星星 | ①背景层 | CSS | 不需要 |
| 背景虚化光斑 | ①背景层 | CSS `radial-gradient` + `filter: blur` | 不需要 |

**完整CSS代码见上方③帐篷层章节。**

---

### ⑥ UI层 — 不需要切图（图标除外）

底部导航栏的图标需要切图或使用icon font：

| 文件名 | 描述 | 风格 |
|--------|------|------|
| `icon-home.png` | 帐篷/小屋图标 | 手绘线条风或粘土风 |
| `icon-fire.png` | 篝火图标 | 同上 |
| `icon-bag.png` | 背包/收纳图标 | 同上 |

尺寸：48x48 @2x = 96x96 PNG 或 SVG

---

## 三、状态组合表

不同状态下，各层的组合（CSS光效跟随状态自动变化）：

| 状态 | 背景(①) | 平台(②) | 帐篷(③)图+CSS | 物件(④) | 角色(⑤) |
|------|---------|---------|--------------|---------|---------|
| **白天·陪伴** | 暖白渐变 | grass | 通用图 + 灯晕亮 + 内光强 | 书+咖啡+纸条+背包 | idle/reading |
| **深夜·陪伴** | 深蓝+月亮星星 | grass | 通用图 + 灯晕暖亮 + 内光最强 | 书+咖啡+纸条+背包+柴火(+CSS火焰) | reading |
| **打盹** | 暖白偏暗 | grass | 通用图 + 灯晕暗 + 内光弱 | 毯子+背包 | sleeping |
| **落灰·等你** | 灰冷渐变 | grass(CSS降饱和度) | 通用图 + 灯晕极暗 + 内光几乎无 | 背包 | waiting |
| **冬日** | 冷白渐变 | snow | 通用图 + 灯晕亮 + 内光强 | 书+咖啡+围巾 | idle |

---

## 四、文件目录结构

```
src/assets/
├── scene/
│   ├── tent-shell.png           帐篷壳体（通用）
│   ├── tent-curtain-left.png    左帘子（P1，掀帘动画用）
│   └── tent-curtain-right.png   右帘子（P1）
│
├── platform/
│   ├── platform-grass.png       草坪平台
│   ├── platform-snow.png        雪地平台
│   ├── platform-sand.png        沙漠平台
│   └── platform-autumn.png      秋叶平台
│
├── character/
│   ├── char-idle.png            默认态
│   ├── char-reading.png         看书
│   ├── char-sleeping.png        打盹
│   ├── char-looking.png         看你
│   ├── char-waiting.png         等你
│   └── char-happy.png           高兴
│
├── props/
│   ├── prop-books.png           书堆
│   ├── prop-coffee.png          咖啡杯
│   ├── prop-note-wall.png       墙上纸条
│   ├── prop-blanket.png         毯子
│   ├── prop-backpack.png        背包
│   ├── prop-plant.png           盆栽
│   ├── prop-camera.png          相机
│   ├── prop-notebook.png        速写本
│   ├── prop-scarf.png           围巾卷
│   ├── prop-firewood.png        柴火堆
│   └── prop-string-lights.png   串灯
│
├── effects/
│   └── campfire.json            篝火 Lottie
│
└── icons/
    ├── icon-home.svg            导航图标
    ├── icon-fire.svg
    └── icon-bag.svg
```

---

## 五、切图技巧与注意事项

### 1. 一致性是最重要的

所有素材必须在同一套视觉风格下生成：
- **相同的光照方向**：左上 45° 暖光
- **相同的视角**：等距略俯视（约30°俯角）
- **相同的材质质感**：粘土/毛毡/布料
- **相同的色温**：暖色为主

如果从不同的AI生成结果里混搭抠图，风格会不统一，观感会"穿帮"。

### 2. 透明背景处理

AI生成的图通常有背景。去除背景的方法：
- **推荐**：remove.bg / Photoshop「选择主体」→ 删除背景
- **批量处理**：rembg（Python CLI工具），`pip install rembg` → `rembg i input.png output.png`
- **注意**：去背景后检查边缘，粘土风格的柔软边缘容易出白边。用 Photoshop「最小值」1px 收缩蒙版可解决。

### 3. 物件定位坐标约定

所有物件在场景中的位置，用百分比相对于场景容器定位：

```css
.prop {
  position: absolute;
}

/* 每个物件的位置写在这里 — 调试时可用Chrome拖拽确认 */
.prop-books     { top: 58%; left: 25%; width: 15%; }
.prop-coffee    { top: 55%; left: 62%; width: 10%; }
.prop-note-wall { top: 25%; left: 60%; width: 16%; }
.prop-blanket   { top: 52%; left: 38%; width: 22%; }
.prop-backpack  { top: 58%; left: 72%; width: 14%; }
```

用百分比而不是px，这样不同屏幕尺寸下位置自适应。

### 4. 图片尺寸与性能

| 层 | 建议尺寸(@2x) | 文件大小控制 |
|----|-------------|-------------|
| 平台 | 750x500 | < 300KB |
| 帐篷 | 750x700 | < 300KB |
| 角色 | 300x300 | < 100KB 每张 |
| 物件 | 60~200px宽 | < 50KB 每个 |

**总素材量控制在 3MB 以内**，保证手机加载速度。

压缩工具：TinyPNG（在线）或 `pngquant`（CLI批量压缩）

### 5. 生成素材时的提示词纪律

为了保持一致性，所有AI生成素材应共用一个**风格锚定前缀**：

```
3D clay render, miniature diorama style, soft warm lighting from
upper left at 45 degrees, isometric perspective at 30 degree angle,
cute cozy camping theme, felt and clay texture, ...
```

后面再拼接具体物件/角色/场景的描述。不要每次生成时随意修改风格描述。

---

## 六、平台主题切换的实现方式

因为平台层是整张PNG切换，CSS实现很简单：

```tsx
function Platform({ theme = 'grass' }) {
  return (
    <img
      className="layer-platform"
      src={`/assets/platform/platform-${theme}.png`}
      alt=""
    />
  )
}
```

```css
.layer-platform {
  position: absolute;
  bottom: 8%;
  left: 50%;
  transform: translateX(-50%);
  width: 95%;
  /* 切换时渐变 */
  transition: opacity 1s ease;
}
```

平台主题可以绑定到：季节、用户设置、或灵魂成长阶段。

---

*深夜施工队 · 2026-04-08*
