# "你不在的时候" — 活动日志功能规划

> 每次打开App，看到它在你不在时做了什么。
> 不是数据报表，是它生活的痕迹。

---

## 一、概念

用户打开帐篷页面时，如果距离上次有间隔，顶部或中间会短暂显示一段"你不在的时候"的活动摘要。像一个温柔的回顾——不是推送通知，是你回来后发现的痕迹。

---

## 二、数据来源（不改后端）

从现有API拼出活动日志：

| 数据 | API | 包含信息 |
|------|-----|---------|
| 纸条 | `GET /api/notes` | 你不在时它写了几张纸条 |
| 房间状态 | `GET /api/room` | 当前场景（整洁/乱/落灰） |
| 性格演化 | `GET /api/personality` | version变化 = 它成长了 |
| 状态 | `GET /api/status` | 当前状态、在桌时间 |

前端用 `localStorage` 记录上次打开的时间戳，对比当前数据推算"你不在期间发生了什么"。

---

## 三、活动日志条目类型

| 类型 | 触发条件 | 展示文案示例 |
|------|---------|-------------|
| **新纸条** | notes数量 > 上次记录 | "它写了 2 张纸条" |
| **性格成长** | personality.version > 上次 | "它的性格又长大了一点" |
| **房间变化** | room.scene 和上次不同 | "帐篷里多了些东西" / "它整理了帐篷" |
| **想你了** | 超过24小时未打开 | "它在帐篷口看了好几次外面" |
| **深夜陪伴** | 上次是深夜离开 | "昨晚它陪你到很晚" |
| **新的一天** | 日期变了 | "新的一天，它已经醒了" |

---

## 四、UI设计

### 入口1：主场景顶部卡片（推荐）

打开帐篷页时，如果有活动日志，在标题下方短暂显示一个卡片，5秒后自动收起。

```
┌─────────────────────────────────┐
│ My Little Camp                  │
│ 早上好 · 陪伴第 3 天             │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 你不在的时候                  │ │  ← 半透明卡片
│ │                             │ │
│ │  📄 它写了 1 张纸条          │ │
│ │  🌱 它的性格又长大了一点      │ │
│ │  🏕 它整理了帐篷             │ │
│ └─────────────────────────────┘ │
│                                 │
│         [视频场景]               │
│                                 │
└─────────────────────────────────┘
```

### 入口2：Tab页"动态"（替代或补充纸条页）

如果想做成一个持久可查看的页面，可以在纸条页顶部加一个"最近动态"区域。

---

## 五、实现方案

### localStorage 记录

```typescript
interface LastVisitData {
  timestamp: number          // 上次打开时间
  noteCount: number          // 上次纸条数量
  personalityVersion: number // 上次性格版本
  roomScene: string          // 上次房间场景
}
```

### 活动日志生成逻辑

```typescript
function generateActivityLog(lastVisit: LastVisitData, current: CurrentData): ActivityItem[] {
  const logs: ActivityItem[] = []
  const hoursSince = (Date.now() - lastVisit.timestamp) / 3600000

  // 新纸条
  const newNotes = current.noteCount - lastVisit.noteCount
  if (newNotes > 0) {
    logs.push({ icon: '📄', text: `它写了 ${newNotes} 张纸条` })
  }

  // 性格成长
  if (current.personalityVersion > lastVisit.personalityVersion) {
    logs.push({ icon: '🌱', text: '它的性格又长大了一点' })
  }

  // 房间变化
  if (current.roomScene !== lastVisit.roomScene) {
    const sceneTexts: Record<string, string> = {
      tidy: '它整理了帐篷',
      messy: '帐篷里有点乱了',
      night: '帐篷里亮着灯',
      dusty: '帐篷落了些灰',
      recovering: '它在慢慢整理帐篷',
    }
    logs.push({ icon: '🏕️', text: sceneTexts[current.roomScene] || '帐篷里有些变化' })
  }

  // 想你了（超过24小时）
  if (hoursSince > 24) {
    logs.push({ icon: '👀', text: '它在帐篷口看了好几次外面' })
  }

  // 深夜
  if (hoursSince > 6 && new Date(lastVisit.timestamp).getHours() >= 22) {
    logs.push({ icon: '🌙', text: '昨晚它陪你到很晚' })
  }

  // 新的一天
  const lastDay = new Date(lastVisit.timestamp).toDateString()
  const today = new Date().toDateString()
  if (lastDay !== today && logs.length === 0) {
    logs.push({ icon: '☀️', text: '新的一天，它已经醒了' })
  }

  return logs
}
```

### 显示时机

- 每次进入帐篷页 `onMounted` 时计算
- 有内容才显示卡片
- 5秒后自动渐隐
- 点击可提前关闭
- 显示后更新 `localStorage` 的记录

---

## 六、开发优先级

**P0（MVP）**：
- 主场景顶部活动卡片
- 新纸条 + 想你了 + 新的一天 三种日志
- localStorage 记录上次状态

**P1（打磨）**：
- 性格成长 + 房间变化日志
- 卡片入场/离场动画
- 纸条页顶部"最近动态"区域

---

*深夜施工队 · 2026-04-09*
