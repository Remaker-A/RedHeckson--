<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'

const router = useRouter()
const store = useCompanionStore()
const loaded = ref(false)
const showResetConfirm = ref(false)
const resetting = ref(false)

const biasLabels: Record<string, string> = {
  decisive: '安静笃定派',
  adventurous: '好奇冒险家',
  slow_down: '慢半拍先生',
  warm_humor: '温柔段子手',
  night_owl: '深夜陪伴者',
  bookish: '小小哲学家',
  custom: '自定义',
}

const daysTogether = computed(() => {
  if (!store.soul?.created_at) return 0
  const created = new Date(store.soul.created_at)
  const now = new Date()
  return Math.max(1, Math.ceil((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24)))
})

const growthStage = computed(() => {
  const days = daysTogether.value
  const version = store.personality?.version ?? 1
  if (days <= 1 && version <= 1) return '初见'
  if (days <= 7) return '相识'
  if (days <= 30) return '默契'
  return '知己'
})

const personalityDescription = computed(() => {
  return store.personality?.natural_description || '正在了解你...'
})

onMounted(async () => {
  const hasSoul = await store.checkSoul()
  if (!hasSoul) { router.replace('/soul'); return }
  await Promise.all([store.fetchPersonality(), store.fetchNotes()])
  loaded.value = true
})

async function handleReset() {
  resetting.value = true
  try {
    await fetch('/api/soul', { method: 'DELETE' })
    router.replace('/soul')
  } finally {
    resetting.value = false
  }
}
</script>

