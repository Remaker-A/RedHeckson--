<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import { useWebSocket } from '../composables/useWebSocket'

const router = useRouter()
const store = useCompanionStore()
const { on, connected } = useWebSocket()

const loaded = ref(false)
const isNight = computed(() => store.isNight)

// Home scene switcher — local, independent from global theme
const homeIsNight = ref(store.isNight)
watch(() => store.isNight, (v) => { homeIsNight.value = v })

const DAY_VIDEOS = ['day-idle', 'day-hackathon', 'day-sleeping', 'day-happy']
const NIGHT_VIDEOS = ['night-reading', 'night-sleeping', 'night-waiting']
const SCENE_LABELS: Record<string, string> = {
  'day-idle': '陪着你',
  'day-hackathon': '在参加小红书黑客松',
  'day-sleeping': '白天打了个盹',
  'day-happy': '蓬蓬心情很好',
  'night-reading': '深夜看书中',
  'night-sleeping': '睡着了',
  'night-waiting': '在等你回来',
}
const sceneIndex = ref(0)
const videoFading = ref(false)
let fadeTimer: ReturnType<typeof setTimeout> | undefined

const currentScenes = computed(() => homeIsNight.value ? NIGHT_VIDEOS : DAY_VIDEOS)
const sceneLabel = computed(() => SCENE_LABELS[currentScenes.value[sceneIndex.value]] ?? '')

function switchScene(delta: number) {
  const len = currentScenes.value.length
  const next = (sceneIndex.value + delta + len) % len
  if (next === sceneIndex.value) return
  videoFading.value = true
  if (fadeTimer) clearTimeout(fadeTimer)
  fadeTimer = setTimeout(() => {
    sceneIndex.value = next
    videoFading.value = false
  }, 250)
}

function toggleHomeTheme() {
  homeIsNight.value = !homeIsNight.value
  sceneIndex.value = 0
}

let touchStartX = 0
function onTouchStart(e: TouchEvent) { touchStartX = e.touches[0].clientX }
function onTouchEnd(e: TouchEvent) {
  const delta = e.changedTouches[0].clientX - touchStartX
  if (Math.abs(delta) > 50) switchScene(delta < 0 ? 1 : -1)
}

/* ---- Activity log ("你不在的时候") ---- */
interface ActivityItem { icon: string; text: string }
const activityLog = ref<ActivityItem[]>([])
const showActivity = ref(false)

function generateActivityLog() {
  const raw = localStorage.getItem('last_visit')
  const last = raw ? JSON.parse(raw) : null
  const logs: ActivityItem[] = []

  // Check if soul was just created (within last 10 minutes)
  const soulAge = store.soul?.created_at
    ? (Date.now() - new Date(store.soul.created_at).getTime()) / 60000
    : 999

  if (!last || soulAge < 10) {
    // First visit or just born — show birth activity
    logs.push({ icon: '✨', text: '蓬蓬诞生了' })
    logs.push({ icon: '🏕️', text: '它在帐篷里安顿好了' })
    logs.push({ icon: '📖', text: '它正在翻看你告诉它的事' })
  } else {
    const hoursSince = (Date.now() - last.timestamp) / 3600000

    const newNotes = store.notes.length - (last.noteCount ?? 0)
    if (newNotes > 0) logs.push({ icon: '📄', text: `蓬蓬写了 ${newNotes} 张纸条` })

    const pv = store.personality?.version ?? 1
    if (pv > (last.personalityVersion ?? 0)) logs.push({ icon: '🌱', text: '蓬蓬的性格又长大了一点' })

    const scene = store.room?.scene ?? 'tidy'
    if (scene !== last.roomScene) {
      const t: Record<string, string> = { tidy: '蓬蓬整理了帐篷', messy: '帐篷里有点乱了', night: '帐篷里亮着灯', dusty: '帐篷落了些灰', recovering: '蓬蓬在慢慢整理帐篷' }
      logs.push({ icon: '🏕️', text: t[scene] || '帐篷里有些变化' })
    }

    if (hoursSince > 24) logs.push({ icon: '👀', text: '蓬蓬在帐篷口看了好几次外面' })
    if (hoursSince > 6 && new Date(last.timestamp).getHours() >= 22) logs.push({ icon: '🌙', text: '昨晚蓬蓬陪你到很晚' })

    const lastDay = new Date(last.timestamp).toDateString()
    if (lastDay !== new Date().toDateString() && logs.length === 0) logs.push({ icon: '☀️', text: '新的一天，蓬蓬已经醒了' })

    // If nothing else happened, show a gentle welcome back
    if (logs.length === 0 && hoursSince > 0.5) {
      logs.push({ icon: '🏕️', text: '蓬蓬一直在帐篷里等你' })
    }
  }

  if (logs.length > 0) {
    activityLog.value = logs
    showActivity.value = true
    setTimeout(() => { showActivity.value = false }, 6000)
  }
}

