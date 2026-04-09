<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'

const router = useRouter()
const store = useCompanionStore()
const isNight = computed(() => store.isNight)

const loaded = ref(false)
const showWrite = ref(false)
const noteText = ref('')
const selectedMood = ref('')
const sendingNote = ref(false)
const sentFeedback = ref(false)

interface DisplayNote {
  id: string
  content: string
  date: string
  time: string
  author: 'agent' | 'user'
  color: string
  sortKey: number
}

// Local user messages (not returned by API, stored locally)
const userMessages = ref<DisplayNote[]>([])

const moods = [
  { value: 'calm', emoji: '😌', label: '平静' },
  { value: 'tired', emoji: '😮‍💨', label: '疲惫' },
  { value: 'happy', emoji: '😊', label: '开心' },
  { value: 'anxious', emoji: '😰', label: '焦虑' },
  { value: 'lonely', emoji: '🫠', label: '孤独' },
  { value: 'excited', emoji: '✨', label: '期待' },
]

function formatDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const displayNotes = computed<DisplayNote[]>(() => {
  const agentNotes: DisplayNote[] = store.notes.map(n => ({
    id: n.id,
    content: n.content,
    date: formatDate(n.created_at),
    time: formatTime(n.created_at),
    author: 'agent' as const,
    color: 'yellow',
    sortKey: new Date(n.created_at).getTime(),
  }))
  const all = [...agentNotes, ...userMessages.value]
  return all.sort((a, b) => b.sortKey - a.sortKey)
})

onMounted(async () => {
  const hasSoul = await store.checkSoul()
  if (!hasSoul) { router.replace('/soul'); return }
  await store.fetchNotes()
  loaded.value = true
})

async function submitNote() {
  const text = noteText.value.trim()
  if (!text) return
  sendingNote.value = true
  try {
    await store.sendMessageWithMood(text, selectedMood.value || undefined)
    // Add user message to local display immediately
    const now = new Date()
    userMessages.value.unshift({
      id: `user-${Date.now()}`,
      content: text,
      date: formatDate(now.toISOString()),
      time: formatTime(now.toISOString()),
      author: 'user',
      color: 'blue',
      sortKey: now.getTime(),
    })
    sentFeedback.value = true
    setTimeout(() => {
      noteText.value = ''
      selectedMood.value = ''
      sentFeedback.value = false
      showWrite.value = false
    }, 1200)
  } finally {
    sendingNote.value = false
  }
}

async function requestNewNote() {
  await store.triggerGenerateNote()
}

function selectMood(mood: string) {
  selectedMood.value = selectedMood.value === mood ? '' : mood
}
</script>

<template>
  <div class="notes-page" :class="{ night: isNight }">
    <header class="notes-header">
      <h1 class="notes-title">纸条</h1>
      <button
        class="gen-btn"
        :disabled="store.generatingNote"
        @click="requestNewNote"
      >
        {{ store.generatingNote ? '蓬蓬在想...' : '让蓬蓬写一张' }}
      </button>
    </header>

    <div v-if="loaded" class="notes-scroll">
      <!-- Empty state -->
      <div v-if="displayNotes.length === 0" class="empty-state">
        <div class="empty-icon">📄</div>
        <p class="empty-text">蓬蓬还没写纸条</p>
        <p class="empty-sub">它可能还在想要对你说什么</p>
      </div>

      <!-- Notes list (single column) -->
      <div v-else class="notes-list">
        <div
          v-for="note in displayNotes"
          :key="note.id"
          class="sticky-note"
          :class="[note.author, note.color]"
          @click="store.markNoteRead(note.id)"
        >
          <div class="note-pin">📌</div>
          <div class="note-date">{{ note.date }} {{ note.time }}</div>
          <p class="note-content">"{{ note.content }}"</p>
          <p v-if="note.author === 'agent'" class="note-sign">── 蓬蓬</p>
          <span v-if="!store.readNoteIds.has(note.id)" class="note-unread" />
        </div>
      </div>
    </div>

    <!-- Write note button (fixed at bottom) -->
    <div class="write-trigger">
      <button class="write-btn" @click="showWrite = true">
        ✏️ 贴一张便签
      </button>
    </div>

    <!-- Write note overlay -->
    <Transition name="slide-up">
      <div v-if="showWrite" class="write-overlay" @click.self="showWrite = false">
        <div class="write-panel" :class="{ sent: sentFeedback }">
          <div class="panel-handle" />

          <Transition name="fade" mode="out-in">
            <div v-if="sentFeedback" key="sent" class="sent-feedback">
              <div class="sent-check">✓</div>
              <p>蓬蓬收到了</p>
            </div>

            <div v-else key="form" class="write-form">
              <p class="write-title">贴一张便签给蓬蓬</p>

              <!-- Mood selector -->
              <div class="mood-row">
                <button
                  v-for="m in moods"
                  :key="m.value"
                  class="mood-chip"
                  :class="{ active: selectedMood === m.value }"
                  @click="selectMood(m.value)"
                >
                  <span class="mood-emoji">{{ m.emoji }}</span>
                  <span class="mood-name">{{ m.label }}</span>
                </button>
              </div>

              <div class="note-paper-input">
                <textarea
                  v-model="noteText"
                  class="note-textarea"
                  placeholder="写点什么..."
                  rows="4"
                  maxlength="500"
                />
              </div>

              <div class="write-actions">
                <button class="cancel-btn" @click="showWrite = false">算了</button>
                <button
                  class="submit-btn"
                  :disabled="!noteText.trim() || sendingNote"
                  @click="submitNote"
                >
                  {{ sendingNote ? '...' : '贴上去' }}
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>

    <div class="tab-spacer" />
  </div>
