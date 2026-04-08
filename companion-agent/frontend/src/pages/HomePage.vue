<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import { useWebSocket } from '../composables/useWebSocket'

const router = useRouter()
const store = useCompanionStore()
const { on, connected } = useWebSocket()

const loaded = ref(false)
const isNight = ref(false)
const bubbleVisible = ref(false)
const bubbleText = ref('')
let bubbleTimer: ReturnType<typeof setTimeout> | undefined

function checkTime() {
  const h = new Date().getHours()
  isNight.value = h >= 18 || h < 6
}

function showBubble(text: string) {
  bubbleText.value = text
  bubbleVisible.value = true
  if (bubbleTimer) clearTimeout(bubbleTimer)
  bubbleTimer = setTimeout(() => { bubbleVisible.value = false }, 5000)
}

const characterState = computed(() => {
  const state = store.status?.state ?? 'idle'
  const creature = store.room?.details?.creature_state ?? 'reading'
  if (state === 'idle' || state === 'leaving') return 'sleeping'
  if (creature === 'lonely') return 'waiting'
  return creature
})

const characterImage = computed(() => {
  const state = characterState.value
  if (state === 'sleeping' || state === 'lonely') return '/assets/character/char-sleeping.png'
  // Reuse sleeping for now - more images can be added later
  return '/assets/character/char-sleeping.png'
})

const sceneImage = computed(() => {
  return isNight.value
    ? '/assets/scene/scene-night-cutout.png'
    : '/assets/scene/scene-day-cutout.png'
})

const lightIntensity = computed(() => {
  const light = store.room?.details?.light ?? 'warm'
  const map: Record<string, number> = {
    warm: 1, dim: 0.5, warm_low: 0.3, almost_off: 0.08, warming_up: 0.6,
  }
  return map[light] ?? 0.8
})

onMounted(async () => {
  const hasSoul = await store.checkSoul()
  if (!hasSoul) {
    router.replace('/soul')
    return
  }
  checkTime()
  await Promise.all([
    store.fetchRoom(),
    store.fetchNotes(),
    store.fetchStatus(),
    store.fetchPersonality(),
  ])
  loaded.value = true

  // Initial speech
  try {
    const resp = await fetch('/api/companion/speak', { method: 'POST' })
    const data = await resp.json()
    if (data.ok && data.say_line) showBubble(data.say_line)
  } catch { /* ignore */ }
})

// Time check interval
let timeInterval: ReturnType<typeof setInterval>
onMounted(() => { timeInterval = setInterval(checkTime, 60_000) })
onUnmounted(() => { clearInterval(timeInterval); if (bubbleTimer) clearTimeout(bubbleTimer) })

// WebSocket events
on('state_change', (data) => {
  store.fetchRoom()
  store.fetchStatus()
  if (data.say_line) showBubble(data.say_line as string)
})
on('personality_update', () => store.fetchPersonality())
on('new_note', () => store.fetchNotes())

function onCharacterTap() {
  fetch('/api/companion/speak', { method: 'POST' })
    .then(r => r.json())
    .then(d => { if (d.ok && d.say_line) showBubble(d.say_line) })
    .catch(() => {})
}
</script>

<template>
  <div class="home-page" :class="{ night: isNight }">
    <!-- Background -->
    <div class="bg-layer" />

    <!-- Stars (night only) -->
    <div v-if="isNight" class="stars-layer">
      <span v-for="i in 20" :key="i" class="star" :style="{
        top: Math.random() * 35 + '%',
        left: Math.random() * 100 + '%',
        width: (Math.random() * 2.5 + 1) + 'px',
        height: (Math.random() * 2.5 + 1) + 'px',
        animationDelay: (Math.random() * 3) + 's',
        animationDuration: (Math.random() * 2 + 2) + 's',
      }" />
      <div class="moon" />
    </div>

    <!-- Connection indicator -->
    <div class="conn-indicator">
      <div class="conn-dot" :class="{ online: connected }" />
    </div>

    <!-- Main content -->
    <Transition name="fade">
      <div v-if="loaded" class="scene-container">

        <!-- Title -->
        <h1 class="camp-title">My Little Camp</h1>

        <!-- Speech bubble -->
        <Transition name="bubble">
          <div v-if="bubbleVisible" class="speech-bubble">
            <p>{{ bubbleText }}</p>
            <div class="bubble-tail" />
          </div>
        </Transition>

        <!-- Scene wrapper -->
        <div class="scene-wrapper" @click="onCharacterTap">
          <!-- Scene image (tent + platform) -->
          <img
            :src="sceneImage"
            alt="帐篷场景"
            class="scene-img"
            draggable="false"
          />

          <!-- Character overlay -->
          <div class="character-layer">
            <img
              :src="characterImage"
              alt="角色"
              class="character-img"
              draggable="false"
            />
            <div class="character-shadow" />
          </div>

          <!-- Lantern glow -->
          <div
            class="lantern-glow"
            :style="{ opacity: lightIntensity * 0.7 }"
          />

          <!-- Inner tent warm light -->
          <div
            class="tent-inner-glow"
            :style="{ opacity: lightIntensity * 0.5 }"
          />
        </div>

        <!-- Status text -->
        <p class="status-text">
          {{ store.room?.details?.description || '帐篷里亮着灯' }}
        </p>

      </div>

      <!-- Loading state -->
      <div v-else class="loading-state">
        <div class="loading-glow" />
        <p class="loading-text">掀开帐篷帘子...</p>
      </div>
    </Transition>

    <!-- Bottom spacer for tab bar -->
    <div class="tab-spacer" />
  </div>
