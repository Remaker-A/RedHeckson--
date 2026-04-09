# 视频素材规范

> 深夜施工队 · H5移动端场景视频方案
> 用循环视频替代静态图+CSS动效，视觉效果直接拉满

---

## 一、方案概述

主场景用**循环短视频**做底，HTML层叠加气泡/按钮/TabBar。

```
┌─────────────────────────┐
│  [HTML] 标题 / 气泡      │  ← 叠加在视频上方
│                         │
│  ┌───────────────────┐  │
│  │                   │  │
│  │  <video> 循环播放   │  │  ← 视频底层
│  │  角色+帐篷+动效     │  │
│  │                   │  │
│  └───────────────────┘  │
│                         │
│  [HTML] TabBar          │  ← 叠加在视频下方
└─────────────────────────┘

状态切换 = 换视频src（crossfade过渡）
```

---

## 二、需要的视频清单

### P0 — 必须有（Demo最低要求）

| 视频 | 文件名 | 场景描述 | 角色状态 |
|------|--------|---------|---------|
| **夜晚·陪伴** | `night-reading.mp4` | 深蓝夜空+月亮星星，帐篷内灯光温暖，篝火微闪 | 角色在帐篷里看书，偶尔翻页，轻微呼吸 |
| **白天·陪伴** | `day-idle.mp4` | 暖白/奶油色背景，阳光柔和 | 角色在帐篷里坐着，微微晃动 |
| **打盹** | `sleeping.mp4` | 灯光很暗，氛围安静 | 角色闭眼侧躺/趴着，呼吸起伏 |

### P1 — 有了更好

| 视频 | 文件名 | 场景描述 | 角色状态 |
|------|--------|---------|---------|
| 夜晚·等你 | `night-waiting.mp4` | 深蓝夜空，帐篷灯微弱 | 角色靠在帐篷口方向，望向外面 |
| 白天·高兴 | `day-happy.mp4` | 明亮温暖 | 角色小幅蹦跳/摇晃 |
| 落灰·久未来 | `dusty.mp4` | 灰暗冷色调，灯几乎灭 | 角色缩在角落发呆 |

---

## 三、视频技术规范

### 基础参数

| 参数 | 要求 | 说明 |
|------|------|------|
| **时长** | 3-5秒 | 循环播放，越短文件越小 |
| **分辨率** | 1080 x 1920（竖屏）或 1080 x 1350 | 手机竖屏比例 |
| **帧率** | 24fps | 够用，文件小 |
| **编码** | H.264（MP4） | 兼容性最好 |
| **码率** | 2-4 Mbps | 画质和大小的平衡点 |
| **单个文件大小** | < 3MB | 手机加载快 |
| **总素材量** | < 15MB（全部视频加起来） | 首屏体验不能卡 |
| **背景** | 不透明（不需要透明背景） | 视频就是完整画面 |
| **音频** | 无（静音） | 前端用 `muted` 播放，音频另做 |

### 循环要求

**视频必须能无缝循环播放**，最后一帧和第一帧要接得上。

实现方法：
- **方案A**：生成时就做循环（提示词加 `seamless loop`）
- **方案B**：后期用 ffmpeg 做镜像循环（播放→倒放→播放）

```bash
# ffmpeg 镜像循环（适合缓慢动作的场景）
ffmpeg -i input.mp4 -filter_complex "[0]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0" -an -y loop.mp4
```

### 压缩命令

```bash
# 压缩到目标大小（约2-3MB/5秒）
ffmpeg -i raw.mp4 -c:v libx264 -crf 28 -preset slow -vf "scale=1080:-2" -an -movflags +faststart -y compressed.mp4
```

`-movflags +faststart` 很重要——让视频在下载完成前就能开始播放。

---

## 四、视频生成方法

### 从现有场景图生成（推荐）

用你们已有的 `scene-day-cutout.png` 和 `scene-night-cutout.png` 做 image-to-video。

**工具选择**：

| 工具 | 效果 | 速度 | 说明 |
|------|------|------|------|
| **Kling** | 好 | 快 | 快手的AI视频，支持img2video |
| **Runway Gen-3** | 很好 | 中 | 效果最稳定 |
| **Pika** | 好 | 快 | 适合短循环 |
| **Vidu** | 好 | 快 | 国内可用 |

### 生成提示词

**夜晚·陪伴（night-reading）**：
```
The cute warm-white creature inside the tent gently reads a tiny book,
occasionally turning a page. The camping lantern flickers softly with
warm amber light. Subtle starlight twinkles in the dark blue sky. 
A small campfire gently flickers. Very gentle, slow breathing movement.
Camera is static, isometric view. Seamless loop animation.
```