</template>

<style scoped>
.notes-page {
  min-height: 100dvh;
  background: #f5f0eb;
  display: flex;
  flex-direction: column;
  transition: background 0.8s ease;
}
.notes-page.night {
  background: var(--bg-dark);
}

/* ═══════ Header ═══════ */
.notes-header {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: max(16px, env(safe-area-inset-top, 16px)) 20px 12px;
  background: #f5f0eb;
  z-index: 10;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: background 0.8s ease, border-color 0.8s ease;
}
.notes-page.night .notes-header {
  background: var(--bg-dark);
  border-bottom-color: rgba(255, 255, 255, 0.04);
}
.notes-title {
  font-family: var(--font-body);
  font-size: 1.2rem;
  font-weight: 400;
  color: var(--text-warm);
  letter-spacing: 0.04em;
}
.notes-page.night .notes-title {
  color: var(--text-light);
}
.gen-btn {
  font-size: 0.75rem;
  padding: 6px 14px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(180, 140, 80, 0.3);
  color: #8a6d3b;
  background: rgba(232, 160, 76, 0.1);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.notes-page.night .gen-btn {
  border-color: rgba(232, 160, 76, 0.3);
  color: var(--accent-warm);
  background: var(--accent-warm-dim);
}
.gen-btn:hover:not(:disabled) {
  background: rgba(232, 160, 76, 0.2);
}
.gen-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ═══════ Scroll area ═══════ */
.notes-scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md) var(--space-lg);
}

/* ═══════ Empty state ═══════ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl) 0;
  gap: var(--space-sm);
}
.empty-icon { font-size: 2.5rem; opacity: 0.4; }
.empty-text { font-size: 0.95rem; color: var(--text-warm); opacity: 0.6; }
.empty-sub { font-size: 0.8rem; color: var(--text-muted); opacity: 0.5; }
.notes-page.night .empty-text { color: var(--text-light); }

/* ═══════ Notes list ═══════ */
.notes-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* ═══════ Sticky note ═══════ */
.sticky-note {
  position: relative;
  padding: var(--space-lg) var(--space-lg) var(--space-md);
  border-radius: var(--radius-md);
  transition: transform var(--duration-fast) var(--ease-out-expo);
}
.sticky-note:active {
  transform: scale(0.98);
}

