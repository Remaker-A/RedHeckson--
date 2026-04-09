import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SoulData, SoulInput, StatusData, PersonalityData, RoomData, NoteData, PresetData, BiasType } from '../composables/useApi'
import * as api from '../composables/useApi'

export const useCompanionStore = defineStore('companion', () => {
  const soul = ref<SoulData | null>(null)
  const status = ref<StatusData | null>(null)
  const personality = ref<PersonalityData | null>(null)
  const room = ref<RoomData | null>(null)
  const notes = ref<NoteData[]>([])
  const latestWords = ref('')
  const sayLine = ref('')
  const loading = ref(false)
  const generatingNote = ref(false)
  const readNoteIds = ref<Set<string>>(new Set())
  const messageSending = ref(false)
  const wsConnected = ref(false)
  const presets = ref<PresetData[]>([])

  /* ---- Day/Night theme ---- */
  type ThemeMode = 'auto' | 'day' | 'night'
  const themeMode = ref<ThemeMode>((localStorage.getItem('theme_mode') as ThemeMode) || 'auto')

  const isNight = computed(() => {
    if (themeMode.value === 'day') return false
    if (themeMode.value === 'night') return true
    const h = new Date().getHours()
    return h >= 18 || h < 6
  })

  function setThemeMode(mode: ThemeMode) {
    themeMode.value = mode
    localStorage.setItem('theme_mode', mode)
  }

  const soulExists = computed(() => soul.value !== null)

  const unreadNoteCount = computed(() =>
    notes.value.filter(n => !readNoteIds.value.has(n.id)).length
  )

  async function checkSoul(): Promise<boolean> {
    try {
      soul.value = await api.getSoul()
      return true
    } catch {
      soul.value = null
      return false
    }
  }

  async function fetchSoul() {
    return checkSoul()
  }

  async function createSoul(input: SoulInput) {
    loading.value = true
    try {
      soul.value = await api.createSoul(input)
      await fetchPersonality()
      return soul.value
    } finally {
      loading.value = false
    }
  }

  async function refreshStatus() {
    try { status.value = await api.getStatus() } catch { /* ignore */ }
  }

  async function fetchStatus() {
    return refreshStatus()
  }

  async function fetchPersonality() {
    try {
      const p = await api.getPersonality()
      if ('error' in p && p.error) return
      personality.value = p as PersonalityData
    } catch {
      /* ignore */
    }
  }

  async function fetchPresets() {
    try {
      const resp = await api.getPresets()
      presets.value = resp.presets
    } catch { /* ignore */ }
  }

  async function updatePersonality(data: { bias?: BiasType; voice_style?: string }) {
    const p = await api.updatePersonality(data)
    personality.value = p
    await checkSoul()
    return p
  }

  async function fetchRoom() {
    try { room.value = await api.getRoom() } catch { /* ignore */ }
  }

  async function fetchNotes() {
    try { notes.value = await api.getNotes() } catch { /* ignore */ }
  }

  async function triggerGenerateNote() {
    generatingNote.value = true
    try {
      const note = await api.generateNote()
      notes.value.push(note)
      return note
    } finally {
      generatingNote.value = false
    }
  }

  function markNoteRead(id: string) {
    readNoteIds.value.add(id)
  }

  async function sendMessageWithMood(text: string, mood?: string) {
    messageSending.value = true
    try {
      await api.sendMessage(text, mood)
    } finally {
      messageSending.value = false
    }
  }

  function setLatestWords(text: string) {
    latestWords.value = text
  }

  function setSayLine(text: string) {
    sayLine.value = text
  }

  function clearSayLine() {
    sayLine.value = ''
  }

  function setWsConnected(val: boolean) {
    wsConnected.value = val
  }

  return {
    soul,
    status,
    personality,
    room,
    notes,
    latestWords,
    sayLine,
    loading,
    generatingNote,
    readNoteIds,
    messageSending,
    wsConnected,
    presets,
    soulExists,
    unreadNoteCount,
    checkSoul,
    fetchSoul,
    createSoul,
    refreshStatus,
    fetchStatus,
    fetchPersonality,
    fetchPresets,
    updatePersonality,
    fetchRoom,
    fetchNotes,
    triggerGenerateNote,
    markNoteRead,
    sendMessageWithMood,
    setLatestWords,
    setSayLine,
    clearSayLine,
    setWsConnected,
    themeMode,
    isNight,
    setThemeMode,
  }
})