**白天·陪伴（day-idle）**：
```
The cute warm-white creature sits peacefully inside the cozy tent,
gently swaying. Soft warm sunlight. A very subtle breeze moves the
tent fabric slightly. The lantern glows softly. Camera is static,
isometric view. Seamless loop animation.
```

**打盹（sleeping）**：
```
The cute warm-white creature is sleeping peacefully inside the tent,
curled up with eyes closed. Very gentle breathing rise and fall.
The lantern light is dim and warm. Everything is quiet and still.
Camera is static, isometric view. Seamless loop animation.
```

### 关键提示词规则

每段视频的提示词都要包含：
- `camera is static` — 镜头不动，否则循环会跳
- `isometric view` — 保持等距视角一致
- `seamless loop` — 尽量让AI生成可循环的
- `very gentle / subtle / slow` — 动作要慢，快动作循环会跳
- 不要加 `zoom`、`pan`、`dolly` 等镜头运动词

---

## 五、当前已有的场景素材

可以直接用来做 img2video 输入：

| 素材 | 路径 | 用途 |
|------|------|------|
| 白天场景（完整参考） | `docs/reference/images/scene-ref-day.png` | 白天视频的参考/输入 |
| 夜晚场景（完整参考） | `docs/reference/images/scene-ref-night.png` | 夜晚视频的参考/输入 |
| 夜晚场景v2 | `docs/reference/images/scene-ref-night-v2.png` | 备选夜晚参考 |
| 白天切图（已抠背景） | `docs/reference/images1/scene-day-cutout.png` | 白天视频输入 |
| 夜晚切图（已抠背景） | `docs/reference/images1/scene-night-cutout.png` | 夜晚视频输入 |
| 角色·睡觉 | `docs/reference/char-sleeping-transparent.png` | 打盹视频的角色参考 |

**建议**：用完整参考图（`scene-ref-day.png`、`scene-ref-night.png`）做 img2video 输入，因为有背景的完整图生成视频效果更好。切图版（透明背景）不适合做视频输入。

---

## 六、前端实现方式

### 视频播放

```html
<video
  :src="currentVideoSrc"
  autoplay loop muted playsinline
  webkit-playsinline
  class="scene-video"
/>
```

**必须的属性**：
- `muted` — iOS要求静音才能自动播放
- `playsinline` — iOS不全屏播放
- `webkit-playsinline` — 旧版iOS兼容
- `loop` — 循环
- `autoplay` — 自动播放

### 状态切换（crossfade两个video标签）

```html
<!-- 两个video叠在一起，opacity交替 -->
<video ref="videoA" class="scene-video" :class="{ active: activeVideo === 'A' }" />
<video ref="videoB" class="scene-video" :class="{ active: activeVideo === 'B' }" />
```

```css
.scene-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  opacity: 0;
  transition: opacity 1.5s ease;
}
.scene-video.active {
  opacity: 1;
}
```

切换时：先让不活跃的video加载新src，load完成后切换active。

### 视频预加载

```javascript
// 页面加载时预加载所有视频
const videoUrls = Object.values(videos)
videoUrls.forEach(url => {
  const link = document.createElement('link')
  link.rel = 'preload'
  link.as = 'video'
  link.href = url
  document.head.appendChild(link)
})
```

---

## 七、文件目录

```
companion-agent/frontend/public/assets/video/
├── night-reading.mp4     夜晚·陪伴（P0）
├── day-idle.mp4          白天·陪伴（P0）
├── sleeping.mp4          打盹（P0）
├── night-waiting.mp4     夜晚·等你（P1）
├── day-happy.mp4         白天·高兴（P1）
└── dusty.mp4             落灰（P1）
```

---

## 八、生产流程

```
1. 选一张完整场景参考图（带背景的）
   ↓
2. 用 Kling/Runway 做 img2video（3-5秒）
   提示词里加 camera static + seamless loop
   ↓
3. 检查循环是否跳帧
   ├── 不跳 → 直接用
   └── 跳 → ffmpeg镜像循环处理
   ↓
4. ffmpeg 压缩（目标<3MB）+ faststart
   ↓
5. 放到 public/assets/video/ 目录
   ↓
6. 前端切换视频src
```

**时间估算**：P0的3段视频，生成+检查+压缩，约1-2小时。

---

*深夜施工队 · 2026-04-09*
