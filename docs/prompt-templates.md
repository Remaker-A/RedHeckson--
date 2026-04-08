# AI素材生成提示词模板

> 深夜施工队 · 统一风格素材生成指南
> 所有素材必须用同一套风格前缀，保证视觉一致性

---

## 一、风格锚定前缀（所有提示词必须带）

每次生成都以这段开头，保证光照、质感、视角统一：

```
3D clay render, hand-sculpted miniature with visible clay fingerprint
texture, cute rounded proportions, isometric top-down-left view,
warm upper-left soft lighting (2800K), muted warm color palette,
4K UHD
```

---

## 二、单物件生成（透明背景，用于切图）

### 模板

```
3D clay render of a single tiny [物件描述], hand-sculpted miniature
with visible clay fingerprint texture, cute rounded proportions,
isometric top-down-left view, warm upper-left soft lighting, solid
white background, muted warm color palette, 4K UHD
--ar 1:1 --stylize 500
```

### 物件清单（复制替换方括号即可）

**P0 必须生成**：

| 物件 | 替换内容 | 文件命名 |
|------|---------|---------|
| 营灯 | `camp lantern with warm golden glow, hanging hook on top` | prop-lantern |
| 咖啡杯 | `enamel camping coffee mug with steam rising, brown and cream colors` | prop-coffee |
| 书堆 | `small stack of three colorful books, slightly worn covers` | prop-books |
| 帐篷壁纸条 | `small note cards and photos pinned to fabric with tape, handwritten text` | prop-notes |
| 毯子 | `folded plaid blanket in green and orange check pattern` | prop-blanket |
| 背包 | `small canvas hiking backpack with buckles, olive and brown color` | prop-backpack |

**P1 有余力生成**：

| 物件 | 替换内容 | 文件命名 |
|------|---------|---------|
| 盆栽 | `tiny succulent plant in a small terracotta pot` | prop-plant |
| 速写本 | `open sketchbook with pencil drawings on pages, spiral bound` | prop-notebook |
| 相机 | `vintage film camera, compact, silver and black` | prop-camera |
| 围巾卷 | `rolled knitted scarf in orange wool` | prop-scarf |
| 柴火堆 | `small pile of firewood logs with stones around it` | prop-firewood |
| 串灯 | `string of warm fairy lights, small bulbs on wire` | prop-string-lights |
| 睡袋 | `rolled camping sleeping bag in forest green` | prop-sleepingbag |
| 指南针 | `small brass compass, open lid` | prop-compass |

---

## 三、角色生成（统一画布、统一大小）

### 模板

```
3D clay render of a cute small [角色描述] character, [状态动作],
miniature proportions, hand-sculpted clay texture with visible
fingerprints, isometric top-down-left view, warm upper-left soft
lighting, solid white background, centered in frame, same scale,
4K UHD
--ar 1:1 --stylize 500
```

### 角色描述（先确定角色设计后统一用）

参考你们图片中的风格，角色描述示例：
```
# 方案A：圆团子（图1风格）
a round soft blob creature, light blue-grey color, simple closed
happy eyes, no arms, sitting on the ground

# 方案B：小机器人（图3风格）
a small cute robot with round white head, glowing orange LED eyes
and smile, wearing an orange knitted scarf, stubby arms and legs

# 方案C：绿色团子（图2风格）
a round green blob creature with tiny dot eyes and a gentle smile,
small stubby arms, soft matte texture
```

### 角色状态替换

| 状态 | 替换[状态动作] |
|------|-------------|
| 默认/陪伴 | `sitting peacefully, looking content, facing slightly left` |
| 看书 | `sitting and reading a tiny book, head slightly tilted down` |
| 打盹 | `sleeping peacefully, eyes closed, head tilted to one side, with a tiny blanket` |
| 看你 | `looking up directly at the camera with curious happy expression` |
| 等你 | `sitting near the edge facing forward, looking slightly lonely, head down` |
| 高兴 | `bouncing slightly with arms up, very happy expression` |

---

## 四、帐篷壳体生成

```
3D clay render of a small camping tent structure only, A-frame canvas
tent with wooden pole on top, fabric walls with visible cloth texture
and stitching details, tent flaps open at the front showing empty
dark interior, a small camp lantern hanging from the top pole inside.
No character inside, no items on the ground. Hand-sculpted clay
texture, isometric top-down-left view, warm upper-left soft lighting,
solid white background, miniature proportions, 4K UHD
--ar 3:4 --stylize 500
```

---

## 五、平台+周边环境生成

### 草坪版（默认）

