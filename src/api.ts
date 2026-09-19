// Single API client for the SMRTBuddy backend (see FRONTEND_CONTRACT.md).
// Base URL: same origin when served by FastAPI at /ui; override with
// VITE_API_BASE at build time or ?api=http://host:port at runtime (dev).
const runtimeBase = new URLSearchParams(window.location.search).get('api')
export const API_BASE: string = runtimeBase ?? import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `HTTP ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(API_BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(res.status, (data as { detail?: unknown }).detail ?? data)
  return data as T
}

// --- contract types (the fields this UI reads) ---------------------------------

export type Leg = {
  mode: 'walk' | 'bus' | 'mrt' | 'taxi'
  from_name: string
  to_name: string
  service: string | null
  depart: string
  arrive: string
  instruction: string
  speech_text: string
  shelter: 'covered' | 'partial' | 'exposed'
  step_free: 'verified' | 'unverified' | 'not_step_free'
  geometry: [number, number][]
  crowding: 'low' | 'medium' | 'high' | null
}

export type Advice = {
  action: 'proceed' | 'wait' | 'reroute' | 'leave_earlier' | 'take_taxi' | 'cancel_trip'
  headline: string
  speech_text: string
  reason: string
  triggered_by: string[]
  decide_by: string | null
  eta_range: [string, string]
  confidence: 'high' | 'medium' | 'low'
  notify_family: boolean
  data_status: Record<string, string>
  legs: Leg[]
  affected_segment: [number, number][] | null
  alternatives: Leg[][]
  driver_card: { destination_en: string; destination_zh: string; arrive_by: string } | null
}

export type Journey = {
  journey_id: string
  origin: string
  destination: string
  arrive_by: string
  scenario: string | null
}

export type LocationAck = {
  journey_id: string
  received_at: string
  wrong_direction: boolean
  notify_family: boolean
}

export type SosResponse = {
  sos_id: string
  status: 'awaiting_confirmation' | 'confirmed'
  notified_user_ids: string[]
}

// Structured 422 the backend returns for unsupported journeys.
export type CorridorHelp = {
  error: 'outside_demo_corridor'
  message: string
  supported_corridor: string
  try: { origin: string; destination: string }
  why_limited: string
}

export function corridorHelp(err: unknown): CorridorHelp | null {
  if (err instanceof ApiError && typeof err.detail === 'object' && err.detail !== null
      && (err.detail as CorridorHelp).error === 'outside_demo_corridor') {
    return err.detail as CorridorHelp
  }
  return null
}

// --- demo scenarios (labelled replay/injected data, PS2 brief §2.6) -------------

export const SCENARIOS = [
  { id: 'clear_day', label: 'Clear day' },
  { id: 'rain', label: 'Heavy rain', preferMode: 'bus' as const },
  { id: 'disruption_on_train', label: 'Disruption (on train)', onTrain: true },
  { id: 'lift_outage', label: 'Lift out of service' },
  { id: 'flood_destination', label: 'Flood at destination' },
  { id: 'crowding_forecast', label: 'Crowding forecast' },
] as const
export type ScenarioId = (typeof SCENARIOS)[number]['id']

const USER = 'mdm_lim'
const FAMILY = 'daughter'
// A position between Paya Lebar and Aljunied, matching the fixture story:
// she is on the train when the disruption lands.
const ON_TRAIN_PING = { lat: 1.3178, lon: 103.8927, accuracy_m: 25 }

export type ProfileOptions = {
  locale: 'en' | 'zh' | 'ms' | 'ta'
  can_use_stairs: boolean
  wheelchair: boolean
  walking_speed_mps: number
  max_walk_metres: number
  prefers_shelter: boolean
}
// Mdm Lim's defaults (the persona in the brief); overwritten by the profile
// setup screen. POST /profiles upserts, so saving again just updates.
export const DEFAULT_PROFILE: ProfileOptions = {
  locale: 'en', can_use_stairs: false, wheelchair: false,
  walking_speed_mps: 0.8, max_walk_metres: 600, prefers_shelter: false,
}
let currentProfile: ProfileOptions = { ...DEFAULT_PROFILE }
let profilesReady = false

export async function saveProfile(opts: ProfileOptions): Promise<void> {
  currentProfile = { ...opts }
  await call('POST', '/profiles', {
    user_id: USER, role: 'user', name: 'Mdm Lim', locale: opts.locale,
    mobility: { can_use_stairs: opts.can_use_stairs, wheelchair: opts.wheelchair,
                walking_speed_mps: opts.walking_speed_mps, max_walk_metres: opts.max_walk_metres,
                prefers_shelter: opts.prefers_shelter },
  })
  await call('POST', '/profiles', { user_id: FAMILY, role: 'family', name: 'Trusted family' })
  await call('POST', `/profiles/${FAMILY}/link`, { linked_user_id: USER })
  profilesReady = true
}

export async function ensureProfiles(): Promise<void> {
  if (profilesReady) return
  await saveProfile(currentProfile)
}

function arriveBy(): string {
  // Next 10:00 SGT: keeps the demo journey in the future without inventing times.
  const now = new Date()
  const sgt = new Date(now.getTime() + (480 + now.getTimezoneOffset()) * 60000)
  const day = new Date(sgt)
  if (sgt.getHours() >= 9) day.setDate(day.getDate() + 1)
  const y = day.getFullYear(), m = String(day.getMonth() + 1).padStart(2, '0'), d = String(day.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}T10:00:00+08:00`
}

