# AI素材生成提示词模板（实测优化版）

> 深夜施工队 · 统一风格素材生成指南
> 基于实际生图测试反馈优化，风格已锁定：3D Diorama + Smooth Texture

---

## 一、风格定义（实测锁定）

| 维度 | 确定方案 | 不要 |
|------|---------|------|
| 质感 | smooth soft texture | ~~clay fingerprint~~ |
| 角色 | 暖白色圆头生物，头顶单球 | ~~机器人/LED/围巾~~ |
| 背景 | 深夜星空（主场景）/ 白色（切图） | ~~cream/奶白~~ |
| 渲染 | low detail soft rendering | ~~4K UHD~~ |
| 视角 | isometric floating platform | 同前 |

---

## 二、风格锚定前缀（所有提示词必须带）

```
3D diorama render, smooth soft texture with gentle lighting, cute
rounded proportions, isometric floating platform view, warm amber
glow from lantern and campfire, cozy camping atmosphere, low detail
soft rendering
```

---

## 三、角色定义（已确认，不可修改）

### 角色核心描述

```
A cute warm-white creature with perfectly round head and single small
sphere on top, tiny black dot eyes, small nose, gentle smile. Smooth
warm-white/cream colored surface, NO scarf, NO accessories, NO patterns.
Soft rounded body proportions.
```

**必须保留的关键词**：
- `warm-white/cream colored` — 暖白色
- `single small sphere on top` — 头顶单圆球
- `tiny black dot eyes` — 小黑点眼睛
- `NO scarf, NO accessories, NO patterns` — 明确排除装饰
- `smooth surface` — 光滑质感

### 角色状态生成模板

```
A cute warm-white creature with perfectly round head and single small
sphere on top, tiny black dot eyes, small nose, [表情描述]. Smooth
warm-white/cream colored surface, NO scarf, NO accessories, NO patterns.
Soft rounded body proportions, [状态动作].

3D diorama render, smooth soft texture, isometric view, warm soft
lighting, solid white background, centered in frame, low detail
soft rendering.
```

### 状态替换表

| 状态 | [状态动作] | [表情描述] | 文件名 |
|------|-----------|-----------|--------|
| 默认/陪伴 | `sitting peacefully` | `gentle smile` | char-idle |
| 看书 | `sitting inside tent reading a book peacefully` | `focused gentle smile` | char-reading |
| 打盹 | `curled up sleeping inside tent` | `closed eyes, peaceful expression` | char-sleeping |
| 休息/喝茶 | `sitting in tent holding a warm cup` | `sparkling dot eyes, gentle smile` | char-rest |
| 等你 | `sitting at tent entrance looking outward` | `patient calm expression` | char-waiting |
| 整理/高兴 | `organizing books and items near tent` | `focused content expression` | char-happy |

---

## 四、完整场景生成（概念图/Slide/Demo用）

### 夜晚版（主视觉，优先级最高）

```
A 3D diorama scene: cute warm-white creature with round head and
single sphere on top, [状态动作], inside a cozy tent on a wooden
platform. The creature has tiny black dot eyes, [表情描述], smooth
warm-white/cream surface, NO accessories.

Tent with beige fabric, warm glowing lantern hanging inside, small
campfire outside with orange glow, scattered books and small plants.
Wooden platform base with stones and greenery.

Dark blue starry night sky background with crescent moon and twinkling
stars. Isometric floating platform view. Warm amber lighting from tent
and fire contrasting with cool night sky.

3D render style, soft shadows, cozy peaceful atmosphere, low detail
soft rendering.
```

### 白天版

```
A 3D diorama scene: cute warm-white creature with round head and
single sphere on top, [状态动作], inside a cozy tent on a wooden
platform. The creature has tiny black dot eyes, [表情描述], smooth
warm-white/cream surface, NO accessories.

Tent with beige fabric, warm glowing lantern hanging inside.
Scattered books, a small coffee mug with steam, small plants.
Wooden platform base with grass, stones and wildflowers.

Soft warm cream background with gentle ambient light. Isometric
floating platform view. Warm amber lighting from tent.

3D render style, soft shadows, cozy peaceful atmosphere, low detail
soft rendering.
```

---

## 五、单物件生成（切图用，白色背景）

### 模板

```
A single [物件名称], miniature scale, smooth 3D render style,
warm color tone, simple clean design, centered on white background,
soft lighting from upper-left, low detail rendering.
```

### 物件替换表

**P0 必须生成**：

| 物件 | 替换内容 | 文件名 |
|------|---------|--------|
| 营灯 | `small camping lantern with warm glow` | prop-lantern |
| 咖啡杯 | `enamel camping mug with steam` | prop-coffee |
| 书堆 | `stack of three small books` | prop-books |
| 纸条 | `small note cards pinned to fabric` | prop-notes |
| 毯子 | `folded blanket in warm colors` | prop-blanket |
| 背包 | `small camping backpack` | prop-backpack |

