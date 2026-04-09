<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import type { SoulInput, BiasType } from '../composables/useApi'

const router = useRouter()
const store = useCompanionStore()

/* ---- Types ---- */
interface ChatMessage {
  role: 'agent' | 'user'
  text: string
  id: number
}

interface QuickReply {
  label: string
  value: string
}

interface BiasOption {
  key: BiasType
  label: string
  short_desc: string
}

/* ---- State ---- */
type Phase = 'intro' | 'chat' | 'done'
const phase = ref<Phase>('intro')
const messages = ref<ChatMessage[]>([])
const userInput = ref('')
const inputDisabled = ref(true)
const typing = ref(false)
const submitting = ref(false)
const firstWords = ref('')
const chatContainer = ref<HTMLElement | null>(null)
const quickReplies = ref<QuickReply[]>([])
const showBiasCards = ref(false)
let msgId = 0

/* ============================================================
 * Onboarding stages (5 rounds + bias selection)
 *
 * 1. open_share   — "现在的你，是什么样的？"
 * 2. struggle     — "最近有什么一直在心里转的事吗？"
 * 3. energy       — "什么事情会让你重新充满能量？"
 * 4. companion    — "你喜欢什么样的陪伴？"
 * 5. bias         — 选性格卡片
 * ============================================================ */
type Stage = 'greet' | 'open_share' | 'struggle' | 'energy' | 'companion' | 'bias' | 'closing'
const stage = ref<Stage>('greet')

/* ---- Progress (5 total steps) ---- */
const totalSteps = 5
const currentStep = ref(0)
const progress = computed(() => Math.round((currentStep.value / totalSteps) * 100))

/* ---- Collected data ---- */
const collectedStateWord = ref('')
const collectedStruggle = ref('')
const collectedBias = ref<BiasType | ''>('')
const collectedExtra = ref<string[]>([]) // energy + companion style for richer context

/* ---- Intro animation ---- */
const tentGlowing = ref(false)
onMounted(() => {
  setTimeout(() => { tentGlowing.value = true }, 600)
})

/* ---- Bias options ---- */
const biasOptions: BiasOption[] = [
  { key: 'decisive', label: '安静笃定派', short_desc: '在你犹豫时，它会先迈出那一步' },
  { key: 'adventurous', label: '好奇冒险家', short_desc: '在你害怕时，它会说"试试看"' },
  { key: 'slow_down', label: '慢半拍先生', short_desc: '在你着急时，它会说"不急"' },
  { key: 'warm_humor', label: '温柔段子手', short_desc: '在你沮丧时，它会找到事情好玩的那一面' },
  { key: 'night_owl', label: '深夜陪伴者', short_desc: '在深夜还亮着的灯旁，它多说两句' },
  { key: 'bookish', label: '小小哲学家', short_desc: '从一件小事能想到很远的地方' },
]

/* ============================================================
 * Chat helpers
 * ============================================================ */
function pushAgent(text: string): Promise<void> {
  return new Promise((resolve) => {
    typing.value = true
    scrollToBottom()
    const delay = Math.min(500 + text.length * 25, 1800)
    setTimeout(() => {
      messages.value = [...messages.value, { role: 'agent', text, id: ++msgId }]
      typing.value = false
      scrollToBottom()
      resolve()
    }, delay)
  })
}

function pushUser(text: string) {
  messages.value = [...messages.value, { role: 'user', text, id: ++msgId }]
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    chatContainer.value?.scrollTo({
      top: chatContainer.value.scrollHeight,
      behavior: 'smooth',
    })
  })
}

function enableInput(placeholder?: string) {
  inputDisabled.value = false
  if (placeholder) inputPlaceholder.value = placeholder
  nextTick(() => {
    const el = document.querySelector('.chat-input') as HTMLInputElement
    el?.focus()
  })
}

const inputPlaceholder = ref('说说看...')

function setQuickReplies(replies: QuickReply[]) {
  quickReplies.value = replies
  scrollToBottom()
}

function clearQuickReplies() {
  quickReplies.value = []
}

/* ============================================================
 * Text analysis helpers
 * ============================================================ */
