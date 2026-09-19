import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, ChevronRight, CircleHelp, HeartHandshake, Home, LocateFixed, LockKeyhole, MapPin, Mic, Navigation, Pause, Phone, RotateCcw, ShieldCheck, Square, Trash2, UserRound, Volume2, X } from 'lucide-react'
import { guideCopy, languages, screenLabels, type Locale, type ScreenId } from './data'
import { legPhoto } from './legMedia'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { uiCopy, type UiCopy } from './uiCopy'
import * as api from './api'

type SpeechEvent = { results: ArrayLike<{ 0: { transcript: string } }> }
type SpeechErrorEvent = { error?: string }
type Recognition = { lang: string; interimResults: boolean; continuous: boolean; onresult: ((event: SpeechEvent) => void) | null; onerror: ((event: SpeechErrorEvent) => void) | null; onend: (() => void) | null; start: () => void; stop: () => void }
type LocationState = 'idle' | 'requesting' | 'active' | 'denied' | 'timeout' | 'unavailable' | 'service-error'
const storageKey = 'mdm-lim-locale'

function App() {
  const [screen, setScreen] = useState<ScreenId>('language')
  const [locale, setLocale] = useState<Locale>(() => { const saved = localStorage.getItem(storageKey); return saved === 'zh' || saved === 'ms' || saved === 'ta' ? saved : 'en' })
  const [destination, setDestination] = useState('')
  const [transcript, setTranscript] = useState('')
  const [notice, setNotice] = useState('')
  const [confirm, setConfirm] = useState<{ title: string; body: string; action: string; onConfirm?: () => void } | null>(null)
  // --- live journey state (wired to the backend; see src/api.ts) ---
  const [scenario, setScenario] = useState<api.ScenarioId | api.StageId>('disruption_on_train')
  const [journey, setJourney] = useState<api.Journey | null>(null)
  const [advice, setAdvice] = useState<api.Advice | null>(null)
  const [corridor, setCorridor] = useState<api.CorridorHelp | null>(null)
  const [busy, setBusy] = useState(false)
  const [activeStep, setActiveStep] = useState(0)
  const [locationState, setLocationState] = useState<LocationState>('idle')
  const [lastLocationAt, setLastLocationAt] = useState<Date | null>(null)
  const watchRef = useRef<number | null>(null)
  const copy = uiCopy[locale]
  useEffect(() => localStorage.setItem(storageKey, locale), [locale])
  useEffect(() => () => { if (watchRef.current !== null) navigator.geolocation.clearWatch(watchRef.current) }, [])
  const navigate = (next: ScreenId) => { setNotice(''); setConfirm(null); setScreen(next) }
  const selectLocale = (next: Locale) => setLocale(next)

  const planJourney = async (dest: string, useScenario: api.ScenarioId | api.StageId = scenario) => {
    const target = dest.trim() || 'Singapore General Hospital'
    setBusy(true); setCorridor(null); setNotice('')
    try {
      const created = await api.createJourney(target, useScenario)
      setJourney(created)
      setAdvice(await api.getAdvice(created.journey_id))
      setScenario(useScenario)
      navigate('overview')
    } catch (err) {
      const help = api.corridorHelp(err)
      if (help) { setCorridor(help); navigate('plan') }
      else setNotice(err instanceof Error ? `Could not reach the journey service. ${err.message}` : 'Could not reach the journey service.')
    } finally { setBusy(false) }
  }

  const runStage = async (stage: api.StageId) => {
    setBusy(true); setNotice(''); setCorridor(null)
    try {
      const result = await api.runStage(stage)
      setJourney(result.journey); setAdvice(result.advice); setScenario(stage); setActiveStep(0)
      navigate('overview')
    } catch (err) {
      setNotice(err instanceof Error ? `Could not run the demo stage. ${err.message}` : 'Could not run the demo stage.')
    } finally { setBusy(false) }
  }

  const startJourney = async () => {
    if (!window.isSecureContext) { setLocationState('unavailable'); return }
    if (!navigator.geolocation) { setLocationState('unavailable'); return }
    setLocationState('requesting')
    navigator.geolocation.getCurrentPosition(async (position) => {
      setLastLocationAt(new Date(position.timestamp))
      try {
        if (journey) await api.postLocation(journey.journey_id, 'walking', { lat: position.coords.latitude, lon: position.coords.longitude, accuracy_m: position.coords.accuracy })
      } catch { setLocationState('service-error'); return }
      setLocationState('active'); setActiveStep(0); navigate('guide')
      watchRef.current = navigator.geolocation.watchPosition((next) => {
        setLastLocationAt(new Date(next.timestamp))
        if (journey) void api.postLocation(journey.journey_id, 'walking', { lat: next.coords.latitude, lon: next.coords.longitude, accuracy_m: next.coords.accuracy }).catch(() => setLocationState('service-error'))
      }, () => setLocationState('denied'), { enableHighAccuracy: true, maximumAge: 15000, timeout: 10000 })
    }, (error) => setLocationState(error.code === error.PERMISSION_DENIED ? 'denied' : error.code === error.TIMEOUT ? 'timeout' : 'unavailable'), { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 })
  }
  const continueWithoutSharing = () => { setLocationState('idle'); setActiveStep(0); navigate('guide') }
  const finishJourney = () => { if (watchRef.current !== null) navigator.geolocation.clearWatch(watchRef.current); watchRef.current = null; setLocationState('idle'); navigate('arrived') }
  const newJourney = () => { setJourney(null); setAdvice(null); setActiveStep(0); setDestination(''); navigate('plan') }
  return <main className="prototype-shell">
    <PrototypeNav screen={screen} locale={locale} activeStep={activeStep} legCount={advice?.legs.length ?? 0} navigate={navigate} selectLocale={selectLocale} setActiveStep={setActiveStep} />
    <section className="device-stage" aria-label="Mdm Lim commuter companion prototype"><div className={`phone locale-${locale}`} data-screen={screen}>
      {screen === 'language' && <LanguageScreen locale={locale} copy={copy} selectLocale={selectLocale} next={() => navigate('profile')} />}
      {screen === 'profile' && <ProfileScreen copy={copy} back={() => navigate('language')} traveller={() => navigate('profile-setup')} family={() => navigate('family')} />}
      {screen === 'profile-setup' && <ProfileSetupScreen locale={locale} copy={copy} back={() => navigate('profile')} done={() => navigate('plan')} />}
      {screen === 'plan' && <PlanScreen copy={copy} destination={destination} setDestination={setDestination} back={() => navigate('profile')} listen={() => navigate('listening')} busy={busy} corridor={corridor} tryCorridor={() => { setCorridor(null); setDestination('Singapore General Hospital'); void planJourney('Singapore General Hospital') }} next={() => { void planJourney(destination) }} />}
      {screen === 'listening' && <ListeningScreen locale={locale} transcript={transcript} setTranscript={setTranscript} back={() => navigate('plan')} accept={() => { setDestination(transcript); void planJourney(transcript) }} busy={busy} />}
      {screen === 'overview' && <OverviewScreen locale={locale} copy={copy} advice={advice} journey={journey} busy={busy} scenario={scenario} runStage={runStage} back={() => navigate('plan')} start={() => navigate('sharing')} notice={notice} />}
      {screen === 'sharing' && <SharingScreen copy={copy} state={locationState} start={() => { void startJourney() }} continueWithout={continueWithoutSharing} back={() => navigate('overview')} />}
      {screen === 'guide' && <GuideScreen locale={locale} activeStep={activeStep} advice={advice} locationState={locationState} lastLocationAt={lastLocationAt} back={() => navigate('overview')} next={() => setActiveStep((step) => Math.min((advice?.legs.length ?? 1) - 1, step + 1))} finish={finishJourney} lost={() => navigate('wrong-way')} sos={() => navigate('sos')} />}
      {screen === 'wrong-way' && <WrongWayScreen locale={locale} journey={journey} back={() => navigate('guide')} correct={() => navigate('guide')} call={() => navigate('sos')} />}
      {screen === 'sos' && <SosScreen locale={locale} back={() => navigate('guide')} record={() => navigate('recording')} confirm={setConfirm} setNotice={setNotice} />}
      {screen === 'recording' && <RecordingScreen back={() => navigate('sos')} />}
      {screen === 'arrived' && <ArrivedScreen copy={copy} locale={locale} journey={journey} again={newJourney} />}
      {screen === 'family' && <FamilyAccessScreen back={() => navigate('profile')} next={() => navigate('family-journey')} />}
      {screen === 'family-journey' && <FamilyJourneyScreen back={() => navigate('family')} />}
      {notice && screen !== 'listening' && screen !== 'overview' && <div className="toast" role="status">{notice}</div>}
      {confirm && <ConfirmSheet {...confirm} cancel={copy.cancel} close={() => setConfirm(null)} />}
    </div></section>
  </main>
}

