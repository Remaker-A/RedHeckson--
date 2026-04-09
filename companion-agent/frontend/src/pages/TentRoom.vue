<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import { useWebSocket } from '../composables/useWebSocket'
import type { RoomScene, BiasType } from '../composables/useApi'

const router = useRouter()
const store = useCompanionStore()
const { on, connected } = useWebSocket()

on('personality_update', () => {
  store.fetchPersonality()
})

const loaded = ref(false)
const showNoteList = ref(false)
const showNoteDetail = ref(false)
const activeNoteIndex = ref(0)
const showMessage = ref(false)
const messageText = ref('')
const selectedMood = ref('')
const messageSent = ref(false)
const scene = computed<RoomScene>(() => store.room?.scene ?? 'tidy')

const showPersonality = ref(false)
const editBias = ref<BiasType>('decisive')
const editVoice = ref('')
const personalitySaving = ref(false)
const personalityPresetRows = computed(() => store.presets.filter(p => p.key !== 'custom'))

async function openPersonalityPanel() {
  await store.checkSoul()
  await Promise.all([store.fetchPersonality(), store.fetchPresets()])
  editBias.value = (store.soul?.bias as BiasType) || 'decisive'
  editVoice.value = store.personality?.voice_style ?? ''
  showPersonality.value = true
}

function pickPresetBias(key: BiasType) {
  editBias.value = key
  const row = store.presets.find(p => p.key === key)
  if (row?.voice_style) editVoice.value = row.voice_style
}

async function savePersonalityEdits() {
  personalitySaving.value = true
  try {
    await store.updatePersonality({
      bias: editBias.value,
      voice_style: editVoice.value,
    })
    showPersonality.value = false
  } catch {
    /* 保持面板打开 */
  } finally {
    personalitySaving.value = false
  }
}

const moods = [
  { value: 'calm', emoji: '😌', label: '平静' },
  { value: 'tired', emoji: '😮‍💨', label: '疲惫' },
  { value: 'happy', emoji: '😊', label: '开心' },
  { value: 'anxious', emoji: '😰', label: '焦虑' },
  { value: 'lonely', emoji: '🫠', label: '孤独' },
  { value: 'excited', emoji: '✨', label: '期待' },
]

const sceneConfig: Record<RoomScene, {
  bg: string
  tentFabric: string
  lightColor: string
  lightIntensity: number
  creatureEyes: string
  creatureMood: string
  items: string[]
  particles: string
  ambientText: string
}> = {
  tidy: {
    bg: 'linear-gradient(180deg, #3D3530 0%, #2A2520 30%, #221E1A 100%)',
    tentFabric: 'rgba(232, 160, 76, 0.08)',
    lightColor: '#E8A04C',
    lightIntensity: 0.8,
    creatureEyes: 'content',
    creatureMood: 'reading',
    items: ['book', 'plant', 'lamp'],
    particles: 'dust-motes',
    ambientText: '温暖的灯光洒在整洁的帐篷里',
  },
  messy: {
    bg: 'linear-gradient(180deg, #2E2823 0%, #221E1A 30%, #1A1612 100%)',
    tentFabric: 'rgba(180, 140, 100, 0.05)',
    lightColor: '#C49A6C',
    lightIntensity: 0.4,
    creatureEyes: 'restless',
    creatureMood: 'fidgeting',
    items: ['papers', 'cup-tipped', 'clothes'],
    particles: 'none',
    ambientText: '东西堆在一起，灯光有些暗',
  },
  night: {
    bg: 'linear-gradient(180deg, #2A3045 0%, #1E2535 30%, #161C28 100%)',
    tentFabric: 'rgba(100, 130, 180, 0.06)',
    lightColor: '#C4A56C',
    lightIntensity: 0.6,
    creatureEyes: 'soft',
    creatureMood: 'awake-late',
    items: ['coffee', 'lamp-warm', 'blanket'],
    particles: 'stars',
    ambientText: '深夜了，帐篷里亮着灯，桌上多了一杯咖啡',
  },
  dusty: {
    bg: 'linear-gradient(180deg, #2A2725 0%, #1E1C1A 30%, #141210 100%)',
    tentFabric: 'rgba(100, 95, 90, 0.04)',
    lightColor: '#8A7E74',
    lightIntensity: 0.15,
    creatureEyes: 'dim',
    creatureMood: 'lonely',
    items: ['cobweb'],
    particles: 'dust-heavy',
    ambientText: '灯几乎灭了，帐篷里落了灰',
  },
  recovering: {
    bg: 'linear-gradient(180deg, #35302A 0%, #2A2520 30%, #1E1A16 100%)',
    tentFabric: 'rgba(232, 160, 76, 0.06)',
    lightColor: '#D4944A',
    lightIntensity: 0.55,
    creatureEyes: 'hopeful',
    creatureMood: 'tidying',
    items: ['broom', 'lamp-dim'],
    particles: 'dust-clearing',
    ambientText: '灯慢慢亮起来了，它在整理帐篷',
  },
}

const currentScene = computed(() => sceneConfig[scene.value])

onMounted(async () => {
  await Promise.all([
    store.checkSoul(),
    store.fetchRoom(),
    store.fetchNotes(),
    store.fetchStatus(),
    store.fetchPresets(),
    store.fetchPersonality(),
  ])
  loaded.value = true
})

on('state_change', (data) => {
  store.fetchRoom()
  store.fetchStatus()
  if (data.say_line) store.setLatestWords(data.say_line as string)
})