const emotionKeywords: Record<string, string[]> = {
  '疲惫': ['累', '疲', '倦', '困', '撑', '熬', '没劲'],
  '迷茫': ['迷', '茫', '不知道', '方向', '看不清', '不确定', '没头绪'],
  '焦虑': ['焦', '急', '慌', '紧张', '压力', '担心', '害怕', '烦'],
  '兴奋': ['兴奋', '激动', '期待', '开心', '爽', '心动', '高兴'],
  '平静': ['平静', '安静', '还好', '挺好', '稳', '淡', '还行', '一般'],
  '孤独': ['孤', '寂', '一个人', '没人', '空', '冷清'],
  '纠结': ['纠结', '犹豫', '矛盾', '两难', '选择', '取舍'],
  '充实': ['充实', '忙', '充', '饱满', '节奏快'],
}

function extractStateWord(text: string): string {
  const stripped = text.replace(/[，。！？,.!?\s""''…—]+/g, '').trim()
  if (stripped.length <= 4) return stripped

  for (const [word, triggers] of Object.entries(emotionKeywords)) {
    if (triggers.some(t => text.includes(t))) return word
  }

  const segments = text.replace(/[，。！？,.!?\s]+/g, ' ').trim().split(' ')
  return (segments[0] || text).slice(0, 6)
}

/* ============================================================
 * Contextual response generators
 * ============================================================ */
function stateResponse(text: string): string {
  const word = extractStateWord(text)
  const map: Record<string, string> = {
    '疲惫': '像是背着什么东西走了很久。',
    '迷茫': '看不清方向的时候，反而说明你在认真找路。',
    '焦虑': '脑子里大概装了太多还没落地的事。',
    '兴奋': '这种状态说明你正在靠近一些让你心动的东西。',
    '平静': '能平静下来的人，通常已经想明白了一些事。',
    '孤独': '一个人待着久了，是会这样。不过你来了。',
    '纠结': '在两条路之间反复看，说明两边你都在乎。',
    '充实': '忙碌有时候是一种幸运，说明你正在往前走。',
  }
  return `「${word}」。${map[word] || '嗯，我记住了。'}`
}

function struggleResponse(text: string): string {
  if (text.length > 60) return '听起来确实不简单。不过你愿意说出来，就已经在面对了。'
  if (text.length > 20) return '嗯，能感觉到这件事在你心里转了有一阵子了。'
  return '简单几个字，但分量不轻。'
}

function energyResponse(text: string): string {
  if (text.includes('音乐') || text.includes('歌')) return '音乐确实是一种很私人的充电方式。'
  if (text.includes('跑') || text.includes('运动') || text.includes('走')) return '身体动起来的时候，脑子反而能安静下来。'
  if (text.includes('睡') || text.includes('觉')) return '有时候最好的修复就是好好睡一觉。'
  if (text.includes('吃') || text.includes('饭') || text.includes('火锅')) return '吃东西的快乐是最诚实的。'
  if (text.includes('朋友') || text.includes('聊天') || text.includes('见人')) return '跟对的人待一会儿，比什么都管用。'
  if (text.includes('独') || text.includes('一个人') || text.includes('安静')) return '独处的时候，反而能听见自己的声音。'
  return '每个人都有自己的充电方式，这很重要。'
}

function companionResponse(text: string): string {
  if (text.includes('安静') || text.includes('不说话') || text.includes('默默')) return '不说话也是一种很好的陪伴。'
  if (text.includes('聊') || text.includes('说') || text.includes('倾听')) return '有人愿意听你说，这本身就是一种温暖。'
  if (text.includes('逗') || text.includes('笑') || text.includes('开心')) return '笑一笑，很多事就没那么重了。'
  if (text.includes('建议') || text.includes('方向') || text.includes('点拨')) return '有时候一句话就能让你看清楚很多东西。'
  return '你需要的陪伴方式，它会慢慢学会的。'
}

/* ============================================================
 * Stage flow
 * ============================================================ */
async function startChat() {
  phase.value = 'chat'
  await nextTick()

  await pushAgent('你来了。这个帐篷里住着蓬蓬，它正在等你。在它醒来之前，让我先认识你。')
  await pushAgent('现在的你，是什么样的？')

  currentStep.value = 1
  stage.value = 'open_share'
  setQuickReplies([
    { label: '有点累但还撑着', value: '有点累但还撑着' },
    { label: '挺迷茫的', value: '挺迷茫的' },
    { label: '还不错', value: '还不错，挺平静的' },
    { label: '说不上来', value: '说不上来，就是有点空' },
  ])
  enableInput('一个词或一句话，都可以...')
}

async function handleSend() {
  const text = userInput.value.trim()
  if (!text || inputDisabled.value) return

  inputDisabled.value = true
  userInput.value = ''
  clearQuickReplies()
  pushUser(text)

  switch (stage.value) {
    case 'open_share':
      await handleOpenShare(text)
      break
    case 'struggle':
      await handleStruggle(text)
      break
    case 'energy':
      await handleEnergy(text)
      break
    case 'companion':
      await handleCompanion(text)
      break
  }
}