function PrototypeNav({ screen, locale, activeStep, legCount, navigate, selectLocale, setActiveStep }: { screen: ScreenId; locale: Locale; activeStep: number; legCount: number; navigate: (screen: ScreenId) => void; selectLocale: (locale: Locale) => void; setActiveStep: (step: number) => void }) {
  return <aside className="prototype-nav" aria-label="Pitch demo navigation"><div className="prototype-brand"><span className="signal-mark"><i /><i /><i /></span><div><strong>Mdm Lim</strong><span>Commuter companion</span></div></div><p className="prototype-note">Jump to any judging moment. This panel is hidden on phones.</p><nav>{screenLabels.map((item, index) => <div key={item.id}>{item.group !== screenLabels[index - 1]?.group && <span className="nav-group">{item.group}</span>}<button className={screen === item.id ? 'active' : ''} onClick={() => navigate(item.id)}><span>{item.label}</span><ChevronRight size={18} /></button></div>)}</nav>{legCount > 0 && <><span className="nav-group">Live step</span><div className="nav-step-grid">{Array.from({ length: legCount }).map((_, index) => <button key={index} className={screen === 'guide' && activeStep === index ? 'active' : ''} onClick={() => { setActiveStep(index); navigate('guide') }}>{index + 1}</button>)}</div></>}<div className="nav-languages"><span className="nav-group">Step language</span><div>{languages.map((item) => <button key={item.id} className={locale === item.id ? 'active' : ''} onClick={() => selectLocale(item.id)}>{item.code}</button>)}</div></div></aside>
}

function BackButton({ onClick, light = false, label = 'Go back' }: { onClick: () => void; light?: boolean; label?: string }) { return <button className={`back-button${light ? ' light' : ''}`} onClick={onClick} aria-label={label}><ArrowLeft /></button> }
function TopBar({ title, back }: { title: string; back: () => void }) { return <header className="top-bar"><BackButton onClick={back} /><strong>{title}</strong><span /></header> }
function PrimaryButton({ children, onClick, disabled = false }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) { return <button className="primary-button" onClick={onClick} disabled={disabled}>{children}</button> }
function SecondaryButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) { return <button className="secondary-button" onClick={onClick}>{children}</button> }

