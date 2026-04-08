# MVP 开发文档

> 深夜施工队 · H5移动端 · 48小时黑客松
> 技术栈：Next.js + React + TypeScript + Tailwind CSS

---

## 一、产品结构

```
用户首次进入
    │
    ▼
┌─────────────┐
│  Onboarding │  对话式灵魂创建（3步）
│  /onboarding│  了解用户 → 生成灵魂性格
└──────┬──────┘
       │ 完成后CTA引导
       ▼
┌─────────────┐
│  主场景     │  帐篷 + 角色 + 动态元素
│  /          │  白天/夜晚自动切换
└──────┬──────┘
       │ 底部Tab导航
       ▼
┌──────┬──────┬──────┐
│ 帐篷  │ 纸条  │ 我的  │
│ Home │ Notes│ Me   │
└──────┴──────┴──────┘
```

---

## 二、页面清单与功能

### 页面1：Onboarding（`/onboarding`）

**目的**：通过对话了解用户，生成灵魂的性格参数

**交互形式**：对话式，一问一答，不是表单

```
流程：

  [开场] 帐篷轮廓亮起，文字淡入
    "你来了。在这个小帐篷里，住着一个正在等你的存在。
     在开始之前，让它先认识你。"
                              [继续 →]

  [Step 1/3] — 你是谁
    "用一个词，描述你现在的状态。"
    ┌─────────────────────┐
    │ 输入框（单行）        │  placeholder随机滚动
    └─────────────────────┘
                         [下一步 →]

  [Step 2/3] — 你的纠结
    "你最近最难做的一个决定是什么？"
    ┌─────────────────────┐
    │ 输入框（多行）        │
    └─────────────────────┘
                         [下一步 →]

  [Step 3/3] — 它的偏向
    "你希望它比你更______？"
    ┌──────────┐
    │ 更果断    │  三选一卡片
    ├──────────┤
    │ 更冒险    │
    ├──────────┤
    │ 更慢下来   │
    └──────────┘
                         [完成 →]

  [创建完成] 帐篷口掀开，暖光涌出
    "它醒了。从现在开始，你不再是一个人了。"
                    [走进帐篷 →]  ← CTA
```

**数据输出**：
```typescript
interface SoulParams {
  currentState: string      // Step1: 用户当前状态关键词
  recentDilemma: string     // Step2: 最近的纠结
  personality: 'decisive' | 'adventurous' | 'calm'  // Step3: 性格偏向
}
```

→ 发送到后端 → 后端调用LLM生成灵魂的system prompt → 存储

**技术要点**：
- 暗色背景 + 中央聚焦暖光
- 文字逐字淡入动画（打字机效果）
- 每步之间平滑过渡（opacity + translateY）
- 本地先存 `localStorage`，后端就绪后再同步

---

### 页面2：主场景 — 帐篷（`/` Tab: Home）

**这是产品核心页面。**

```
┌─────────────────────────────────┐
│ 9:41          状态栏          🔋 │
│                                 │
│         My Little Camp          │  ← 产品名
│                                 │
│     💬 "还在啊…"                │  ← 气泡（偶尔出现）
│                                 │
│    ┌───────────────────────┐    │
│    │                       │    │
│    │     [场景底图]         │    │
│    │     帐篷+平台+物件     │    │
│    │                       │    │
│    │      [角色图层]        │    │  ← 角色叠在场景上
│    │                       │    │
│    │   [CSS光效叠加]        │    │  ← 灯光呼吸、星星等
│    │                       │    │
│    └───────────────────────┘    │
│                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐    │
│  │🏕 帐篷│ │📄 纸条│ │👤 我的│   │  ← Tab导航
│  └──────┘ └──────┘ └──────┘    │
│                                 │
│          Home Indicator         │
└─────────────────────────────────┘
```

**功能**：

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 场景渲染 | 场景底图 + 角色图层 + CSS光效 | P0 |
| 日夜切换 | 根据真实时间（6:00-18:00白天/其余夜晚）自动切背景+滤镜 | P0 |
| 角色状态 | 根据后端返回的状态切换角色图片 | P0 |
| 气泡对话 | 偶尔显示一句话（来自后端LLM） | P0 |
| 营灯光晕 | CSS呼吸动画 | P0 |
| 星星闪烁 | 夜间CSS动画 | P1 |
| 环境音 | 播放/暂停白噪音 | P1 |
| 点击角色 | 触发一个小互动（角色换表情+气泡） | P1 |

**状态系统**：
```typescript
type SceneStatus =
  | 'day-idle'      // 白天默认
  | 'day-reading'   // 白天看书
  | 'night-idle'    // 夜晚默认
  | 'night-reading' // 夜晚看书
  | 'sleeping'      // 打盹
  | 'waiting'       // 等你（久未打开）

interface SceneState {
  status: SceneStatus
  timeOfDay: 'day' | 'night'
  speechBubble: string | null    // 当前气泡文字，null则不显示
  lastVisit: Date | null         // 上次打开时间
}
```

