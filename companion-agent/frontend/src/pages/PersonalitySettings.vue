<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import type { BiasType } from '../composables/useApi'

const router = useRouter()
const store = useCompanionStore()

const voiceDraft = ref('')
const selectedBias = ref<BiasType | ''>('')
const saving = ref(false)
const loadError = ref('')
const saveError = ref('')

const fallbackOptions = [
  { key: 'decisive', label: '安静笃定派', short_desc: '在你犹豫时，它会先迈出那一步' },
  { key: 'adventurous', label: '好奇冒险家', short_desc: '在你害怕时，它会说「试试看」' },
  { key: 'slow_down', label: '慢半拍先生', short_desc: '在你着急时，它会说「不急」' },
  { key: 'warm_humor', label: '温柔段子手', short_desc: '在你沮丧时，它会找到事情好玩的那一面' },
  { key: 'night_owl', label: '深夜陪伴者', short_desc: '在深夜还亮着的灯旁，它多说两句' },
  { key: 'bookish', label: '小小哲学家', short_desc: '从一件小事能想到很远的地方' },
]

const presetRows = computed(() => {
  if (store.presets.length > 0) {
    return store.presets.map((p) => ({
      key: p.key as BiasType,
      label: p.label,
      short_desc: p.short_desc,
      voice_style: p.voice_style,
    }))
  }
  return fallbackOptions.map((o) => ({
    key: o.key as BiasType,
    label: o.label,
    short_desc: o.short_desc,
    voice_style: '',
  }))
})

function applyPresetVoice(key: BiasType) {
  const row = presetRows.value.find((r) => r.key === key)
  if (row?.voice_style) voiceDraft.value = row.voice_style
}

function selectPreset(key: BiasType) {
  selectedBias.value = key
  applyPresetVoice(key)
}

function selectCustom() {
  selectedBias.value = 'custom'
}

onMounted(async () => {
  await store.fetchPresets()
  const ok = await store.checkSoul()
  if (!ok) {
    router.replace('/soul')
    return
  }
  await store.fetchPersonality()
  if (!store.personality) {
    loadError.value = '性格数据未就绪'
    return
  }
  const b = store.personality.params.bias as BiasType
  selectedBias.value = b
  voiceDraft.value = store.personality.voice_style || ''
  if (b !== 'custom' && !voiceDraft.value) applyPresetVoice(b)
})

async function save() {
  saveError.value = ''
  if (selectedBias.value === '') {
    saveError.value = '请先选择一种性格'
    return
  }
  if (selectedBias.value === 'custom' && !voiceDraft.value.trim()) {
    saveError.value = '自定义时请填写说话风格'
    return
  }
  saving.value = true
  try {
    await store.updatePersonality({
      bias: selectedBias.value,
      voice_style: voiceDraft.value.trim(),
    })
    router.push('/tent')
  } catch (e) {
    saveError.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <header class="settings-header">
      <button type="button" class="back-btn" @click="router.push('/tent')">← 返回帐篷</button>
      <h1>它的说话方式</h1>
      <p class="sub">切换预设或直接改下面的描述，保存后对话里会跟着变。</p>
    </header>

    <p v-if="loadError" class="msg err">{{ loadError }}</p>
    <template v-else>
      <div class="bias-cards">
        <button
          v-for="opt in presetRows"
          :key="opt.key"
          type="button"
          class="bias-card"
          :class="{ selected: selectedBias === opt.key }"
          @click="selectPreset(opt.key)"
        >
          <span class="bias-label">{{ opt.label }}</span>
          <span class="bias-desc">{{ opt.short_desc }}</span>
        </button>

        <button
          type="button"
          class="bias-card"
          :class="{ selected: selectedBias === 'custom' }"
          @click="selectCustom"
        >
          <span class="bias-label">自定义</span>
          <span class="bias-desc">完全按你自己的话定义</span>
        </button>
      </div>

      <label class="field-label">说话风格（会写入 prompt）</label>
      <textarea
        v-model="voiceDraft"
        class="voice-textarea"
        rows="6"
        maxlength="800"
        placeholder="描述你希望它怎么和你说话……"
      />

      <p v-if="saveError" class="msg err">{{ saveError }}</p>

      <button type="button" class="save-btn" :disabled="saving" @click="save">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </template>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100dvh;
  padding: var(--space-lg);
  padding-bottom: calc(var(--space-xl) + env(safe-area-inset-bottom));
  max-width: 480px;
  margin: 0 auto;
  background: var(--bg-darker);
  color: var(--text-light);
}

.settings-header {
  margin-bottom: var(--space-xl);
}
.settings-header h1 {
  font-weight: 400;
  font-size: 1.35rem;
  letter-spacing: 0.04em;
  margin: var(--space-md) 0 var(--space-sm);
}
.sub {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

.back-btn {
  font-size: 0.85rem;
  color: var(--accent-warm);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  letter-spacing: 0.04em;
}
.back-btn:hover {
  text-decoration: underline;
}

.bias-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  max-height: 40vh;
  overflow-y: auto;
  padding-right: 4px;
}
@media (min-width: 400px) {
  .bias-cards {
    grid-template-columns: 1fr 1fr;
  }
}

.bias-card {
  text-align: left;
  padding: var(--space-md);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.02);
  color: inherit;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.bias-card:hover {
  border-color: rgba(232, 160, 76, 0.25);
}
.bias-card.selected {
  border-color: var(--accent-warm);
  background: var(--accent-warm-dim);
}
.bias-label {
  display: block;
  font-size: 1rem;
  margin-bottom: 4px;
}
.bias-card.selected .bias-label {
  color: var(--accent-warm);
}
.bias-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  line-height: 1.45;
}

.field-label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: var(--space-sm);
}

.voice-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: var(--space-md);
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--bg-cream);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
  resize: vertical;
  margin-bottom: var(--space-lg);
}
.voice-textarea:focus {
  outline: none;
  border-color: rgba(232, 160, 76, 0.35);
}

.save-btn {
  width: 100%;
  padding: var(--space-md);
  font-size: 1rem;
  letter-spacing: 0.06em;
  border-radius: var(--radius-full);
  border: 1px solid var(--accent-warm);
  background: var(--accent-warm-dim);
  color: var(--accent-warm);
  cursor: pointer;
}
.save-btn:hover:not(:disabled) {
  background: var(--accent-warm);
  color: var(--bg-darker);
}
.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.msg {
  font-size: 0.85rem;
  margin-bottom: var(--space-md);
}
.msg.err {
  color: #e88;
}
</style>