export async function createJourney(destination: string, scenario: ScenarioId | StageId): Promise<Journey> {
  await ensureProfiles()
  const spec = SCENARIOS.find((s) => s.id === scenario)
  const body: Record<string, unknown> = {
    user_id: USER, origin: 'Home (Bedok)', destination,
    arrive_by: arriveBy(), scenario,
  }
  if (spec && 'preferMode' in spec) body.prefer_mode = spec.preferMode
  const journey = await call<Journey>('POST', '/journeys', body)
  if (spec && 'onTrain' in spec) {
    await postLocation(journey.journey_id, 'on_train', undefined, true)
  }
  return journey
}


// --- the three-stage demo (see FRONTEND_CONTRACT.md, "The three-stage demo").
// One journey, escalating events; every stage runs through the real engine
// from her pinged position. Fixtures are labelled; the UI shows the REPLAY tag.
export const STAGES = [
  { id: 'demo_stage1_peak_crowding', ping: null },
  { id: 'demo_stage2_planned_closure',
    ping: { lat: 1.317585, lon: 103.892281, accuracy_m: 25 } },  // Paya Lebar
  { id: 'demo_stage3_breakdown',
    ping: { lat: 1.281812, lon: 103.859152, accuracy_m: 25 } },  // Bayfront
] as const
export type StageId = (typeof STAGES)[number]['id']

export async function runStage(stage: StageId): Promise<{ journey: Journey; advice: Advice }> {
  const spec = STAGES.find((s) => s.id === stage)!
  const journey = await createJourney('Singapore General Hospital', stage)
  if (spec.ping) await postLocation(journey.journey_id, 'on_train', spec.ping, true)
  return { journey, advice: await getAdvice(journey.journey_id) }
}

export function getAdvice(journeyId: string): Promise<Advice> {
  return call('GET', `/journeys/${journeyId}/advice`)
}

export function postLocation(journeyId: string,
                             state: 'at_home' | 'walking' | 'on_bus' | 'on_train' | 'on_platform',
                             coords?: { lat: number; lon: number; accuracy_m?: number },
                             setState = false): Promise<LocationAck> {
  // Pings are transient unless setState is true (a deliberate state change,
  // e.g. she boarded the train). See FRONTEND_CONTRACT.md.
  const p = coords ?? ON_TRAIN_PING
  return call('POST', `/journeys/${journeyId}/location`, {
    ...p, recorded_at: new Date().toISOString(), location_state: state, set_state: setState,
  })
}

export async function sosOpen(): Promise<SosResponse> {
  await ensureProfiles()
  return call('POST', '/sos', { user_id: USER })
}

export function sosConfirm(sosId: string): Promise<SosResponse> {
  return call('POST', '/sos', { user_id: USER, sos_id: sosId, confirm: true })
}

export function anyFixture(advice: Advice): boolean {
  return Object.values(advice.data_status).some((v) => v === 'fixture')
}

export function fmtTime(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
}