function handleQuickReply(reply: QuickReply) {
  userInput.value = reply.value
  handleSend()
}

/* ---- Stage handlers ---- */
async function handleOpenShare(text: string) {
  collectedStateWord.value = extractStateWord(text)
  await pushAgent(stateResponse(text) + '\n\n最近有没有什么事，一直在心里转的？或者让你特别纠结的？')

  currentStep.value = 2
  stage.value = 'struggle'
  setQuickReplies([
    { label: '工作上的选择', value: '工作上一直在纠结要不要做出改变' },
    { label: '和人的关系', value: '跟身边一些人的关系让我有点拿不准' },
    { label: '对未来的方向', value: '不太确定接下来该往哪走' },
    { label: '没有特别的', value: '没有特别具体的，就是一种说不清的感觉' },
  ])
  enableInput('说说看...')
}

async function handleStruggle(text: string) {
  collectedStruggle.value = text.slice(0, 500)
  await pushAgent(struggleResponse(text) + '\n\n那什么事情会让你重新充满能量？累了的时候你会做什么？')

  currentStep.value = 3
  stage.value = 'energy'
  setQuickReplies([
    { label: '听音乐 / 看剧', value: '听听音乐或者看看剧' },
    { label: '一个人安静待着', value: '找个安静的地方一个人待一会儿' },
    { label: '出去走走', value: '出去走走，换个环境' },
    { label: '跟朋友聊聊', value: '找朋友聊聊天' },
    { label: '好好睡一觉', value: '什么都不想，好好睡一觉' },
  ])
  enableInput('比如...')
}

async function handleEnergy(text: string) {
  collectedExtra.value = [...collectedExtra.value, `充电方式: ${text}`]
  await pushAgent(energyResponse(text) + '\n\n最后一个问题。你理想中的陪伴是什么样的？')

  currentStep.value = 4
  stage.value = 'companion'
  setQuickReplies([
    { label: '安安静静在旁边就好', value: '不用说什么，安安静静在旁边就好' },
    { label: '能聊聊天、倾听我', value: '能聊聊天，愿意听我说' },
    { label: '偶尔逗我笑', value: '偶尔能逗我笑一下的那种' },
    { label: '给我一些方向感', value: '能在我纠结的时候给我一点方向感' },
  ])
  enableInput('你觉得呢...')
}

async function handleCompanion(text: string) {
  collectedExtra.value = [...collectedExtra.value, `陪伴偏好: ${text}`]
  await pushAgent(companionResponse(text) + '\n\n好，我已经认识你了。现在来给它选一个性格——你希望帐篷里的这个存在，是什么样的？')

  currentStep.value = 5
  stage.value = 'bias'
  showBiasCards.value = true
  inputDisabled.value = true
  clearQuickReplies()
  scrollToBottom()
}

/* ---- Bias selection ---- */
async function selectBias(key: BiasType) {
  if (stage.value !== 'bias') return
  showBiasCards.value = false
  collectedBias.value = key

  const selected = biasOptions.find(o => o.key === key)
  pushUser(selected?.label || key)

  await pushAgent(`${selected?.short_desc || ''}。好，它的轮廓已经有了。`)
  await pushAgent('让我把它叫醒。')

  stage.value = 'closing'
  await handleComplete()
}

/* ---- Submit to backend ---- */
async function handleComplete() {
  submitting.value = true

  // Combine struggle with extra context for richer personality seeding
  const fullStruggle = [
    collectedStruggle.value,
    ...collectedExtra.value,
  ].filter(Boolean).join('\n')

  try {
    const input: SoulInput = {
      current_state_word: collectedStateWord.value,
      struggle: fullStruggle.slice(0, 500),
      bias: collectedBias.value as BiasType,
    }
    const result = await store.createSoul(input)
    firstWords.value = result?.opening_response || '蓬蓬醒了。从现在开始，你不再是一个人了。'
  } catch {
    firstWords.value = '蓬蓬醒了。从现在开始，你不再是一个人了。'
  } finally {
    submitting.value = false
  }

  await new Promise(r => setTimeout(r, 1500))
  phase.value = 'done'
}

function enterHome() {
  router.push('/home')
}

