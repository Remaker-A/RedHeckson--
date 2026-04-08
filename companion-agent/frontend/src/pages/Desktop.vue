<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import * as api from '../composables/useApi'
import { useWebSocket } from '../composables/useWebSocket'
import WhiteNoise from '../components/desktop/WhiteNoise.vue'

const router = useRouter()
const store = useCompanionStore()
const { connected, on: wsOn } = useWebSocket()

watch(connected, (val) => store.setWsConnected(val), { immediate: true })

wsOn('state_change', (data) => {
  const d = data as Record<string, unknown>
  if (d.status) store.status = d.status as api.StatusData
  if (d.say_line && typeof d.say_line === 'string') store.setSayLine(d.say_line)
})

wsOn('personality_update', () => {
  store.fetchPersonality()
})

const expanded = ref(true)
const focusActive = ref(false)
const focusMinutes = ref(25)
const focusRemaining = ref(0)
let focusTimer: number | null = null

const stateLabel = computed(() => {
  const map: Record<string, string> = {
    idle: '它在帐篷里休息',
    passerby: '它探出头看了一眼',
    companion: '它出来陪你了',
    focus: '安静陪你专注',
    deep_night: '它也在熬夜',
    leaving: '它缩回帐篷了',
  }
  return map[store.status?.state ?? ''] || '未知'
})

const tentIcon = computed(() => {
  const map: Record<string, string> = {
    idle: '🏕️💤',
    passerby: '🏕️👀',
    companion: '🏕️✨',
    focus: '🏕️🔥',
    deep_night: '🏕️🌙',
    leaving: '🏕️',
  }
  return map[store.status?.state ?? ''] || '🏕️'
})

const seatedTime = computed(() => {
  const m = store.status?.seated_minutes || 0
  if (m < 60) return `${m}分钟`
  return `${Math.floor(m / 60)}小时${m % 60}分钟`
})

const isNight = computed(() => store.status?.is_night || false)

onMounted(async () => {
  const exists = await store.checkSoul()
  if (!exists) {
    router.replace('/soul')
    return
  }
  await Promise.all([
    store.refreshStatus(),
    store.fetchPersonality(),
  ])
})

watch(() => store.sayLine, (val) => {
  if (val) setTimeout(() => store.clearSayLine(), 10000)
})

async function startFocus() {
  await api.startFocus(focusMinutes.value)
  focusActive.value = true
  focusRemaining.value = focusMinutes.value * 60
  focusTimer = window.setInterval(() => {
    focusRemaining.value--
    if (focusRemaining.value <= 0) endFocus()
  }, 1000)
}

async function endFocus() {
  if (focusTimer) clearInterval(focusTimer)
  focusTimer = null
  focusActive.value = false
  await api.stopFocus()
}

onUnmounted(() => { if (focusTimer) clearInterval(focusTimer) })

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

async function simArrive() { await api.simArrive(); await store.refreshStatus() }
async function simSit() { await api.simSit(); await store.refreshStatus() }
async function simLeave() { await api.simLeave(); await store.refreshStatus() }
async function simNight() { await api.simSetTime(23, 30); await store.refreshStatus() }
async function simDay() { await api.simSetTime(14, 0); await store.refreshStatus() }
async function simFastForward() {
  await api.simFastForward(7)
  await store.fetchPersonality()
  alert(`快进了7天，性格已演化到 v${store.personality?.version || '?'}`)
}
</script>

