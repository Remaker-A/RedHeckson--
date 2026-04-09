<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  params: Record<string, number>
  isNight: boolean
}>()

const dimensions = [
  { key: 'night_owl_index', label: '夜猫子' },
  { key: 'anxiety_sensitivity', label: '敏感度' },
  { key: 'quietness', label: '安静' },
  { key: 'playfulness', label: '活泼' },
  { key: 'attachment_level', label: '依赖' },
]

const size = 200
const cx = size / 2
const cy = size / 2
const maxR = 70
const levels = [0.25, 0.5, 0.75, 1.0]

function polarToXY(angle: number, r: number) {
  const rad = (angle - 90) * (Math.PI / 180)
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

const angleStep = 360 / dimensions.length

const gridPaths = computed(() =>
  levels.map((level) => {
    const r = maxR * level
    const pts = dimensions.map((_, i) => {
      const { x, y } = polarToXY(i * angleStep, r)
      return `${x},${y}`
    })
    return `M${pts.join('L')}Z`
  }),
)

const axisLines = computed(() =>
  dimensions.map((_, i) => {
    const { x, y } = polarToXY(i * angleStep, maxR)
    return { x1: cx, y1: cy, x2: x, y2: y }
  }),
)

const labelPositions = computed(() =>
  dimensions.map((dim, i) => {
    const { x, y } = polarToXY(i * angleStep, maxR + 18)
    return { ...dim, x, y }
  }),
)

const dataPath = computed(() => {
  const pts = dimensions.map((dim, i) => {
    const val = props.params[dim.key] ?? 0
    const r = maxR * Math.max(0.05, val)
    const { x, y } = polarToXY(i * angleStep, r)
    return `${x},${y}`
  })
  return `M${pts.join('L')}Z`
})

const dotPositions = computed(() =>
  dimensions.map((dim, i) => {
    const val = props.params[dim.key] ?? 0
    const r = maxR * Math.max(0.05, val)
    return polarToXY(i * angleStep, r)
  }),
)
</script>

<template>
  <div class="radar-wrap" :class="{ night: isNight }">
    <svg :viewBox="`0 0 ${size} ${size}`" class="radar-svg">
      <!-- Grid rings -->
      <path
        v-for="(d, i) in gridPaths"
        :key="'grid-' + i"
        :d="d"
        class="grid-ring"
      />

      <!-- Axis lines -->
      <line
        v-for="(a, i) in axisLines"
        :key="'axis-' + i"
        :x1="a.x1" :y1="a.y1" :x2="a.x2" :y2="a.y2"
        class="axis-line"
      />

      <!-- Data polygon -->
      <path :d="dataPath" class="data-fill" />
      <path :d="dataPath" class="data-stroke" />

      <!-- Data points -->
      <circle
        v-for="(pt, i) in dotPositions"
        :key="'pt-' + i"
        :cx="pt.x"
        :cy="pt.y"
        r="3"
        class="data-dot"
      />

      <!-- Labels -->
      <text
        v-for="lbl in labelPositions"
        :key="'lbl-' + lbl.key"
        :x="lbl.x" :y="lbl.y"
        class="dim-label"
        text-anchor="middle"
        dominant-baseline="central"
      >{{ lbl.label }}</text>
    </svg>
  </div>
</template>

<style scoped>
.radar-wrap {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}
.radar-svg {
  width: 100%;
  max-width: 240px;
}
.grid-ring {
  fill: none;
  stroke: rgba(180, 170, 155, 0.18);
  stroke-width: 0.8;
}
.night .grid-ring {
  stroke: rgba(180, 170, 155, 0.08);
}
.axis-line {
  stroke: rgba(180, 170, 155, 0.15);
  stroke-width: 0.6;
}
.night .axis-line {
  stroke: rgba(180, 170, 155, 0.06);
}
.data-fill {
  fill: rgba(232, 160, 76, 0.15);
  transition: d 0.6s ease;
}
.night .data-fill {
  fill: rgba(232, 160, 76, 0.12);
}
.data-stroke {
  fill: none;
  stroke: rgba(232, 160, 76, 0.6);
  stroke-width: 1.5;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 4px rgba(232, 160, 76, 0.3));
  transition: d 0.6s ease;
}
.night .data-stroke {
  stroke: rgba(232, 160, 76, 0.7);
  filter: drop-shadow(0 0 6px rgba(232, 160, 76, 0.4));
}
.data-dot {
  fill: #e8a04c;
  opacity: 0.8;
}
.dim-label {
  font-size: 9px;
  fill: #9a8e82;
  letter-spacing: 0.04em;
}
.night .dim-label {
  fill: rgba(180, 170, 160, 0.6);
}
</style>