on('new_note', () => {
  store.fetchNotes()
})

const sortedNotes = computed(() =>
  [...store.notes].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
)

const activeNote = computed(() => sortedNotes.value[activeNoteIndex.value] ?? null)

function formatDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function openNoteDetail(index: number) {
  activeNoteIndex.value = index
  const note = sortedNotes.value[index]
  if (note) store.markNoteRead(note.id)
  showNoteDetail.value = true
}

function prevNote() {
  if (activeNoteIndex.value > 0) {
    activeNoteIndex.value--
    const note = sortedNotes.value[activeNoteIndex.value]
    if (note) store.markNoteRead(note.id)
  }
}
function nextNote() {
  if (activeNoteIndex.value < sortedNotes.value.length - 1) {
    activeNoteIndex.value++
    const note = sortedNotes.value[activeNoteIndex.value]
    if (note) store.markNoteRead(note.id)
  }
}

async function requestNewNote() {
  await store.triggerGenerateNote()
  activeNoteIndex.value = 0
  showNoteDetail.value = true
}

async function submitMessage() {
  const text = messageText.value.trim()
  if (!text && !selectedMood.value) return
  await store.sendMessageWithMood(text, selectedMood.value || undefined)
  messageSent.value = true
  setTimeout(() => {
    messageText.value = ''
    selectedMood.value = ''
    messageSent.value = false
    showMessage.value = false
  }, 1500)
}

function selectMood(mood: string) {
  selectedMood.value = selectedMood.value === mood ? '' : mood
}
</script>

