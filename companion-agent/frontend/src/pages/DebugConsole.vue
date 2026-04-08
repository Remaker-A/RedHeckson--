<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCompanionStore } from '../stores/companion'
import { useWebSocket } from '../composables/useWebSocket'
import * as api from '../composables/useApi'

const store = useCompanionStore()
const { connected, on: wsOn } = useWebSocket()

const logs = ref<Array<{ time: string; type: string; data: string }>>([])
const generating = ref(false)
const fastForwarding = ref(false)

function addLog(type: string, data: unknown) {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  logs.value.unshift({ time, type, data: JSON.stringify(data, null, 2) })
  if (logs.value.length > 50) logs.value.pop()
}

wsOn('state_change', (data) => {
  addLog('state_change', data)
  const d = data as Record<string, unknown>
  if (d.status) store.status = d.status as api.StatusData
  if (d.say_line && typeof d.say_line === 'string') {
    store.setSayLine(d.say_line)
    addLog('say_line', d.say_line)
  }
})

wsOn('personality_update', (data) => {
  addLog('personality_update', data)
  store.fetchPersonality()
})

wsOn('new_note', (data) => {
  addLog('new_note', data)
  store.fetchNotes()
})

onMounted(async () => {
  await Promise.all([
    store.checkSoul(),
    store.refreshStatus(),
    store.fetchPersonality(),
    store.fetchRoom(),
    store.fetchNotes(),
  ])
  addLog('init', { soulExists: store.soulExists, state: store.status?.state })
})

const stateLabel: Record<string, string> = {
  idle: '💤 休息', passerby: '👀 路过', companion: '✨ 陪伴',
  focus: '🔥 专注', deep_night: '🌙 深夜', leaving: '🚪 离开',
}

const personalityBars = computed(() => {
  if (!store.personality) return []
  const p = store.personality.params
  const labels: Record<string, string> = {
    night_owl_index: '🦉 夜猫子',
    anxiety_sensitivity: '😰 焦虑敏感',
    quietness: '🤫 安静度',
    attachment_level: '💕 依恋度',
  }
  return Object.entries(labels).map(([key, label]) => ({
    key,
    label,
    value: Number((p as Record<string, unknown>)[key] ?? 0),
  }))
})

async function doSim(action: string) {
  try {
    let result: unknown
    switch (action) {
      case 'arrive': result = await api.simArrive(); break
      case 'sit': result = await api.simSit(); break
      case 'leave': result = await api.simLeave(); break
      case 'night': result = await api.simSetTime(23, 30); break
      case 'day': result = await api.simSetTime(14, 0); break
    }
    addLog(`sim:${action}`, result)
    await store.refreshStatus()
    await store.fetchRoom()
  } catch (e) {
    addLog('error', String(e))
  }
}

async function doFastForward() {
  fastForwarding.value = true
  try {
    const result = await api.simFastForward(7, 0.4, 0.5)
    addLog('fast_forward', result)
    await store.fetchPersonality()
  } catch (e) {
    addLog('error', String(e))
  } finally {
    fastForwarding.value = false
  }
}

async function doGenerateNote() {
  generating.value = true
  try {
    const note = await api.generateNote()
    addLog('note_generated', note)
    store.notes.push(note)
  } catch (e) {
    addLog('error', String(e))
  } finally {
    generating.value = false
  }
}

async function doReset() {
  if (!confirm('确认重置所有数据？')) return
  try {
    await api.resetSoul()
    addLog('reset', { ok: true })
    store.soul = null
    store.status = null
    store.personality = null
    store.notes = []
    store.sayLine = ''
  } catch (e) {
    addLog('error', String(e))
  }
}

async function doCreateSoul() {
  try {
    await api.createSoul({
      current_state_word: '迷茫',
      struggle: '不知道该不该换工作，现在稳定但没有成长空间',
      bias: 'adventurous',
    })
    addLog('soul_created', { bias: 'adventurous' })
    await Promise.all([store.checkSoul(), store.fetchPersonality()])
  } catch (e) {
    addLog('error', String(e))
  }
}

async function doMessage(text: string) {
  try {
    await api.sendMessage(text, 'calm')
    addLog('message_sent', { text })
  } catch (e) {
    addLog('error', String(e))
  }
}
</script>

