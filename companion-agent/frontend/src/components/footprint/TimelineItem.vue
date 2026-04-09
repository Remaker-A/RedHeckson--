<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FootprintEvent } from '../../composables/useApi'

const props = defineProps<{
  event: FootprintEvent
  night?: boolean
}>()

const night = computed(() => !!props.night)
const expanded = ref(false)

const timeStr = computed(() => {
  const d = new Date(props.event.timestamp)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
})

const versionStr = computed(() => {
  const v = props.event.personality_version
  if (v == null || v === 0) return ''
  return `v${v}`
})

const iconClass = computed(() => {
  if (props.event.kind === 'soul') return 'soul'
  if (props.event.event_type === 'dialogue_digest') return 'digest'
  return 'rhythm'
})

const displaySummary = computed(() => {
  return props.event.summary || props.event.change || ''
})

const displayHint = computed(() => {
  if (props.event.context_hint) return props.event.context_hint
  const raw = props.event.reason || ''
  return raw
    .replace(/^conversation_digest:\s*/i, '')
    .replace(/^rule-based periodic update/i, '')
    .replace(/^LLM analysis/i, '')
    .trim()
})
</script>

<template>
  <article class="tl-item" :class="[iconClass, { night: night, open: expanded }]">
    <button type="button" class="tl-head" @click="expanded = !expanded">
      <span class="tl-dot" aria-hidden="true" />
      <div class="tl-main">
        <div class="tl-meta">
          <span v-if="versionStr" class="tl-ver">{{ versionStr }}</span>
          <span class="tl-time">{{ timeStr }}</span>
          <span class="tl-tag">{{ event.label_zh }}</span>
        </div>
        <p class="tl-summary">{{ displaySummary }}</p>
      </div>
    </button>
    <div v-if="displayHint && expanded" class="tl-reason">
      {{ displayHint }}
    </div>
  </article>
</template>

<style scoped>
.tl-item {
  position: relative;
  margin-left: 12px;
  padding-left: 20px;
  border-left: 1px solid rgba(120, 100, 80, 0.15);
  padding-bottom: 20px;
}
.tl-item.night {
  border-left-color: rgba(200, 190, 220, 0.12);
}
.tl-item:last-child {
  border-left-color: transparent;
}

.tl-head {
  display: flex;
  gap: 10px;
  width: 100%;
  text-align: left;
  background: rgba(255, 252, 248, 0.65);
  border: 1px solid rgba(120, 100, 80, 0.08);
  border-radius: 14px;
  padding: 12px 14px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: background 0.25s ease, border-color 0.25s ease;
}
.tl-item.night .tl-head {
  background: rgba(35, 38, 52, 0.55);
  border-color: rgba(200, 190, 220, 0.08);
}
.tl-head:active {
  transform: scale(0.99);
}

.tl-dot {
  position: absolute;
  left: -6px;
  top: 18px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #c4783a;
  box-shadow: 0 0 0 3px rgba(196, 120, 58, 0.2);
}
.tl-item.digest .tl-dot {
  background: #6a9e7d;
  box-shadow: 0 0 0 3px rgba(106, 158, 125, 0.2);
}
.tl-item.rhythm .tl-dot {
  background: #7eb8da;
  box-shadow: 0 0 0 3px rgba(126, 184, 218, 0.2);
}
.tl-item.soul .tl-dot {
  background: #d4a5e8;
  box-shadow: 0 0 0 3px rgba(212, 165, 232, 0.2);
}

.tl-main {
  flex: 1;
  min-width: 0;
}
.tl-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  font-size: 11px;
  letter-spacing: 0.04em;
  color: #8a7e74;
}
.tl-item.night .tl-meta {
  color: rgba(170, 165, 180, 0.75);
}
.tl-ver {
  font-weight: 600;
  color: #5a4a3e;
}
.tl-item.night .tl-ver {
  color: rgba(230, 215, 185, 0.9);
}
.tl-tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(196, 120, 58, 0.12);
  color: #8a5a30;
  font-size: 10px;
}
.tl-item.night .tl-tag {
  background: rgba(232, 160, 76, 0.15);
  color: rgba(232, 200, 160, 0.9);
}
.tl-item.soul .tl-tag {
  background: rgba(180, 120, 200, 0.15);
  color: #6a4a78;
}
.tl-item.night.soul .tl-tag {
  color: rgba(220, 190, 235, 0.9);
}

.tl-summary {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.45;
  color: #3d3530;
  word-break: break-word;
}
.tl-item.night .tl-summary {
  color: rgba(240, 235, 228, 0.92);
}

.tl-reason {
  margin: 8px 0 0 4px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #6a6058;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 10px;
}
.tl-item.night .tl-reason {
  color: rgba(190, 185, 200, 0.85);
  background: rgba(0, 0, 0, 0.2);
}
</style>