/* Agent notes - yellow paper */
.sticky-note.agent {
  background: linear-gradient(135deg, #F2E8D5 0%, #EBE0CC 100%);
  border: 1px solid rgba(200, 180, 140, 0.3);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}
.sticky-note.agent .note-date { color: #A09080; }
.sticky-note.agent .note-content { color: #4A3F35; }
.sticky-note.agent .note-sign { color: #B0A090; }

/* User notes - soft blue */
.sticky-note.user {
  background: linear-gradient(135deg, #D8E8F5 0%, #CEDBE8 100%);
  border: 1px solid rgba(140, 170, 200, 0.3);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}
.sticky-note.user .note-date { color: #8098B0; }
.sticky-note.user .note-content { color: #3A4A5A; }
.sticky-note.user .note-sign { color: #90A8C0; }

.note-pin {
  position: absolute;
  top: -4px;
  left: 16px;
  font-size: 0.9rem;
}

.note-date {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: var(--space-sm);
  letter-spacing: 0.04em;
}

.note-content {
  font-size: 0.92rem;
  color: var(--text-light);
  line-height: 1.8;
  letter-spacing: 0.02em;
}

.note-sign {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: var(--space-md);
  opacity: 0.6;
  text-align: right;
}

.note-unread {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-warm);
  box-shadow: 0 0 6px var(--accent-warm-glow);
}

/* ═══════ Write trigger ═══════ */
.write-trigger {
  position: fixed;
  bottom: 80px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  padding: var(--space-sm);
  z-index: 10;
}
.write-btn {
  padding: 10px 28px;
  font-size: 0.88rem;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.08);
  color: var(--text-warm);
  cursor: pointer;
  backdrop-filter: blur(12px);
  transition: all var(--duration-fast) var(--ease-out-expo);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}
.notes-page.night .write-btn {
  background: var(--bg-darker);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--text-light);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}
.write-btn:hover {
  border-color: var(--accent-warm);
  color: var(--accent-warm);
}

/* ═══════ Write overlay ═══════ */
.write-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 200;
}
.notes-page.night .write-overlay {
  background: rgba(0, 0, 0, 0.5);
}
.write-panel {
  width: 100%;
  max-width: 440px;
  background: #f5f0eb;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-bottom: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: var(--space-md) var(--space-lg) var(--space-xl);
}
.notes-page.night .write-panel {
  background: var(--bg-dark);
  border-color: rgba(255, 255, 255, 0.06);
}
.panel-handle {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  margin: 0 auto var(--space-lg);
}

.write-title {
  font-size: 1rem;
  color: var(--text-warm);
  text-align: center;
  margin-bottom: var(--space-md);
  letter-spacing: 0.04em;
}
.notes-page.night .write-title {
  color: var(--text-light);
}

/* ═══════ Mood grid ═══════ */
.mood-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: var(--space-md);
}
.mood-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.03);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.notes-page.night .mood-chip {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
}
.mood-chip.active {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
  color: var(--accent-warm);
}
.mood-emoji { font-size: 1rem; }

/* ═══════ Note paper input ═══════ */
.note-paper-input {
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-md);
  padding: 2px;
}
.notes-page.night .note-paper-input {
  background: rgba(242, 232, 213, 0.05);
  border-color: rgba(242, 232, 213, 0.1);
}
.note-textarea {
  width: 100%;
  padding: var(--space-md);
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-warm);
  background: transparent;
  border: none;
  resize: none;
}
.notes-page.night .note-textarea {
  color: var(--bg-cream);
}
.note-textarea::placeholder {
  color: var(--text-muted);
  opacity: 0.5;
}

/* ═══════ Actions ═══════ */
.write-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  margin-top: var(--space-md);
}
.cancel-btn {
  font-size: 14px;
  color: var(--text-muted);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer;
}
.submit-btn {
  font-size: 14px;
  padding: var(--space-sm) var(--space-xl);
  border-radius: var(--radius-full);
  border: 1px solid var(--accent-warm);
  color: var(--accent-warm);
  background: var(--accent-warm-dim);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.submit-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.submit-btn:hover:not(:disabled) {
  background: rgba(232, 160, 76, 0.2);
}

/* ═══════ Sent feedback ═══════ */
.sent-feedback {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-xl) 0;
  gap: var(--space-md);
}
.sent-check {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent-warm-dim);
  color: var(--accent-warm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}
.sent-feedback p {
  color: var(--text-light);
  font-size: 0.9rem;
}

.tab-spacer { height: 80px; flex-shrink: 0; }

/* ═══════ Slide-up ═══════ */
.slide-up-enter-active {
  transition: transform 0.4s var(--ease-out-expo), opacity 0.3s ease;
}
.slide-up-leave-active {
  transition: transform 0.3s ease, opacity 0.2s ease;
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateY(40%);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(30%);
}
</style>
