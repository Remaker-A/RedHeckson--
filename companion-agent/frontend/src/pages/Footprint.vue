<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { SnapshotPoint } from '../components/footprint/TrendLine.vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import { useWebSocket } from '../composables/useWebSocket'
import type { FootprintEvent } from '../composables/useApi'
import TimelineItem from '../components/footprint/TimelineItem.vue'
import RadarChart from '../components/footprint/RadarChart.vue'
import TrendLine from '../components/footprint/TrendLine.vue'

const router = useRouter()
const store = useCompanionStore()
const loaded = ref(false)
const isNight = computed(() => store.isNight)

type ChartMode = 'radar' | 'trend'
const chartMode = ref<ChartMode>('radar')

const overview = computed(() => store.footprintTimeline?.overview)
const events = computed<FootprintEvent[]>(() => store.footprintTimeline?.events ?? [])
const trendSeries = computed(() => store.footprintTimeline?.trend_series ?? [])

const PARAM_KEYS = [
  'night_owl_index',
  'anxiety_sensitivity',
  'quietness',
  'playfulness',
  'attachment_level',
] as const

function clampParamsRecord(p: Record<string, unknown>): Record<string, number> {
  const out: Record<string, number> = {}
  for (const k of PARAM_KEYS) {
    const v = p[k]
    const n = typeof v === 'number' ? v : Number(v)
    out[k] = Number.isFinite(n) ? Math.max(0, Math.min(1, n)) : 0
  }
  return out
}

const radarParams = computed(() => clampParamsRecord(overview.value?.params ?? {}))

const trendSnapshots = computed((): SnapshotPoint[] =>
  trendSeries.value.map((t) => ({
    timestamp: t.timestamp,
    params: clampParamsRecord(t.params),
  })),
)

const daysTogether = computed(() => overview.value?.days_together ?? 0)
const personalityVersion = computed(() => overview.value?.personality_version ?? 0)

const hasParams = computed(() => PARAM_KEYS.some((k) => k in (overview.value?.params ?? {})))

onMounted(async () => {
  const hasSoul = await store.checkSoul()
  if (!hasSoul) {
    router.replace('/soul')
    return
  }
  await store.loadFootprint()
  loaded.value = true
})

const { on } = useWebSocket()
on('personality_update', () => store.loadFootprint())
on('soul_update', () => store.loadFootprint())
</script>

<template>
  <div class="footprint-page" :class="{ night: isNight }">
    <div class="page-header">
      <h1 class="page-title">蓬蓬的足迹</h1>
      <p class="page-sub">每一次变化，都是和你相处的痕迹</p>
    </div>

    <template v-if="loaded && overview">
      <!-- Section 1: Overview cards -->
      <div class="overview-row">
        <div class="ov-card">
          <span class="ov-num">{{ daysTogether }}</span>
          <span class="ov-label">相处天数</span>
        </div>
        <div class="ov-card">
          <span class="ov-num">v{{ personalityVersion }}</span>
          <span class="ov-label">性格版本</span>
        </div>
        <div class="ov-card" v-if="overview.current_state_word">
          <span class="ov-num ov-text">{{ overview.current_state_word }}</span>
          <span class="ov-label">当前状态</span>
        </div>
        <div class="ov-card wide" v-if="overview.struggle">
          <span class="ov-num ov-text">{{ overview.struggle }}</span>
          <span class="ov-label">当前纠结</span>
        </div>
      </div>

      <!-- Section 2: Visualization -->
      <section v-if="hasParams" class="viz-section">
        <div class="viz-toggle">
          <button
            :class="{ active: chartMode === 'radar' }"
            @click="chartMode = 'radar'"
          >当前态</button>
          <button
            :class="{ active: chartMode === 'trend' }"
            @click="chartMode = 'trend'"
          >趋势</button>
        </div>

        <Transition name="chart-fade" mode="out-in">
          <RadarChart
            v-if="chartMode === 'radar'"
            :params="radarParams"
            :is-night="isNight"
            key="radar"
          />
          <TrendLine
            v-else
            :snapshots="trendSnapshots"
            :is-night="isNight"
            key="trend"
          />
        </Transition>
      </section>

      <!-- Section 3: Timeline -->
      <section class="timeline-section">
        <h2 class="section-title">演进时间线</h2>

        <div v-if="events.length === 0" class="empty-state">
          <div class="empty-glow" />
          <p class="empty-text">还没有记录</p>
          <p class="empty-hint">蓬蓬的每一天都会留下痕迹</p>
        </div>

        <div v-else class="timeline-list">
          <TimelineItem
            v-for="evt in events"
            :key="evt.id"
            :event="evt"
            :night="isNight"
          />
        </div>
      </section>
    </template>

    <div v-else-if="loaded && !overview" class="empty-state">
      <p class="empty-text">足迹数据暂时无法加载</p>
    </div>

    <!-- Loading state -->
    <div v-if="!loaded" class="loading-state">
      <div class="loading-glow" />
    </div>

    <div class="tab-spacer" />
  </div>