<template>
  <div class="desktop-page">
    <div class="desktop-container">
      <!-- Menubar -->
      <div class="menubar" @click="expanded = !expanded">
        <div class="menubar-left">
          <span class="tent-icon">{{ tentIcon }}</span>
          <span class="app-title">帐篷里的存在</span>
        </div>
        <div class="menubar-right">
          <span class="ws-indicator" :class="{ on: store.wsConnected }"></span>
          <span class="expand-arrow" :class="{ open: expanded }">&#9662;</span>
        </div>
      </div>

      <!-- Panel -->
      <transition name="panel">
        <div v-if="expanded" class="panel">
          <!-- Status section -->
          <div class="section">
            <div class="status-row">
              <span class="status-emoji">{{ tentIcon }}</span>
              <div class="status-info">
                <div class="status-main">{{ stateLabel }}</div>
                <div v-if="store.status?.state !== 'idle'" class="status-sub">
                  和你待了 {{ seatedTime }}
                </div>
              </div>
            </div>
          </div>

          <!-- Say line -->
          <transition name="sayFade">
            <div v-if="store.sayLine" class="section say-section" @click="store.clearSayLine()">
              <span class="say-quote">"</span>
              <span class="say-text">{{ store.sayLine }}</span>
              <span class="say-quote">"</span>
            </div>
          </transition>

          <!-- White noise -->
          <div class="section">
            <div class="section-label">环境音</div>
            <WhiteNoise :is-night="isNight" />
          </div>

          <!-- Focus -->
          <div class="section">
            <div class="section-label">专注模式</div>
            <div v-if="!focusActive" class="focus-setup">
              <div class="focus-presets">
                <button
                  v-for="m in [25, 45, 60]"
                  :key="m"
                  class="preset-btn"
                  :class="{ selected: focusMinutes === m }"
                  @click="focusMinutes = m"
                >{{ m }}min</button>
              </div>
              <button class="start-btn" @click="startFocus">
                开始专注
              </button>
            </div>
            <div v-else class="focus-active">
              <div class="timer-display">
                <div class="timer-ring">
                  <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(245,240,235,0.06)" stroke-width="3" />
                    <circle
                      cx="50" cy="50" r="42"
                      fill="none"
                      stroke="var(--accent-orange)"
                      stroke-width="3"
                      stroke-linecap="round"
                      :stroke-dasharray="264"
                      :stroke-dashoffset="264 * (1 - focusRemaining / (focusMinutes * 60))"
                      transform="rotate(-90 50 50)"
                      style="transition: stroke-dashoffset 1s linear"
                    />
                  </svg>
                  <span class="timer-text">{{ formatTime(focusRemaining) }}</span>
                </div>
              </div>
              <button class="stop-btn" @click="endFocus">结束专注</button>
            </div>
          </div>

          <!-- Go to tent room -->
          <div class="section link-section" @click="router.push('/tent')">
            <span class="link-text">它写了一张纸条，去看看 →</span>
          </div>

          <!-- Personality info -->
          <div v-if="store.personality" class="section personality-section">
            <div class="section-label">它的性格 · v{{ store.personality.version }}</div>
            <div class="personality-desc">{{ store.personality.natural_description }}</div>
            <div class="personality-bars">
              <div class="bar-item" v-for="(value, key) in store.personality.params" :key="key as string">
                <template v-if="key !== 'bias'">
                  <span class="bar-label">{{ {night_owl_index:'夜猫子',anxiety_sensitivity:'焦虑敏感',quietness:'安静',attachment_level:'依恋'}[key as string] || key }}</span>
                  <div class="bar-track">
                    <div class="bar-fill" :style="{ width: `${(value as number) * 100}%` }"></div>
                  </div>
                  <span class="bar-value">{{ ((value as number) * 100).toFixed(0) }}%</span>
                </template>
              </div>
            </div>
          </div>

          <!-- Sim controls -->
          <div class="section sim-section">
            <div class="section-label sim-label">模拟控制台</div>
            <div class="sim-grid">
              <button @click="simArrive">👤 人走近</button>
              <button @click="simSit">🪑 人坐下</button>
              <button @click="simLeave">🚪 人离开</button>
              <button @click="simNight">🌙 设为深夜</button>
              <button @click="simDay">☀️ 设为下午</button>
              <button @click="simFastForward">⏩ 快进7天</button>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.desktop-page {
  min-height: 100vh;
  background: var(--bg-dark);
  display: flex;
  justify-content: center;
  padding: 3rem 1rem;
}

.desktop-container {
  width: 100%;
  max-width: 380px;
}

