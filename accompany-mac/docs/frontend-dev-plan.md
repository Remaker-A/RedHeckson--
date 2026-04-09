# 前端开发完整方案

> 深夜施工队 · H5移动端
> 基于后端 companion-agent 服务（FastAPI + WebSocket）

---

## 一、技术栈

```
框架      Next.js 16 + React 19 + TypeScript
样式      Tailwind CSS 4
状态      Zustand
动画      Framer Motion（页面过渡）+ lottie-react（精细动效）+ CSS Animations
请求      fetch（REST API）+ 原生 WebSocket（实时推送）
部署      Vercel
```

---

## 二、后端API对接总览

后端地址：`http://localhost:8000`（开发）

### REST API

| 接口 | 方法 | 用途 | 前端页面 |
|------|------|------|---------|
| `/api/soul` | POST | 创建灵魂 | Onboarding |
| `/api/soul` | GET | 查询灵魂 | 我的、主场景 |
| `/api/soul` | DELETE | 重置灵魂 | 我的（设置） |
| `/api/status` | GET | 获取当前状态 | 主场景 |
| `/api/personality` | GET | 获取性格信息 | 我的 |
| `/api/personality/presets` | GET | 性格预设列表 | Onboarding（Step3展示） |
| `/api/room` | GET | 房间场景状态 | 主场景 |
| `/api/companion/speak` | POST | 生成一句话 | 主场景气泡 |
| `/api/companion/chat` | POST | 多轮对话 | 纸条页（留言后触发） |
| `/api/notes` | GET | 获取纸条列表 | 纸条墙 |
| `/api/notes/generate` | POST | 生成新纸条 | 纸条墙 |
| `/api/message` | POST | 用户留言 | 纸条墙 |
| `/api/focus/start` | POST | 开始专注 | 主场景（P1） |
| `/api/focus/stop` | POST | 停止专注 | 主场景（P1） |
| `/api/sim/person-sit` | POST | 模拟人坐下 | Demo演示 |
| `/api/sim/person-leave` | POST | 模拟人离开 | Demo演示 |
| `/api/sim/set-time` | POST | 模拟时间 | Demo演示 |

### WebSocket

连接：`ws://localhost:8000/ws/live`

| 事件 | 数据 | 前端处理 |
|------|------|---------|
| `state_change` | `{from, to, status, say_line}` | 更新角色状态 + 显示气泡 |
| `personality_update` | `{version, params, natural_description}` | 更新我的页面 |
| `soul_update` | `{soul}` | 更新灵魂信息 |

---

## 三、页面与路由

```
/onboarding          灵魂创建（首次进入）
/                    主应用（Tab容器）
  ├── Tab: Home      帐篷主场景
  ├── Tab: Notes     纸条墙
  └── Tab: Me        我的
```

---

## 四、状态管理（Zustand Stores）

### soul.ts — 灵魂状态

```typescript
interface SoulStore {
  // 状态
  soul: Soul | null
  personality: Personality | null
  isCreated: boolean

  // 动作
  createSoul: (params: CreateSoulRequest) => Promise<void>
  fetchSoul: () => Promise<void>
  fetchPersonality: () => Promise<void>
  resetSoul: () => Promise<void>
}

interface Soul {
  created_at: string
  current_state_word: string
  struggle: string
  bias: string
  opening_response: string
}

interface Personality {
  version: number
  updated_at: string
  params: {
    bias: string
    night_owl_index: number
    anxiety_sensitivity: number
    quietness: number
    playfulness: number
    attachment_level: number
  }
  natural_description: string
  voice_style: string
  evolution_log: Array<{
    day: number
    change: string
    reason: string
    timestamp: string
  }>
}
```

### scene.ts — 场景状态

```typescript
interface SceneStore {
  // 状态
  state: string           // idle | passerby | companion | focus | deep_night | leaving
  timeOfDay: 'day' | 'night'
  speechBubble: string | null
  room: RoomState | null
  status: StatusResponse | null

  // 动作
  fetchStatus: () => Promise<void>
  fetchRoom: () => Promise<void>
  setSpeechBubble: (text: string | null) => void
  updateFromWebSocket: (event: StateChangeEvent) => void
}

interface RoomState {
  scene: 'tidy' | 'messy' | 'night' | 'dusty' | 'recovering'
  details: {
    description: string
    light: 'warm' | 'dim' | 'warm_low' | 'almost_off' | 'warming_up'
    items: string[]
    creature_state: string
  }
}
```