function LanguageScreen({ locale, copy, selectLocale, next }: { locale: Locale; copy: UiCopy; selectLocale: (locale: Locale) => void; next: () => void }) {
  return <div className={`screen language-screen locale-${locale}`}><section className="language-sheet"><p className="welcome">{copy.language.welcome}</p><h1>{copy.language.title}</h1><p className="helper">{copy.language.helper}</p><div className="language-list" role="radiogroup" aria-label={copy.language.aria}>{languages.map((item) => <button key={item.id} className={locale === item.id ? 'selected' : ''} onClick={() => selectLocale(item.id)} role="radio" aria-checked={locale === item.id}><span>{item.label}</span><b>{item.code}</b></button>)}</div><PrimaryButton onClick={next}>{copy.language.continue}</PrimaryButton></section></div>
}

function ProfileScreen({ copy, back, traveller, family }: { copy: UiCopy; back: () => void; traveller: () => void; family: () => void }) {
  return <div className="screen paper-screen profile-screen"><TopBar title={copy.profile.top} back={back} /><h1>{copy.profile.title}</h1><div className="role-list"><button onClick={traveller}><b>A</b><span><strong>{copy.profile.traveller}</strong><small>{copy.profile.travellerDetail}</small></span><ArrowRight /></button><button onClick={family}><b>B</b><span><strong>{copy.profile.family}</strong><small>{copy.profile.familyDetail}</small></span><ArrowRight /></button></div><p className="consent-copy">{copy.profile.consent}</p></div>
}


// Profile setup: every control maps 1:1 to a backend MobilityProfile field and
// is saved via POST /profiles, so the choices genuinely change the advice.
// Pace mapping: "slowly" = 0.8 m/s (the persona default), "average" = 1.4 m/s
// (a typical adult walking pace; a routing parameter, not a measurement).
function ProfileSetupScreen({ locale, copy, back, done }: { locale: Locale; copy: UiCopy; back: () => void; done: () => void }) {
  const [stairs, setStairs] = useState(false)        // can_use_stairs
  const [wheelchair, setWheelchair] = useState(false)
  const [slow, setSlow] = useState(true)             // walking_speed_mps
  const [maxWalk, setMaxWalk] = useState(600)        // max_walk_metres
  const [shelter, setShelter] = useState(false)      // prefers_shelter
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const save = async () => {
    setSaving(true); setError('')
    try {
      await api.saveProfile({ locale, can_use_stairs: stairs, wheelchair,
        walking_speed_mps: slow ? 0.8 : 1.4, max_walk_metres: maxWalk, prefers_shelter: shelter })
      done()
    } catch { setError(copy.setup.failed) } finally { setSaving(false) }
  }
  const pair = (label: string, value: boolean, set: (v: boolean) => void, yes: string, no: string) =>
    <fieldset className="setup-field"><legend>{label}</legend><div className="setup-pair">
      <button type="button" className={!value ? 'selected' : ''} aria-pressed={!value} onClick={() => set(false)}>{no}</button>
      <button type="button" className={value ? 'selected' : ''} aria-pressed={value} onClick={() => set(true)}>{yes}</button>
    </div></fieldset>
  return <div className={`screen paper-screen setup-screen locale-${locale}`}><TopBar title={copy.setup.top} back={back} /><h1>{copy.setup.title}</h1>
    {pair(copy.setup.shelter, shelter, setShelter, copy.setup.shelterYes, copy.setup.shelterNo)}
    {pair(copy.setup.stairs, stairs, setStairs, copy.setup.stairsOk, copy.setup.stairsAvoid)}
    {pair(copy.setup.wheelchair, wheelchair, setWheelchair, copy.setup.wcYes, copy.setup.wcNo)}
    {pair(copy.setup.pace, !slow, (v) => setSlow(!v), copy.setup.paceAvg, copy.setup.paceSlow)}
    <fieldset className="setup-field"><legend>{copy.setup.walk}</legend><div className="setup-pair walk-options">
      {[200, 400, 600, 800].map((m) => <button type="button" key={m} className={maxWalk === m ? 'selected' : ''} aria-pressed={maxWalk === m} onClick={() => setMaxWalk(m)}>{copy.setup.metres(m)}</button>)}
    </div></fieldset>
    {error && <p className="overview-notice" role="alert">{error}</p>}
    <div className="screen-actions"><PrimaryButton onClick={() => { void save() }} disabled={saving}>{saving ? copy.setup.saving : copy.setup.save}</PrimaryButton></div></div>
}

function PlaceField({ label, value, placeholder, icon, onChange, listen }: { label: string; value: string; placeholder?: string; icon: React.ReactNode; onChange?: (value: string) => void; listen: () => void }) {
  return <label className="place-field"><span>{label}</span><div>{icon}<input value={value} placeholder={placeholder} onChange={(event) => onChange?.(event.target.value)} readOnly={!onChange} /><button onClick={listen} type="button" aria-label={`Speak ${label.toLowerCase()} location`}><Mic /></button></div></label>
}

function CorridorHelpCard({ copy, help, tryCorridor }: { copy: UiCopy; help: api.CorridorHelp; tryCorridor: () => void }) {
  return <div className="corridor-help" role="status">
    <strong>{copy.plan.uncovered}</strong>
    <p>{copy.plan.corridor} {help.supported_corridor}.</p>
    <PrimaryButton onClick={tryCorridor}>{copy.plan.try}</PrimaryButton>
  </div>
}