<template>
  <div class="debug-page">
    <header class="debug-header">
      <h1>🔧 Debug Console</h1>
      <div class="ws-status" :class="{ on: connected }">
        WS {{ connected ? '已连接' : '断开' }}
      </div>
    </header>

    <div class="debug-grid">
      <!-- Left: Controls -->
      <div class="debug-col">
        <!-- Soul -->
        <section class="card">
          <h2>灵魂</h2>
          <div v-if="store.soulExists" class="soul-info">
            <div>状态词: <b>{{ store.soul?.current_state_word }}</b></div>
            <div>纠结: {{ store.soul?.struggle }}</div>
            <div>偏向: {{ store.soul?.bias }}</div>
          </div>
          <div v-else class="empty">未创建</div>
          <div class="btn-row">
            <button v-if="!store.soulExists" @click="doCreateSoul" class="btn btn-primary">快速创建</button>
            <button @click="doReset" class="btn btn-danger">重置全部</button>
          </div>
        </section>

        <!-- State machine -->
        <section class="card">
          <h2>状态机</h2>
          <div class="state-display">
            <span class="state-badge">{{ stateLabel[store.status?.state ?? ''] || store.status?.state || '—' }}</span>
            <span class="state-meta">{{ store.status?.time_period }} · 坐了{{ store.status?.seated_minutes ?? 0 }}min</span>
          </div>
          <div class="btn-grid">
            <button @click="doSim('arrive')" class="btn">👤 人走近</button>
            <button @click="doSim('sit')" class="btn">🪑 人坐下</button>
            <button @click="doSim('leave')" class="btn">🚪 人离开</button>
            <button @click="doSim('night')" class="btn">🌙 切深夜</button>
            <button @click="doSim('day')" class="btn">☀️ 切下午</button>
          </div>
        </section>

        <!-- Personality -->
        <section class="card">
          <h2>性格 <span v-if="store.personality" class="version">v{{ store.personality.version }}</span></h2>
          <div v-if="store.personality" class="personality-info">
            <div class="desc">{{ store.personality.natural_description }}</div>
            <div v-for="bar in personalityBars" :key="bar.key" class="bar-row">
              <span class="bar-label">{{ bar.label }}</span>
              <div class="bar-track"><div class="bar-fill" :style="{ width: `${bar.value * 100}%` }"></div></div>
              <span class="bar-val">{{ (bar.value * 100).toFixed(0) }}%</span>
            </div>
          </div>
          <div class="btn-row">
            <button @click="doFastForward" :disabled="fastForwarding" class="btn btn-accent">
              {{ fastForwarding ? '演化中...' : '⏩ 快进7天演化' }}
            </button>
          </div>
        </section>

        <!-- Notes & Actions -->
        <section class="card">
          <h2>纸条 <span class="count">({{ store.notes.length }})</span></h2>
          <div class="btn-row">
            <button @click="doGenerateNote" :disabled="generating" class="btn btn-primary">
              {{ generating ? '生成中...' : '📝 生成纸条' }}
            </button>
            <button @click="doMessage('测试留言：今天有点累')" class="btn">💬 测试留言</button>
          </div>
          <div v-if="store.notes.length" class="note-list">
            <div v-for="note in store.notes.slice(-5).reverse()" :key="note.id" class="note-item">
              <span class="note-id">#{{ note.id }}</span>
              <span class="note-ver">v{{ note.personality_version }}</span>
              <div class="note-content">{{ note.content }}</div>
            </div>
          </div>
        </section>

        <!-- Say line -->
        <section v-if="store.sayLine" class="card say-card">
          <h2>它说</h2>
          <div class="say-text">「{{ store.sayLine }}」</div>
        </section>
      </div>

      <!-- Right: Log -->
      <div class="debug-col log-col">
        <section class="card log-card">
          <h2>事件日志 <button @click="logs = []" class="btn-clear">清空</button></h2>
          <div class="log-list">
            <div v-for="(log, i) in logs" :key="i" class="log-entry" :class="log.type.startsWith('error') ? 'log-error' : ''">
              <div class="log-header">
                <span class="log-time">{{ log.time }}</span>
                <span class="log-type">{{ log.type }}</span>
              </div>
              <pre class="log-data">{{ log.data }}</pre>
            </div>
            <div v-if="!logs.length" class="empty">等待事件...</div>
          </div>
        </section>
      </div>
    </div>

    <!-- Nav -->
    <nav class="debug-nav">
      <router-link to="/soul">灵魂创建</router-link>
      <router-link to="/tent">帐篷</router-link>
      <router-link to="/desktop">桌面</router-link>
      <a href="/docs" target="_blank">Swagger</a>
    </nav>
  </div>
</template>

<style scoped>
.debug-page {
  min-height: 100vh;
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 1rem;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.debug-header h1 { font-size: 1.1rem; font-weight: 600; margin: 0; }

.ws-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  background: rgba(255,80,80,0.15);
  color: #ff6b6b;
}
.ws-status.on { background: rgba(80,255,120,0.12); color: #4ade80; }

.debug-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  max-width: 1200px;
}