```
3D clay render of a round wooden deck platform base, miniature scale,
surrounded by lush green clay grass, tiny wildflowers, small rocks
and pebbles, warm string lights draped around the edge, a few small
mushrooms. No tent, no character. Hand-sculpted clay texture with
visible fingerprints, isometric top-down-left view, warm upper-left
soft lighting, solid white background, 4K UHD
--ar 3:2 --stylize 500
```

### 雪地版

```
3D clay render of a round wooden deck platform base, miniature scale,
surrounded by soft white clay snow, tiny pine branches with snow,
small ice crystals, frozen berries, a few pinecones. No tent, no
character. Hand-sculpted clay texture, isometric top-down-left view,
cool-warm soft lighting, solid white background, 4K UHD
--ar 3:2 --stylize 500
```

### 沙漠/海滩版

```
3D clay render of a round wooden deck platform base, miniature scale,
surrounded by warm sandy ground, tiny clay cacti, small seashells,
smooth pebbles, a piece of driftwood. No tent, no character.
Hand-sculpted clay texture, isometric top-down-left view, warm
golden lighting, solid white background, 4K UHD
--ar 3:2 --stylize 500
```

### 秋叶版

```
3D clay render of a round wooden deck platform base, miniature scale,
surrounded by fallen autumn leaves in orange red and yellow, tiny
clay mushrooms, acorns, a small wooden log. No tent, no character.
Hand-sculpted clay texture, isometric top-down-left view, warm
amber lighting, solid white background, 4K UHD
--ar 3:2 --stylize 500
```

---

## 六、完整场景生成（概念图/Slide用）

### 白天版

```
3D clay render, miniature camping diorama on a round wooden platform.
A small canvas A-frame tent with warm golden glow from a lantern
inside. A cute [角色描述] sitting inside the tent reading a book.
Around the platform: green grass, tiny wildflowers, small rocks,
warm string lights. Items near the tent: a stack of books, an enamel
coffee mug with steam, a small backpack. Hand-sculpted clay texture
with visible fingerprints, isometric view, warm upper-left soft
lighting, cream background, cozy autumn color palette, 4K UHD
--ar 9:16 --stylize 600
```

### 夜晚版

```
3D clay render, miniature camping diorama on a round wooden platform,
floating in dark navy blue sky with crescent moon and tiny stars.
A small canvas A-frame tent with warm golden glow from lantern inside.
A cute [角色描述] sitting inside reading. A small campfire with
orange clay flames in front of the tent. Green grass, tiny plants,
warm string lights around the platform edge. Hand-sculpted clay
texture with visible fingerprints, isometric view, dramatic warm
lighting against dark background, 4K UHD
--ar 9:16 --stylize 600
```

---

## 七、保持一致性的关键技巧

### 1. Midjourney SREF（风格参考码）

生成第一张满意的图后，用 `--sref [图片URL]` 让后续生成保持同风格：

```
[你的prompt] --sref https://你第一张满意图的URL --stylize 500
```

或者去 https://midlibrary.io/styles/claymation 找现成的 Claymation SREF 码。

### 2. 固定不变的关键词

每次都要带的词，不要随意删改：
- `3D clay render`
- `hand-sculpted`
- `visible clay fingerprint texture`（或 `visible fingerprints`）
- `isometric top-down-left view`
- `warm upper-left soft lighting`
- `miniature proportions`

### 3. 固定色板描述

统一使用这组颜色词：
```
muted warm color palette: cream, cinnamon brown, forest green,
warm orange, soft amber gold
```

### 4. 去背景处理

AI生成的图都有白色背景，需要去掉：
- **在线工具**：remove.bg（最快）
- **批量CLI**：`pip install rembg` → `rembg i input.png output.png`
- **Photoshop**：选择主体 → 删除背景 → 最小值1px收边（防白边）

---

## 八、导航栏图标

```
3D clay render of a single tiny [图标描述], cute miniature icon,
hand-sculpted clay texture, front-facing view, warm soft lighting,
solid white background, simple and clean, 256x256
--ar 1:1 --stylize 400
```

| 图标 | 替换内容 |
|------|---------|
| 帐篷/首页 | `camping tent icon, simple A-frame tent shape` |
| 篝火 | `small campfire with orange flames and logs` |
| 背包/收纳 | `small hiking backpack, front view` |
| 纸条/日记 | `small notebook or letter with writing` |
| 个人 | `small cute blob character face, happy expression` |

---

*生成素材时间估算：用Midjourney批量跑，约1-2小时可以出齐全套。*
*深夜施工队 · 2026-04-08*