function PlanScreen({ copy, destination, setDestination, back, listen, next, busy, corridor, tryCorridor }: { copy: UiCopy; destination: string; setDestination: (value: string) => void; back: () => void; listen: () => void; next: () => void; busy: boolean; corridor: api.CorridorHelp | null; tryCorridor: () => void }) {
  return <div className="screen paper-screen plan-screen"><TopBar title={copy.plan.top} back={back} /><section className="page-title"><h1>{copy.plan.title}</h1><p>{copy.plan.helper}</p></section><div className="place-fields"><PlaceField label={copy.plan.from} value={copy.plan.home} icon={<Home />} listen={listen} /><PlaceField label={copy.plan.to} value={destination} placeholder={copy.plan.placeholder} icon={<MapPin />} onChange={setDestination} listen={listen} /></div>{corridor && <CorridorHelpCard copy={copy} help={corridor} tryCorridor={tryCorridor} />}<div className="screen-actions"><PrimaryButton onClick={next} disabled={busy}>{busy ? copy.plan.planning : copy.plan.show}</PrimaryButton></div></div>
}

function ListeningScreen({ locale, transcript, setTranscript, back, accept, busy }: { locale: Locale; transcript: string; setTranscript: (value: string) => void; back: () => void; accept: () => void; busy: boolean }) {
  const copy = uiCopy[locale]
  const [state, setState] = useState<'idle' | 'requesting' | 'listening' | 'heard' | 'denied' | 'unsupported' | 'no-speech' | 'error'>('idle')
  const [level, setLevel] = useState(0)
  const recognitionRef = useRef<Recognition | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const frameRef = useRef<number | null>(null)
  const stopMeter = () => {
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current)
    frameRef.current = null; streamRef.current?.getTracks().forEach((track) => track.stop()); streamRef.current = null; setLevel(0)
  }
  useEffect(() => () => { recognitionRef.current?.stop(); stopMeter() }, [])
  const begin = async () => {
    setTranscript(''); setState('requesting')
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) { setState('unsupported'); return }
    const scope = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition }
    const SpeechCtor = scope.SpeechRecognition ?? scope.webkitSpeechRecognition
    if (!SpeechCtor) { setState('unsupported'); return }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); streamRef.current = stream
      const context = new AudioContext(); const analyser = context.createAnalyser(); analyser.fftSize = 256; context.createMediaStreamSource(stream).connect(analyser)
      const samples = new Uint8Array(analyser.frequencyBinCount)
      const meter = () => { analyser.getByteFrequencyData(samples); setLevel(Math.min(1, samples.reduce((sum, value) => sum + value, 0) / samples.length / 90)); frameRef.current = requestAnimationFrame(meter) }; meter()
      const recognition = new SpeechCtor(); recognition.lang = guideCopy[locale].speechLanguage; recognition.interimResults = false; recognition.continuous = false
      recognition.onresult = (event) => { const heard = event.results[0]?.[0]?.transcript?.trim() ?? ''; setTranscript(heard); setState(heard ? 'heard' : 'no-speech'); stopMeter(); void context.close() }
      recognition.onerror = (event) => { setState(event.error === 'not-allowed' || event.error === 'service-not-allowed' ? 'denied' : event.error === 'no-speech' ? 'no-speech' : 'error'); stopMeter(); void context.close() }
      recognition.onend = () => { setState((current) => current === 'listening' ? 'no-speech' : current); stopMeter(); void context.close() }
      recognitionRef.current = recognition; recognition.start(); setState('listening')
    } catch (error) {
      const denied = error instanceof DOMException && (error.name === 'NotAllowedError' || error.name === 'SecurityError')
      setState(denied ? 'denied' : 'error'); stopMeter()
    }
  }
  const heading = state === 'listening' ? copy.voice.listening : state === 'heard' ? copy.voice.check : copy.voice.say
  const message = state === 'idle' ? copy.voice.idle : state === 'requesting' ? copy.voice.requesting : state === 'listening' ? copy.voice.live : state === 'denied' ? copy.voice.denied : state === 'unsupported' ? copy.voice.unsupported : state === 'no-speech' ? copy.voice.noSpeech : state === 'error' ? copy.voice.error : copy.voice.confirm
  return <div className={`screen paper-screen listening-screen locale-${locale}`}><TopBar title={copy.voice.top} back={back} /><section className="listening-title"><h1>{heading}</h1><p>{message}</p></section><div className="capture-card real-capture"><button className={`big-mic${state === 'listening' ? ' active' : ''}`} onClick={() => { void begin() }} disabled={state === 'requesting'} aria-label={state === 'listening' ? copy.voice.listening : copy.voice.tap}><Mic /></button><div className="voice-meter" aria-hidden="true">{[.55,.8,1,.7,.45].map((weight, index) => <i key={index} style={{ transform: `scaleY(${state === 'listening' ? Math.max(.15, level * weight) : .15})` }} />)}</div><span>{transcript ? copy.voice.heard : state === 'listening' ? copy.voice.micLive : copy.voice.nothing}</span><strong>{transcript || '—'}</strong></div><div className="privacy-strip"><ShieldCheck /><span>{copy.voice.privacy}</span></div><div className="screen-actions voice-actions"><PrimaryButton onClick={accept} disabled={!transcript || busy}>{busy ? copy.plan.planning : copy.voice.use}</PrimaryButton><SecondaryButton onClick={() => { void begin() }}>{state === 'idle' ? copy.voice.tap : copy.voice.retry}</SecondaryButton><button className="plain-action" onClick={back}>{copy.voice.type}</button></div></div>
}