</template>

<style scoped>
.home-page {
  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

/* ═══════ Background ═══════ */
.bg-layer {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at 50% 40%, #f5e6d0 0%, #e8dcc8 50%, #d4c4a8 100%);
  transition: background 2s var(--ease-out-expo);
  z-index: 0;
}
.home-page.night .bg-layer {
  background: radial-gradient(ellipse at 50% 30%, #2a3a5a 0%, #1a2540 60%, #0f1520 100%);
}

/* ═══════ Stars ═══════ */
.stars-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
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

/* ═══════ Connection ═══════ */
.conn-indicator {
  position: fixed;
  top: 12px;
  right: 16px;
  z-index: 20;
}
.conn-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger-soft);
  transition: background var(--duration-normal);
}
.conn-dot.online {
  background: var(--success-soft);
}

/* ═══════ Scene Container ═══════ */
.scene-container {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: max(60px, env(safe-area-inset-top, 60px));
  width: 100%;
  max-width: 430px;
}

.camp-title {
  font-family: var(--font-display);
  font-size: 1.6rem;
  font-weight: 400;
  color: var(--text-warm);
  letter-spacing: 0.04em;
  margin-bottom: var(--space-md);
  text-align: center;
}
.home-page.night .camp-title {
  color: var(--bg-cream);
}

/* ═══════ Speech Bubble ═══════ */
.speech-bubble {
  position: relative;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 20px;
  padding: 10px 20px;
  margin-bottom: var(--space-sm);
  max-width: 260px;
  z-index: 10;
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
.home-page.night .speech-bubble p {
  color: var(--bg-cream);
}
.home-page.night .bubble-tail {
  background: rgba(42, 37, 32, 0.92);
}

.bubble-enter-active { transition: all 0.5s var(--ease-out-expo); }
.bubble-leave-active { transition: all 0.3s ease; }
.bubble-enter-from { opacity: 0; transform: translateY(10px) scale(0.9); }
.bubble-leave-to { opacity: 0; transform: translateY(-5px); }

/* ═══════ Scene Wrapper ═══════ */
.scene-wrapper {
  position: relative;
  width: 92%;
  max-width: 380px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.scene-img {
  width: 100%;
  height: auto;
  display: block;
  filter: drop-shadow(0 20px 40px rgba(0, 0, 0, 0.15));
  transition: filter 2s var(--ease-out-expo);
}
.home-page.night .scene-img {
  filter: drop-shadow(0 20px 60px rgba(232, 160, 76, 0.15));
}

/* ═══════ Character Layer ═══════ */
.character-layer {
  position: absolute;
  /* Position inside the tent opening - on the plaid blanket area */
  top: 38%;
  left: 50%;
  transform: translateX(-55%);
  width: 22%;
  z-index: 5;
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
.character-shadow {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 8px;
  background: radial-gradient(ellipse, rgba(60, 40, 20, 0.15) 0%, transparent 70%);
  border-radius: 50%;
}

/* ═══════ Light Effects ═══════ */
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
  pointer-events: none;
  animation: glow-pulse 3.5s ease-in-out infinite;
  z-index: 3;
}
@keyframes glow-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: var(--glow-base, 0.7); }
  50% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; }
}

.tent-inner-glow {
  position: absolute;
  top: 15%;
  left: 25%;
  width: 50%;
  height: 45%;
  background: radial-gradient(ellipse at 50% 40%,
    rgba(255, 200, 100, 0.12) 0%,
    transparent 70%
  );
  pointer-events: none;
  z-index: 2;
  mix-blend-mode: screen;
}

/* ═══════ Status Text ═══════ */
.status-text {
  font-size: 0.78rem;
  color: var(--text-muted);
  text-align: center;
  letter-spacing: 0.04em;
  margin-top: var(--space-md);
  opacity: 0.7;
  max-width: 280px;
  line-height: 1.6;
}
.home-page.night .status-text {
  color: var(--text-light);
  opacity: 0.5;
}

/* ═══════ Loading ═══════ */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  z-index: 2;
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

.tab-spacer {
  height: 80px;
  flex-shrink: 0;
}
</style>
