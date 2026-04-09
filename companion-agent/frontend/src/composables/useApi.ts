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
    playfulness: number
    attachment_level: number
  }
  natural_description: string
  voice_style: string
  evolution_log: Array<{
    day: number
    change: string
    reason: string
    timestamp: string
    personality_version?: number
    event_type?: string
    params_snapshot?: Record<string, unknown>
  }>
}

export interface FootprintParamDelta {
  key: string
  label: string
  delta: number
  before: number
  after: number
}

export interface FootprintEvent {
  id: string
  kind: 'personality' | 'soul'
  timestamp: string
  event_type: string
  label_zh: string
  day?: number
  personality_version?: number | null
  change?: string
  reason?: string
  params_snapshot?: Record<string, unknown>
  param_deltas: FootprintParamDelta[]
  soul_field?: string
  soul_field_label?: string
  old_value?: string
  new_value?: string
  summary?: string
  context_hint?: string
}

export interface FootprintOverview {
  soul_created_at: string
  days_together: number
  personality_version: number
  current_state_word: string
  struggle: string
  user_facts: string
  params: Record<string, unknown>
}

export interface FootprintTrendPoint {
  timestamp: string
  personality_version?: number | null
  params: Record<string, unknown>
}

export interface FootprintTimelineResponse {
  overview: FootprintOverview
  events: FootprintEvent[]
  trend_series: FootprintTrendPoint[]
}

export function getFootprintTimeline() {
  return request<FootprintTimelineResponse>('GET', '/api/footprint/timeline')
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

/* ---------- Desktop (Mac 上报 L4，前端拉取展示) ---------- */

export interface AppUsageRecord {
  app_name: string
  bundle_id: string
  duration_minutes: number
  category: string
}

export interface DesktopSnapshot {
  timestamp: string
  frontmost_app: string
  frontmost_category: string
  window_title_hint: string
  activity_summary: string
  hourly_usage: AppUsageRecord[]
  app_switch_count_last_hour: number
  screen_time_today_minutes: number
}

export interface DesktopContextData {
  updated_at: string
  current_snapshot: DesktopSnapshot
  daily_top_apps: AppUsageRecord[]
  avg_daily_screen_time_minutes: number
  work_pattern: string
}

/** 原始桌面上下文（与 Mac POST 写入一致） */
export function getDesktopContext() {
  return request<DesktopContextData>('GET', '/api/desktop/context')
}

/** 聚合结果：结构化 + 可读摘要，适合页面一次请求展示 */
export interface DesktopSummary {
  ok: boolean
  has_desktop: boolean
  context: DesktopContextData
  formatted: string
  work_pattern: string
  work_pattern_label_zh: string
}

export function getDesktopSummary() {
  return request<DesktopSummary>('GET', '/api/desktop/summary')
}