/* ---- Keyboard ---- */
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="soul-creation">
    <div class="bg-glow" :class="{ active: tentGlowing }" />

    <Transition name="phase" mode="out-in">

      <!-- ====== Intro ====== -->
      <div v-if="phase === 'intro'" key="intro" class="screen intro-screen">
        <div class="tent-silhouette" :class="{ glowing: tentGlowing }">
          <svg viewBox="0 0 200 180" class="tent-svg">
            <path d="M100 20 L30 150 L170 150 Z" fill="none" stroke="currentColor" stroke-width="2" />
            <path d="M85 150 L85 100 L115 100 L115 150" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.6" />
          </svg>
          <div class="tent-light" />
        </div>

        <div class="intro-text">
          <p class="line line-1">你来了。</p>
          <p class="line line-2">在这个帐篷里，</p>
          <p class="line line-3">住着蓬蓬，它正在等你。</p>
          <p class="line line-4 dimmed">在无人时共舞，在深夜里陪你。</p>
        </div>

        <button class="btn-continue" @click="startChat">
          继续
          <span class="arrow">&rarr;</span>
        </button>
      </div>

      <!-- ====== Chat ====== -->
      <div v-else-if="phase === 'chat'" key="chat" class="screen chat-screen">

        <!-- Header with progress -->
        <div class="chat-header">
          <div class="chat-indicator">
            <span class="pulse-dot" />
            <span class="chat-label">灵魂构建中</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }" />
          </div>
        </div>

        <!-- Messages -->
        <div ref="chatContainer" class="chat-messages">
          <TransitionGroup name="msg">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="msg-row"
              :class="msg.role"
            >
              <div class="msg-bubble" :class="msg.role">
                {{ msg.text }}
              </div>
            </div>
          </TransitionGroup>

          <!-- Typing indicator -->
          <div v-if="typing" class="msg-row agent">
            <div class="msg-bubble agent typing-bubble">
              <span class="typing-dot" />
              <span class="typing-dot" />
              <span class="typing-dot" />
            </div>
          </div>

          <!-- Quick replies -->
          <Transition name="cards">
            <div v-if="quickReplies.length > 0" class="quick-replies">
              <button
                v-for="(qr, i) in quickReplies"
                :key="i"
                class="quick-chip"
                @click="handleQuickReply(qr)"
              >
                {{ qr.label }}
              </button>
            </div>
          </Transition>

          <!-- Bias cards -->
          <Transition name="cards">
            <div v-if="showBiasCards" class="bias-section">
              <div class="bias-grid">
                <button
                  v-for="opt in biasOptions"
                  :key="opt.key"
                  class="bias-chip"
                  @click="selectBias(opt.key)"
                >
                  <span class="chip-label">{{ opt.label }}</span>
                  <span class="chip-desc">{{ opt.short_desc }}</span>
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Input bar -->
        <div class="chat-input-bar" :class="{ hidden: stage === 'bias' || stage === 'closing' }">
          <input
            v-model="userInput"
            class="chat-input"
            :placeholder="inputPlaceholder"
            :disabled="inputDisabled"
            @keydown="onKeydown"
          />
          <button
            class="send-btn"
            :disabled="!userInput.trim() || inputDisabled"
            @click="handleSend"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" />
            </svg>
          </button>
        </div>
      </div>

      <!-- ====== Done ====== -->
      <div v-else-if="phase === 'done'" key="done" class="screen done-screen">
        <div class="tent-open">
          <svg viewBox="0 0 200 180" class="tent-svg open">
            <path d="M100 20 L30 150 L170 150 Z" fill="none" stroke="currentColor" stroke-width="2" />
            <path d="M75 150 L75 90 Q100 80 125 90 L125 150" fill="none" stroke="currentColor" stroke-width="1.5" />
          </svg>
          <div class="tent-light-burst" />
        </div>

        <div class="done-text">
          <p class="line line-awake">蓬蓬醒了。</p>
          <p class="line line-words">{{ firstWords }}</p>
          <p class="line line-sub dimmed">即使你爆肝不睡，它依然在那等你。</p>
        </div>

        <button class="btn-enter" @click="enterHome">
          走进蓬蓬的帐篷
          <span class="arrow">&rarr;</span>
        </button>
      </div>

    </Transition>
  </div>
</template>