<template>
  <div class="tent-room" :class="scene" :style="{ background: currentScene.bg }">

    <!-- ═══════ Tent Structure ═══════ -->
    <div class="tent-structure">
      <!-- Tent roof lines -->
      <svg class="tent-roof" viewBox="0 0 400 100" preserveAspectRatio="none">
        <path d="M0 100 L200 8 L400 100" fill="none" :stroke="currentScene.lightColor" stroke-width="1.5" opacity="0.2" />
        <path d="M20 100 L200 18 L380 100" :fill="currentScene.tentFabric" stroke="none" />
        <!-- Tent seam -->
        <line x1="200" y1="8" x2="200" y2="100" :stroke="currentScene.lightColor" stroke-width="0.5" opacity="0.1" />
      </svg>
      <!-- Tent side drapes -->
      <div class="tent-drape left" :style="{ borderColor: currentScene.lightColor }" />
      <div class="tent-drape right" :style="{ borderColor: currentScene.lightColor }" />
    </div>

    <!-- ═══════ Top bar ═══════ -->
    <div class="top-bar">
      <button type="button" class="personality-entry" title="它的说话方式" @click="openPersonalityPanel">
        说话方式
      </button>
      <div class="conn-dot" :class="{ online: connected }" />
    </div>

    <!-- ═══════ Main content ═══════ -->
    <Transition name="fade">
      <div v-if="loaded" class="room-content">

        <!-- Ambient text -->
        <p class="ambience">{{ currentScene.ambientText }}</p>

        <!-- ─── Scene Layer: Items ─── -->
        <div class="scene-layer">

          <!-- Ground / floor -->
          <div class="tent-floor" />

          <!-- Lamp -->
          <div class="item lamp" :class="scene">
            <div class="lamp-post" />
            <div class="lamp-shade" :style="{ boxShadow: `0 0 ${30 * currentScene.lightIntensity}px ${15 * currentScene.lightIntensity}px ${currentScene.lightColor}` }" />
            <div class="lamp-glow" :style="{ background: `radial-gradient(ellipse, ${currentScene.lightColor} 0%, transparent 70%)`, opacity: currentScene.lightIntensity * 0.5 }" />
          </div>

          <!-- Book (tidy) -->
          <div v-if="scene === 'tidy'" class="item book-stack">
            <div class="book b1" /><div class="book b2" /><div class="book b3" />
          </div>

          <!-- Plant (tidy) -->
          <div v-if="scene === 'tidy'" class="item plant">
            <div class="pot" />
            <div class="stem" /><div class="leaf l1" /><div class="leaf l2" />
          </div>

          <!-- Coffee (night) -->
          <div v-if="scene === 'night'" class="item coffee">
            <div class="mug" />
            <div class="mug-handle" />
            <div class="steam s1" /><div class="steam s2" /><div class="steam s3" />
          </div>

          <!-- Blanket (night) -->
          <div v-if="scene === 'night'" class="item blanket" />

          <!-- Scattered papers (messy) -->
          <div v-if="scene === 'messy'" class="item papers">
            <div class="paper p1" /><div class="paper p2" /><div class="paper p3" />
          </div>

          <!-- Tipped cup (messy) -->
          <div v-if="scene === 'messy'" class="item tipped-cup">
            <div class="cup-body" /><div class="spill" />
          </div>

          <!-- Cobweb (dusty) -->
          <div v-if="scene === 'dusty'" class="item cobweb">
            <svg viewBox="0 0 60 60" width="60" height="60">
              <path d="M0 0 Q30 15 60 0" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.5" />
              <path d="M0 0 Q15 30 0 60" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="0.5" />
              <path d="M0 0 L30 30" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="0.5" />
            </svg>
          </div>

          <!-- Broom (recovering) -->
          <div v-if="scene === 'recovering'" class="item broom">
            <div class="broom-handle" />
            <div class="broom-head" />
          </div>

          <!-- ─── Creature ─── -->
          <div class="creature-area">
            <div class="creature" :class="[scene, currentScene.creatureMood]">
              <div class="creature-body">
                <div class="eye left" :class="currentScene.creatureEyes" />
                <div class="eye right" :class="currentScene.creatureEyes" />
              </div>
              <div class="creature-glow" :style="{ background: `radial-gradient(circle, ${currentScene.lightColor}40 0%, transparent 70%)` }" />
              <!-- Shadow -->
              <div class="creature-shadow" />
            </div>
          </div>
        </div>

        <!-- ─── Latest words ─── -->
        <Transition name="fade">
          <p v-if="store.latestWords" class="latest-words">"{{ store.latestWords }}"</p>
        </Transition>

        <!-- ─── Note corner hint ─── -->
        <div v-if="sortedNotes.length > 0" class="note-corner" @click="showNoteList = true">
          <div class="note-icon-wrap">
            <div class="note-paper" />
            <span v-if="store.unreadNoteCount > 0" class="unread-dot" />
          </div>
          <span class="note-hint">它写了{{ sortedNotes.length }}张纸条</span>
        </div>

        <!-- ─── Particle overlay ─── -->
        <div class="particles" :class="currentScene.particles">
          <span v-for="i in 12" :key="i" class="particle" :style="{ '--i': i }" />
        </div>

        <!-- ═══════ Bottom Nav ═══════ -->
        <nav class="bottom-nav">
          <button class="nav-btn" @click="showNoteList = true">
            <span class="nav-icon-wrap">
              <span class="nav-icon">&#9998;</span>
              <span v-if="store.unreadNoteCount > 0" class="nav-badge">{{ store.unreadNoteCount }}</span>
            </span>
            <span class="nav-label">纸条</span>
          </button>
          <button class="nav-btn" @click="showMessage = true">
            <span class="nav-icon-wrap">
              <span class="nav-icon">&#9993;</span>
            </span>
            <span class="nav-label">留言</span>
          </button>
          <button class="nav-btn" @click="router.push('/desktop')">
            <span class="nav-icon-wrap">
              <span class="nav-icon">&#9202;</span>
            </span>
            <span class="nav-label">时光</span>
          </button>
          <button class="nav-btn" @click="openPersonalityPanel">
            <span class="nav-icon-wrap">
              <span class="nav-icon">&#9881;</span>
            </span>
            <span class="nav-label">说话方式</span>
          </button>
        </nav>
      </div>

      <!-- Loading -->
      <div v-else class="loading">
        <div class="loading-tent">
          <div class="tent-loading-shape" />
        </div>
        <p>掀开帐篷帘子...</p>
      </div>
    </Transition>

    <!-- ═══════ Note List Overlay ═══════ -->
    <Transition name="slide-up">
      <div v-if="showNoteList" class="overlay" @click.self="showNoteList = false">
        <div class="note-list-panel">
          <div class="panel-handle" />
          <div class="note-list-header">
            <h3>它的纸条</h3>
            <button
              class="generate-btn"
              :disabled="store.generatingNote"
              @click="requestNewNote"
            >
              {{ store.generatingNote ? '它在想...' : '让它写一张' }}
            </button>
          </div>

          <div v-if="sortedNotes.length === 0" class="note-empty">
            <p>帐篷里还没有纸条</p>
            <p class="note-empty-sub">它可能还在想要对你说什么</p>
          </div>

          <div v-else class="note-list-scroll">
            <button
              v-for="(note, idx) in sortedNotes"
              :key="note.id"
              class="note-list-item"
              :class="{ unread: !store.readNoteIds.has(note.id) }"
              @click="openNoteDetail(idx)"
            >
              <div class="note-item-paper" />
              <div class="note-item-content">
                <span class="note-item-text">{{ note.content.slice(0, 40) }}{{ note.content.length > 40 ? '...' : '' }}</span>
                <span class="note-item-date">{{ formatDate(note.created_at) }} {{ formatTime(note.created_at) }}</span>
              </div>
              <span v-if="!store.readNoteIds.has(note.id)" class="note-item-dot" />
            </button>
          </div>

          <button class="panel-close" @click="showNoteList = false">收起</button>
        </div>
      </div>
    </Transition>

    <!-- ═══════ Note Detail Overlay ═══════ -->
    <Transition name="slide-up">
      <div v-if="showNoteDetail && activeNote" class="overlay" @click.self="showNoteDetail = false">
        <div class="note-detail-card">
          <!-- Paper texture bg -->
          <div class="note-texture" />

          <div class="note-detail-nav">
            <button class="note-nav-btn" :disabled="activeNoteIndex <= 0" @click="prevNote">‹</button>
            <span class="note-counter">{{ activeNoteIndex + 1 }} / {{ sortedNotes.length }}</span>
            <button class="note-nav-btn" :disabled="activeNoteIndex >= sortedNotes.length - 1" @click="nextNote">›</button>
          </div>

          <p class="note-detail-date">{{ formatDate(activeNote.created_at) }} {{ formatTime(activeNote.created_at) }}</p>
          <p class="note-detail-content">"{{ activeNote.content }}"</p>
          <p class="note-detail-sign">── 来自蓬蓬</p>

          <button class="note-detail-close" @click="showNoteDetail = false">收起</button>
        </div>
      </div>
    </Transition>

    <!-- ═══════ Personality / 说话方式 ═══════ -->
    <Transition name="slide-up">
      <div v-if="showPersonality" class="overlay" @click.self="showPersonality = false">
        <div class="personality-panel" @click.stop>
          <div class="panel-handle" />
          <h3 class="personality-title">它的说话方式</h3>
          <p class="personality-hint">选一个基调，再在下面微调具体说法。</p>
          <div class="personality-preset-grid">
            <button
              v-for="row in personalityPresetRows"
              :key="row.key"
              type="button"
              class="personality-preset-chip"
              :class="{ active: editBias === row.key }"
              @click="pickPresetBias(row.key as BiasType)"
            >
              {{ row.label }}
            </button>
            <button
              type="button"
              class="personality-preset-chip"
              :class="{ active: editBias === 'custom' }"
              @click="editBias = 'custom'"
            >
              自定义
            </button>
          </div>
          <label class="personality-label">风格描述（会写进它的自我认知）</label>
          <textarea
            v-model="editVoice"
            class="personality-textarea"
            rows="5"
            maxlength="600"
            placeholder="例如：话不多但很暖、喜欢用比喻、偶尔会轻轻开玩笑……"
          />
          <div class="personality-actions">
            <button type="button" class="personality-cancel" @click="showPersonality = false">取消</button>
            <button
              type="button"
              class="personality-save"
              :disabled="personalitySaving"
              @click="savePersonalityEdits"
            >
              {{ personalitySaving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ═══════ Message Overlay ═══════ -->
    <Transition name="slide-up">
      <div v-if="showMessage" class="overlay" @click.self="showMessage = false">
        <div class="message-panel" :class="{ sent: messageSent }">
          <div class="panel-handle" />

          <Transition name="fade" mode="out-in">
            <div v-if="messageSent" key="sent" class="message-sent-feedback">
              <div class="sent-check">✓</div>
              <p>它收到了</p>
            </div>

            <div v-else key="form" class="message-form">
              <p class="message-title">给它留点什么</p>

              <!-- Mood selector -->
              <div class="mood-selector">
                <p class="mood-label">此刻的心情</p>
                <div class="mood-grid">
                  <button
                    v-for="m in moods"
                    :key="m.value"
                    class="mood-btn"
                    :class="{ active: selectedMood === m.value }"
                    @click="selectMood(m.value)"
                  >
                    <span class="mood-emoji">{{ m.emoji }}</span>
                    <span class="mood-name">{{ m.label }}</span>
                  </button>
                </div>
              </div>

              <textarea
                v-model="messageText"
                class="message-input"
                placeholder="今天发生了什么..."
                rows="3"
              />

              <div class="message-actions">
                <button class="msg-cancel" @click="showMessage = false">算了</button>
                <button
                  class="msg-send"
                  :disabled="!messageText.trim() && !selectedMood"
                  @click="submitMessage"
                >
                  <span v-if="store.messageSending" class="send-loading" />
                  <span v-else>留下</span>
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ╔══════════════════════════════════════╗
   ║         TENT ROOM - 帐篷房间         ║
   ╚══════════════════════════════════════╝ */

.tent-room {
  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  transition: background 2s var(--ease-out-expo);
  overflow: hidden;
}

/* ═══════ Tent Structure ═══════ */
.tent-structure {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.tent-roof {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;
}

.tent-drape {
  position: absolute;
  bottom: 0;
  width: 1px;
  height: 100%;
  opacity: 0.06;
}
.tent-drape.left {
  left: 8%;
  border-left: 1px solid;
  transform: rotate(2deg);
  transform-origin: top;
}
.tent-drape.right {
  right: 8%;
  border-right: 1px solid;
  transform: rotate(-2deg);
  transform-origin: top;
}

/* Tent fabric sway animation */
.tent-room.tidy .tent-drape,
.tent-room.recovering .tent-drape {
  animation: sway 8s ease-in-out infinite;
}
.tent-room.night .tent-drape {
  animation: sway 12s ease-in-out infinite;
}

@keyframes sway {
  0%, 100% { transform: rotate(2deg); }
  50% { transform: rotate(-1deg); }
}
.tent-drape.right { animation-delay: -4s; }

/* ═══════ Top bar + personality panel ═══════ */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  z-index: 20;
  pointer-events: none;
}
.top-bar > * {
  pointer-events: auto;
}
.personality-entry {
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  opacity: 0.5;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 4px;
}
.personality-entry:hover {
  opacity: 0.95;
  color: var(--text-warm);
}
.conn-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger-soft);
  flex-shrink: 0;
  transition: background var(--duration-normal);
}
.conn-dot.online {
  background: var(--success-soft);
}
.personality-panel {
  width: 100%;
  max-width: 440px;
  max-height: 85vh;
  overflow-y: auto;
  background: var(--bg-dark);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.personality-title {
  font-size: 1.05rem;
  font-weight: 400;
  color: var(--text-light);
  text-align: center;
  letter-spacing: 0.06em;
  margin: 0;
}
.personality-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
  margin: 0;
  opacity: 0.75;
  line-height: 1.5;
}
.personality-preset-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: var(--space-xs);
}
.personality-preset-chip {
  font-size: 0.72rem;
  padding: 8px 12px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.personality-preset-chip:hover {
  border-color: rgba(232, 160, 76, 0.25);
  color: var(--text-light);
}
.personality-preset-chip.active {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
  color: var(--accent-warm);
}
.personality-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: var(--space-sm);
  opacity: 0.8;
}
.personality-textarea {
  width: 100%;
  padding: var(--space-md);
  font-size: 0.88rem;
  line-height: 1.75;
  color: var(--bg-cream);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-md);
  resize: none;
}
.personality-textarea:focus {
  outline: none;
  border-color: rgba(232, 160, 76, 0.25);
}
.personality-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  margin-top: var(--space-sm);
}
.personality-cancel {
  font-size: 0.82rem;
  padding: var(--space-sm) var(--space-md);
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
}
.personality-cancel:hover {
  color: var(--text-light);
}
.personality-save {
  font-size: 0.82rem;
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-full);
  border: 1px solid var(--accent-warm);
  color: var(--accent-warm);
  background: var(--accent-warm-dim);
  cursor: pointer;
}
.personality-save:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.personality-save:hover:not(:disabled) {
  background: rgba(232, 160, 76, 0.2);
}