// OSM map of the advice: recommended route solid, alternatives dotted, the
// disrupted segment dashed red. Everything drawn comes from the API response.
function RouteMap({ advice }: { advice: api.Advice }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const map = L.map(ref.current, { scrollWheelZoom: false })
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map)
    const pts: [number, number][] = []
    for (const leg of advice.legs) if (leg.geometry.length > 1) { L.polyline(leg.geometry, { color: '#0a4faa', weight: 6, opacity: .9 }).addTo(map); pts.push(...leg.geometry) }
    for (const alt of advice.alternatives) for (const leg of alt) if (leg.geometry.length > 1) { L.polyline(leg.geometry, { color: '#666', weight: 4, dashArray: '2 8' }).addTo(map); pts.push(...leg.geometry) }
    if (advice.affected_segment && advice.affected_segment.length > 1) { L.polyline(advice.affected_segment, { color: '#a11212', weight: 8, dashArray: '10 8' }).addTo(map); pts.push(...advice.affected_segment) }
    if (pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.18))
    return () => { map.remove() }
  }, [advice])
  return <div className="route-map" ref={ref} aria-label="Journey map" />
}

// The three-stage demo driver (FRONTEND_CONTRACT.md). Each control re-plans
// the journey against a LABELLED replay fixture and shows whatever the engine
// actually returns — nothing here writes expected outputs into the UI.
function StageBar({ copy, active, busy, run }: { copy: UiCopy; active: string; busy: boolean; run: (stage: api.StageId) => void }) {
  const labels: Record<api.StageId, string> = {
    demo_stage1_peak_crowding: copy.stages.s1,
    demo_stage2_planned_closure: copy.stages.s2,
    demo_stage3_breakdown: copy.stages.s3,
  }
  return <div className="stage-bar" role="group" aria-label={copy.stages.title}>
    <span className="stage-caption">{copy.stages.title} · {copy.overview.simulated}</span>
    <div className="stage-chips">{api.STAGES.map((stage) => <button key={stage.id} disabled={busy} className={active === stage.id ? 'active' : ''} onClick={() => run(stage.id)}>{labels[stage.id]}</button>)}</div>
  </div>
}

function StepFreeBadge({ copy, leg }: { copy: UiCopy; leg: api.Leg }) {
  return <span className={`stepfree-badge ${leg.step_free}`}>{copy.legs.stepFree[leg.step_free]}</span>
}
function LegTimes({ copy, leg }: { copy: UiCopy; leg: api.Leg }) {
  return <small className="leg-times">{api.fmtTime(leg.depart)}–{api.fmtTime(leg.arrive)}{leg.crowding ? ` · ${copy.legs.crowd[leg.crowding]}` : ''}</small>
}
function legTitle(copy: UiCopy, leg: api.Leg): string {
  return `${copy.legs.modes[leg.mode]}${leg.service ? ` ${leg.service}` : ''}: ${leg.from_name} → ${leg.to_name}`
}

const ACTION_LABEL: Record<Locale, Record<api.Advice['action'], string>> = {
  en: { proceed: 'All clear', wait: 'Wait', reroute: 'Change of plan', leave_earlier: 'Leave earlier', take_taxi: 'Take a taxi', cancel_trip: 'Do not travel' },
  zh: { proceed: '路线正常', wait: '请稍候', reroute: '路线已更改', leave_earlier: '请提前出发', take_taxi: '建议乘出租车', cancel_trip: '请勿出行' },
  ms: { proceed: 'Laluan selamat', wait: 'Tunggu', reroute: 'Laluan berubah', leave_earlier: 'Keluar lebih awal', take_taxi: 'Naik teksi', cancel_trip: 'Jangan teruskan' },
  ta: { proceed: 'பாதை சரியாக உள்ளது', wait: 'காத்திருக்கவும்', reroute: 'பாதை மாற்றப்பட்டது', leave_earlier: 'முன்னதாக புறப்படவும்', take_taxi: 'டாக்சியில் செல்லவும்', cancel_trip: 'பயணம் செய்ய வேண்டாம்' },
}
const ADVICE_SUMMARY: Record<Locale, string> = { en: 'Your journey has been updated for current travel conditions.', zh: '已根据当前交通情况更新您的行程。', ms: 'Perjalanan anda telah dikemas kini mengikut keadaan semasa.', ta: 'தற்போதைய பயண நிலைக்கு ஏற்ப உங்கள் பயணம் புதுப்பிக்கப்பட்டது.' }

function AdviceBanner({ locale, copy, advice }: { locale: Locale; copy: UiCopy; advice: api.Advice }) {
  const summary = advice.reason.split('. ')[0]
  return <div className={`advice-banner action-${advice.action}`} role="status">
    <span className="advice-action">{ACTION_LABEL[locale][advice.action]}</span>
    <strong>{locale === 'en' ? advice.headline : ACTION_LABEL[locale][advice.action]}</strong>
    <p>{locale === 'en' ? `${summary}${summary.endsWith('.') ? '' : '.'}` : ADVICE_SUMMARY[locale]}</p>
    {locale === 'en' && <details><summary>{copy.overview.why}</summary><p>{advice.reason}</p><small>Arrive {api.fmtTime(advice.eta_range[0])}–{api.fmtTime(advice.eta_range[1])}{advice.decide_by ? ` · decide by ${api.fmtTime(advice.decide_by)}` : ''}{advice.notify_family ? ' · family notified' : ''}</small></details>}
    {api.anyFixture(advice) && <span className="replay-tag">{copy.overview.simulated}</span>}
  </div>
}