</template>

<style scoped>
.footprint-page {
  min-height: 100dvh;
  background: #f5f0eb;
  padding: calc(env(safe-area-inset-top, 44px) + 16px) 20px calc(88px + env(safe-area-inset-bottom, 0px));
  transition: background 0.6s ease;
}
.footprint-page.night {
  background: var(--bg-dark, #2a2520);
}

/* Header */
.page-header {
  padding: 0 0 20px;
}
.page-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #3d3530;
  letter-spacing: 0.04em;
}
.footprint-page.night .page-title {
  color: #f0ece6;
}
.page-sub {
  font-size: 12px;
  color: #8a7e74;
  margin-top: 4px;
  letter-spacing: 0.04em;
}
.footprint-page.night .page-sub {
  color: rgba(180, 170, 160, 0.7);
}

/* Overview cards */
.overview-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
  gap: 10px;
  margin-bottom: 24px;
}
.ov-card.wide {
  grid-column: 1 / -1;
}
.ov-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 8px;
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid rgba(61, 53, 48, 0.06);
  border-radius: var(--radius-md, 12px);
  gap: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  transition: background 0.8s ease, border-color 0.8s ease;
}
.footprint-page.night .ov-card {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: none;
}
.ov-num {
  font-size: 1.3rem;
  font-weight: 400;
  color: var(--text-warm, #3d3530);
}
.ov-num.ov-text {
  font-size: 1rem;
}
.footprint-page.night .ov-num {
  color: var(--text-light, #c8beb4);
}
.ov-label {
  font-size: 11px;
  color: #9a8e82;
  letter-spacing: 0.06em;
}
.footprint-page.night .ov-label {
  color: var(--text-muted, #8a7e74);
}

/* Visualization section */
.viz-section {
  margin-bottom: 28px;
}
.viz-toggle {
  display: flex;
  justify-content: center;
  gap: 0;
  background: rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-full, 999px);
  padding: 3px;
  margin-bottom: 12px;
  max-width: 200px;
  margin-left: auto;
  margin-right: auto;
}
.footprint-page.night .viz-toggle {
  background: rgba(255, 255, 255, 0.06);
}
.viz-toggle button {
  flex: 1;
  font-size: 0.75rem;
  padding: 6px 16px;
  border-radius: var(--radius-full, 999px);
  color: var(--text-muted, #8a7e74);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.25s var(--ease-out-expo, cubic-bezier(0.16, 1, 0.3, 1));
  letter-spacing: 0.04em;
}
.viz-toggle button.active {
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-warm, #3d3530);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}
.footprint-page.night .viz-toggle button.active {
  background: rgba(232, 160, 76, 0.2);
  color: var(--accent-warm, #e8a04c);
  box-shadow: none;
}

/* Chart fade transition */
.chart-fade-enter-active,
.chart-fade-leave-active {
  transition: opacity 0.25s ease;
}
.chart-fade-enter-from,
.chart-fade-leave-to {
  opacity: 0;
}

/* Timeline section */
.timeline-section {
  padding-bottom: 20px;
}
.section-title {
  font-size: 13px;
  font-weight: 400;
  color: #9a8e82;
  letter-spacing: 0.08em;
  margin-bottom: 16px;
}
.footprint-page.night .section-title {
  color: var(--text-muted, #8a7e74);
}

.timeline-list {
  padding-left: 4px;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 48px;
  gap: 12px;
}
.empty-glow {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232, 160, 76, 0.3) 0%, transparent 70%);
  animation: breathe 3s ease-in-out infinite;
}
.empty-text {
  font-size: 0.9rem;
  color: #8a7e74;
}
.footprint-page.night .empty-text {
  color: rgba(180, 170, 160, 0.6);
}
.empty-hint {
  font-size: 12px;
  color: #b0a49a;
  letter-spacing: 0.04em;
}
.footprint-page.night .empty-hint {
  color: rgba(160, 150, 140, 0.5);
}

/* Loading state */
.loading-state {
  display: flex;
  justify-content: center;
  padding-top: 80px;
}
.loading-glow {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232, 160, 76, 0.25) 0%, transparent 70%);
  animation: breathe 2s ease-in-out infinite;
}

.tab-spacer { height: 20px; flex-shrink: 0; }
</style>