/* ═══════ Room Content ═══════ */
.room-content {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 90px var(--space-lg) 130px;
  gap: var(--space-lg);
  z-index: 2;
}

.ambience {
  font-size: 0.82rem;
  color: var(--text-muted);
  text-align: center;
  letter-spacing: 0.06em;
  opacity: 0.7;
}

/* ═══════ Scene Layer ═══════ */
.scene-layer {
  position: relative;
  width: 100%;
  max-width: 360px;
  height: 280px;
  flex-shrink: 0;
}

.tent-floor {
  position: absolute;
  bottom: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06) 20%, rgba(255,255,255,0.06) 80%, transparent);
}

/* ─── Items ─── */
.item {
  position: absolute;
  transition: opacity 1.5s var(--ease-out-expo);
}

/* Lamp */
.lamp {
  bottom: 0;
  right: 15%;
}
.lamp-post {
  width: 2px;
  height: 50px;
  background: rgba(255,255,255,0.12);
  margin: 0 auto;
}
.lamp-shade {
  width: 24px;
  height: 14px;
  border-radius: 12px 12px 4px 4px;
  background: rgba(255,255,255,0.08);
  margin: 0 auto;
  transition: box-shadow 2s var(--ease-out-expo);
}
.lamp.dusty .lamp-shade { opacity: 0.3; }
.lamp-glow {
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 100px;
  pointer-events: none;
  animation: breathe 5s ease-in-out infinite;
  transition: opacity 2s;
}

