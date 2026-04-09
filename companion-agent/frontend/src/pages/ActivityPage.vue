<script setup lang="ts">
import { computed } from 'vue'
import { useCompanionStore } from '../stores/companion'

const store = useCompanionStore()
const isNight = computed(() => store.isNight)
</script>

<template>
  <div class="activity-page" :class="{ night: isNight }">
    <div class="page-header">
      <h1 class="page-title">蓬蓬的足迹</h1>
      <p class="page-sub">它做过的事，都在这里</p>
    </div>

    <div class="empty-state">
      <div class="empty-glow" />
      <p class="empty-text">还没有记录</p>
      <p class="empty-hint">蓬蓬的每一天都会留下痕迹</p>
    </div>
  </div>
</template>

<style scoped>
.activity-page {
  min-height: 100dvh;
  background: #f5f0eb;
  padding: calc(env(safe-area-inset-top, 44px) + 16px) 20px calc(88px + env(safe-area-inset-bottom, 0px));
  transition: background 0.6s ease;
}
.activity-page.night {
  background: #1e1a16;
}

.page-header {
  padding: 16px 0 24px;
}
.page-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #3d3530;
  letter-spacing: 0.04em;
}
.activity-page.night .page-title {
  color: #f0ece6;
}
.page-sub {
  font-size: 12px;
  color: #8a7e74;
  margin-top: 4px;
  letter-spacing: 0.04em;
}
.activity-page.night .page-sub {
  color: rgba(180, 170, 160, 0.7);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 80px;
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
.activity-page.night .empty-text {
  color: rgba(180, 170, 160, 0.6);
}
.empty-hint {
  font-size: 12px;
  color: #b0a49a;
  letter-spacing: 0.04em;
}
.activity-page.night .empty-hint {
  color: rgba(160, 150, 140, 0.5);
}
</style>