<template>
  <div class="me-page">
    <header class="me-header">
      <h1 class="me-title">我的伙伴</h1>
    </header>

    <div v-if="loaded" class="me-content">
      <!-- Avatar section -->
      <div class="avatar-section">
        <div class="avatar-ring">
          <img
            src="/assets/character/char-sleeping.png"
            alt="我的伙伴"
            class="avatar-img"
          />
        </div>
        <div class="avatar-info">
          <span class="bias-tag">{{ biasLabels[store.soul?.bias ?? ''] || store.soul?.bias }}</span>
          <span class="days-tag">相处 {{ daysTogether }} 天</span>
        </div>
      </div>

      <!-- Stats cards -->
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-num">{{ store.notes.length }}</span>
          <span class="stat-label">纸条</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">v{{ store.personality?.version ?? 1 }}</span>
          <span class="stat-label">性格版本</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ growthStage }}</span>
          <span class="stat-label">成长阶段</span>
        </div>
      </div>

      <!-- Soul profile section -->
      <section class="profile-section">
        <h2 class="section-title">灵魂档案</h2>

        <div class="profile-card">
          <div class="profile-row">
            <span class="profile-label">初始状态</span>
            <span class="profile-value">{{ store.soul?.current_state_word || '-' }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">最初纠结</span>
            <span class="profile-value text-long">{{ store.soul?.struggle || '-' }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">性格方向</span>
            <span class="profile-value accent">{{ biasLabels[store.soul?.bias ?? ''] || '-' }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">性格描述</span>
            <span class="profile-value text-long">{{ personalityDescription }}</span>
          </div>
        </div>
      </section>

      <!-- Personality params -->
      <section v-if="store.personality?.params" class="profile-section">
        <h2 class="section-title">性格参数</h2>
        <div class="params-card">
          <div class="param-row">
            <span class="param-label">夜猫子指数</span>
            <div class="param-bar">
              <div class="param-fill" :style="{ width: (store.personality.params.night_owl_index * 100) + '%' }" />
            </div>
            <span class="param-val">{{ (store.personality.params.night_owl_index * 100).toFixed(0) }}%</span>
          </div>
          <div class="param-row">
            <span class="param-label">焦虑敏感度</span>
            <div class="param-bar">
              <div class="param-fill" :style="{ width: (store.personality.params.anxiety_sensitivity * 100) + '%' }" />
            </div>
            <span class="param-val">{{ (store.personality.params.anxiety_sensitivity * 100).toFixed(0) }}%</span>
          </div>
          <div class="param-row">
            <span class="param-label">沉默程度</span>
            <div class="param-bar">
              <div class="param-fill" :style="{ width: (store.personality.params.quietness * 100) + '%' }" />
            </div>
            <span class="param-val">{{ (store.personality.params.quietness * 100).toFixed(0) }}%</span>
          </div>
          <div class="param-row">
            <span class="param-label">依恋程度</span>
            <div class="param-bar">
              <div class="param-fill" :style="{ width: (store.personality.params.attachment_level * 100) + '%' }" />
            </div>
            <span class="param-val">{{ (store.personality.params.attachment_level * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </section>

      <!-- Settings -->
      <section class="profile-section">
        <h2 class="section-title">设置</h2>
        <div class="settings-card">
          <button class="settings-row" @click="router.push('/settings')">
            <span>修改说话方式</span>
            <span class="arrow">→</span>
          </button>
          <button class="settings-row danger" @click="showResetConfirm = true">
            <span>重新初始化灵魂</span>
            <span class="arrow">→</span>
          </button>
        </div>
      </section>

      <!-- About -->
      <div class="about">
        <p>深夜施工队 · 小红书黑客松</p>
      </div>
    </div>

    <!-- Reset confirm -->
    <Transition name="fade">
      <div v-if="showResetConfirm" class="confirm-overlay" @click.self="showResetConfirm = false">
        <div class="confirm-card">
          <p class="confirm-text">确定要重新初始化灵魂吗？<br />所有纸条和记忆都会消失。</p>
          <div class="confirm-actions">
            <button class="confirm-cancel" @click="showResetConfirm = false">算了</button>
            <button class="confirm-danger" :disabled="resetting" @click="handleReset">
              {{ resetting ? '重置中...' : '确定重置' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <div class="tab-spacer" />
  </div>
</template>

<style scoped>
.me-page {
  min-height: 100dvh;
  background: var(--bg-dark);
  display: flex;
  flex-direction: column;
}

.me-header {
  padding: max(16px, env(safe-area-inset-top, 16px)) 20px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.me-title {
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 400;
  color: var(--text-light);
  letter-spacing: 0.04em;
}

.me-content {
  flex: 1;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  max-width: 440px;
  width: 100%;
  margin: 0 auto;
}

/* ═══════ Avatar ═══════ */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
}
.avatar-ring {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--accent-warm-dim);
  border: 2px solid rgba(232, 160, 76, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 8px;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.avatar-info {
  display: flex;
  gap: var(--space-sm);
}
.bias-tag,
.days-tag {
  font-size: 0.72rem;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  letter-spacing: 0.04em;
}
.bias-tag {
  background: var(--accent-warm-dim);
  color: var(--accent-warm);
  border: 1px solid rgba(232, 160, 76, 0.2);
}
.days-tag {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

/* ═══════ Stats ═══════ */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-md);
  gap: 4px;
}
.stat-num {
  font-size: 1.3rem;
  font-weight: 400;
  color: var(--text-light);
}
.stat-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

/* ═══════ Profile section ═══════ */
.section-title {
  font-size: 0.82rem;
  font-weight: 400;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  margin-bottom: var(--space-sm);
}

.profile-card,
.params-card,
.settings-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  gap: var(--space-md);
}
.profile-row:last-child {
  border-bottom: none;
}
.profile-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  flex-shrink: 0;
  letter-spacing: 0.04em;
}
.profile-value {
  font-size: 0.85rem;
  color: var(--text-light);
  text-align: right;
}
.profile-value.accent {
  color: var(--accent-warm);
}
.profile-value.text-long {
  font-size: 0.8rem;
  line-height: 1.6;
  max-width: 240px;
}

/* ═══════ Params ═══════ */
.param-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px var(--space-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.param-row:last-child {
  border-bottom: none;
}
.param-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  width: 80px;
  flex-shrink: 0;
}
.param-bar {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}
.param-fill {
  height: 100%;
  background: var(--accent-warm);
  border-radius: 3px;
  transition: width var(--duration-slow) var(--ease-out-expo);
}
.param-val {
  font-size: 0.7rem;
  color: var(--text-muted);
  width: 36px;
  text-align: right;
}

/* ═══════ Settings ═══════ */
.settings-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: var(--space-md);
  font-size: 0.88rem;
  color: var(--text-light);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background var(--duration-fast);
  text-align: left;
}
.settings-row:last-child { border-bottom: none; }
.settings-row:active { background: rgba(255, 255, 255, 0.03); }
.settings-row .arrow { color: var(--text-muted); font-size: 0.8rem; }
.settings-row.danger { color: var(--danger-soft); }

/* ═══════ About ═══════ */
.about {
  text-align: center;
  padding: var(--space-lg) 0;
}
.about p {
  font-size: 0.7rem;
  color: var(--text-muted);
  opacity: 0.4;
  letter-spacing: 0.08em;
}

/* ═══════ Confirm overlay ═══════ */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.confirm-card {
  background: var(--bg-dark);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  max-width: 320px;
  text-align: center;
}
.confirm-text {
  font-size: 0.9rem;
  color: var(--text-light);
  line-height: 1.8;
  margin-bottom: var(--space-lg);
}
.confirm-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
}
.confirm-cancel {
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.85rem;
  color: var(--text-muted);
  cursor: pointer;
}
.confirm-danger {
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.85rem;
  border-radius: var(--radius-full);
  border: 1px solid var(--danger-soft);
  color: var(--danger-soft);
  background: rgba(196, 116, 116, 0.1);
  cursor: pointer;
}
.confirm-danger:disabled { opacity: 0.4; cursor: not-allowed; }

.tab-spacer { height: 80px; flex-shrink: 0; }
</style>