/* Book stack */
.book-stack {
  bottom: 0;
  left: 18%;
}
.book {
  border-radius: 1px;
}
.book.b1 { width: 28px; height: 5px; background: #6B5B4E; margin-bottom: 1px; }
.book.b2 { width: 24px; height: 4px; background: #8B7355; margin-bottom: 1px; margin-left: 2px; }
.book.b3 { width: 30px; height: 5px; background: #5C6B5E; }

/* Plant */
.plant {
  bottom: 0;
  left: 35%;
}
.pot {
  width: 16px;
  height: 14px;
  background: #8B6B4E;
  border-radius: 2px 2px 4px 4px;
  margin: 0 auto;
}
.stem {
  width: 2px;
  height: 18px;
  background: #5A7E5A;
  margin: 0 auto;
  margin-top: -2px;
}
.leaf {
  position: absolute;
  width: 10px;
  height: 6px;
  background: #5A7E5A;
  border-radius: 50%;
}
.leaf.l1 { top: -16px; left: -4px; transform: rotate(-30deg); }
.leaf.l2 { top: -22px; right: -4px; transform: rotate(20deg); }
.plant .leaf {
  animation: leaf-sway 6s ease-in-out infinite;
}
.plant .leaf.l2 { animation-delay: -3s; }
@keyframes leaf-sway {
  0%, 100% { transform: rotate(-30deg); }
  50% { transform: rotate(-25deg); }
}

/* Coffee */
.coffee {
  bottom: 0;
  left: 25%;
}
.mug {
  width: 18px;
  height: 16px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px 2px 4px 4px;
  border: 1px solid rgba(255,255,255,0.08);
}
.mug-handle {
  position: absolute;
  right: -6px;
  top: 4px;
  width: 6px;
  height: 8px;
  border: 1px solid rgba(255,255,255,0.08);
  border-left: none;
  border-radius: 0 4px 4px 0;
}
.steam {
  position: absolute;
  width: 2px;
  background: rgba(255,255,255,0.08);
  border-radius: 1px;
  animation: steam-rise 3s ease-out infinite;
}
.steam.s1 { left: 5px; height: 12px; top: -14px; animation-delay: 0s; }
.steam.s2 { left: 9px; height: 10px; top: -12px; animation-delay: 1s; }
.steam.s3 { left: 13px; height: 14px; top: -16px; animation-delay: 2s; }

@keyframes steam-rise {
  0% { opacity: 0; transform: translateY(0) scaleX(1); }
  30% { opacity: 0.5; }
  100% { opacity: 0; transform: translateY(-20px) scaleX(2); }
}

/* Blanket */
.blanket {
  bottom: 0;
  right: 30%;
  width: 40px;
  height: 8px;
  background: rgba(100, 130, 180, 0.15);
  border-radius: 4px 4px 2px 2px;
  border: 1px solid rgba(100, 130, 180, 0.1);
}

/* Papers (messy) */
.papers {
  bottom: 0;
  left: 15%;
}
.paper {
  position: absolute;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: 1px;
}
.paper.p1 { width: 22px; height: 16px; bottom: 0; left: 0; transform: rotate(-8deg); }
.paper.p2 { width: 18px; height: 14px; bottom: 3px; left: 15px; transform: rotate(12deg); }
.paper.p3 { width: 20px; height: 15px; bottom: -2px; left: 8px; transform: rotate(-3deg); }

/* Tipped cup */
.tipped-cup {
  bottom: 0;
  right: 25%;
}
.cup-body {
  width: 14px;
  height: 12px;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  transform: rotate(70deg);
  transform-origin: bottom left;
}
.spill {
  position: absolute;
  bottom: -1px;
  left: 10px;
  width: 20px;
  height: 4px;
  background: rgba(180, 140, 100, 0.1);
  border-radius: 50%;
}

/* Cobweb */
.cobweb {
  top: 10px;
  right: 12%;
  opacity: 0.6;
}

/* Broom */
.broom {
  bottom: 0;
  left: 20%;
  transform: rotate(-15deg);
  transform-origin: bottom center;
}
.broom-handle {
  width: 3px;
  height: 45px;
  background: rgba(180, 140, 100, 0.2);
  margin: 0 auto;
  border-radius: 1px;
}
.broom-head {
  width: 16px;
  height: 10px;
  background: rgba(180, 140, 100, 0.15);
  border-radius: 2px 2px 0 0;
  margin: 0 auto;
}

/* ═══════ Creature ═══════ */
.creature-area {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
}

.creature {
  position: relative;
  width: 56px;
  height: 56px;
  animation: float 6s ease-in-out infinite;
}

.creature.dusty { animation-duration: 10s; }
.creature.night { animation-duration: 8s; }

.creature-body {
  width: 100%;
  height: 100%;
  border-radius: 50% 50% 48% 48%;
  background: radial-gradient(circle at 38% 38%, #E8A04C 0%, #C47D35 60%, #A0652A 100%);
  position: relative;
  transition: all 2s var(--ease-out-expo);
}

.tent-room.dusty .creature-body {
  background: radial-gradient(circle at 38% 38%, #9A8A74 0%, #7A6A5A 60%, #5A4A3A 100%);
  opacity: 0.6;
}

.tent-room.night .creature-body {
  background: radial-gradient(circle at 38% 38%, #C4A56C 0%, #A48B55 60%, #8A7545 100%);
}

/* Eyes */
.eye {
  position: absolute;
  top: 40%;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--bg-darker);
  transition: all 1s var(--ease-out-expo);
}
.eye.left { left: 32%; }
.eye.right { right: 32%; }

.eye.content { height: 3px; border-radius: 3px; top: 42%; }
.eye.restless { animation: blink-restless 2s ease-in-out infinite; }
.eye.soft { height: 2px; border-radius: 2px; top: 44%; opacity: 0.7; }
.eye.dim { opacity: 0.3; height: 2px; }
.eye.hopeful { animation: blink-slow 4s ease-in-out infinite; }

@keyframes blink-restless {
  0%, 85%, 100% { transform: scaleY(1); }
  90% { transform: scaleY(0.1); }
}
@keyframes blink-slow {
  0%, 90%, 100% { transform: scaleY(1); }
  93% { transform: scaleY(0.1); }
}

.creature-glow {
  position: absolute;
  inset: -24px;
  border-radius: 50%;
  animation: breathe 4s ease-in-out infinite;
  pointer-events: none;
  transition: opacity 2s;
}

.creature-shadow {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 6px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 50%;
  animation: shadow-pulse 6s ease-in-out infinite;
}
@keyframes shadow-pulse {
  0%, 100% { transform: translateX(-50%) scaleX(1); opacity: 0.15; }
  50% { transform: translateX(-50%) scaleX(0.85); opacity: 0.1; }
}

/* ═══════ Particles ═══════ */
.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 1;
}
.particle {
  position: absolute;
  border-radius: 50%;
  opacity: 0;
}

.particles.dust-motes .particle {
  width: 2px;
  height: 2px;
  background: rgba(232, 160, 76, 0.2);
  animation: dust-float 15s linear infinite;
  animation-delay: calc(var(--i) * -1.2s);
  left: calc(var(--i) * 8%);
  top: calc(20% + var(--i) * 5%);
}
.particles.dust-heavy .particle {
  width: 3px;
  height: 3px;
  background: rgba(180, 170, 160, 0.15);
  animation: dust-fall 10s linear infinite;
  animation-delay: calc(var(--i) * -0.8s);
  left: calc(var(--i) * 8%);
}
.particles.dust-clearing .particle {
  width: 2px;
  height: 2px;
  background: rgba(232, 160, 76, 0.15);
  animation: dust-clear 8s ease-out infinite;
  animation-delay: calc(var(--i) * -0.6s);
  left: calc(var(--i) * 8%);
  bottom: 30%;
}
.particles.stars .particle {
  width: 1.5px;
  height: 1.5px;
  background: rgba(200, 210, 230, 0.3);
  animation: twinkle 6s ease-in-out infinite;
  animation-delay: calc(var(--i) * -0.5s);
  left: calc(5% + var(--i) * 7.5%);
  top: calc(5% + var(--i) * 3%);
}

@keyframes dust-float {
  0% { opacity: 0; transform: translate(0, 0); }
  10% { opacity: 0.4; }
  90% { opacity: 0.4; }
  100% { opacity: 0; transform: translate(30px, -60px); }
}
@keyframes dust-fall {
  0% { opacity: 0; transform: translateY(-20px); }
  10% { opacity: 0.3; }
  90% { opacity: 0.2; }
  100% { opacity: 0; transform: translateY(100vh); }
}
@keyframes dust-clear {
  0% { opacity: 0.3; transform: translate(0, 0); }
  100% { opacity: 0; transform: translate(40px, -40px); }
}
@keyframes twinkle {
  0%, 100% { opacity: 0.1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.4); }
}

/* ═══════ Latest Words ═══════ */
.latest-words {
  font-size: 1.05rem;
  color: var(--text-light);
  text-align: center;
  letter-spacing: 0.06em;
  line-height: 1.8;
  animation: float 10s ease-in-out infinite;
}

/* ═══════ Note Corner ═══════ */
.note-corner {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out-expo);
  border: 1px solid rgba(255,255,255,0.04);
}
.note-corner:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255,255,255,0.08);
}