### notes.ts — 纸条状态

```typescript
interface NotesStore {
  // 状态
  notes: Note[]
  isLoading: boolean

  // 动作
  fetchNotes: () => Promise<void>
  generateNote: () => Promise<void>
  sendMessage: (content: string, mood?: string) => Promise<void>
}

interface Note {
  id: string
  content: string
  created_at: string
  personality_version: number
}
```

---

## 五、API封装层

```typescript
// lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}

// Soul
export const api = {
  // Soul
  createSoul: (body: CreateSoulRequest) =>
    request<CreateSoulResponse>('/api/soul', { method: 'POST', body: JSON.stringify(body) }),
  getSoul: () => request<Soul>('/api/soul'),
  deleteSoul: () => request('/api/soul', { method: 'DELETE' }),

  // Status & Room
  getStatus: () => request<StatusResponse>('/api/status'),
  getRoom: () => request<RoomState>('/api/room'),

  // Personality
  getPersonality: () => request<Personality>('/api/personality'),
  getPresets: () => request<{ presets: PresetInfo[] }>('/api/personality/presets'),

  // Companion
  speak: () => request<{ ok: boolean; say_line: string }>('/api/companion/speak', { method: 'POST' }),
  chat: (message: string, history: ChatMessage[]) =>
    request<{ ok: boolean; reply: string }>('/api/companion/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history }),
    }),

  // Notes
  getNotes: () => request<Note[]>('/api/notes'),
  generateNote: () => request<Note>('/api/notes/generate', { method: 'POST' }),

  // Message
  sendMessage: (content: string, mood?: string) =>
    request('/api/message', { method: 'POST', body: JSON.stringify({ content, mood }) }),

  // Focus
  startFocus: (minutes = 25) =>
    request('/api/focus/start', { method: 'POST', body: JSON.stringify({ duration_minutes: minutes }) }),
  stopFocus: () => request('/api/focus/stop', { method: 'POST' }),

  // Sim (Demo用)
  simPersonSit: () => request('/api/sim/person-sit', { method: 'POST' }),
  simPersonLeave: () => request('/api/sim/person-leave', { method: 'POST' }),
  simSetTime: (hour: number, minute = 0) =>
    request('/api/sim/set-time', { method: 'POST', body: JSON.stringify({ hour, minute }) }),
}
```

---

## 六、WebSocket管理

```typescript
// lib/ws.ts

type WSEventType = 'state_change' | 'personality_update' | 'soul_update'

class CompanionWS {
  private ws: WebSocket | null = null
  private listeners = new Map<WSEventType, Set<(data: any) => void>>()
  private reconnectTimer: NodeJS.Timeout | null = null

  connect(url: string) {
    this.ws = new WebSocket(url)

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      const handlers = this.listeners.get(msg.type)
      handlers?.forEach(fn => fn(msg.data))
    }

    this.ws.onclose = () => {
      // 3秒后自动重连
      this.reconnectTimer = setTimeout(() => this.connect(url), 3000)
    }
  }

  on(type: WSEventType, handler: (data: any) => void) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(handler)
    return () => this.listeners.get(type)!.delete(handler)
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
  }
}

export const companionWS = new CompanionWS()
```

### React Hook

```typescript
// hooks/useCompanionWS.ts

export function useCompanionWS() {
  const updateScene = useSceneStore(s => s.updateFromWebSocket)
  const setSpeechBubble = useSceneStore(s => s.setSpeechBubble)
  const fetchPersonality = useSoulStore(s => s.fetchPersonality)
  const fetchSoul = useSoulStore(s => s.fetchSoul)

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/live'
    companionWS.connect(wsUrl)

    const unsubs = [
      companionWS.on('state_change', (data) => {
        updateScene(data)
        if (data.say_line) setSpeechBubble(data.say_line)
      }),
      companionWS.on('personality_update', () => fetchPersonality()),
      companionWS.on('soul_update', () => fetchSoul()),
    ]

    return () => {
      unsubs.forEach(fn => fn())
      companionWS.disconnect()
    }
  }, [])
}
```