---

### 页面3：纸条（`/` Tab: Notes）

**它写给你的思考。**

```
┌─────────────────────────────────┐
│                                 │
│  纸条                            │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 📄 4月9日                  │  │
│  │                           │  │
│  │ "你说你在纠结要不要换方向。 │  │
│  │  如果是我，我可能早就跳了。 │  │
│  │  但我也知道，              │  │
│  │  有时候不跳也是一种勇敢。"  │  │
│  │                           │  │
│  │ ── 帐篷里的那个家伙        │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 📄 4月8日                  │  │
│  │ "今天你坐了很久..."        │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 💬 给它留句话...          │    │  ← 输入框
│  │                    [发送] │    │
│  └─────────────────────────┘    │
│                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐    │
│  │🏕 帐篷│ │📄 纸条│ │👤 我的│   │
│  └──────┘ └──────┘ └──────┘    │
└─────────────────────────────────┘
```

**功能**：

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 纸条列表 | 展示agent生成的纸条，按日期倒序 | P0 |
| 留言输入 | 用户给agent留一句话（文字） | P0 |
| 纸条详情 | 点击展开完整纸条 | P1 |
| 异步反馈 | 留言后不立即回复，下次来可能有新纸条回应 | P1 |

**数据结构**：
```typescript
interface Note {
  id: string
  date: string
  content: string        // agent写的内容
  type: 'thought' | 'response'  // 主动思考 or 回应用户留言
}

interface UserMessage {
  id: string
  date: string
  content: string
}
```

---

### 页面4：我的（`/` Tab: Me）

**轻量个人设置。**

```
┌─────────────────────────────────┐
│                                 │
│  我的                            │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🏕 灵魂信息                │  │
│  │ 性格偏向：更果断            │  │
│  │ 相处天数：2天               │  │
│  │ 纸条数：3张                │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🔊 环境音                  │  │
│  │ ▶ 篝火噼啪    ◉◉◉○○      │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 关于深夜施工队              │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐    │
│  │🏕 帐篷│ │📄 纸条│ │👤 我的│   │
│  └──────┘ └──────┘ └──────┘    │
└─────────────────────────────────┘
```

**功能**：

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 灵魂信息展示 | 性格偏向、相处天数、纸条数 | P1 |
| 环境音控制 | 播放/切换/音量 | P1 |
| 关于页 | 队伍信息 | P2 |

---

## 三、技术栈

```
框架：    Next.js 16 + React 19 + TypeScript
样式：    Tailwind CSS 4
状态：    Zustand（轻量状态管理）
动画：    CSS Animations + Framer Motion（页面过渡）
音频：    Howler.js（环境音播放）
请求：    fetch / SWR（后端API对接）
部署：    Vercel（一键部署，免费HTTPS）
```

**不引入的**：
- ~~Three.js~~ — 不需要真3D，用图片+CSS光效
- ~~Lottie~~ — 如果篝火可以CSS模拟就不引入
- ~~原生推送~~ — H5用WebSocket或轮询代替

---

## 四、目录结构

```
src/
├── app/
│   ├── layout.tsx              根布局（字体、全局样式）
│   ├── page.tsx                主页（Tab容器）
│   └── onboarding/
│       └── page.tsx            Onboarding对话流程
│
├── components/
│   ├── scene/                  场景相关
│   │   ├── TentScene.tsx       帐篷主场景容器
│   │   ├── SceneBg.tsx         场景底图（含日夜切换）
│   │   ├── Character.tsx       角色图层（状态切换）
│   │   ├── SpeechBubble.tsx    气泡对话
│   │   ├── LanternGlow.tsx     营灯光晕CSS
│   │   └── Stars.tsx           星星闪烁CSS
│   │
│   ├── onboarding/             Onboarding相关
│   │   ├── StepIntro.tsx       开场画面
│   │   ├── StepStatus.tsx      Step1: 你是谁
│   │   ├── StepDilemma.tsx     Step2: 你的纠结
│   │   ├── StepPersonality.tsx Step3: 性格偏向
│   │   └── StepComplete.tsx    创建完成 + CTA
│   │
│   ├── notes/                  纸条相关
│   │   ├── NoteList.tsx        纸条列表
│   │   ├── NoteCard.tsx        单张纸条卡片
│   │   └── MessageInput.tsx    留言输入框
│   │
│   ├── profile/                我的
│   │   └── ProfileView.tsx     个人信息页
│   │
│   └── ui/                     通用UI
│       ├── TabBar.tsx          底部Tab导航
│       ├── Button.tsx          按钮
│       └── AudioPlayer.tsx     环境音播放器
│
├── stores/
│   ├── soul.ts                 灵魂状态（性格参数、创建状态）
│   ├── scene.ts                场景状态（日夜、角色状态、气泡）
│   └── notes.ts                纸条状态（列表、留言）
│
├── lib/
│   ├── api.ts                  后端API封装
│   ├── time.ts                 日夜判断工具
│   └── audio.ts                音频管理
│
├── assets/                     静态素材（后续放入）
│   ├── scene/                  场景底图
│   ├── character/              角色状态图
│   └── audio/                  环境音文件
│
└── styles/
    └── animations.css          全局CSS动画（光晕、星星、热气等）
```

