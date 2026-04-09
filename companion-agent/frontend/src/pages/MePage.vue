<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '../stores/companion'
import type { BiasType } from '../composables/useApi'

const router = useRouter()
const store = useCompanionStore()
const loaded = ref(false)
const isNight = computed(() => store.isNight)

/* ---- Reset ---- */
const showResetConfirm = ref(false)
const resetting = ref(false)

/* ---- Edit personality modal ---- */
const showEditModal = ref(false)
const editBias = ref<BiasType | ''>('')
const editVoice = ref('')
const saving = ref(false)

const biasLabels: Record<string, string> = {
  decisive: '安静笃定派',
  adventurous: '好奇冒险家',
  slow_down: '慢半拍先生',
  warm_humor: '温柔段子手',
  night_owl: '深夜陪伴者',
  bookish: '小小哲学家',
  custom: '自定义',
}

const biasOptions: Array<{ key: BiasType; label: string; desc: string }> = [
  { key: 'decisive', label: '安静笃定派', desc: '在你犹豫时，它会先迈出那一步' },
  { key: 'adventurous', label: '好奇冒险家', desc: '在你害怕时，它会说"试试看"' },
  { key: 'slow_down', label: '慢半拍先生', desc: '在你着急时，它会说"不急"' },
  { key: 'warm_humor', label: '温柔段子手', desc: '在你沮丧时，它会找到事情好玩的那一面' },
  { key: 'night_owl', label: '深夜陪伴者', desc: '在深夜还亮着的灯旁，它多说两句' },
  { key: 'bookish', label: '小小哲学家', desc: '从一件小事能想到很远的地方' },
]

const daysTogether = computed(() => {
  if (!store.soul?.created_at) return 0
  const created = new Date(store.soul.created_at)
  const now = new Date()
  return Math.max(1, Math.ceil((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24)))
})

const growthStage = computed(() => {
  const days = daysTogether.value
  if (days <= 1) return '初见'
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
  await Promise.all([store.fetchPersonality(), store.fetchNotes(), store.fetchPresets()])
  loaded.value = true
})

/* ---- Edit modal ---- */
function openEditModal() {
  editBias.value = (store.personality?.params?.bias as BiasType) || ''
  editVoice.value = store.personality?.voice_style || ''
  showEditModal.value = true
}

async function saveEdit() {
  if (!editBias.value) return
  saving.value = true
  try {
    await store.updatePersonality({
      bias: editBias.value,
      voice_style: editVoice.value.trim(),
    })
    showEditModal.value = false
  } finally {
    saving.value = false
  }
}

