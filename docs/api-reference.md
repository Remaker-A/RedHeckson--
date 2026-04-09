# Companion Agent 后端 — 完整 API 接口文档

> Base URL: `http://<host>:8000` · 版本 0.1.0 · 2026-04-09

---

## 目录

| 分组 | 端点数 | 说明 |
|------|--------|------|
| [Root](#1-root) | 2 | 健康检查 + WebSocket |
| [Soul 灵魂](#2-soul-灵魂) | 3 | 创建 / 读取 / 重置 |
| [Personality 性格](#3-personality-性格) | 3 | 读取 / 修改 / 预设列表 |
| [Companion 陪伴](#4-companion-陪伴) | 4 | 说话 / 对话 / 整理 / 上下文导出 |
| [Room 房间](#5-room-房间) | 1 | 房间场景 |
| [Notes 纸条](#6-notes-纸条) | 3 | 列表 / 最新 / 生成 |
| [Focus 专注](#7-focus-专注) | 3 | 开始 / 停止 / 状态 |
| [Message 留言](#8-message-留言) | 2 | 留言 / 情绪标记 |
| [Status 状态](#9-status-状态) | 1 | 状态机实时状态 |
| [Desktop 桌面上下文](#10-desktop-桌面上下文) | 4 | Mac 端上报 + 前端拉取 |
| [Simulate 模拟](#11-simulate-模拟开发用) | 10 | 硬件 / 对话 / 桌面场景模拟 |

共 **36 个端点**。

---

## 1. Root

### GET /

健康检查，返回后端基本信息。

**响应**:
```json
{
  "name": "Companion Agent Backend",
  "version": "0.1.0",
  "status": { "state": "idle", "time_period": "afternoon", ... },
  "ws_clients": 0
}
```

### WebSocket /ws/live

实时事件推送（状态切换、say_line 等）。

**连接**: `ws://<host>:8000/ws/live`

**服务端推送消息格式**:
```json
{
  "type": "state_change",
  "data": {
    "from": "idle",
    "to": "companion",
    "status": { ... },
    "say_line": "你来了。"
  }
}
```

---

## 2. Soul 灵魂

### POST /api/soul

创建灵魂（只能创建一次，已存在则返回 409）。

**请求**:
```json
{
  "current_state_word": "疲惫",
  "struggle": "要不要换方向",
  "bias": "adventurous",
  "custom_voice_style": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `current_state_word` | string | 是 | 用户当前状态词 |
| `struggle` | string | 是 | 用户最近纠结的事 |
| `bias` | string | 是 | 性格偏向：`decisive` / `adventurous` / `slow_down` / `warm_humor` / `night_owl` / `bookish` / `custom` |
| `custom_voice_style` | string | 否 | bias 为 `custom` 时必填，自定义说话风格描述 |

**响应 200**:
```json
{
  "ok": true,
  "soul": {
    "created_at": "2026-04-09T15:00:00",
    "current_state_word": "疲惫",
    "struggle": "要不要换方向",
    "bias": "adventurous",
    "opening_response": "你来了。"
  }
}
```

**响应 409**: `Soul already exists. Delete soul.json to recreate.`

---

### GET /api/soul

读取当前灵魂。

**响应 200**: Soul 对象（同上 `soul` 字段）

**响应 404**: `Soul not created yet.`

---

### DELETE /api/soul

重置灵魂及所有关联数据（soul / personality / rhythm / events / notes / messages / chat_history / digest_state）。

**响应**:
```json
{ "ok": true, "message": "Soul and all data reset." }
```

---

## 3. Personality 性格

### GET /api/personality

读取当前性格参数。

**响应**:
```json
{
  "version": 3,
  "updated_at": "2026-04-09T16:00:00",
  "params": {
    "bias": "adventurous",
    "night_owl_index": 0.15,
    "anxiety_sensitivity": 0.1,
    "quietness": 0.4,
    "playfulness": 0.5,
    "attachment_level": 0.2
  },
  "natural_description": "它开始了解你了...",
  "voice_style": "说话直接，喜欢追问...",
  "evolution_log": [
    { "day": 3, "change": "playfulness +0.05", "reason": "对话中有互怼", "timestamp": "..." }
  ]
}
```

---

### PATCH /api/personality

修改性格偏向 / 说话风格。

**请求**:
```json
{
  "bias": "warm_humor",
  "voice_style": "说话温暖，偶尔幽默"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `bias` | string | 否 | 新的性格偏向 |
| `voice_style` | string | 否 | 新的说话风格描述 |

**响应**: `{ "ok": true, "personality": { ... } }`

---

### GET /api/personality/presets

列出所有性格预设。

**响应**:
```json
{
  "presets": [
    {
      "key": "decisive",
      "label": "果断型",
      "short_desc": "...",
      "voice_style": "...",
      "default_params": { "quietness": 0.3, ... }
    }
  ]
}
```

---

## 4. Companion 陪伴

### POST /api/companion/speak

生成一句话（基于当前 L0-L4 上下文，不超过 15 字）。

**请求**: 无 Body

**响应**:
```json
{ "ok": true, "say_line": "Xcode 写了两小时了，休息下？" }
```

**失败**: `{ "ok": false, "say_line": null, "error": "LLM 未配置（检查 SILICONFLOW_API_KEY 等）" }`

---

### POST /api/companion/chat

多轮对话。

**请求**:
```json
{
  "message": "最近在忙什么呢？",
  "history": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "嗯，来了。" }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | 是 | 本轮用户消息 |
| `history` | ChatTurn[] | 否 | 之前的对话记录（role + content） |

**响应**: `{ "ok": true, "reply": "..." }`

---

### POST /api/companion/digest

手动触发对话整理（从 chat_history 提取关系信号 → 更新 personality / soul）。

**请求**: 无 Body

**响应**: 包含 `ok`、`processed_lines`、`personality_update`、`user_snapshot` 等字段。

---

### GET /api/companion/context-markdown

导出当前 L0-L4 多级上下文为 Markdown 文本。

**响应**: `Content-Type: text/plain`，Markdown 格式的可读快照。

---

## 5. Room 房间

### GET /api/room

获取当前房间场景（由性格 + 节律 + 状态自动计算）。

**响应**:
```json
{
  "scene": "tidy",
  "details": {
    "description": "帐篷内整洁明亮，小物件摆放整齐，灯光温暖",
    "light": "warm",
    "items": ["book", "plant"],
    "creature_state": "reading"
  }
}
```

**scene 枚举值**:

| 值 | 含义 | 触发条件 |
|----|------|---------|
| `tidy` | 整洁 | 默认 / 亲近度高 + 节律稳定 |
| `messy` | 凌乱 | 焦虑敏感度 > 0.5 |
| `night` | 深夜 | 当前状态为 deep_night |
| `dusty` | 落灰 | 相处超 3 天但今天没来 |
| `recovering` | 恢复中 | 刚相处 1 天以内 |

---

## 6. Notes 纸条

### GET /api/notes

获取所有纸条列表。

**响应**: `NoteData[]`
```json
[
  {
    "id": "a1b2c3d4",
    "content": "如果是我，我可能会先试试...",
    "created_at": "2026-04-09T14:00:00",
    "personality_version": 2
  }
]
```

---

### GET /api/notes/latest

获取最新一张纸条。

**响应**: 单个 NoteData 对象

**响应 404**: `No notes yet.`

---

### POST /api/notes/generate

通过 LLM 生成一张新纸条（基于 L0-L2 上下文）。

**请求**: 无 Body

**响应**: 新生成的 NoteData 对象

---

## 7. Focus 专注

### POST /api/focus/start

开始专注模式（番茄钟）。

**请求**:
```json
{ "duration_minutes": 25 }
```

**响应**: 完整的 StatusData 对象（状态变为 `focus`）

---

### POST /api/focus/stop

结束专注模式。

**请求**: 无 Body

**响应**: 完整的 StatusData 对象（状态回到 `companion` / `deep_night`）

---

### GET /api/focus

获取当前专注状态。

**响应**:
```json
{
  "active": true,
  "duration_minutes": 25,
  "started_at": "2026-04-09T15:30:00"
}
```

---

## 8. Message 留言

### POST /api/message

留言给帐篷里的存在。

**请求**:
```json
{ "content": "今天好累，但看到你在还挺好的", "mood": "tired" }
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | 否 | 留言文字内容 |
| `mood` | string | 否 | 留言时的情绪标记 |

**响应**: `{ "ok": true }`

---

### POST /api/mood

单独标记情绪（不带文字内容）。

**请求**:
```json
{ "mood": "calm" }
```

**响应**: `{ "ok": true, "mood": "calm" }`

---

## 9. Status 状态

### GET /api/status

获取状态机的实时状态（L3 层数据）。

**响应**:
```json
{
  "state": "companion",
  "state_since": "2026-04-09T15:00:00",
  "seated_minutes": 45,
  "distance_cm": 50.0,
  "time_period": "afternoon",
  "is_night": false,
  "today_total_minutes": 120,
  "current_time": "15:45",
  "current_date": "2026-04-09",
  "weekday": 4,
  "focus": {
    "active": false,
    "duration_minutes": 25,
    "started_at": null
  }
}
```

**state 枚举值**:

| 值 | 含义 |
|----|------|
| `idle` | 无人在桌前 |
| `passerby` | 有人路过 |
| `companion` | 主人坐下，陪伴中 |
| `focus` | 主人在专注工作 |
| `deep_night` | 深夜仍在桌前 |
| `leaving` | 主人起身离开 |

**time_period 枚举值**: `morning` / `noon` / `afternoon` / `evening` / `late_night`

---

## 10. Desktop 桌面上下文

Mac 灵动岛应用上报桌面活动，前端拉取展示。

### POST /api/desktop/heartbeat

Mac 端轻量心跳（每次应用切换 / 每分钟定时）。

**请求**:
```json
{
  "frontmost_app": "Xcode",
  "frontmost_category": "coding",
  "bundle_id": "com.apple.dt.Xcode"
}
```

**响应**: `{ "ok": true }`

---

### POST /api/desktop/snapshot

Mac 端完整快照（每 5 分钟一次）。

**请求**:
```json
{
  "frontmost_app": "Xcode",
  "frontmost_category": "coding",
  "window_title_hint": "在 Xcode 中编辑 Swift 项目",
  "activity_summary": "用户在 IDE 中编写 SwiftUI 视图代码",
  "hourly_usage": [
    { "app_name": "Xcode", "bundle_id": "com.apple.dt.Xcode", "duration_minutes": 42.5, "category": "coding" },
    { "app_name": "Safari", "bundle_id": "com.apple.Safari", "duration_minutes": 8.3, "category": "browser" }
  ],
  "app_switch_count_last_hour": 7,
  "screen_time_today_minutes": 185
}
```

**响应**: `{ "ok": true, "work_pattern": "deep_focus" }`

---

### GET /api/desktop/context

返回原始桌面上下文 JSON。

**响应**: 完整的 DesktopContext 对象（`updated_at` / `current_snapshot` / `daily_top_apps` / `work_pattern` 等）。

---

### GET /api/desktop/summary

聚合接口：结构化数据 + 可读文本 + 中文标签，前端一次请求搞定。

**响应**:
```json
{
  "ok": true,
  "has_desktop": true,
  "context": { ... },
  "formatted": "主人正在使用: Xcode（coding）\n窗口提示: ...\n今日常用: ...\n工作模式: 深度专注中",
  "work_pattern": "deep_focus",
  "work_pattern_label_zh": "深度专注中"
}
```

| 字段 | 说明 |
|------|------|
| `has_desktop` | Mac 是否上报过有效数据 |
| `formatted` | 与 LLM prompt L4 段相同的可读文本 |
| `work_pattern` | 枚举：`deep_focus` / `multitasking` / `browsing` / `meeting` / `general` |
| `work_pattern_label_zh` | 中文：深度专注中 / 多任务并行 / 浏览网页中 / 会议中 / 一般使用 |

---

## 11. Simulate 模拟（开发用）

### 11.1 硬件模拟

| 方法 | 路径 | 请求 Body | 说明 |
|------|------|-----------|------|
| POST | `/api/sim/person-arrive` | 无 | 模拟人走近（→ passerby） |
| POST | `/api/sim/person-sit` | 无 | 模拟人坐下（→ companion / deep_night） |
| POST | `/api/sim/person-leave` | 无 | 模拟人离开（→ leaving → idle） |
| POST | `/api/sim/set-distance` | `{ "distance_cm": 50.0 }` | 设置距离 |
| POST | `/api/sim/set-time` | `{ "hour": 23, "minute": 30 }` | 设置模拟时间 |
| POST | `/api/sim/fast-forward` | `{ "days": 7, "late_night_ratio": 0.3, "focus_ratio": 0.4 }` | 快进 N 天，生成节律数据 + 触发性格演化 |

`fast-forward` 响应:
```json
{
  "days_generated": 7,
  "records": 7,
  "late_night_ratio": 0.43,
  "regularity_score": 0.75,
  "personality": { ... }
}
```

### 11.2 对话模拟

| 方法 | 路径 | 请求 Body | 说明 |
|------|------|-----------|------|
| GET | `/api/sim/chat-scenarios` | 无 | 列出对话场景名：deep_night / stress_vent / playful_banter / quiet_companion / trust_building / daily_routine |
| POST | `/api/sim/inject-chat` | `{ "scenarios": ["all"], "reset_digest": true, "clear_history": false }` | 注入模拟对话记录 |
| POST | `/api/sim/run-digest-test` | `{ "scenarios": ["all"], "clear_history": true }` | 注入 + 跑 digest 循环，返回性格前后对比 |

### 11.3 桌面场景模拟

| 方法 | 路径 | 请求 Body | 说明 |
|------|------|-----------|------|
| GET | `/api/sim/desktop-scenarios` | 无 | 列出 7 个预置桌面场景 |
| POST | `/api/sim/desktop-scenario` | `{ "scenario": "deep_focus_coding" }` | 一键切换桌面场景 |
| POST | `/api/sim/desktop-random` | 无 | 随机桌面场景 |
| DELETE | `/api/sim/desktop-context` | 无 | 清除桌面上下文 |

**可用场景**:

| scenario | 标签 | 前台应用 | work_pattern |
|----------|------|---------|--------------|
| `deep_focus_coding` | 深度编码 | Xcode | deep_focus |
| `distracted_browsing` | 分心刷网页 | Safari | multitasking |
| `in_meeting` | 会议中 | Zoom | meeting |
| `writing_doc` | 写文档 | Notion | general |
| `late_night_grind` | 深夜赶工 | VSCode | deep_focus |
| `design_review` | 设计评审 | Figma | general |
| `idle` | 离开电脑 | Finder | general |

---

## 附录 A：枚举值速查

### bias（性格偏向）
`decisive` / `adventurous` / `slow_down` / `warm_humor` / `night_owl` / `bookish` / `custom`

### state（状态机）
`idle` / `passerby` / `companion` / `focus` / `deep_night` / `leaving`

### room scene（房间场景）
`tidy` / `messy` / `night` / `dusty` / `recovering`

### category（应用类别）
`coding` / `terminal` / `browser` / `communication` / `meeting` / `media` / `office` / `design` / `other`

### work_pattern（工作模式）
`deep_focus` / `multitasking` / `browsing` / `meeting` / `general`

---

## 附录 B：上下文分层体系

| 层 | 名称 | 数据来源 | 持久化 |
|----|------|---------|--------|
| L0 | Soul 灵魂 | 用户创建 + 对话整理 | soul.json |
| L1 | Personality 性格 | 创建 + 演化 + 对话整理 | personality.json |
| L2 | Rhythm 节律 | 硬件 / 模拟 / 快进 | rhythm.json |
| L3 | Realtime 实时 | 状态机内存 | 不持久化 |
| L4 | Desktop 桌面 | Mac 灵动岛上报 | desktop_context.json |

**各接口使用的层级**:

| 接口 | L0 | L1 | L2 | L3 | L4 |
|------|----|----|----|----|-----|
| `/companion/speak` | Y | Y | - | Y | Y |
| `/companion/chat` | Y | Y | Y | Y | Y |
| `/notes/generate` | Y | Y | Y | - | - |
| `/room` | - | Y | Y | - | - |
| `/companion/context-markdown` | Y | Y | Y | Y | Y |

---

*深夜施工队 · 2026-04-09*