<style scoped>
.soul-creation {
  position: relative;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: radial-gradient(ellipse at 50% 40%, #f5e6d0 0%, #e8dcc8 50%, #d4c4a8 100%);
}

/* ---- Background glow ---- */
.bg-glow {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at 50% 70%, rgba(232, 160, 76, 0.12) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 2s var(--ease-out-expo);
  pointer-events: none;
}
.bg-glow.active { opacity: 1; }

/* ---- Phase transitions ---- */
.phase-enter-active,
.phase-leave-active {
  transition: all var(--duration-slow) var(--ease-out-expo);
}
.phase-enter-from { opacity: 0; transform: translateY(20px); }
.phase-leave-to { opacity: 0; transform: translateY(-20px); }

/* ---- Screen layout ---- */
.screen {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.intro-screen {
  padding: var(--space-xl) var(--space-lg);
  min-height: 100dvh;
  justify-content: center;
  gap: var(--space-xl);
}

/* ---- Tent silhouette (intro) ---- */
.tent-silhouette {
  position: relative;
  width: 160px;
  height: 150px;
  color: #b8a896;
  transition: color 1.5s var(--ease-out-expo);
}
.tent-silhouette.glowing { color: #8b6b4a; }
.tent-svg { width: 100%; height: 100%; }
.tent-light {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 60px;
  background: radial-gradient(ellipse, rgba(200, 140, 50, 0.35) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 2s var(--ease-out-expo) 0.8s;
  filter: blur(8px);
}
.tent-silhouette.glowing .tent-light {
  opacity: 1;
  animation: breathe 4s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* ---- Intro text ---- */
.intro-text {
  text-align: center;
  line-height: 2;
  color: var(--text-warm);
}
.intro-text .line {
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) forwards;
  font-size: 1.15rem;
  letter-spacing: 0.04em;
}
.line-1 { animation-delay: 1s; font-size: 1.3rem; }
.line-2 { animation-delay: 1.8s; }
.line-3 { animation-delay: 2.6s; }
.line-4 { animation-delay: 3.4s; }
.dimmed { color: #9a8e82; font-size: 0.95rem; }

@keyframes text-fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Buttons ---- */
.btn-continue,
.btn-enter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  font-weight: 400;
  color: var(--text-warm);
  letter-spacing: 0.06em;
  border-radius: var(--radius-full);
  border: 1px solid rgba(61, 53, 48, 0.2);
  transition: all var(--duration-normal) var(--ease-out-expo);
  backdrop-filter: blur(4px);
  cursor: pointer;
}
.btn-continue:hover,
.btn-enter:hover {
  border-color: #8b6b4a;
  background: rgba(139, 107, 74, 0.1);
  box-shadow: 0 0 20px rgba(139, 107, 74, 0.1);
}
.arrow {
  transition: transform var(--duration-fast) var(--ease-out-expo);
}
.btn-continue:hover .arrow,
.btn-enter:hover .arrow {
  transform: translateX(4px);
}

/* ======== Chat Screen ======== */
.chat-screen {
  height: 100dvh;
  padding: 0;
}

/* ---- Header ---- */
.chat-header {
  flex-shrink: 0;
  width: 100%;
  padding: var(--space-lg) var(--space-lg) var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.chat-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8b6b4a;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.4; box-shadow: 0 0 0 0 rgba(139, 107, 74, 0.3); }
  50% { opacity: 1; box-shadow: 0 0 8px 2px rgba(139, 107, 74, 0.3); }
}

.chat-label {
  font-size: 0.85rem;
  color: #9a8e82;
  letter-spacing: 0.08em;
}

/* ---- Progress bar ---- */
.progress-bar {
  width: 100%;
  height: 3px;
  background: rgba(61, 53, 48, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #8b6b4a;
  border-radius: 2px;
  transition: width 0.8s var(--ease-out-expo);
  box-shadow: 0 0 6px rgba(139, 107, 74, 0.3);
}

/* ---- Messages area ---- */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md) var(--space-lg) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}
.chat-messages::-webkit-scrollbar { width: 0; }

/* ---- Message rows ---- */
.msg-row {
  display: flex;
  max-width: 85%;
}
.msg-row.agent { align-self: flex-start; }
.msg-row.user { align-self: flex-end; }

/* ---- Bubbles ---- */
.msg-bubble {
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  line-height: 1.7;
  letter-spacing: 0.02em;
}

.msg-bubble.agent {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: var(--text-warm);
  border-bottom-left-radius: var(--space-xs);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  white-space: pre-line;
}

.msg-bubble.user {
  background: rgba(139, 107, 74, 0.15);
  border: 1px solid rgba(139, 107, 74, 0.15);
  color: var(--text-warm);
  border-bottom-right-radius: var(--space-xs);
}

/* ---- Message enter animation ---- */
.msg-enter-active { transition: all 0.4s var(--ease-out-expo); }
.msg-enter-from { opacity: 0; transform: translateY(12px); }

/* ---- Typing indicator ---- */
.typing-bubble {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9a8e82;
  animation: typing-bounce 1.4s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-4px); }
}