.note-icon-wrap {
  position: relative;
  width: 20px;
  height: 24px;
}
.note-paper {
  width: 100%;
  height: 100%;
  background: var(--paper-yellow);
  border-radius: 1px;
  opacity: 0.6;
  transform: rotate(-3deg);
}
.unread-dot {
  position: absolute;
  top: -3px;
  right: -3px;
  width: 7px;
  height: 7px;
  background: var(--accent-warm);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--accent-warm-glow);
}

.note-hint {
  font-size: 0.82rem;
  color: var(--text-muted);
}

/* ═══════ Bottom Nav ═══════ */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: var(--space-2xl);
  padding: var(--space-lg) var(--space-lg) var(--space-xl);
  background: linear-gradient(transparent, rgba(20,18,16,0.95) 50%);
  z-index: 5;
}

.nav-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: transform var(--duration-fast) var(--ease-out-expo);
}
.nav-btn:active { transform: scale(0.9); }

.nav-icon-wrap {
  position: relative;
  font-size: 1.3rem;
  line-height: 1;
}
.nav-icon {
  opacity: 0.7;
  transition: opacity var(--duration-fast);
}
.nav-btn:hover .nav-icon { opacity: 1; }

.nav-badge {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 16px;
  height: 16px;
  font-size: 0.65rem;
  font-weight: 500;
  line-height: 16px;
  text-align: center;
  background: var(--accent-warm);
  color: var(--bg-darker);
  border-radius: var(--radius-full);
  padding: 0 4px;
}