/* ---- Reset ---- */
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
  <div class="me-page" :class="{ night: isNight }">
    <header class="me-header">
      <h1 class="me-title">蓬蓬</h1>
    </header>

    <div v-if="loaded" class="me-content">
      <!-- Avatar section -->
      <div class="avatar-section">
        <div class="avatar-ring">
          <img
            :src="isNight ? '/assets/character/char-night.png' : '/assets/character/char-day.png'"
            alt="蓬蓬"
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
          <span class="stat-num">{{ growthStage }}</span>
          <span class="stat-label">成长阶段</span>
        </div>
      </div>

      <!-- Soul profile section -->
      <section class="profile-section">
        <h2 class="section-title">灵魂档案</h2>
        <div class="profile-card">
          <div class="profile-row">
            <span class="profile-label">当前状态</span>
            <span class="profile-value">{{ store.soul?.current_state_word || '-' }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">心里在想的事</span>
            <span class="profile-value text-long">{{ store.soul?.struggle || '-' }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">性格方向</span>
            <span class="profile-value accent">{{ biasLabels[store.soul?.bias ?? ''] || '-' }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">它的样子</span>
            <span class="profile-value text-long">{{ personalityDescription }}</span>
          </div>
        </div>
      </section>

      <!-- Settings -->
      <section class="profile-section">
        <h2 class="section-title">设置</h2>
        <div class="settings-card">
          <div class="settings-row theme-row">
            <span>外观模式</span>
            <div class="theme-toggle">
              <button
                :class="{ active: store.themeMode === 'auto' }"
                @click="store.setThemeMode('auto')"
              >自动</button>
              <button
                :class="{ active: store.themeMode === 'day' }"
                @click="store.setThemeMode('day')"
              >白天</button>
              <button
                :class="{ active: store.themeMode === 'night' }"
                @click="store.setThemeMode('night')"
              >夜晚</button>
            </div>
          </div>
          <button class="settings-row" @click="openEditModal">
            <span>修改它的性格</span>
            <span class="row-arrow">&rsaquo;</span>
          </button>
          <button class="settings-row danger" @click="showResetConfirm = true">
            <span>重新开始</span>
            <span class="row-arrow">&rsaquo;</span>
          </button>
        </div>
      </section>

      <!-- About -->
      <div class="about">
        <p>深夜施工队 · 小红书黑客松</p>
      </div>
    </div>

    <!-- ====== Edit personality modal ====== -->
    <Transition name="modal">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal-card">
          <div class="modal-header">
            <h3>修改它的性格</h3>
            <button class="modal-close" @click="showEditModal = false">&times;</button>
          </div>

          <div class="modal-body">
            <div class="edit-bias-list">
              <button
                v-for="opt in biasOptions"
                :key="opt.key"
                class="edit-bias-chip"
                :class="{ selected: editBias === opt.key }"
                @click="editBias = opt.key"
              >
                <span class="ebias-label">{{ opt.label }}</span>
                <span class="ebias-desc">{{ opt.desc }}</span>
              </button>
            </div>

            <label class="field-label">说话风格</label>
            <textarea
              v-model="editVoice"
              class="voice-textarea"
              rows="3"
              maxlength="800"
              placeholder="描述你希望它怎么和你说话..."
            />
          </div>

          <div class="modal-footer">
            <button class="modal-cancel" @click="showEditModal = false">取消</button>
            <button class="modal-save" :disabled="!editBias || saving" @click="saveEdit">
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ====== Reset confirm ====== -->
    <Transition name="modal">
      <div v-if="showResetConfirm" class="modal-overlay" @click.self="showResetConfirm = false">
        <div class="modal-card compact">
          <p class="confirm-text">确定要重新开始吗？<br />所有纸条和记忆都会消失。</p>
          <div class="confirm-actions">
            <button class="modal-cancel" @click="showResetConfirm = false">算了</button>
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
  background: #f5f0eb;
  display: flex;
  flex-direction: column;
  transition: background 0.8s ease;
}
.me-page.night {
  background: var(--bg-dark);
}

/* ═══════ Header ═══════ */
.me-header {
  padding: max(16px, env(safe-area-inset-top, 16px)) 20px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: border-color 0.8s ease;
}
.me-page.night .me-header {
  border-bottom-color: rgba(255, 255, 255, 0.04);
}
.me-title {
  font-family: var(--font-body);
  font-size: 1.2rem;
  font-weight: 400;
  color: var(--text-warm);
  letter-spacing: 0.04em;
}
.me-page.night .me-title {
  color: var(--text-light);
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
  background: rgba(255, 255, 255, 0.5);
  border: 2px solid rgba(139, 107, 74, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
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
  background: rgba(139, 107, 74, 0.1);
  color: #8b6b4a;
  border: 1px solid rgba(139, 107, 74, 0.15);
}
.days-tag {
  background: rgba(255, 255, 255, 0.45);
  color: #9a8e82;
  border: 1px solid rgba(61, 53, 48, 0.08);
}

/* ═══════ Stats ═══════ */
.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-sm);
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid rgba(61, 53, 48, 0.06);
  border-radius: var(--radius-md);
  gap: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  transition: background 0.8s ease, border-color 0.8s ease;
}
.me-page.night .stat-card {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: none;
}
.stat-num {
  font-size: 1.3rem;
  font-weight: 400;
  color: var(--text-warm);
}
.me-page.night .stat-num { color: var(--text-light); }
.stat-label {
  font-size: 12px;
  color: #9a8e82;
  letter-spacing: 0.06em;
}
.me-page.night .stat-label { color: var(--text-muted); }

/* ═══════ Profile section ═══════ */
.section-title {
  font-size: 13px;
  font-weight: 400;
  color: #9a8e82;
  letter-spacing: 0.08em;
  margin-bottom: var(--space-sm);
}
.me-page.night .section-title { color: var(--text-muted); }

.profile-card,
.settings-card {
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid rgba(61, 53, 48, 0.06);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: background 0.8s ease, border-color 0.8s ease;
}
.me-page.night .profile-card,
.me-page.night .settings-card {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-md);
  border-bottom: 1px solid rgba(61, 53, 48, 0.05);
  gap: var(--space-md);
}
.profile-row:last-child { border-bottom: none; }
.me-page.night .profile-row { border-bottom-color: rgba(255, 255, 255, 0.05); }
.profile-label {
  font-size: 13px;
  color: #9a8e82;
  flex-shrink: 0;
  letter-spacing: 0.04em;
}
.me-page.night .profile-label { color: rgba(180, 170, 160, 0.7); }
.profile-value {
  font-size: 14px;
  color: var(--text-warm);
  text-align: right;
}
.me-page.night .profile-value { color: var(--text-light); }
.profile-value.accent { color: #8b6b4a; }
.me-page.night .profile-value.accent { color: var(--accent-warm); }
.profile-value.text-long {
  font-size: 13px;
  line-height: 1.6;
  max-width: 240px;
}

/* ═══════ Settings ═══════ */
.settings-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: var(--space-md);
  font-size: 14px;
  color: var(--text-warm);
  border-bottom: 1px solid rgba(61, 53, 48, 0.05);
  cursor: pointer;
  transition: background var(--duration-fast);
  text-align: left;
}
.me-page.night .settings-row { color: var(--text-light); border-bottom-color: rgba(255, 255, 255, 0.05); }
.settings-row:last-child { border-bottom: none; }
.settings-row:active { background: rgba(139, 107, 74, 0.06); }
.me-page.night .settings-row:active { background: rgba(255, 255, 255, 0.03); }
.row-arrow { color: #b0a598; font-size: 1.2rem; }
.settings-row.danger { color: #c47474; }

/* Theme toggle */
.theme-row {
  cursor: default;
}
.theme-row:active {
  background: transparent !important;
}
.theme-toggle {
  display: flex;
  gap: 0;
  background: rgba(0, 0, 0, 0.05);
  border-radius: var(--radius-full);
  padding: 2px;
}
.me-page.night .theme-toggle {
  background: rgba(255, 255, 255, 0.06);
}
.theme-toggle button {
  font-size: 0.72rem;
  padding: 5px 14px;
  border-radius: var(--radius-full);
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out-expo);
}
.theme-toggle button.active {
  background: rgba(255, 255, 255, 0.8);
  color: var(--text-warm);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}
.me-page.night .theme-toggle button.active {
  background: rgba(232, 160, 76, 0.2);
  color: var(--accent-warm);
  box-shadow: none;
}

/* ═══════ About ═══════ */
.about {
  text-align: center;
  padding: var(--space-lg) 0;
}
.about p {
  font-size: 0.7rem;
  color: #b0a598;
  letter-spacing: 0.08em;
}

/* ═══════ Modal ═══════ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 200;
}
.modal-card {
  width: 100%;
  max-width: 440px;
  max-height: 85dvh;
  background: #f5efe7;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.1);
}
.modal-card.compact {
  border-radius: var(--radius-lg);
  margin: auto;
  max-width: 320px;
  padding: var(--space-xl);
  text-align: center;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg) var(--space-lg) var(--space-md);
  flex-shrink: 0;
}
.modal-header h3 {
  font-size: 1.1rem;
  font-weight: 400;
  color: var(--text-warm);
  letter-spacing: 0.04em;
}
.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: #9a8e82;
  cursor: pointer;
  border-radius: 50%;
  transition: background var(--duration-fast);
}
.modal-close:hover { background: rgba(61, 53, 48, 0.06); }

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-lg) var(--space-md);
}

/* ---- Edit bias list ---- */
.edit-bias-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}
.edit-bias-chip {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid rgba(61, 53, 48, 0.08);
  border-radius: var(--radius-md);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.5);
  transition: all var(--duration-normal) var(--ease-out-expo);
}
.edit-bias-chip:hover {
  border-color: rgba(139, 107, 74, 0.25);
}
.edit-bias-chip.selected {
  border-color: #8b6b4a;
  background: rgba(139, 107, 74, 0.1);
}
.ebias-label {
  font-size: 0.95rem;
  color: var(--text-warm);
}
.edit-bias-chip.selected .ebias-label { color: #8b6b4a; }
.ebias-desc {
  font-size: 0.78rem;
  color: #9a8e82;
  line-height: 1.4;
}

.field-label {
  display: block;
  font-size: 0.82rem;
  color: #9a8e82;
  margin-bottom: var(--space-sm);
  letter-spacing: 0.04em;
}
.voice-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: var(--space-md);
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--text-warm);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(61, 53, 48, 0.1);
  border-radius: var(--radius-md);
  resize: none;
}
.voice-textarea:focus {
  outline: none;
  border-color: rgba(139, 107, 74, 0.35);
}
.voice-textarea::placeholder { color: #b0a598; }

/* ---- Modal footer ---- */
.modal-footer {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  padding-bottom: calc(var(--space-lg) + env(safe-area-inset-bottom));
  border-top: 1px solid rgba(61, 53, 48, 0.06);
  flex-shrink: 0;
}
.modal-cancel {
  flex: 1;
  padding: var(--space-md);
  font-size: 0.9rem;
  color: #9a8e82;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: background var(--duration-fast);
}
.modal-cancel:hover { background: rgba(61, 53, 48, 0.05); }
.modal-save {
  flex: 1;
  padding: var(--space-md);
  font-size: 0.9rem;
  color: #f5efe7;
  background: #8b6b4a;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: opacity var(--duration-fast);
}
.modal-save:hover:not(:disabled) { opacity: 0.9; }
.modal-save:disabled { opacity: 0.4; cursor: not-allowed; }

/* ---- Confirm ---- */
.confirm-text {
  font-size: 0.9rem;
  color: var(--text-warm);
  line-height: 1.8;
  margin-bottom: var(--space-lg);
}
.confirm-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
}
.confirm-danger {
  padding: var(--space-sm) var(--space-lg);
  font-size: 0.85rem;
  border-radius: var(--radius-full);
  border: 1px solid #c47474;
  color: #c47474;
  background: rgba(196, 116, 116, 0.08);
  cursor: pointer;
}
.confirm-danger:disabled { opacity: 0.4; cursor: not-allowed; }

/* ---- Modal transitions ---- */
.modal-enter-active { transition: all 0.35s var(--ease-out-expo); }
.modal-leave-active { transition: all 0.25s ease; }
.modal-enter-from .modal-card { transform: translateY(100%); }
.modal-leave-to .modal-card { transform: translateY(100%); }
.modal-enter-from { opacity: 0; }
.modal-leave-to { opacity: 0; }

.tab-spacer { height: 80px; flex-shrink: 0; }
</style>
