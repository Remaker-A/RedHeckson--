<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps<{
  autoPlay?: boolean
  isNight?: boolean
}>()

interface Track {
  id: string
  name: string
  category: string
  frequency: number // for generated white noise / brown noise
  type: 'generated' | 'label'
}

const tracks: Track[] = [
  { id: 'white', name: '白噪音', category: '基础', frequency: 0, type: 'generated' },
  { id: 'brown', name: '棕噪音', category: '基础', frequency: 1, type: 'generated' },
  { id: 'pink', name: '粉噪音', category: '基础', frequency: 2, type: 'generated' },
]

const playing = ref(false)
const currentTrack = ref<Track>(tracks[0])
const volume = ref(0.3)

let audioCtx: AudioContext | null = null
let noiseNode: AudioBufferSourceNode | null = null
let gainNode: GainNode | null = null

function createNoiseBuffer(ctx: AudioContext, type: string): AudioBuffer {
  const sampleRate = ctx.sampleRate
  const length = sampleRate * 5
  const buffer = ctx.createBuffer(1, length, sampleRate)
  const data = buffer.getChannelData(0)

  if (type === 'brown') {
    let last = 0
    for (let i = 0; i < length; i++) {
      const white = Math.random() * 2 - 1
      data[i] = (last + 0.02 * white) / 1.02
      last = data[i]
      data[i] *= 3.5
    }
  } else if (type === 'pink') {
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0
    for (let i = 0; i < length; i++) {
      const white = Math.random() * 2 - 1
      b0 = 0.99886 * b0 + white * 0.0555179
      b1 = 0.99332 * b1 + white * 0.0750759
      b2 = 0.96900 * b2 + white * 0.1538520
      b3 = 0.86650 * b3 + white * 0.3104856
      b4 = 0.55000 * b4 + white * 0.5329522
      b5 = -0.7616 * b5 - white * 0.0168980
      data[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.11
      b6 = white * 0.115926
    }
  } else {
    for (let i = 0; i < length; i++) {
      data[i] = Math.random() * 2 - 1
    }
  }

  return buffer
}

function startNoise() {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }

  stopNoise()

  const buffer = createNoiseBuffer(audioCtx, currentTrack.value.id)
  noiseNode = audioCtx.createBufferSource()
  noiseNode.buffer = buffer
  noiseNode.loop = true

  gainNode = audioCtx.createGain()
  gainNode.gain.value = volume.value

  noiseNode.connect(gainNode)
  gainNode.connect(audioCtx.destination)
  noiseNode.start()
  playing.value = true
}

function stopNoise() {
  if (noiseNode) {
    try { noiseNode.stop() } catch {}
    noiseNode.disconnect()
    noiseNode = null
  }
  if (gainNode) {
    gainNode.disconnect()
    gainNode = null
  }
  playing.value = false
}

function toggle() {
  if (playing.value) {
    stopNoise()
  } else {
    startNoise()
  }
}

function selectTrack(track: Track) {
  currentTrack.value = track
  if (playing.value) {
    startNoise()
  }
}

watch(volume, (v) => {
  if (gainNode) {
    gainNode.gain.setTargetAtTime(v, audioCtx!.currentTime, 0.1)
  }
})

onUnmounted(() => {
  stopNoise()
  if (audioCtx) {
    audioCtx.close()
    audioCtx = null
  }
})
</script>

<template>
  <div class="white-noise">
    <div class="noise-header">
      <button class="play-toggle" @click="toggle">
        <span v-if="!playing">&#9654;</span>
        <span v-else>&#10074;&#10074;</span>
      </button>
      <span class="current-name">{{ currentTrack.name }}</span>
    </div>

    <div class="tracks">
      <button
        v-for="track in tracks"
        :key="track.id"
        class="track-chip"
        :class="{ active: currentTrack.id === track.id }"
        @click="selectTrack(track)"
      >{{ track.name }}</button>
    </div>

    <div class="volume-row">
      <span class="vol-icon">🔈</span>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        v-model.number="volume"
        class="vol-slider"
      />
      <span class="vol-icon">🔊</span>
    </div>
  </div>
</template>

<style scoped>
.white-noise {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.noise-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.play-toggle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(232, 160, 76, 0.15);
  border: 1px solid rgba(232, 160, 76, 0.3);
  color: var(--accent-orange);
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.play-toggle:hover {
  background: rgba(232, 160, 76, 0.25);
}

.current-name {
  font-size: 0.85rem;
  color: rgba(245, 240, 235, 0.7);
}

.tracks {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.track-chip {
  padding: 0.3rem 0.7rem;
  border-radius: 10px;
  background: rgba(245, 240, 235, 0.05);
  border: 1px solid rgba(245, 240, 235, 0.08);
  color: rgba(245, 240, 235, 0.5);
  font-size: 0.72rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.track-chip.active {
  border-color: rgba(232, 160, 76, 0.4);
  color: var(--accent-orange);
  background: rgba(232, 160, 76, 0.08);
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.vol-icon {
  font-size: 0.7rem;
  opacity: 0.4;
}

.vol-slider {
  flex: 1;
  height: 3px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(245, 240, 235, 0.1);
  border-radius: 2px;
  outline: none;
}

.vol-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent-orange);
  cursor: pointer;
}
</style>
