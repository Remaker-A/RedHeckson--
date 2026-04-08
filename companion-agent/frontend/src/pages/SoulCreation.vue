<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import type { SoulInput, BiasType } from '../composables/useApi'

const router = useRouter()
const store = useCompanionStore()

/* ---- Step management ---- */
type Step = 'intro' | 'step1' | 'step2' | 'step3' | 'done'
const step = ref<Step>('intro')
const direction = ref<'forward' | 'backward'>('forward')

const steps: Step[] = ['intro', 'step1', 'step2', 'step3', 'done']

function goNext() {
  const idx = steps.indexOf(step.value)
  if (idx < steps.length - 1) {
    direction.value = 'forward'
    step.value = steps[idx + 1]
  }
}

/* ---- Form data ---- */
const stateWord = ref('')
const struggle = ref('')
const bias = ref<BiasType | ''>('')
const customVoiceStyle = ref('')
const canProceedStep1 = computed(() => stateWord.value.trim().length > 0)
const canProceedStep2 = computed(() => struggle.value.trim().length > 0)
const canProceedStep3 = computed(() => bias.value !== '')

/* ---- Rotating placeholder ---- */
const placeholders = ['疲惫', '迷茫', '兴奋', '焦虑', '平静', '期待', '孤独', '充实']
const currentPlaceholder = ref(0)
let placeholderTimer: ReturnType<typeof setInterval>

onMounted(() => {
  placeholderTimer = setInterval(() => {
    currentPlaceholder.value = (currentPlaceholder.value + 1) % placeholders.length
  }, 2000)
  store.fetchPresets()
})

onUnmounted(() => clearInterval(placeholderTimer))

/* ---- Tent animation state ---- */
const tentGlowing = ref(false)
onMounted(() => {
  setTimeout(() => { tentGlowing.value = true }, 600)
})

/* ---- Submit ---- */
const submitting = ref(false)
const firstWords = ref('')

async function handleComplete() {
  if (step.value !== 'step3' || !canProceedStep3.value) return
  submitting.value = true
  try {
    const input: SoulInput = {
      current_state_word: stateWord.value.trim(),
      struggle: struggle.value.trim(),
      bias: bias.value as BiasType,
    }
    if (bias.value === 'custom') {
      const t = customVoiceStyle.value.trim()
      if (t) input.custom_voice_style = t
    }
    const result = await store.createSoul(input)
    firstWords.value = result?.opening_response || '从现在开始，你不再是一个人了。'
    direction.value = 'forward'
    step.value = 'done'
  } catch {
    firstWords.value = '从现在开始，你不再是一个人了。'
    direction.value = 'forward'
    step.value = 'done'
  } finally {
    submitting.value = false
  }
}

function enterTent() {
  router.push('/tent')
}

/* ---- Bias options (dynamic from API, with hardcoded fallback) ---- */
const fallbackOptions = [
  { key: 'decisive', label: '安静笃定派', short_desc: '在你犹豫时，它会先迈出那一步' },
  { key: 'adventurous', label: '好奇冒险家', short_desc: '在你害怕时，它会说"试试看"' },
  { key: 'slow_down', label: '慢半拍先生', short_desc: '在你着急时，它会说"不急"' },
  { key: 'warm_humor', label: '温柔段子手', short_desc: '在你沮丧时，它会找到事情好玩的那一面' },
  { key: 'night_owl', label: '深夜陪伴者', short_desc: '在深夜还亮着的灯旁，它多说两句' },
  { key: 'bookish', label: '小小哲学家', short_desc: '从一件小事能想到很远的地方' },
]

const biasOptions = computed(() => {
  if (store.presets.length > 0) {
    return store.presets
      .filter(p => p.key !== 'custom')
      .map(p => ({ key: p.key, label: p.label, short_desc: p.short_desc }))
  }
  return fallbackOptions
})

function selectCustom() {
  bias.value = 'custom'
}
</script>

