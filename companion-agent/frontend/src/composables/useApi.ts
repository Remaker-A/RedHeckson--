const BASE = ''

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body) opts.body = JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${method} ${path} → ${res.status}: ${text}`)
  }
  return res.json()
}

/* ---------- Soul ---------- */

export type BiasType = 'decisive' | 'adventurous' | 'slow_down' | 'warm_humor' | 'night_owl' | 'bookish' | 'custom'

export interface SoulInput {
  current_state_word: string
  struggle: string
  bias: BiasType
  custom_voice_style?: string
}

export interface SoulData {
  created_at: string
  current_state_word: string
  struggle: string
  bias: string
  opening_response: string
}

export async function createSoul(data: SoulInput): Promise<SoulData> {
  const resp = await request<{ ok: boolean; soul: SoulData }>('POST', '/api/soul', data)
  return resp.soul
}

export function getSoul() {
  return request<SoulData>('GET', '/api/soul')
}

export function resetSoul() {
  return request<{ ok: boolean }>('DELETE', '/api/soul')
}

/* ---------- Status ---------- */

export interface StatusData {
  state: string
  state_since: string
  seated_minutes: number
  distance_cm: number
  time_period: string
  today_total_minutes: number
  is_night: boolean
  focus: {
    active: boolean
    duration_minutes: number
    started_at: string | null
  }
}

export function getStatus() {
  return request<StatusData>('GET', '/api/status')
}

/* ---------- Personality ---------- */

export interface PersonalityData {
  version: number
  updated_at: string
  params: {
    bias: string
    night_owl_index: number
    anxiety_sensitivity: number
    quietness: number
    attachment_level: number
  }
  natural_description: string
  voice_style: string
  evolution_log: Array<{
    day: number
    change: string
    reason: string
    timestamp: string
  }>
}

export function getPersonality() {
  return request<PersonalityData>('GET', '/api/personality')
}

/* ---------- Personality Presets ---------- */

export interface PresetData {
  key: string
  label: string
  short_desc: string
  voice_style: string
  default_params: Record<string, unknown>
}

export function getPresets() {
  return request<{ presets: PresetData[] }>('GET', '/api/personality/presets')
}

export function updatePersonality(data: { bias?: BiasType; voice_style?: string }) {
  return request<PersonalityData>('PATCH', '/api/personality', data)
}

/* ---------- Room ---------- */

export type RoomScene = 'tidy' | 'messy' | 'night' | 'dusty' | 'recovering'

export interface RoomData {
  scene: RoomScene
  details: {
    description: string
    light: string
    items: string[]
    creature_state: string
  }
}

export function getRoom() {
  return request<RoomData>('GET', '/api/room')
}

/* ---------- Notes ---------- */

export interface NoteData {
  id: string
  content: string
  created_at: string
  personality_version: number
}

export function getNotes() {
  return request<NoteData[]>('GET', '/api/notes')
}

export function getLatestNote() {
  return request<NoteData>('GET', '/api/notes/latest')
}

export function generateNote() {
  return request<NoteData>('POST', '/api/notes/generate')
}

/* ---------- Interaction ---------- */

export function sendMessage(text: string, mood?: string) {
  return request<{ ok: boolean }>('POST', '/api/message', { content: text, mood })
}

export function sendMood(mood: string) {
  return request<{ ok: boolean }>('POST', '/api/mood', { mood })
}

/* ---------- Focus ---------- */

export interface FocusData {
  active: boolean
  started_at: string | null
  duration_minutes: number
}

export function startFocus(duration_minutes = 25) {
  return request<StatusData>('POST', '/api/focus/start', { duration_minutes })
}

export function stopFocus() {
  return request<StatusData>('POST', '/api/focus/stop')
}

export function getFocus() {
  return request<FocusData>('GET', '/api/focus')
}

/* ---------- Simulate (dev/demo) ---------- */

export function simArrive() {
  return request<StatusData>('POST', '/api/sim/person-arrive')
}

export function simSit() {
  return request<StatusData>('POST', '/api/sim/person-sit')
}

export function simLeave() {
  return request<StatusData>('POST', '/api/sim/person-leave')
}

export function simSetDistance(distance_cm: number) {
  return request<StatusData>('POST', '/api/sim/set-distance', { distance_cm })
}

export function simSetTime(hour: number, minute = 0) {
  return request<Record<string, unknown>>('POST', '/api/sim/set-time', { hour, minute })
}

export interface FastForwardResult {
  days_generated: number
  records: number
  late_night_ratio: number
  regularity_score: number
  personality: PersonalityData | null
}

export function simFastForward(days = 7, late_night_ratio = 0.3, focus_ratio = 0.4) {
  return request<FastForwardResult>('POST', '/api/sim/fast-forward', { days, late_night_ratio, focus_ratio })
}
