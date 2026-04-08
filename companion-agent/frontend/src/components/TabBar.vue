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
  <div class="tab-bar-wrap">
    <nav class="tab-bar-glass">
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
  </div>
</template>

<style scoped>
/* ═══════ Liquid Glass Tab Bar ═══════ */
.tab-bar-wrap {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 12px 24px calc(env(safe-area-inset-bottom, 8px) + 8px);
  z-index: 100;
  pointer-events: none;
}

.tab-bar-glass {
  display: flex;
  justify-content: space-around;
  align-items: center;
  width: 100%;
  max-width: 360px;
  height: 56px;
  border-radius: 28px;
  /* Liquid glass effect */
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(24px) saturate(1.4);
  -webkit-backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    inset 0 -1px 0 rgba(0, 0, 0, 0.05);
  pointer-events: auto;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 24px;
  border-radius: 20px;
  transition: all var(--duration-fast) var(--ease-out-expo);
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
}

.tab-item.active {
  background: rgba(255, 255, 255, 0.15);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.tab-icon {
  font-size: 1.3rem;
  line-height: 1;
  filter: grayscale(0.7) opacity(0.5);
  transition: filter var(--duration-normal) var(--ease-out-expo);
}

.tab-item.active .tab-icon {
  filter: grayscale(0) opacity(1);
}

.tab-label {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 0.06em;
  transition: color var(--duration-normal) var(--ease-out-expo);
}

.tab-item.active .tab-label {
  color: rgba(255, 255, 255, 0.9);
}

.tab-badge {
  position: absolute;
  top: 2px;
  right: 16px;
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