**P1 有余力生成**：

| 物件 | 替换内容 | 文件名 |
|------|---------|--------|
| 盆栽 | `tiny succulent in small pot` | prop-plant |
| 速写本 | `open sketchbook` | prop-notebook |
| 柴火堆 | `small campfire logs with stones` | prop-firewood |
| 围巾 | `rolled warm scarf` | prop-scarf |
| 串灯 | `string of warm fairy lights` | prop-string-lights |
| 睡袋 | `rolled camping sleeping bag` | prop-sleepingbag |

---

## 六、帐篷壳体生成（切图用）

```
Small A-frame tent with beige fabric, warm amber glow from inside,
tent flaps open showing interior, warm glowing lantern hanging from
top pole. NO character inside, NO items on ground.

Smooth 3D render style, miniature scale, isometric view, solid white
background, soft lighting, low detail rendering.
```

---

## 七、平台+周边环境生成（切图用）

### 草坪版（默认）

```
Wooden platform base floating in space, with small plants, stones,
and greenery around the edges. NO tent, NO character. Smooth 3D
render, miniature scale, isometric view, transparent or white
background, soft shadows, low detail rendering.
```

### 雪地版

```
Wooden platform base with snow covering, small pine branches, ice
crystals, pinecones around the edges. NO tent, NO character. Smooth
3D render, miniature scale, isometric view, white background, soft
cool-warm lighting, low detail rendering.
```

### 沙漠版

```
Wooden platform base with sandy ground, small cacti, seashells,
smooth pebbles around edges. NO tent, NO character. Smooth 3D render,
miniature scale, isometric view, white background, warm golden
lighting, low detail rendering.
```

---

## 八、分层切图场景生成

当需要单独生成每一层时，使用以下提示词（保持相同视角）：

### 背景层（夜空）

```
Dark blue starry night sky with crescent moon and twinkling stars,
gradient from deep navy to midnight blue, dreamy bokeh effect,
no objects, 9:16 aspect ratio.
```

### 平台+环境层

```
Wooden platform base floating in space, with small plants, stones,
and greenery around the edges. Small campfire with orange glow.
NO tent, NO character. Transparent background for layering.
Isometric view, soft shadows.
```

### 帐篷层

```
Small A-frame tent with beige fabric, warm amber glow from inside,
tent flaps open showing interior. NO character inside. Transparent
background. Isometric view matching platform angle.
```

### 角色层

```
Cute warm-white creature with round head and single sphere on top,
[状态动作], smooth cream surface, tiny dot eyes, [表情描述].
Transparent background. Same isometric angle. Soft ambient lighting.
```

---

## 九、导航栏图标

```
A single tiny [图标描述], cute miniature icon, smooth 3D render
style, warm color tone, front-facing view, solid white background,
simple and clean, low detail rendering.
```

| 图标 | 替换内容 | 文件名 |
|------|---------|--------|
| 帐篷/首页 | `A-frame tent icon` | icon-home |
| 篝火 | `small campfire with flames` | icon-fire |
| 背包/收纳 | `small backpack` | icon-bag |
| 纸条/日记 | `small notebook or letter` | icon-journal |
| 角色头像 | `round white creature face with dot eyes` | icon-profile |

---

## 十、一致性保障

### 1. 必须保留的关键词（每次都带）

- `3D diorama render` 或 `smooth 3D render style`
- `smooth soft texture`
- `isometric floating platform view`（场景）或 `isometric view`（切图）
- `low detail soft rendering`
- `warm amber glow`

### 2. 必须排除的关键词

- ~~`clay`~~, ~~`fingerprint texture`~~, ~~`hand-sculpted`~~
- ~~`4K UHD`~~, ~~`highly detailed`~~, ~~`super detail`~~
- ~~`robot`~~, ~~`LED`~~, ~~`scarf`~~, ~~`accessories`~~

### 3. 固定色板

```
warm-white/cream（角色）, beige（帐篷布）, warm amber/orange（灯光/火光）,
dark navy blue（夜空）, forest green（植物）, warm brown（木平台）
```

### 4. 风格参考锁定

生成第一张满意的完整场景后，用 `--sref [图片URL]` 锁定后续所有生成的风格。

### 5. 去背景处理

- **在线**：remove.bg
- **批量CLI**：`pip install rembg` → `rembg i input.png output.png`
- **PS**：选择主体 → 删除背景 → 最小值1px收边

---

*深夜施工队 · 2026-04-09 · 基于实测反馈优化*