@media (max-width: 768px) {
  .debug-grid { grid-template-columns: 1fr; }
}

.debug-col { display: flex; flex-direction: column; gap: 0.8rem; }

.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 0.9rem;
}

.card h2 {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255,255,255,0.5);
  margin: 0 0 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.version { color: #e8a04c; font-size: 0.7rem; }
.count { color: rgba(255,255,255,0.3); font-weight: 400; }

.empty { color: rgba(255,255,255,0.25); font-size: 0.8rem; font-style: italic; }

.btn-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.5rem; }
.btn-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.35rem; margin-top: 0.5rem; }

.btn {
  padding: 0.4rem 0.7rem;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.7);
  font-size: 0.72rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
  white-space: nowrap;
}
.btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-primary { border-color: rgba(100,180,255,0.3); color: #64b5f6; }
.btn-primary:hover { background: rgba(100,180,255,0.12); }

.btn-accent { border-color: rgba(232,160,76,0.3); color: #e8a04c; }
.btn-accent:hover { background: rgba(232,160,76,0.12); }

.btn-danger { border-color: rgba(255,100,100,0.2); color: #ff6b6b; }
.btn-danger:hover { background: rgba(255,100,100,0.12); }

.btn-clear {
  background: none;
  border: none;
  color: rgba(255,255,255,0.3);
  font-size: 0.65rem;
  cursor: pointer;
  margin-left: auto;
}

/* Soul */
.soul-info { font-size: 0.78rem; line-height: 1.6; }
.soul-info b { color: #e8a04c; }

/* State */
.state-display { display: flex; align-items: center; gap: 0.8rem; }
.state-badge { font-size: 0.9rem; font-weight: 500; }
.state-meta { font-size: 0.7rem; color: rgba(255,255,255,0.35); }

/* Personality */
.personality-info { font-size: 0.78rem; }
.desc { color: rgba(255,255,255,0.6); margin-bottom: 0.6rem; line-height: 1.4; }
.bar-row { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.3rem; }
.bar-label { width: 80px; font-size: 0.7rem; color: rgba(255,255,255,0.45); flex-shrink: 0; }
.bar-track { flex: 1; height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; background: #e8a04c; border-radius: 2px; transition: width 0.4s; }
.bar-val { width: 32px; text-align: right; font-size: 0.65rem; color: rgba(255,255,255,0.35); font-variant-numeric: tabular-nums; }

/* Notes */
.note-list { margin-top: 0.6rem; display: flex; flex-direction: column; gap: 0.4rem; }
.note-item { background: rgba(255,255,255,0.03); border-radius: 6px; padding: 0.5rem; }
.note-id { font-size: 0.65rem; color: rgba(255,255,255,0.25); margin-right: 0.3rem; }
.note-ver { font-size: 0.6rem; color: #e8a04c; }
.note-content { font-size: 0.78rem; color: rgba(255,255,255,0.7); line-height: 1.4; margin-top: 0.25rem; }

/* Say line */
.say-card { border-color: rgba(232,160,76,0.2); }
.say-text { font-size: 0.95rem; color: #e8a04c; text-align: center; }

/* Log */
.log-card { max-height: calc(100vh - 6rem); display: flex; flex-direction: column; }
.log-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.3rem; }
.log-entry { background: rgba(255,255,255,0.02); border-radius: 4px; padding: 0.4rem 0.5rem; }
.log-error { border-left: 2px solid #ff6b6b; }
.log-header { display: flex; gap: 0.5rem; margin-bottom: 0.2rem; }
.log-time { font-size: 0.65rem; color: rgba(255,255,255,0.25); font-variant-numeric: tabular-nums; }
.log-type { font-size: 0.65rem; color: #64b5f6; font-weight: 500; }
.log-data {
  font-size: 0.68rem;
  color: rgba(255,255,255,0.5);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  max-height: 120px;
  overflow-y: auto;
  font-family: 'Cascadia Code', 'Fira Code', monospace;
}

/* Nav */
.debug-nav {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  display: flex;
  gap: 0.5rem;
  background: rgba(26,26,46,0.9);
  backdrop-filter: blur(8px);
  padding: 0.5rem 0.8rem;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.08);
}
.debug-nav a {
  font-size: 0.7rem;
  color: rgba(255,255,255,0.4);
  text-decoration: none;
  transition: color 0.15s;
}
.debug-nav a:hover { color: #fff; }
</style>
