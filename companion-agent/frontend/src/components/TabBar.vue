<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'

const route = useRoute()
const router = useRouter()
const store = useCompanionStore()

const tabs = [
  { path: '/home',     label: '帐篷', key: 'home' },
  { path: '/notes',    label: '纸条', key: 'notes' },
  { path: '/activity', label: '动态', key: 'activity' },
  { path: '/me',       label: '我的', key: 'me' },
]

const currentPath = computed(() => route.path)
const isNight = computed(() => store.isNight)

function iconSrc(key: string, active: boolean) {
  const mode = isNight.value ? 'night' : 'day'
  const state = active ? '-active' : ''
  return `/assets/icons/tab-${key}-${mode}${state}.png`
}

function go(path: string) {
  if (currentPath.value !== path) router.push(path)
}
</script>

<template>
  <nav class="tab-bar" :class="{ night: isNight }">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab-item"
      :class="{ active: currentPath === tab.path }"
      @click="go(tab.path)"
    >
      <div class="icon-wrap">
        <img
          :src="iconSrc(tab.key, currentPath === tab.path)"
          :alt="tab.label"
          class="tab-icon"
          draggable="false"
        />
        <span v-if="tab.path === '/notes' && store.unreadNoteCount > 0" class="tab-badge">
          {{ store.unreadNoteCount }}
        </span>
      </div>
      <span class="tab-label">{{ tab.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: calc(88px + env(safe-area-inset-bottom, 0px));
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: #ede2c8;
  border-top: none;
  transition: background 0.6s ease;
}
.tab-bar.night {
  background: #1b2540;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex: 1;
  height: 100%;
  background: none;
  border: none;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  padding: 0 0 4px;
}

.icon-wrap {
  position: relative;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
  display: block;
  transition: transform 0.2s var(--ease-out-expo);
}
.tab-item:active .tab-icon {
  transform: scale(0.93);
}

.tab-label {
  font-size: 13px;
  letter-spacing: 0.04em;
  color: rgba(100, 85, 65, 0.5);
  transition: color 0.3s ease;
  line-height: 1;
}
.tab-item.active .tab-label {
  color: rgba(80, 60, 40, 0.9);
}
.tab-bar.night .tab-label {
  color: rgba(160, 155, 175, 0.5);
}
.tab-bar.night .tab-item.active .tab-label {
  color: rgba(230, 215, 185, 0.9);
}

.tab-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  background: #e89040;
  color: #fff;
  font-size: 0.55rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}
</style>