.nav-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

/* ═══════ Loading ═══════ */
.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
}
.tent-loading-shape {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--accent-warm-glow) 0%, transparent 70%);
  animation: breathe 2s ease-in-out infinite;
}
.loading p {
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* ═══════ Overlays (shared) ═══════ */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 20;
  padding: 0;
}

.panel-handle {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: rgba(255,255,255,0.12);
  margin: 0 auto var(--space-md);
}

/* ═══════ Note List Panel ═══════ */
.note-list-panel {
  width: 100%;
  max-width: 440px;
  max-height: 70vh;
  background: var(--bg-dark);
  border: 1px solid rgba(255,255,255,0.06);
  border-bottom: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.note-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.note-list-header h3 {
  font-size: 1rem;
  font-weight: 400;
  color: var(--text-light);
  letter-spacing: 0.04em;
}

.generate-btn {
  padding: 6px 14px;
  font-size: 0.8rem;
  color: var(--accent-warm);
  border: 1px solid rgba(232,160,76,0.3);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.generate-btn:hover:not(:disabled) {
  background: var(--accent-warm-dim);
  border-color: var(--accent-warm);
}
.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.note-empty {
  padding: var(--space-xl) 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.9rem;
}
.note-empty-sub {
  font-size: 0.8rem;
  opacity: 0.5;
  margin-top: var(--space-sm);
}

.note-list-scroll {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-height: 50vh;
  padding-right: var(--space-xs);
}

.note-list-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  text-align: left;
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.note-list-item:hover {
  background: rgba(255,255,255,0.04);
  border-color: rgba(255,255,255,0.08);
}
.note-list-item.unread {
  border-color: rgba(232,160,76,0.15);
}

.note-item-paper {
  width: 18px;
  height: 22px;
  min-width: 18px;
  background: var(--paper-yellow);
  border-radius: 1px;
  opacity: 0.5;
}

.note-item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.note-item-text {
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note-item-date {
  font-size: 0.72rem;
  color: var(--text-muted);
  opacity: 0.6;
}

.note-item-dot {
  width: 6px;
  height: 6px;
  min-width: 6px;
  border-radius: 50%;
  background: var(--accent-warm);
}

.panel-close {
  padding: var(--space-sm);
  font-size: 0.8rem;
  color: var(--text-muted);
  text-align: center;
  border-radius: var(--radius-sm);
  transition: color var(--duration-fast);
}
.panel-close:hover { color: var(--text-light); }

/* ═══════ Note Detail Card ═══════ */
.note-detail-card {
  position: relative;
  width: 100%;
  max-width: 400px;
  background: var(--paper-yellow);
  color: var(--text-warm);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-xl) var(--space-lg) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  font-family: var(--font-mono);
  overflow: hidden;
  margin: 0 var(--space-lg);
}

.note-texture {
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(transparent, transparent 27px, rgba(0,0,0,0.03) 27px, rgba(0,0,0,0.03) 28px);
  pointer-events: none;
}

.note-detail-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
  position: relative;
  z-index: 1;
}
.note-nav-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0,0,0,0.06);
  color: var(--text-warm);
  font-size: 1.1rem;
  line-height: 28px;
  text-align: center;
  transition: all var(--duration-fast);
}
.note-nav-btn:hover:not(:disabled) { background: rgba(0,0,0,0.1); }
.note-nav-btn:disabled { opacity: 0.2; cursor: not-allowed; }
.note-counter {
  font-size: 0.75rem;
  opacity: 0.4;
}