function OverviewScreen({ locale, copy, advice, journey, busy, scenario, runStage, back, start, notice }: { locale: Locale; copy: UiCopy; advice: api.Advice | null; journey: api.Journey | null; busy: boolean; scenario: string; runStage: (stage: api.StageId) => void; back: () => void; start: () => void; notice: string }) {
  if (!advice || !journey) return <div className={`screen paper-screen overview-screen locale-${locale}`}><TopBar title={copy.overview.top} back={back} /><section className="overview-heading"><h1>{busy ? copy.overview.planning : copy.overview.empty}</h1><p>{busy ? copy.overview.checking : copy.overview.emptyDetail}</p></section></div>
  const legs = advice.legs
  const total = Math.round((new Date(legs[legs.length - 1]?.arrive ?? journey.arrive_by).getTime() - new Date(legs[0]?.depart ?? journey.arrive_by).getTime()) / 60000)
  return <div className={`screen paper-screen overview-screen locale-${locale}`}><TopBar title={copy.overview.top} back={back} /><section className="overview-heading"><div><span>{journey.origin}</span><ArrowRight /><span>{journey.destination}</span></div><h1>{copy.overview.title(legs.length)}</h1><p>{copy.overview.about(total)}</p></section><div className="journey-badges"><span><LocateFixed /> {copy.overview.landmarks}</span></div><AdviceBanner locale={locale} copy={copy} advice={advice} /><RouteMap advice={advice} /><StageBar copy={copy} active={scenario} busy={busy} run={runStage} /><ol className="journey-list photo-list">{legs.map((leg, index) => { const photo = legPhoto(leg); return <li key={index}>{photo && <span className="leg-photo"><img src={photo.image} alt={photo.alt} /><i>{copy.legs.illustrative}</i></span>}<b>{index + 1}</b><span><strong>{legTitle(copy, leg)}</strong><LegTimes copy={copy} leg={leg} /><small>{leg.instruction}</small><StepFreeBadge copy={copy} leg={leg} /></span></li> })}</ol>{notice && <p className="overview-notice" role="status">{notice}</p>}<div className="screen-actions"><PrimaryButton onClick={start}><Navigation /> {copy.overview.start}</PrimaryButton></div></div>
}

function SharingScreen({ copy, state, start, continueWithout, back }: { copy: UiCopy; state: LocationState; start: () => void; continueWithout: () => void; back: () => void }) {
  const failed = state === 'denied' || state === 'timeout' || state === 'unavailable' || state === 'service-error'
  const message = state === 'requesting' ? copy.sharing.requesting : state === 'denied' ? copy.sharing.denied : state === 'timeout' ? copy.sharing.timeout : state === 'service-error' ? copy.sharing.service : state === 'unavailable' ? copy.sharing.unavailable : copy.sharing.idle
  return <div className="screen paper-screen sharing-screen"><TopBar title={copy.sharing.top} back={back} /><section className="sharing-heading"><span><HeartHandshake /></span><h1>{copy.sharing.title}</h1><p>{message}</p></section><div className="sharing-details"><div><LocateFixed /><span><strong>{copy.sharing.location}</strong><small>{copy.sharing.locationDetail}</small></span></div><div><ShieldCheck /><span><strong>{copy.sharing.control}</strong><small>{copy.sharing.controlDetail}</small></span></div></div><div className="screen-actions two"><PrimaryButton onClick={start} disabled={state === 'requesting'}><LocateFixed />{state === 'requesting' ? copy.sharing.request : failed ? copy.sharing.retry : copy.sharing.start}</PrimaryButton><SecondaryButton onClick={continueWithout}>{copy.sharing.skip}</SecondaryButton></div></div>
}