<template>
  <div class="soul-creation">
    <!-- Background glow -->
    <div class="bg-glow" :class="{ active: tentGlowing }" />

    <Transition :name="direction === 'forward' ? 'step-forward' : 'step-back'" mode="out-in">

      <!-- ====== Intro ====== -->
      <div v-if="step === 'intro'" key="intro" class="screen">
        <div class="tent-silhouette" :class="{ glowing: tentGlowing }">
          <svg viewBox="0 0 200 180" class="tent-svg">
            <path d="M100 20 L30 150 L170 150 Z" fill="none" stroke="currentColor" stroke-width="2" />
            <path d="M85 150 L85 100 L115 100 L115 150" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.6" />
          </svg>
          <div class="tent-light" />
        </div>

        <div class="intro-text">
          <p class="line line-1">你来了。</p>
          <p class="line line-2">在这个小帐篷里，</p>
          <p class="line line-3">住着一个正在等你的存在。</p>
          <p class="line line-4 dimmed">在开始之前，让它先认识你。</p>
        </div>

        <button class="btn-continue" @click="goNext">
          继续
          <span class="arrow">→</span>
        </button>
      </div>

      <!-- ====== Step 1: 你是谁 ====== -->
      <div v-else-if="step === 'step1'" key="step1" class="screen">
        <div class="step-indicator">
          <span class="dot active" />
          <span class="dot" />
          <span class="dot" />
        </div>

        <div class="step-content">
          <h2 class="question">
            用一个词，<br />描述你现在的状态。
          </h2>

          <div class="input-wrap">
            <input
              v-model="stateWord"
              type="text"
              class="soul-input"
              :placeholder="placeholders[currentPlaceholder]"
              maxlength="10"
              autofocus
              @keyup.enter="canProceedStep1 && goNext()"
            />
            <div class="input-glow" />
          </div>
        </div>

        <button
          class="btn-continue"
          :class="{ disabled: !canProceedStep1 }"
          :disabled="!canProceedStep1"
          @click="goNext"
        >
          下一步
          <span class="arrow">→</span>
        </button>
      </div>

      <!-- ====== Step 2: 你的纠结 ====== -->
      <div v-else-if="step === 'step2'" key="step2" class="screen">
        <div class="step-indicator">
          <span class="dot done" />
          <span class="dot active" />
          <span class="dot" />
        </div>

        <div class="step-content">
          <h2 class="question">
            你最近最难做的<br />一个决定是什么？
          </h2>

          <textarea
            v-model="struggle"
            class="soul-textarea"
            placeholder="不用写很多，几句话就好..."
            rows="4"
            maxlength="500"
          />
        </div>

        <button
          class="btn-continue"
          :class="{ disabled: !canProceedStep2 }"
          :disabled="!canProceedStep2"
          @click="goNext"
        >
          下一步
          <span class="arrow">→</span>
        </button>
      </div>

      <!-- ====== Step 3: 它的偏向 ====== -->
      <div v-else-if="step === 'step3'" key="step3" class="screen">
        <div class="step-indicator">
          <span class="dot done" />
          <span class="dot done" />
          <span class="dot active" />
        </div>

        <div class="step-content">
          <h2 class="question">
            选择它的性格
          </h2>

          <div class="bias-cards">
            <button
              v-for="opt in biasOptions"
              :key="opt.key"
              class="bias-card"
              :class="{ selected: bias === opt.key }"
              @click="bias = opt.key as BiasType"
            >
              <span class="bias-label">{{ opt.label }}</span>
              <span class="bias-desc">{{ opt.short_desc }}</span>
            </button>

            <button
              class="bias-card custom-card"
              :class="{ selected: bias === 'custom' }"
              @click="selectCustom"
            >
              <span class="bias-label">自定义</span>
              <span class="bias-desc">用你自己的话描述它的性格</span>
            </button>
          </div>

          <div v-if="bias === 'custom'" class="custom-voice-wrap">
            <textarea
              v-model="customVoiceStyle"
              class="soul-textarea"
              placeholder="描述你希望它怎么和你说话，比如：话不多但很暖、喜欢用比喻、偶尔会冷幽默……"
              rows="4"
              maxlength="800"
            />
          </div>
        </div>

        <button
          class="btn-continue"
          :class="{ disabled: !canProceedStep3 || submitting }"
          :disabled="!canProceedStep3 || submitting"
          @click="handleComplete"
        >
          {{ submitting ? '它正在醒来...' : '完成' }}
          <span v-if="!submitting" class="arrow">→</span>
        </button>
      </div>

      <!-- ====== Done ====== -->
      <div v-else-if="step === 'done'" key="done" class="screen done-screen">
        <div class="tent-open">
          <svg viewBox="0 0 200 180" class="tent-svg open">
            <path d="M100 20 L30 150 L170 150 Z" fill="none" stroke="currentColor" stroke-width="2" />
            <path d="M75 150 L75 90 Q100 80 125 90 L125 150" fill="none" stroke="currentColor" stroke-width="1.5" />
          </svg>
          <div class="tent-light-burst" />
        </div>

        <div class="done-text">
          <p class="line line-awake">它醒了。</p>
          <p class="line line-words">{{ firstWords }}</p>
        </div>

        <button class="btn-enter" @click="enterTent">
          走进它的家
          <span class="arrow">→</span>
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
  background: var(--bg-darker);
}