function saveVisitState() {
  localStorage.setItem('last_visit', JSON.stringify({
    timestamp: Date.now(),
    noteCount: store.notes.length,
    personalityVersion: store.personality?.version ?? 1,
    roomScene: store.room?.scene ?? 'tidy',
  }))
}

const topSubtext = computed(() => {
  const days = store.soul?.created_at
    ? Math.max(1, Math.ceil((Date.now() - new Date(store.soul.created_at).getTime()) / 86400000))
    : 0
  if (!days) return ''
  const period = store.status?.time_period ?? ''
  const periodMap: Record<string, string> = {
    morning: '早上好',
    noon: '中午好',
    afternoon: '下午好',
    evening: '晚上好',
    late_night: '夜深了',
  }
  const greeting = periodMap[period] || ''
  return greeting ? `${greeting} · 陪伴第 ${days} 天` : `陪伴第 ${days} 天`
})
const bubbleVisible = ref(false)
const bubbleText = ref('')
let bubbleTimer: ReturnType<typeof setTimeout> | undefined

function showBubble(text: string) {
  bubbleText.value = text
  bubbleVisible.value = true
  if (bubbleTimer) clearTimeout(bubbleTimer)
  bubbleTimer = setTimeout(() => { bubbleVisible.value = false }, 5000)
}

const sceneVideo = computed(() => `/assets/video/${currentScenes.value[sceneIndex.value]}.mp4`)

const sceneImage = computed(() => homeIsNight.value
  ? '/assets/scene/scene-night-cutout.png'
  : '/assets/scene/scene-day-cutout.png'
)

const hasVideo = ref(false)
function checkVideoAvailable() {
  const video = document.createElement('video')
  video.src = sceneVideo.value
  video.onloadeddata = () => { hasVideo.value = true }
  video.onerror = () => { hasVideo.value = false }
}

const characterImage = computed(() =>
  homeIsNight.value ? '/assets/character/char-night.png' : '/assets/character/char-day.png'
)

const lightIntensity = computed(() => {
  const light = store.room?.details?.light ?? 'warm'
  const map: Record<string, number> = {
    warm: 1, dim: 0.5, warm_low: 0.3, almost_off: 0.08, warming_up: 0.6,
  }
  return map[light] ?? 0.8
})

// Background fill color — matches the top/bottom edge of the video
const bgFillColor = computed(() => homeIsNight.value ? '#1a2540' : '#f0e8dc')

onMounted(async () => {
  const hasSoul = await store.checkSoul()
  if (!hasSoul) {
    router.replace('/soul')
    return
  }
  await Promise.all([
    store.fetchRoom(),
    store.fetchNotes(),
    store.fetchStatus(),
    store.fetchPersonality(),
  ])
  loaded.value = true
  checkVideoAvailable()
  generateActivityLog()
  saveVisitState()

  try {
    const resp = await fetch('/api/companion/speak', { method: 'POST' })
    const data = await resp.json()
    if (data.ok && data.say_line) showBubble(data.say_line)
  } catch { /* ignore */ }
})

onUnmounted(() => {
  if (bubbleTimer) clearTimeout(bubbleTimer)
  if (fadeTimer) clearTimeout(fadeTimer)
})

on('state_change', (data) => {
  store.fetchRoom()
  store.fetchStatus()
  if (data.say_line) showBubble(data.say_line as string)
})
on('personality_update', () => store.fetchPersonality())
on('new_note', () => store.fetchNotes())
</script>