/* ---- Quick replies ---- */
.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
}

.quick-chip {
  padding: 8px 16px;
  font-size: 0.85rem;
  color: var(--text-warm);
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid rgba(61, 53, 48, 0.1);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out-expo);
  letter-spacing: 0.02em;
  white-space: nowrap;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.quick-chip:hover {
  border-color: rgba(139, 107, 74, 0.3);
  background: rgba(139, 107, 74, 0.12);
  color: #5a4030;
}
.quick-chip:active {
  transform: scale(0.96);
}

/* ---- Bias cards in chat ---- */
.bias-section {
  padding: var(--space-md) 0;
}

.bias-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.bias-chip {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid rgba(61, 53, 48, 0.1);
  border-radius: var(--radius-lg);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all var(--duration-normal) var(--ease-out-expo);
  background: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.bias-chip:hover {
  border-color: rgba(139, 107, 74, 0.3);
  background: rgba(139, 107, 74, 0.12);
  box-shadow: 0 2px 12px rgba(139, 107, 74, 0.1);
}
.bias-chip:active { transform: scale(0.98); }

.chip-label {
  font-size: 1rem;
  color: var(--text-warm);
  letter-spacing: 0.04em;
}
.chip-desc {
  font-size: 0.8rem;
  color: #9a8e82;
  line-height: 1.4;
}

.cards-enter-active { transition: all 0.5s var(--ease-out-expo); }
.cards-enter-from { opacity: 0; transform: translateY(16px); }
.cards-leave-active { transition: all 0.3s var(--ease-out-expo); }
.cards-leave-to { opacity: 0; transform: scale(0.96); }

/* ---- Input bar ---- */
.chat-input-bar {
  flex-shrink: 0;
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  padding-bottom: calc(var(--space-lg) + env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  border-top: 1px solid rgba(61, 53, 48, 0.06);
  background: rgba(232, 220, 200, 0.85);
  backdrop-filter: blur(12px);
  transition: opacity var(--duration-normal) var(--ease-out-expo);
}
.chat-input-bar.hidden {
  opacity: 0;
  pointer-events: none;
}

.chat-input {
  flex: 1;
  padding: var(--space-md);
  font-size: 1rem;
  color: var(--text-warm);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(61, 53, 48, 0.1);
  border-radius: var(--radius-full);
  letter-spacing: 0.02em;
  transition: border-color var(--duration-normal) var(--ease-out-expo);
}
.chat-input:focus { border-color: rgba(139, 107, 74, 0.4); }
.chat-input::placeholder { color: #b0a598; }
.chat-input:disabled { opacity: 0.4; }

.send-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #9a8e82;
  transition: all var(--duration-normal) var(--ease-out-expo);
  cursor: pointer;
}
.send-btn:not(:disabled):hover {
  color: #8b6b4a;
  background: rgba(139, 107, 74, 0.1);
}
.send-btn:disabled { opacity: 0.2; cursor: not-allowed; }

/* ======== Done Screen ======== */
.done-screen {
  padding: var(--space-xl) var(--space-lg);
  min-height: 100dvh;
  justify-content: center;
  gap: var(--space-xl);
  text-align: center;
}

.tent-open {
  position: relative;
  width: 180px;
  height: 160px;
  color: #8b6b4a;
}
.tent-open .tent-svg { width: 100%; height: 100%; }
.tent-light-burst {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 100px;
  background: radial-gradient(ellipse, rgba(200, 140, 50, 0.3) 0%, transparent 60%);
  filter: blur(12px);
  animation: burst 2s var(--ease-out-expo) forwards;
}
@keyframes burst {
  from { opacity: 0; width: 20px; height: 30px; }
  to { opacity: 1; width: 80px; height: 100px; }
}

.done-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  line-height: 1.8;
}
.line-awake {
  font-size: 1.6rem;
  color: #8b6b4a;
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) 0.5s forwards;
}
.line-words {
  font-size: 1.05rem;
  color: var(--text-warm);
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) 1.5s forwards;
}

.btn-enter {
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) 2.5s forwards;
  border-color: #8b6b4a;
  color: #8b6b4a;
}
.btn-enter:hover {
  background: #8b6b4a;
  color: #f5e6d0;
}
</style>