.note-detail-date {
  font-size: 0.82rem;
  opacity: 0.5;
  position: relative;
  z-index: 1;
}

.note-detail-content {
  font-size: 1rem;
  line-height: 2;
  white-space: pre-line;
  position: relative;
  z-index: 1;
}

.note-detail-sign {
  font-size: 0.78rem;
  opacity: 0.4;
  text-align: right;
  margin-top: var(--space-sm);
  position: relative;
  z-index: 1;
}

.note-detail-close {
  align-self: flex-end;
  padding: var(--space-sm) var(--space-md);
  font-size: 0.82rem;
  color: var(--text-warm);
  opacity: 0.4;
  border-radius: var(--radius-sm);
  transition: opacity var(--duration-fast);
  position: relative;
  z-index: 1;
}
.note-detail-close:hover { opacity: 0.8; }

/* ═══════ Message Panel ═══════ */
.message-panel {
  width: 100%;
  max-width: 440px;
  background: var(--bg-dark);
  border: 1px solid rgba(255,255,255,0.06);
  border-bottom: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  transition: all var(--duration-normal) var(--ease-out-expo);
}

.message-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.message-title {
  font-size: 1.05rem;
  color: var(--text-light);
  text-align: center;
  letter-spacing: 0.04em;
}

/* Mood selector */
.mood-selector {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.mood-label {
  font-size: 0.78rem;
  color: var(--text-muted);
  opacity: 0.6;
}
.mood-grid {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.mood-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all var(--duration-fast) var(--ease-out-expo);
  min-width: 52px;
}
.mood-btn:hover {
  border-color: rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.03);
}
.mood-btn.active {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
}
.mood-emoji {
  font-size: 1.2rem;
  line-height: 1;
}
.mood-name {
  font-size: 0.65rem;
  color: var(--text-muted);
}
.mood-btn.active .mood-name { color: var(--accent-warm); }

.message-input {
  width: 100%;
  padding: var(--space-md);
  font-size: 0.92rem;
  line-height: 1.8;
  color: var(--bg-cream);
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-md);
  resize: none;
  transition: border-color var(--duration-normal);
}
.message-input:focus {
  border-color: rgba(232,160,76,0.25);
}

.message-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}
.msg-cancel {
  padding: var(--space-sm) var(--space-md);
  font-size: 0.85rem;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
}
.msg-send {
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.85rem;
  color: var(--accent-warm);
  border: 1px solid var(--accent-warm);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast);
  min-width: 60px;
}
.msg-send:hover:not(:disabled) {
  background: var(--accent-warm);
  color: var(--bg-darker);
}
.msg-send:disabled {
  opacity: 0.25;
  cursor: not-allowed;
}

.send-loading {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--accent-warm);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Sent feedback */
.message-sent-feedback {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-xl) 0;
}
.sent-check {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent-warm-dim);
  color: var(--accent-warm);
  font-size: 1.4rem;
  line-height: 48px;
  text-align: center;
  animation: pop-in 0.4s var(--ease-out-expo);
}
@keyframes pop-in {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.message-sent-feedback p {
  font-size: 0.9rem;
  color: var(--text-muted);
}

/* ═══════ Settings Panel ═══════ */
.settings-panel {
  width: 100%;
  max-width: 440px;
  max-height: 80vh;
  overflow-y: auto;
  background: var(--bg-dark);
  border: 1px solid rgba(255,255,255,0.06);
  border-bottom: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  transition: all var(--duration-normal) var(--ease-out-expo);
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.settings-title {
  font-size: 1.05rem;
  color: var(--text-light);
  text-align: center;
  letter-spacing: 0.04em;
}

.settings-presets {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-xs);
}

.settings-preset-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-md);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 2px;
  transition: all var(--duration-fast) var(--ease-out-expo);
  background: rgba(255,255,255,0.02);
}
.settings-preset-btn:hover {
  border-color: rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
}
.settings-preset-btn.active {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
}
.sp-label {
  font-size: 0.9rem;
  color: var(--bg-cream);
}
.settings-preset-btn.active .sp-label {
  color: var(--accent-warm);
}
.sp-desc {
  font-size: 0.72rem;
  color: var(--text-muted);
  line-height: 1.3;
}

.settings-voice-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.settings-voice-label {
  font-size: 0.78rem;
  color: var(--text-muted);
  opacity: 0.6;
}
.settings-textarea {
  width: 100%;
  padding: var(--space-md);
  font-size: 0.88rem;
  line-height: 1.7;
  color: var(--bg-cream);
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-md);
  resize: none;
  transition: border-color var(--duration-normal);
}
.settings-textarea:focus {
  border-color: rgba(232,160,76,0.25);
}
.settings-textarea::placeholder {
  color: var(--text-muted);
  opacity: 0.5;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}
</style>