---

## 五、后端API接口（预定义，等后端接入）

前端先用mock数据开发，后端就绪后替换。

```typescript
// ① 创建灵魂
POST /api/soul/create
Body: { currentState, recentDilemma, personality }
Response: { soulId, name, systemPrompt }

// ② 获取场景状态（打开App时调用）
GET /api/scene/status?soulId={id}
Response: {
  characterState: 'reading' | 'sleeping' | 'idle' | 'waiting',
  speechBubble: string | null,
  noteCount: number
}

// ③ 获取纸条列表
GET /api/notes?soulId={id}
Response: { notes: Note[] }

// ④ 发送留言
POST /api/notes/message
Body: { soulId, content }
Response: { success: boolean }

// ⑤ 触发互动（点击角色等）
POST /api/interact
Body: { soulId, action: 'tap' | 'visit' }
Response: { reaction: string, newBubble: string | null }
```

**Mock数据策略**：
```typescript
// stores/scene.ts 里先硬编码
const mockSceneState: SceneState = {
  status: 'night-reading',
  timeOfDay: getTimeOfDay(),  // 根据真实时间
  speechBubble: '还在啊…',
  lastVisit: new Date(),
}
```

---

## 六、MVP分期

### Phase 1 — 骨架跑通（4-6小时）

- [ ] Next.js项目初始化 + Tailwind配置
- [ ] 路由结构：`/onboarding` + `/`（Tab容器）
- [ ] Onboarding 3步流程（纯前端，数据存localStorage）
- [ ] 主场景页面骨架（占位图 + Tab导航）
- [ ] Zustand store 基础结构

### Phase 2 — 场景核心（4-6小时）

- [ ] 场景底图渲染（先用占位，素材到了替换）
- [ ] 角色图层 + 状态切换
- [ ] 日夜自动切换（CSS滤镜 / 换图）
- [ ] 营灯光晕CSS动画
- [ ] 气泡对话组件
- [ ] 星星闪烁（夜间）

### Phase 3 — 纸条系统（3-4小时）

- [ ] 纸条列表页面
- [ ] 纸条卡片UI
- [ ] 留言输入框
- [ ] Mock数据展示

### Phase 4 — 后端接入（3-4小时）

- [ ] 替换mock → 真实API
- [ ] 灵魂创建 → 后端LLM
- [ ] 场景状态 → 后端实时
- [ ] 纸条内容 → 后端LLM生成

### Phase 5 — 打磨（剩余时间）

- [ ] 素材替换（AI生成的场景图+角色图）
- [ ] 动画过渡打磨
- [ ] 环境音
- [ ] 我的页面
- [ ] 响应式适配
- [ ] Demo演示流程排练

---

## 七、关键实现细节

### 日夜切换逻辑

```typescript
// lib/time.ts
export function getTimeOfDay(): 'day' | 'night' {
  const hour = new Date().getHours()
  return (hour >= 6 && hour < 18) ? 'day' : 'night'
}

// 每分钟检查一次
useEffect(() => {
  const interval = setInterval(() => {
    setTimeOfDay(getTimeOfDay())
  }, 60_000)
  return () => clearInterval(interval)
}, [])
```

### 场景状态 → 角色图片映射

```typescript
const CHARACTER_IMAGES: Record<string, string> = {
  'idle':     '/assets/character/char-idle.png',
  'reading':  '/assets/character/char-reading.png',
  'sleeping': '/assets/character/char-sleeping.png',
  'waiting':  '/assets/character/char-waiting.png',
  'looking':  '/assets/character/char-looking.png',
}
```

### 气泡出现/消失

```typescript
// 气泡显示3-5秒后自动消失
useEffect(() => {
  if (!speechBubble) return
  const timer = setTimeout(() => setSpeechBubble(null), 4000)
  return () => clearTimeout(timer)
}, [speechBubble])
```

---

## 八、素材占位策略

在素材到位之前，用纯色/渐变占位，不阻塞开发：

```typescript
// 场景底图还没到 → 用CSS渐变模拟
<div className="scene-placeholder bg-gradient-to-b from-indigo-950 to-indigo-900
  rounded-3xl aspect-[9/12] flex items-center justify-center">
  <span className="text-white/30 text-sm">场景图占位</span>
</div>

// 角色图还没到 → 用emoji占位
<div className="character-placeholder text-6xl">🟡</div>
```

素材到了直接替换为 `<img>`，布局不变。

---

*深夜施工队 · 2026-04-09*