function GuideScreen({ locale, activeStep, advice, locationState, lastLocationAt, back, next, finish, lost, sos }: { locale: Locale; activeStep: number; advice: api.Advice | null; locationState: LocationState; lastLocationAt: Date | null; back: () => void; next: () => void; finish: () => void; lost: () => void; sos: () => void }) {
  const copy = uiCopy[locale]; const [speaking, setSpeaking] = useState(false)
  const legs = advice?.legs ?? []
  const index = Math.min(activeStep, Math.max(0, legs.length - 1))
  const leg = legs[index]
  const photo = leg ? legPhoto(leg) : null
  const spokenText = leg ? leg.speech_text : ''
  const speak = () => { if (!('speechSynthesis' in window)) return; if (speaking) { speechSynthesis.cancel(); setSpeaking(false); return }; const utterance = new SpeechSynthesisUtterance(spokenText); utterance.lang = guideCopy[locale].speechLanguage; utterance.rate = .72; utterance.onend = () => setSpeaking(false); utterance.onerror = () => setSpeaking(false); speechSynthesis.cancel(); speechSynthesis.speak(utterance); setSpeaking(true) }
  useEffect(() => () => window.speechSynthesis?.cancel(), [])
  const time = lastLocationAt?.toLocaleTimeString(locale === 'zh' ? 'zh-SG' : locale === 'ms' ? 'ms-SG' : locale === 'ta' ? 'ta-SG' : 'en-SG', { hour: '2-digit', minute: '2-digit' })
  if (!leg) return <div className={`screen paper-screen overview-screen locale-${locale}`}><TopBar title={copy.overview.top} back={back} /><section className="overview-heading"><h1>{copy.overview.empty}</h1><p>{copy.overview.emptyDetail}</p></section></div>
  const last = index === legs.length - 1
  return <div className={`screen guide-screen locale-${locale}${photo ? '' : ' no-photo'}`}>{photo && <img src={photo.image} alt={photo.alt} className="guide-photo" />}<div className="photo-shade" /><div className="guide-top"><BackButton onClick={back} light label={copy.back} /><strong>{leg.to_name}</strong><span /></div><button className="floating-sos" onClick={sos}>SOS</button><section className="guide-sheet multi-step-sheet"><div className="progress-row"><strong>{copy.guide.step(index + 1, legs.length)}</strong><span style={{ '--progress': `${((index + 1) / legs.length) * 100}%` } as React.CSSProperties}><i /></span></div><h1>{legTitle(copy, leg)}</h1><p className="instruction">{leg.instruction}</p><div className="distance"><LegTimes copy={copy} leg={leg} /><StepFreeBadge copy={copy} leg={leg} /></div>{photo && <p className="photo-note">{copy.legs.illustrative}</p>}<div className="sharing-status"><LocateFixed /><span><strong>{locationState === 'active' ? copy.guide.sharing : copy.guide.saved}</strong><small>{locationState === 'active' && time ? copy.guide.updated(time) : copy.guide.notShared}</small></span></div><div className="guide-actions"><button className={speaking ? 'speaking' : ''} onClick={speak}>{speaking ? <Pause /> : <Volume2 />}<span>{speaking ? copy.guide.playing : copy.guide.play}</span></button><button onClick={lost}><CircleHelp /><span>{copy.guide.help}</span></button></div><PrimaryButton onClick={last ? finish : next}>{last ? copy.guide.finish : copy.guide.next}<ArrowRight /></PrimaryButton></section></div>
}

function WrongWayScreen({ locale, journey, back, correct, call }: { locale: Locale; journey: api.Journey | null; back: () => void; correct: () => void; call: () => void }) {
  const copy = uiCopy[locale]
  const [ack, setAck] = useState<api.LocationAck | null>(null)
  const [checking, setChecking] = useState(false)
  useEffect(() => {
    if (!journey) return
    setChecking(true)
    const send = (coords?: { lat: number; lon: number; accuracy_m?: number }) =>
      api.postLocation(journey.journey_id, 'walking', coords).then(setAck).catch(() => setAck(null)).finally(() => setChecking(false))
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => { void send({ lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy_m: pos.coords.accuracy }) },
        () => { void send() }, { timeout: 4000 })
    } else void send()
  }, [journey])
  const wrong = Boolean(ack?.wrong_direction)
  const body = checking ? copy.help.checking : !journey ? copy.help.noJourney : !ack ? copy.help.unavailable : wrong ? `${copy.help.wrongBody}${ack.notify_family ? ` ${copy.help.familyTold}` : ''}` : copy.help.safe
  return <div className={`screen wrong-screen${wrong ? ' confirmed-wrong' : ''}`}><div className="warning-top"><BackButton onClick={back} label={copy.back} /><strong>{copy.help.top}</strong></div><RotateCcw className="turn-symbol" /><section className="wrong-sheet"><h1>{wrong ? copy.help.wrong : copy.help.lost}</h1><p role="status">{body}</p><div className="screen-actions two"><PrimaryButton onClick={correct}>{copy.help.correct}</PrimaryButton><SecondaryButton onClick={call}>{copy.help.call}</SecondaryButton></div></section></div>
}

function SosScreen({ locale, back, record, confirm, setNotice }: { locale: Locale; back: () => void; record: () => void; confirm: (value: { title: string; body: string; action: string; onConfirm?: () => void }) => void; setNotice: (value: string) => void }) {
  const copy = uiCopy[locale]
  const contactFamily = async () => {
    try {
      const opened = await api.sosOpen()
      confirm({
        title: copy.sos.sendTitle, body: copy.sos.sendBody, action: copy.sos.send,
        onConfirm: () => { void api.sosConfirm(opened.sos_id).then((done) => setNotice(done.notified_user_ids.length ? 'Help request sent to Hui Ling.' : 'The request was confirmed, but Hui Ling is not linked yet.')).catch(() => setNotice('We could not send the request. Try again or call Hui Ling directly.')) },
      })
    } catch { setNotice('We could not reach the help service. Try again or call Hui Ling directly.') }
  }
  const option = (icon: React.ReactNode, title: string, detail: string | undefined, onClick: () => void) => <button className="help-option" onClick={onClick}><span>{icon}</span><span><strong>{title}</strong>{detail && <small>{detail}</small>}</span><ChevronRight /></button>
  return <div className="screen paper-screen sos-screen"><header className="simple-header"><BackButton onClick={back} label={copy.back} /><strong>{copy.sos.top}</strong></header><span className="sos-mark">SOS</span><section className="sos-title"><h1>{copy.sos.title}</h1><p>{copy.sos.idle}</p></section><div className="help-options">{option(<UserRound />, copy.sos.family, copy.sos.familyDetail, () => { void contactFamily() })}{option(<Phone />, copy.sos.emergency, copy.sos.emergencyDetail, () => confirm({ title: copy.sos.emergencyTitle, body: copy.sos.emergencyBody, action: '995', onConfirm: () => { window.location.href = 'tel:995' } }))}{option(<Mic />, copy.sos.record, copy.sos.recordDetail, record)}</div><p className="privacy-footer"><Check />{copy.sos.privacy}</p></div>
}

