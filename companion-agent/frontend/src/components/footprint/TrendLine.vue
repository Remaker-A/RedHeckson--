<script setup lang="ts">
import { computed } from 'vue'

export interface SnapshotPoint {
  timestamp: string
  params: Record<string, number>
}

const props = defineProps<{
  snapshots: SnapshotPoint[]
  isNight: boolean
}>()

const dimensions = [
  { key: 'night_owl_index', label: '夜猫子', color: '#e8a04c' },
  { key: 'anxiety_sensitivity', label: '敏感度', color: '#c47474' },
  { key: 'quietness', label: '安静', color: '#7db88f' },
  { key: 'playfulness', label: '活泼', color: '#6ba3c4' },
  { key: 'attachment_level', label: '依赖', color: '#c490d1' },
]

const width = 320
const height = 160
const padX = 36
const padY = 20
const plotW = width - padX * 2
const plotH = height - padY * 2

const yTicks = [0, 0.25, 0.5, 0.75, 1.0]

const paths = computed(() => {
  const n = props.snapshots.length
  if (n < 2) return []

  return dimensions.map((dim) => {
    const pts = props.snapshots.map((snap, i) => {
      const x = padX + (i / (n - 1)) * plotW
      const val = snap.params[dim.key] ?? 0
      const y = padY + plotH - val * plotH
      return `${x},${y}`
    })
    return {
      ...dim,
      d: `M${pts.join('L')}`,
    }
  })
})

const xLabels = computed(() => {
  const n = props.snapshots.length
  if (n < 2) return []
  const step = Math.max(1, Math.floor(n / 5))
  const labels: Array<{ x: number; text: string }> = []
  for (let i = 0; i < n; i += step) {
    const d = new Date(props.snapshots[i].timestamp)
    labels.push({
      x: padX + (i / (n - 1)) * plotW,
      text: `${d.getMonth() + 1}/${d.getDate()}`,
    })
  }
  return labels
})
</script>

<template>
  <div class="trend-wrap" :class="{ night: isNight }">
    <svg v-if="snapshots.length >= 2" :viewBox="`0 0 ${width} ${height}`" class="trend-svg">
      <!-- Y grid lines -->
      <line
        v-for="tick in yTicks"
        :key="'y-' + tick"
        :x1="padX" :x2="width - padX"
        :y1="padY + plotH - tick * plotH"
        :y2="padY + plotH - tick * plotH"
        class="grid-line"
      />
      <!-- Y labels -->
      <text
        v-for="tick in yTicks"
        :key="'yl-' + tick"
        :x="padX - 6"
        :y="padY + plotH - tick * plotH + 3"
        class="y-label"
        text-anchor="end"
      >{{ tick.toFixed(1) }}</text>

      <!-- X labels -->
      <text
        v-for="xl in xLabels"
        :key="'xl-' + xl.x"
        :x="xl.x"
        :y="height - 4"
        class="x-label"
        text-anchor="middle"
      >{{ xl.text }}</text>

      <!-- Data lines -->
      <path
        v-for="p in paths"
        :key="'p-' + p.key"
        :d="p.d"
        :stroke="p.color"
        class="data-line"
      />
    </svg>

    <p v-else class="no-data">数据不足，至少需要两次演化记录</p>

    <!-- Legend -->
    <div v-if="snapshots.length >= 2" class="legend">
      <span v-for="dim in dimensions" :key="dim.key" class="legend-item">
        <span class="legend-dot" :style="{ background: dim.color }" />
        {{ dim.label }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.trend-wrap {
  padding: 8px 0;
}
.trend-svg {
  width: 100%;
  max-width: 400px;
  display: block;
  margin: 0 auto;
}
.grid-line {
  stroke: rgba(180, 170, 155, 0.15);
  stroke-width: 0.5;
  stroke-dasharray: 3,3;
}
.night .grid-line {
  stroke: rgba(180, 170, 155, 0.08);
}
.y-label, .x-label {
  font-size: 7px;
  fill: #b0a498;
}
.night .y-label, .night .x-label {
  fill: rgba(180, 170, 160, 0.4);
}
.data-line {
  fill: none;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0.75;
}
.no-data {
  text-align: center;
  font-size: 0.8rem;
  color: #b0a498;
  padding: 24px 0;
}
.night .no-data {
  color: rgba(180, 170, 160, 0.4);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  color: #9a8e82;
}
.night .legend-item {
  color: rgba(180, 170, 160, 0.6);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