---

## 七、核心页面实现要点

### Onboarding

```
流程：

  检查 GET /api/soul
  ├── 200 → 跳转主页面（已创建过）
  └── 404 → 进入Onboarding

  Step 1: 输入 current_state_word
  Step 2: 输入 struggle
  Step 3: 选择 bias（从 GET /api/personality/presets 加载选项）

  完成 → POST /api/soul 创建灵魂
       → 成功后跳转主页面
       → 409 → 说明已存在，跳转主页面
```

**后端返回的bias选项（6种，比我们之前设计的3种更多）**：

| key | label | 一句话描述 |
|-----|-------|-----------|
| decisive | 安静笃定派 | 在你犹豫时，它会先迈出那一步 |
| adventurous | 好奇冒险家 | 追问有趣细节，鼓励你去尝试 |
| slow_down | 慢半拍先生 | 节奏缓，喜欢带你一起想 |
| warm_humor | 温柔段子手 | 找到事情好玩的那个角度 |
| night_owl | 深夜陪伴者 | 夜晚话变多，语调变轻 |
| bookish | 小小哲学家 | 从小事想到大问题 |

前端可以展示其中3-6个供选择，用卡片形式。

### 主场景（Home Tab）

```
初始化：
  1. GET /api/status → 获取当前状态（state, is_night等）
  2. GET /api/room → 获取房间场景（scene, light, items, creature_state）
  3. 连接 WebSocket → 监听实时状态变化
  4. POST /api/companion/speak → 获取一句气泡话

状态映射到UI：
  status.state → 角色图片
    companion → char-reading / char-idle
    deep_night → char-reading（夜间版）
    focus → char-idle（专注表情）
    idle / leaving → char-sleeping
    passerby → char-looking

  room.details.light → CSS灯光强度
    warm → 灯晕opacity 1.0
    dim → 灯晕opacity 0.5
    warm_low → 灯晕opacity 0.3
    almost_off → 灯晕opacity 0.08
    warming_up → 灯晕从0.1渐变到0.8

  status.is_night → 日夜切换
    true → 深色背景 + 星星 + 月亮
    false → 浅色背景

WebSocket state_change事件 → 自动更新角色+气泡：
  say_line → 显示气泡3-5秒
  status → 更新角色图 + 灯光
```

### 纸条墙（Notes Tab）

**单栏上下排布，不随意贴。** 像一叠纸条从上到下，按时间排列。

```
初始化：
  GET /api/notes → 获取所有纸条

贴便签：
  用户输入文字 → POST /api/message → 本地立即展示用户便签
                                   → 不等待回复（异步）

纸条生成（可选手动触发）：
  POST /api/notes/generate → 获取新纸条 → 插入列表

便签数据映射：
  agent的纸条 → Note对象，cream/白色便签纸样式
  用户的留言 → 彩色便签纸样式
  按时间倒序，单栏排列，最新的在上面
```

### 我的（Me Tab）

```
初始化：
  GET /api/soul → 灵魂基础信息
  GET /api/personality → 性格参数 + 自然描述 + 演化日志

展示：
  性格偏向 → soul.bias → 对应中文label
  相处天数 → 计算 daysSince(soul.created_at)
  性格描述 → personality.natural_description
  演化版本 → personality.version
  性格参数 → personality.params（可视化展示）
  成长阶段 → 根据version和天数推算

设置：
  重新初始化 → DELETE /api/soul → 跳转Onboarding
```

---

## 八、目录结构