function RecordingScreen({ back }: { back: () => void }) {
  const [recording, setRecording] = useState(false); const [seconds, setSeconds] = useState(0); const [audioUrl, setAudioUrl] = useState(''); const [error, setError] = useState(''); const recorder = useRef<MediaRecorder | null>(null); const chunks = useRef<Blob[]>([])
  useEffect(() => { if (!recording) return; const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000); return () => window.clearInterval(timer) }, [recording])
  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl) }, [audioUrl])
  const start = async () => { try { const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); const next = new MediaRecorder(stream); chunks.current = []; next.ondataavailable = (event) => chunks.current.push(event.data); next.onstop = () => { setAudioUrl(URL.createObjectURL(new Blob(chunks.current, { type: next.mimeType }))); stream.getTracks().forEach((track) => track.stop()) }; next.start(); recorder.current = next; setSeconds(0); setRecording(true); setError('') } catch { setError('Microphone permission was not granted. You can go back without recording.') } }
  const stop = () => { recorder.current?.stop(); setRecording(false) }; const clear = () => { if (audioUrl) URL.revokeObjectURL(audioUrl); setAudioUrl(''); setSeconds(0) }
  return <div className="screen paper-screen recording-screen"><TopBar title="Audio message" back={back} /><section><span className={`recording-orb${recording ? ' active' : ''}`}>{recording ? <Square /> : <Mic />}</span><h1>{recording ? 'Recording…' : audioUrl ? 'Message ready' : 'Record a short message'}</h1><p>{recording ? 'Tell your family what happened and where you are.' : 'Nothing is shared until you confirm.'}</p><strong className="recording-time">{String(Math.floor(seconds / 60)).padStart(2, '0')}:{String(seconds % 60).padStart(2, '0')}</strong></section>{error && <p className="recording-error" role="alert">{error}</p>}{audioUrl && <audio className="audio-player" controls src={audioUrl} />}<div className="screen-actions two">{recording ? <PrimaryButton onClick={stop}><Square /> Stop recording</PrimaryButton> : !audioUrl ? <PrimaryButton onClick={start}><Mic /> Start recording</PrimaryButton> : <><PrimaryButton onClick={() => setError('Recording stays on this device in the demo — upload is not wired yet.')}>Confirm message</PrimaryButton><SecondaryButton onClick={clear}><Trash2 /> Delete and try again</SecondaryButton></>}</div></div>
}

function FamilyAccessScreen({ back, next }: { back: () => void; next: () => void }) {
  const [code, setCode] = useState('LIM-7284')
  return <div className="screen paper-screen family-screen"><TopBar title="Family access" back={back} /><section className="family-intro"><span><HeartHandshake /></span><h1>Follow a shared journey.</h1><p>Mdm Lim must choose to share each active journey.</p></section><label className="code-field"><span>SHARING CODE</span><input value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} /></label><div className="family-consent"><LockKeyhole /><span><strong>Consent comes first</strong><small>Location sharing ends when the journey ends.</small></span></div><div className="screen-actions"><PrimaryButton onClick={next}>Open demo journey</PrimaryButton></div></div>
}

function FamilyJourneyScreen({ back }: { back: () => void }) {
  return <div className="screen paper-screen family-journey"><TopBar title="Mdm Lim’s journey" back={back} /><section className="family-status"><span className="live-dot"><i /> Journey active</span><h1>On the way to SGH</h1><p>Simulated family view</p></section><div className="current-step"><span>6</span><div><small>CURRENT STEP</small><strong>Following the lift signs</strong><p>Outram Park MRT</p></div></div><dl><div><dt>Expected arrival</dt><dd>About 24 minutes</dd></div><div><dt>Direction</dt><dd className="positive"><Check /> On the right path</dd></div><div><dt>Sharing</dt><dd>Until journey ends</dd></div></dl><div className="family-note"><ShieldCheck /><span>No help is needed right now. You’ll be alerted if Mdm Lim asks for help.</span></div><div className="screen-actions"><SecondaryButton onClick={back}>Stop viewing demo</SecondaryButton></div></div>
}


function ArrivedScreen({ copy, locale, journey, again }: { copy: UiCopy; locale: Locale; journey: api.Journey | null; again: () => void }) {
  return <div className={`screen paper-screen arrived-screen locale-${locale}`}><span className="arrived-mark"><Check /></span><h1>{copy.arrived.title}</h1><p>{journey ? journey.destination : ''}</p><p>{copy.arrived.detail}</p><div className="screen-actions"><PrimaryButton onClick={again}>{copy.arrived.again}</PrimaryButton></div></div>
}

function ConfirmSheet({ title, body, action, onConfirm, cancel, close }: { title: string; body: string; action: string; onConfirm?: () => void; cancel: string; close: () => void }) {
  return <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><button className="modal-backdrop" onClick={close} aria-label={cancel} /><section><button className="modal-close" onClick={close} aria-label={cancel}><X /></button><span className="modal-icon"><Phone /></span><h2 id="confirm-title">{title}</h2><p>{body}</p><button className="danger-button" onClick={() => { onConfirm?.(); close() }}>{action}</button><SecondaryButton onClick={close}>{cancel}</SecondaryButton></section></div>
}

export default App