<template>
  <div class="home-page" :class="{ night: homeIsNight }" :style="{ backgroundColor: bgFillColor }"
       @touchstart="onTouchStart" @touchend="onTouchEnd">

    <!-- ═══ Video background layer ═══ -->
    <div class="video-bg-layer">
      <video
        v-if="hasVideo"
        :src="sceneVideo"
        autoplay loop muted playsinline webkit-playsinline
        class="bg-video"
        :class="{ fading: videoFading }"
      />
      <!-- Image fallback -->
      <div v-else class="bg-image-wrap">
        <img :src="sceneImage" alt="" class="bg-image" draggable="false" />
        <!-- CSS effects for image mode -->
        <div class="character-layer">
          <img :src="characterImage" alt="" class="character-img" draggable="false" />
        </div>
        <div class="lantern-glow" :style="{ opacity: lightIntensity * 0.7 }" />
      </div>
    </div>

    <!-- ═══ Stars (night only, behind UI) ═══ -->
    <div v-if="isNight && !hasVideo" class="stars-layer">
      <span v-for="i in 20" :key="i" class="star" :style="{
        top: Math.random() * 30 + '%',
        left: Math.random() * 100 + '%',
        width: (Math.random() * 2.5 + 1) + 'px',
        height: (Math.random() * 2.5 + 1) + 'px',
        animationDelay: (Math.random() * 3) + 's',
        animationDuration: (Math.random() * 2 + 2) + 's',
      }" />
      <div class="moon" />
    </div>

    <!-- ═══ Top bar: gradient fade + title left + subtitle right ═══ -->
    <div class="top-bar" :style="{ background: `linear-gradient(to bottom, ${bgFillColor} 40%, transparent 100%)` }">
      <div class="top-left">
        <h1 class="camp-title">蓬蓬的帐篷</h1>
        <p v-if="topSubtext" class="camp-sub">{{ topSubtext }}</p>
      </div>
      <div class="top-right">
        <button class="theme-toggle" @click="toggleHomeTheme" :class="{ night: homeIsNight }">
          <span>{{ homeIsNight ? '🌙' : '☀️' }}</span>
        </button>
        <div class="conn-dot" :class="{ online: connected }" />
      </div>
    </div>

    <!-- ═══ Scene label + dots ═══ -->
    <div class="scene-label-wrap">
      <Transition name="scene-text">
        <span :key="sceneLabel" class="scene-label">{{ sceneLabel }}</span>
      </Transition>
    </div>
    <div class="scene-dots">
      <span
        v-for="(_, i) in currentScenes"
        :key="i"
        class="scene-dot"
        :class="{ active: i === sceneIndex }"
        @click="sceneIndex = i"
      />
    </div>

    <!-- ═══ Activity log card ("你不在的时候") ═══ -->
    <Transition name="activity">
      <div v-if="showActivity" class="activity-card" @click="showActivity = false">
        <p class="activity-title">你不在的时候</p>
        <div v-for="(item, i) in activityLog" :key="i" class="activity-item">
          <span class="activity-icon">{{ item.icon }}</span>
          <span class="activity-text">{{ item.text }}</span>
        </div>
      </div>
    </Transition>

    <!-- ═══ Speech bubble (floats over video) ═══ -->
    <Transition name="bubble">
      <div v-if="bubbleVisible && !showActivity" class="speech-bubble">
        <p>{{ bubbleText }}</p>
        <div class="bubble-tail" />
      </div>
    </Transition>

    <!-- Loading -->
    <Transition name="fade">
      <div v-if="!loaded" class="loading-state">
        <div class="loading-glow" />
        <p class="loading-text">掀开帐篷帘子...</p>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.home-page {
  position: relative;
  width: 100%;
  height: 100dvh;
  overflow: hidden;
  transition: background-color 2s var(--ease-out-expo);
}

/* ═══════ Video Background Layer ═══════ */
.video-bg-layer {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  pointer-events: none;
}

.bg-video {
  width: 100%;
  height: auto;
  display: block;
  transition: opacity 0.25s ease;
}
.bg-video.fading {
  opacity: 0;
}

/* Image fallback */
.bg-image-wrap {
  position: relative;
  width: 100%;
}
.bg-image {
  width: 100%;
  height: auto;
  display: block;
}

/* Character (image mode only) */
.character-layer {
  position: absolute;
  top: 38%;
  left: 50%;
  transform: translateX(-55%);
  width: 22%;
}
.character-img {
  width: 100%;
  height: auto;
  display: block;
  animation: char-breathe 4s ease-in-out infinite;
  filter: drop-shadow(0 3px 6px rgba(60, 40, 20, 0.25));
}
@keyframes char-breathe {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

/* Lantern glow (image mode only) */
.lantern-glow {
  position: absolute;
  top: 25%;
  left: 45%;
  width: 120px;
  height: 120px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle,
    rgba(255, 180, 60, 0.4) 0%,
    rgba(255, 150, 30, 0.15) 40%,
    transparent 70%
  );
  border-radius: 50%;
  animation: glow-pulse 3.5s ease-in-out infinite;
}
@keyframes glow-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.7; }
  50% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; }
}

/* ═══════ Stars (night, no-video mode) ═══════ */
.stars-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle ease-in-out infinite;
}
@keyframes twinkle {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 0.9; }
}
.moon {
  position: absolute;
  top: 6%;
  left: 22%;
  width: 36px;
  height: 36px;
  background: #ffe8a0;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(255, 232, 160, 0.5), 0 0 60px rgba(255, 232, 160, 0.2);
}

/* ═══════ Top Bar ═══════ */
.top-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top, 12px) + 8px) 20px 28px;
  min-height: 96px;
}

