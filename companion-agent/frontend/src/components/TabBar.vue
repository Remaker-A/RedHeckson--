<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'

const route = useRoute()
const router = useRouter()
const store = useCompanionStore()

const tabs = [
  { path: '/home', label: '帐篷', icon: '🏕️' },
  { path: '/notes', label: '纸条', icon: '📄' },
  { path: '/me', label: '我的', icon: '👤' },
]

const currentPath = computed(() => route.path)

function go(path: string) {
  if (currentPath.value !== path) router.push(path)
}
</script>

<template>
  <nav class="tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab-item"
      :class="{ active: currentPath === tab.path }"
      @click="go(tab.path)"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span v-if="tab.path === '/notes' && store.unreadNoteCount > 0" class="tab-badge">{{ store.unreadNoteCount }}</span>
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
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 72px;
  padding-bottom: env(safe-area-inset-bottom, 8px);
  background: rgba(30, 26, 22, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 100;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-out-expo);
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
}

.tab-icon {
  font-size: 1.4rem;
  line-height: 1;
  filter: grayscale(0.8) opacity(0.5);
  transition: filter var(--duration-normal) var(--ease-out-expo);
}

.tab-item.active .tab-icon {
  filter: grayscale(0) opacity(1);
}

.tab-label {
  font-size: 0.65rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
  transition: color var(--duration-normal) var(--ease-out-expo);
}

.tab-item.active .tab-label {
  color: var(--accent-warm);
}

.tab-badge {
  position: absolute;
  top: 4px;
  right: 12px;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  background: var(--accent-warm);
  color: var(--bg-darker);
  font-size: 0.6rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}
</style>