/* ---- Background glow ---- */
.bg-glow {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at 50% 45%, var(--accent-warm-dim) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 2s var(--ease-out-expo);
  pointer-events: none;
}
.bg-glow.active {
  opacity: 1;
}

/* ---- Screen layout ---- */
.screen {
  width: 100%;
  max-width: 420px;
  padding: var(--space-xl) var(--space-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100dvh;
  justify-content: center;
  gap: var(--space-xl);
}

/* ---- Step transitions ---- */
.step-forward-enter-active,
.step-forward-leave-active {
  transition: all var(--duration-slow) var(--ease-out-expo);
}
.step-forward-enter-from {
  opacity: 0;
  transform: translateX(60px);
}
.step-forward-leave-to {
  opacity: 0;
  transform: translateX(-40px);
}

.step-back-enter-active,
.step-back-leave-active {
  transition: all var(--duration-slow) var(--ease-out-expo);
}
.step-back-enter-from {
  opacity: 0;
  transform: translateX(-60px);
}
.step-back-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

/* ---- Tent silhouette (intro) ---- */
.tent-silhouette {
  position: relative;
  width: 160px;
  height: 150px;
  color: var(--text-muted);
  transition: color 1.5s var(--ease-out-expo);
}
.tent-silhouette.glowing {
  color: var(--accent-warm);
}
.tent-svg {
  width: 100%;
  height: 100%;
}
.tent-light {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 60px;
  background: radial-gradient(ellipse, var(--accent-warm-glow) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 2s var(--ease-out-expo) 0.8s;
  filter: blur(8px);
}
.tent-silhouette.glowing .tent-light {
  opacity: 1;
  animation: breathe 4s ease-in-out infinite;
}

/* ---- Intro text ---- */
.intro-text {
  text-align: center;
  line-height: 2;
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
.dimmed { color: var(--text-muted); font-size: 0.95rem; }

@keyframes text-fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- Step indicator ---- */
.step-indicator {
  display: flex;
  gap: 10px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  opacity: 0.3;
  transition: all var(--duration-normal) var(--ease-out-expo);
}
.dot.active {
  background: var(--accent-warm);
  opacity: 1;
  box-shadow: 0 0 8px var(--accent-warm-glow);
}
.dot.done {
  background: var(--accent-warm);
  opacity: 0.5;
}

/* ---- Step content ---- */
.step-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xl);
}

.question {
  font-family: var(--font-body);
  font-weight: 300;
  font-size: 1.4rem;
  line-height: 1.8;
  text-align: center;
  color: var(--text-light);
  letter-spacing: 0.03em;
}

/* ---- Input (Step 1) ---- */
.input-wrap {
  position: relative;
  width: 100%;
  max-width: 280px;
}
.soul-input {
  width: 100%;
  text-align: center;
  font-size: 1.5rem;
  font-weight: 400;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1.5px solid var(--text-muted);
  color: var(--bg-cream);
  background: transparent;
  transition: border-color var(--duration-normal) var(--ease-out-expo);
  letter-spacing: 0.1em;
}
.soul-input:focus {
  border-color: var(--accent-warm);
}
.soul-input::placeholder {
  color: var(--text-muted);
  opacity: 0.5;
  transition: opacity 0.6s;
}
.input-glow {
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 2px;
  background: var(--accent-warm);
  border-radius: 1px;
  transition: width var(--duration-normal) var(--ease-out-expo);
  box-shadow: 0 0 10px var(--accent-warm-glow);
}
.soul-input:focus ~ .input-glow {
  width: 100%;
}

/* ---- Textarea (Step 2) ---- */
.soul-textarea {
  width: 100%;
  max-width: 340px;
  padding: var(--space-md);
  font-size: 1rem;
  line-height: 1.8;
  color: var(--bg-cream);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  resize: none;
  transition: border-color var(--duration-normal) var(--ease-out-expo),
              background var(--duration-normal) var(--ease-out-expo);
}
.soul-textarea:focus {
  border-color: rgba(232, 160, 76, 0.3);
  background: rgba(255, 255, 255, 0.05);
}
.soul-textarea::placeholder {
  color: var(--text-muted);
  opacity: 0.5;
}

/* ---- Bias cards (Step 3) ---- */
.bias-cards {
  width: 100%;
  max-width: 460px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-sm);
  max-height: min(52vh, 440px);
  overflow-y: auto;
  padding-right: 4px;
}
@media (max-width: 379px) {
  .bias-cards {
    grid-template-columns: 1fr;
  }
}
.bias-card {
  width: 100%;
  padding: var(--space-md) var(--space-md);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  transition: all var(--duration-normal) var(--ease-out-expo);
  background: rgba(255, 255, 255, 0.02);
}
.bias-card.custom-card {
  grid-column: 1 / -1;
  border-style: dashed;
}
.custom-voice-wrap {
  width: 100%;
  max-width: 460px;
  margin-top: var(--space-sm);
}
.custom-voice-wrap .soul-textarea {
  max-width: 100%;
}
.bias-card:hover {
  border-color: rgba(232, 160, 76, 0.2);
  background: rgba(255, 255, 255, 0.04);
}
.bias-card.selected {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
  box-shadow: 0 0 20px var(--accent-warm-dim);
}
.bias-label {
  font-size: 1.05rem;
  font-weight: 400;
  color: var(--bg-cream);
  letter-spacing: 0.05em;
}
.bias-card.selected .bias-label {
  color: var(--accent-warm);
}
.bias-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* ---- Continue button ---- */
.btn-continue,
.btn-enter {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
  font-size: 1rem;
  font-weight: 400;
  color: var(--bg-cream);
  letter-spacing: 0.06em;
  border-radius: var(--radius-full);
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all var(--duration-normal) var(--ease-out-expo);
  backdrop-filter: blur(4px);
}
.btn-continue:hover:not(.disabled),
.btn-enter:hover {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
  box-shadow: 0 0 20px var(--accent-warm-dim);
}
.btn-continue.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.arrow {
  transition: transform var(--duration-fast) var(--ease-out-expo);
}
.btn-continue:hover:not(.disabled) .arrow,
.btn-enter:hover .arrow {
  transform: translateX(4px);
}

/* ---- Done screen ---- */
.done-screen {
  text-align: center;
}

.tent-open {
  position: relative;
  width: 180px;
  height: 160px;
  color: var(--accent-warm);
}
.tent-open .tent-svg {
  width: 100%;
  height: 100%;
}
.tent-light-burst {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 100px;
  background: radial-gradient(ellipse, var(--accent-warm-glow) 0%, transparent 60%);
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
  color: var(--accent-warm);
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) 0.5s forwards;
}
.line-words {
  font-size: 1.05rem;
  color: var(--text-light);
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) 1.5s forwards;
}

.btn-enter {
  opacity: 0;
  animation: text-fade-in 1s var(--ease-out-expo) 2.5s forwards;
  border-color: var(--accent-warm);
  color: var(--accent-warm);
}
.btn-enter:hover {
  background: var(--accent-warm);
  color: var(--bg-darker);
}
</style>