/* Menubar */
.menubar {
  background: rgba(61, 53, 48, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(245, 240, 235, 0.06);
  border-radius: 14px 14px 0 0;
  padding: 0.75rem 1.2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.menubar:hover { background: rgba(61, 53, 48, 0.95); }

.menubar-left { display: flex; align-items: center; gap: 0.6rem; }
.tent-icon { font-size: 1.2rem; }
.app-title { font-size: 0.82rem; color: rgba(245, 240, 235, 0.55); font-weight: 300; }

.menubar-right { display: flex; align-items: center; gap: 0.6rem; }

.ws-indicator {
  width: 5px; height: 5px; border-radius: 50%;
  background: rgba(245, 240, 235, 0.15);
  transition: background 0.3s;
}
.ws-indicator.on { background: #4ADE80; }

.expand-arrow {
  font-size: 0.7rem;
  color: rgba(245, 240, 235, 0.3);
  transition: transform 0.3s;
}
.expand-arrow.open { transform: rotate(180deg); }

/* Panel */
.panel {
  background: rgba(55, 48, 42, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(245, 240, 235, 0.05);
  border-top: none;
  border-radius: 0 0 14px 14px;
  overflow: hidden;
}

.panel-enter-active, .panel-leave-active {
  transition: all 0.35s ease;
  max-height: 1000px;
}
.panel-enter-from, .panel-leave-to {
  max-height: 0;
  opacity: 0;
}

/* Sections */
.section {
  padding: 1rem 1.3rem;
  border-bottom: 1px solid rgba(245, 240, 235, 0.04);
}
.section:last-child { border-bottom: none; }

.section-label {
  font-size: 0.7rem;
  color: rgba(245, 240, 235, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.7rem;
}

/* Status */
.status-row { display: flex; align-items: center; gap: 1rem; }
.status-emoji { font-size: 1.8rem; }
.status-main { font-size: 0.95rem; color: var(--text-light); font-weight: 300; }
.status-sub { font-size: 0.75rem; color: rgba(245, 240, 235, 0.35); margin-top: 0.15rem; }

/* Say line */
.say-section {
  text-align: center;
  cursor: pointer;
  padding: 0.8rem 1.3rem;
}
.say-quote { color: rgba(232, 160, 76, 0.4); font-size: 1.1rem; }
.say-text { font-size: 0.95rem; color: rgba(245, 240, 235, 0.8); font-weight: 300; margin: 0 0.3rem; }

.sayFade-enter-active { animation: sayIn 0.5s ease-out; }
.sayFade-leave-active { animation: sayIn 0.3s ease-in reverse; }
@keyframes sayIn {
  from { opacity: 0; max-height: 0; padding: 0 1.3rem; }
  to { opacity: 1; max-height: 60px; }
}

/* Focus */
.focus-setup { display: flex; flex-direction: column; gap: 0.7rem; }

.focus-presets { display: flex; gap: 0.4rem; }

.preset-btn {
  flex: 1;
  padding: 0.45rem;
  background: rgba(245, 240, 235, 0.04);
  border: 1px solid rgba(245, 240, 235, 0.08);
  border-radius: 10px;
  color: rgba(245, 240, 235, 0.5);
  font-size: 0.78rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.preset-btn.selected {
  border-color: rgba(232, 160, 76, 0.5);
  color: var(--accent-orange);
  background: rgba(232, 160, 76, 0.06);
}

.start-btn {
  padding: 0.6rem;
  background: rgba(232, 160, 76, 0.1);
  border: 1px solid rgba(232, 160, 76, 0.25);
  border-radius: 12px;
  color: var(--accent-orange);
  font-size: 0.85rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}
.start-btn:hover { background: rgba(232, 160, 76, 0.2); }

.focus-active {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.timer-display { position: relative; }

.timer-ring {
  width: 120px;
  height: 120px;
  position: relative;
}
.timer-ring svg { width: 100%; height: 100%; }
.timer-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 300;
  color: var(--accent-orange);
  font-variant-numeric: tabular-nums;
}

.stop-btn {
  padding: 0.4rem 1.5rem;
  background: none;
  border: 1px solid rgba(245, 240, 235, 0.15);
  border-radius: 12px;
  color: rgba(245, 240, 235, 0.45);
  font-size: 0.78rem;
  cursor: pointer;
  font-family: inherit;
}

/* Link section */
.link-section {
  cursor: pointer;
  text-align: center;
  transition: background 0.2s;
}
.link-section:hover { background: rgba(245, 240, 235, 0.02); }
.link-text { font-size: 0.82rem; color: rgba(245, 240, 235, 0.3); }

/* Personality */
.personality-desc {
  font-size: 0.82rem;
  color: rgba(245, 240, 235, 0.55);
  line-height: 1.5;
  margin-bottom: 0.8rem;
}

.personality-bars { display: flex; flex-direction: column; gap: 0.5rem; }

.bar-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bar-label {
  font-size: 0.7rem;
  color: rgba(245, 240, 235, 0.35);
  width: 56px;
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 3px;
  background: rgba(245, 240, 235, 0.06);
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--accent-orange);
  border-radius: 2px;
  transition: width 0.5s ease;
  opacity: 0.7;
}

.bar-value {
  font-size: 0.65rem;
  color: rgba(245, 240, 235, 0.3);
  width: 30px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Sim */
.sim-section {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 0 0 14px 14px;
}

.sim-label { color: rgba(245, 240, 235, 0.2); }

.sim-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.4rem;
}

.sim-grid button {
  padding: 0.5rem 0.3rem;
  background: rgba(245, 240, 235, 0.03);
  border: 1px solid rgba(245, 240, 235, 0.06);
  border-radius: 8px;
  color: rgba(245, 240, 235, 0.4);
  font-size: 0.68rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
  white-space: nowrap;
}

.sim-grid button:hover {
  background: rgba(245, 240, 235, 0.08);
  color: rgba(245, 240, 235, 0.7);
}
</style>