```
src/
├── app/
│   ├── layout.tsx                 根布局
│   ├── page.tsx                   主页（检查灵魂→跳转）
│   ├── onboarding/
│   │   └── page.tsx               Onboarding
│   └── home/
│       └── page.tsx               Tab容器（Home/Notes/Me）
│
├── components/
│   ├── scene/
│   │   ├── TentScene.tsx          帐篷主场景
│   │   ├── Character.tsx          角色图层
│   │   ├── SpeechBubble.tsx       气泡
│   │   ├── LanternGlow.tsx        灯光CSS
│   │   └── Stars.tsx              星星
│   │
│   ├── onboarding/
│   │   ├── StepIntro.tsx          开场
│   │   ├── StepStatus.tsx         Step1
│   │   ├── StepDilemma.tsx        Step2
│   │   ├── StepPersonality.tsx    Step3
│   │   └── StepComplete.tsx       完成CTA
│   │
│   ├── notes/
│   │   ├── NoteWall.tsx           便签墙
│   │   ├── StickyNote.tsx         单张便签
│   │   └── WriteNote.tsx          写便签
│   │
│   ├── profile/
│   │   ├── SoulProfile.tsx        灵魂档案
│   │   └── Settings.tsx           设置
│   │
│   └── ui/
│       ├── TabBar.tsx             底部Tab
│       └── Button.tsx             按钮
│
├── stores/
│   ├── soul.ts                    灵魂+性格
│   ├── scene.ts                   场景+状态
│   └── notes.ts                   纸条+留言
│
├── lib/
│   ├── api.ts                     REST API封装
│   ├── ws.ts                      WebSocket管理
│   └── time.ts                    时间工具
│
├── hooks/
│   └── useCompanionWS.ts          WebSocket React Hook
│
├── assets/                        静态素材（后续放入）
│   ├── scene/
│   ├── character/
│   └── lottie/
│
└── styles/
    └── animations.css             CSS动画
```

---

## 九、开发顺序

### Phase 1：骨架（~4h）
- [ ] `npx create-next-app` + Tailwind + Zustand + lottie-react
- [ ] 路由：`/onboarding` + `/home`
- [ ] `lib/api.ts` API封装层
- [ ] `lib/ws.ts` WebSocket管理
- [ ] Zustand stores 基础结构
- [ ] TabBar组件

### Phase 2：Onboarding（~3h）
- [ ] 开场画面 + 3步对话流程
- [ ] 对接 `POST /api/soul` + `GET /api/personality/presets`
- [ ] 完成CTA → 跳转主场景
- [ ] 已创建检测 → 自动跳过

### Phase 3：主场景（~4h）
- [ ] 场景容器（占位图 → 后续替换素材）
- [ ] 角色图层 + 状态切换
- [ ] 对接 `GET /api/status` + `GET /api/room`
- [ ] WebSocket连接 + state_change处理
- [ ] 气泡显示/隐藏
- [ ] CSS灯光 + 日夜切换 + 星星

### Phase 4：纸条墙（~3h）
- [ ] 便签墙布局（随机旋转、颜色区分）
- [ ] 对接 `GET /api/notes`
- [ ] 写便签 → `POST /api/message`
- [ ] 生成纸条 → `POST /api/notes/generate`

### Phase 5：我的（~2h）
- [ ] Agent档案信息展示
- [ ] 对接 `GET /api/soul` + `GET /api/personality`
- [ ] 重新初始化 → `DELETE /api/soul`

### Phase 6：打磨（剩余时间）
- [ ] 素材替换
- [ ] Lottie动效接入
- [ ] 过渡动画
- [ ] Demo演示流程
- [ ] 模拟API（`/api/sim/*`）做Demo控制面板

---

## 十、Demo演示控制

后端提供了完整的模拟API，可以在Demo时控制场景：

```typescript
// 可以做一个隐藏的Demo控制面板（比如长按标题5秒弹出）

// 模拟人坐下 → 触发 idle→companion，角色出来
await api.simPersonSit()

// 模拟深夜 → 触发夜间模式
await api.simSetTime(23, 30)

// 模拟人离开 → 触发 companion→leaving→idle
await api.simPersonLeave()

// 快进7天 → 生成历史数据，触发性格演化
await api.simFastForward(7, 0.3, 0.4)
```

Demo时可以按脚本依次调用这些API，配合现场演示。

---

## 十一、环境变量

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/live
```

生产部署时替换为实际后端地址。

---

*深夜施工队 · 2026-04-09*