.top-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.camp-title {
  font-family: var(--font-body);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-warm);
  letter-spacing: 0.04em;
  line-height: 1;
}
.home-page.night .camp-title {
  color: #f0ece6;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.4);
}

.camp-sub {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  opacity: 0.8;
  margin-top: 2px;
}
.home-page.night .camp-sub {
  color: rgba(220, 210, 200, 0.8);
}

/* ═══════ Top Right Controls ═══════ */
.top-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.theme-toggle {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.3s ease, transform 0.15s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.theme-toggle:active { transform: scale(0.9); }
.theme-toggle.night {
  background: rgba(30, 40, 60, 0.45);
}

/* ═══════ Scene Label ═══════ */
.scene-label-wrap {
  position: absolute;
  bottom: 220px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  height: 28px;
  display: flex;
  align-items: center;
  pointer-events: none;
}
.scene-label {
  font-family: 'ZCOOL KuaiLe', var(--font-body);
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.88);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.3);
  white-space: nowrap;
}
.home-page:not(.night) .scene-label {
  color: rgba(55, 40, 28, 0.78);
  text-shadow: 0 1px 6px rgba(255, 255, 255, 0.6);
}
.scene-text-enter-active { transition: opacity 0.3s ease, transform 0.3s var(--ease-out-expo); }
.scene-text-leave-active { transition: opacity 0.2s ease; position: absolute; }
.scene-text-enter-from { opacity: 0; transform: translateY(4px); }
.scene-text-leave-to { opacity: 0; }

/* ═══════ Scene Dots ═══════ */
.scene-dots {
  position: absolute;
  bottom: 196px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  display: flex;
  gap: 6px;
  pointer-events: auto;
}
.scene-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transition: background 0.3s ease, transform 0.2s ease;
  cursor: pointer;
}
.scene-dot.active {
  background: rgba(255, 255, 255, 0.9);
  transform: scale(1.3);
}
.home-page.night .scene-dot { background: rgba(200, 210, 255, 0.35); }
.home-page.night .scene-dot.active { background: rgba(200, 210, 255, 0.9); }

.conn-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger-soft);
  transition: background var(--duration-normal);
  margin-bottom: 4px;
}
.conn-dot.online {
  background: var(--success-soft);
}

/* ═══════ Activity Card ═══════ */
.activity-card {
  position: absolute;
  top: max(100px, calc(env(safe-area-inset-top, 44px) + 60px));
  left: 50%;
  transform: translateX(-50%);
  z-index: 12;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 14px 20px;
  min-width: 220px;
  max-width: 280px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}
.home-page.night .activity-card {
  background: rgba(42, 37, 32, 0.88);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.activity-title {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 8px;
  letter-spacing: 0.06em;
}
.home-page.night .activity-title {
  color: rgba(180, 170, 160, 0.7);
}
.activity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}
.activity-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
}
.activity-text {
  font-size: 0.82rem;
  color: var(--text-warm);
  line-height: 1.4;
}
.home-page.night .activity-text {
  color: var(--bg-cream);
}

.activity-enter-active { transition: all 0.6s var(--ease-out-expo); }
.activity-leave-active { transition: all 0.4s ease; }
.activity-enter-from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
.activity-leave-to { opacity: 0; transform: translateX(-50%) translateY(-5px); }

/* ═══════ Speech Bubble ═══════ */
.speech-bubble {
  position: absolute;
  top: max(90px, calc(env(safe-area-inset-top, 44px) + 50px));
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 20px;
  padding: 10px 20px;
  max-width: 260px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
.speech-bubble p {
  font-size: 0.9rem;
  color: var(--text-warm);
  line-height: 1.6;
  text-align: center;
}
.bubble-tail {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 8px;
  background: rgba(255, 255, 255, 0.92);
  clip-path: polygon(0 0, 100% 0, 50% 100%);
}
.home-page.night .speech-bubble {
  background: rgba(42, 37, 32, 0.92);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.home-page.night .speech-bubble p { color: var(--bg-cream); }
.home-page.night .bubble-tail { background: rgba(42, 37, 32, 0.92); }

.bubble-enter-active { transition: all 0.5s var(--ease-out-expo); }
.bubble-leave-active { transition: all 0.3s ease; }
.bubble-enter-from { opacity: 0; transform: translateX(-50%) translateY(10px) scale(0.9); }
.bubble-leave-to { opacity: 0; transform: translateX(-50%) translateY(-5px); }

/* ═══════ Loading ═══════ */
.loading-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  z-index: 20;
  background: var(--bg-darker);
}
.loading-glow {
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, var(--accent-warm-glow) 0%, transparent 70%);
  border-radius: 50%;
  animation: breathe 3s ease-in-out infinite;
}
.loading-text {
  font-size: 0.9rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
}
</style>
