import { useEffect, useRef, useState } from 'react'
import { Accessibility, ArrowLeft, ArrowRight, Check, ChevronRight, CircleHelp, HeartHandshake, Home, Languages, LocateFixed, LockKeyhole, MapPin, Mic, Navigation, Pause, Phone, RotateCcw, ShieldCheck, Square, Trash2, UserRound, Volume2, X } from 'lucide-react'
import { guideCopy, languages, screenLabels, type Locale, type ScreenId } from './data'
import * as api from './api'
import exitPhoto from './assets/images/outram-exit-7.jpg'

type SpeechEvent = { results: ArrayLike<{ 0: { transcript: string } }> }
type Recognition = { lang: string; interimResults: boolean; continuous: boolean; onresult: ((event: SpeechEvent) => void) | null; onerror: (() => void) | null; onend: (() => void) | null; start: () => void; stop: () => void }
const storageKey = 'mdm-lim-locale'

function App() {
  const [screen, setScreen] = useState<ScreenId>('language')
  const [locale, setLocale] = useState<Locale>(() => { const saved = localStorage.getItem(storageKey); return saved === 'zh' || saved === 'ms' || saved === 'ta' ? saved : 'en' })
  const [destination, setDestination] = useState('')
  const [transcript, setTranscript] = useState('Singapore General Hospital')
  const [notice, setNotice] = useState('')
  const [confirm, setConfirm] = useState<{ title: string; body: string; action: string; onConfirm?: () => void } | null>(null)
  // --- live journey state (wired to the backend; see src/api.ts) ---
  const [scenario, setScenario] = useState<api.ScenarioId>('disruption_on_train')
  const [journey, setJourney] = useState<api.Journey | null>(null)
  const [advice, setAdvice] = useState<api.Advice | null>(null)
  const [corridor, setCorridor] = useState<api.CorridorHelp | null>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => localStorage.setItem(storageKey, locale), [locale])
  const navigate = (next: ScreenId) => { setNotice(''); setConfirm(null); setScreen(next) }
  const selectLocale = (next: Locale) => setLocale(next)

  const planJourney = async (dest: string, useScenario: api.ScenarioId = scenario) => {
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

  const switchScenario = async (next: api.ScenarioId) => {
    if (busy) return
    await planJourney(journey?.destination ?? destination, next)
  }

  const startJourney = () => {
    if (!navigator.geolocation) { setNotice('Live location is unavailable. Cached directions will still work.'); window.setTimeout(() => navigate('guide'), 900); return }
    setNotice('Checking location permission…')
    navigator.geolocation.getCurrentPosition(() => navigate('guide'), () => { setNotice('Location was not shared. Continuing with cached directions.'); window.setTimeout(() => navigate('guide'), 1100) }, { enableHighAccuracy: true, timeout: 5000 })
  }
  return <main className="prototype-shell">
    <PrototypeNav screen={screen} locale={locale} navigate={navigate} selectLocale={selectLocale} />
    <section className="device-stage" aria-label="Mdm Lim commuter companion prototype"><div className="phone" data-screen={screen}>
      {screen === 'language' && <LanguageScreen locale={locale} selectLocale={selectLocale} next={() => navigate('profile')} />}
      {screen === 'profile' && <ProfileScreen back={() => navigate('language')} traveller={() => navigate('plan')} family={() => navigate('family')} />}
      {screen === 'plan' && <PlanScreen destination={destination} setDestination={setDestination} back={() => navigate('profile')} listen={() => navigate('listening')} busy={busy} corridor={corridor} tryCorridor={() => { setCorridor(null); setDestination('Singapore General Hospital'); void planJourney('Singapore General Hospital') }} next={() => { void planJourney(destination) }} />}
      {screen === 'listening' && <ListeningScreen transcript={transcript} setTranscript={setTranscript} back={() => navigate('plan')} accept={() => { setDestination(transcript || 'Singapore General Hospital'); navigate('recognised') }} notice={notice} setNotice={setNotice} />}
      {screen === 'recognised' && <RecognisedScreen destination={destination || 'Singapore General Hospital'} back={() => navigate('plan')} busy={busy} next={() => { void planJourney(destination || 'Singapore General Hospital') }} />}
      {screen === 'overview' && <OverviewScreen advice={advice} journey={journey} scenario={scenario} switchScenario={switchScenario} busy={busy} back={() => navigate('plan')} start={startJourney} notice={notice} />}
      {screen === 'guide' && <GuideScreen locale={locale} selectLocale={selectLocale} advice={advice} scenario={scenario} switchScenario={switchScenario} busy={busy} back={() => navigate('overview')} lost={() => navigate('wrong-way')} sos={() => navigate('sos')} />}
      {screen === 'wrong-way' && <WrongWayScreen journey={journey} back={() => navigate('guide')} correct={() => navigate('guide')} call={() => setConfirm({ title: 'Call trusted family?', body: 'A call will only begin after you confirm.', action: 'Call family' })} />}
      {screen === 'sos' && <SosScreen back={() => navigate('guide')} record={() => navigate('recording')} confirm={setConfirm} setNotice={setNotice} />}
      {screen === 'recording' && <RecordingScreen back={() => navigate('sos')} />}
      {screen === 'family' && <FamilyAccessScreen back={() => navigate('profile')} next={() => navigate('family-journey')} />}
      {screen === 'family-journey' && <FamilyJourneyScreen back={() => navigate('family')} />}
      {notice && screen !== 'listening' && screen !== 'overview' && <div className="toast" role="status">{notice}</div>}
      {confirm && <ConfirmSheet {...confirm} close={() => setConfirm(null)} />}
    </div></section>
  </main>
}

function PrototypeNav({ screen, locale, navigate, selectLocale }: { screen: ScreenId; locale: Locale; navigate: (screen: ScreenId) => void; selectLocale: (locale: Locale) => void }) {
  return <aside className="prototype-nav" aria-label="Pitch demo navigation"><div className="prototype-brand"><span className="signal-mark"><i /><i /><i /></span><div><strong>Mdm Lim</strong><span>Commuter companion</span></div></div><p className="prototype-note">Jump to any judging moment. This panel is hidden on phones.</p><nav>{screenLabels.map((item, index) => <div key={item.id}>{item.group !== screenLabels[index - 1]?.group && <span className="nav-group">{item.group}</span>}<button className={screen === item.id ? 'active' : ''} onClick={() => navigate(item.id)}><span>{item.label}</span><ChevronRight size={18} /></button></div>)}</nav><div className="nav-languages"><span className="nav-group">Step language</span><div>{languages.map((item) => <button key={item.id} className={locale === item.id ? 'active' : ''} onClick={() => { selectLocale(item.id); navigate('guide') }}>{item.code}</button>)}</div></div></aside>
}

function BackButton({ onClick, light = false }: { onClick: () => void; light?: boolean }) { return <button className={`back-button${light ? ' light' : ''}`} onClick={onClick} aria-label="Go back"><ArrowLeft /></button> }
function TopBar({ title, back }: { title: string; back: () => void }) { return <header className="top-bar"><BackButton onClick={back} /><strong>{title}</strong><span /></header> }
function PrimaryButton({ children, onClick, disabled = false }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) { return <button className="primary-button" onClick={onClick} disabled={disabled}>{children}</button> }
function SecondaryButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) { return <button className="secondary-button" onClick={onClick}>{children}</button> }

// Visible label for screens whose content is design work, not live data (§3.2.4:
// mocked data must never be presented as live).
function PreviewBadge() { return <span className="preview-badge">Design preview — not live data</span> }

// Scenario switcher: the six labelled replay/injected-data scenarios the brief
// permits (§2.6). Switching re-plans the same journey and re-requests advice.
function ScenarioBar({ scenario, switchScenario, busy }: { scenario: api.ScenarioId; switchScenario: (s: api.ScenarioId) => void; busy: boolean }) {
  return <div className="scenario-bar" role="group" aria-label="Replay scenarios">
    <span className="scenario-caption">REPLAY DATA — labelled test scenarios</span>
    <div className="scenario-chips">{api.SCENARIOS.map((s) => <button key={s.id} disabled={busy} className={s.id === scenario ? 'active' : ''} onClick={() => switchScenario(s.id)}>{s.label}</button>)}</div>
  </div>
}

function LanguageScreen({ locale, selectLocale, next }: { locale: Locale; selectLocale: (locale: Locale) => void; next: () => void }) {
  return <div className="screen language-screen"><section className="language-sheet"><p className="welcome">Welcome!</p><h1>Choose your language.</h1><p className="helper">You can change this at any time.</p><div className="language-list" role="radiogroup" aria-label="Choose your language">{languages.map((item) => <button key={item.id} className={locale === item.id ? 'selected' : ''} onClick={() => selectLocale(item.id)} role="radio" aria-checked={locale === item.id}><span>{item.label}</span><b>{item.code}</b></button>)}</div><PrimaryButton onClick={next}>Continue</PrimaryButton><PreviewBadge /></section></div>
}

function ProfileScreen({ back, traveller, family }: { back: () => void; traveller: () => void; family: () => void }) {
  return <div className="screen paper-screen profile-screen"><TopBar title="Choose your profile" back={back} /><h1>Who is using this app?</h1><div className="role-list"><button onClick={traveller}><b>A</b><span><strong>I am travelling</strong><small>Plan and follow my own journey.</small></span><ArrowRight /></button><button onClick={family}><b>B</b><span><strong>I am family</strong><small>Follow journeys that are shared with me.</small></span><ArrowRight /></button></div><p className="consent-copy">Location will never be shared automatically without your permission.</p><PreviewBadge /></div>
}

function PlaceField({ label, value, placeholder, icon, onChange, listen }: { label: string; value: string; placeholder?: string; icon: React.ReactNode; onChange?: (value: string) => void; listen: () => void }) {
  return <label className="place-field"><span>{label}</span><div>{icon}<input value={value} placeholder={placeholder} onChange={(event) => onChange?.(event.target.value)} readOnly={!onChange} /><button onClick={listen} type="button" aria-label={`Speak ${label.toLowerCase()} location`}><Mic /></button></div></label>
}
function AccessibleStrip() { return <div className="accessible-strip"><Accessibility /><span><strong>Accessible route is on</strong><small>Lifts and sheltered paths preferred</small></span></div> }

function CorridorHelpCard({ help, tryCorridor }: { help: api.CorridorHelp; tryCorridor: () => void }) {
  return <div className="corridor-help" role="status">
    <strong>That place isn’t covered yet.</strong>
    <p>This prototype covers one corridor: {help.supported_corridor}.</p>
    <p className="corridor-why">{help.why_limited}</p>
    <PrimaryButton onClick={tryCorridor}>Try {help.try.origin} → {help.try.destination}</PrimaryButton>
  </div>
}

function PlanScreen({ destination, setDestination, back, listen, next, busy, corridor, tryCorridor }: { destination: string; setDestination: (value: string) => void; back: () => void; listen: () => void; next: () => void; busy: boolean; corridor: api.CorridorHelp | null; tryCorridor: () => void }) {
  return <div className="screen paper-screen plan-screen"><TopBar title="Plan a journey" back={back} /><section className="page-title"><h1>Where are you going?</h1><p>Speak or type a place.</p></section><div className="place-fields"><PlaceField label="From" value="Home in Bedok" icon={<Home />} listen={listen} /><PlaceField label="To" value={destination} placeholder="Enter a place" icon={<MapPin />} onChange={setDestination} listen={listen} /></div><AccessibleStrip />{corridor && <CorridorHelpCard help={corridor} tryCorridor={tryCorridor} />}<div className="screen-actions"><PrimaryButton onClick={next} disabled={busy}>{busy ? 'Planning…' : 'Show my journey'}</PrimaryButton></div></div>
}

function ListeningScreen({ transcript, setTranscript, back, accept, notice, setNotice }: { transcript: string; setTranscript: (value: string) => void; back: () => void; accept: () => void; notice: string; setNotice: (value: string) => void }) {
  const recognitionRef = useRef<Recognition | null>(null); const [active, setActive] = useState(false)
  useEffect(() => {
    const scope = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition }
    const SpeechCtor = scope.SpeechRecognition ?? scope.webkitSpeechRecognition
    if (!SpeechCtor) { setNotice('Live speech recognition is unavailable here. A demo transcript is ready to use.'); return }
    const recognition = new SpeechCtor(); recognition.lang = 'en-SG'; recognition.interimResults = false; recognition.continuous = false
    recognition.onresult = (event) => { const heard = event.results[0]?.[0]?.transcript; if (heard) setTranscript(heard); setNotice('Destination heard. Check it before continuing.') }
    recognition.onerror = () => { setNotice('I could not hear that. You can use the demo destination or try again.'); setActive(false) }; recognition.onend = () => setActive(false); recognitionRef.current = recognition
    try { recognition.start(); setActive(true) } catch { setNotice('Microphone is already active.') }
    return () => recognition.stop()
  }, [setNotice, setTranscript])
  const retry = () => { try { recognitionRef.current?.start(); setActive(true); setNotice('Listening…') } catch { setNotice('Unable to restart the microphone. Use the current destination.') } }
  return <div className="screen paper-screen listening-screen"><TopBar title="Voice destination" back={back} /><section className="listening-title"><h1>{active ? 'Listening…' : 'Check destination'}</h1><p>{active ? 'Say where you want to go.' : 'Use the destination below or try again.'}</p></section><div className="capture-card"><button className={`big-mic${active ? ' active' : ''}`} onClick={retry} aria-label="Listen again"><Mic /></button><span>I heard:</span><strong>{transcript}</strong></div><div className="privacy-strip"><ShieldCheck /><span>Microphone is active only while this screen is open.</span></div>{notice && <p className="inline-notice" role="status">{notice}</p>}<div className="screen-actions two"><PrimaryButton onClick={accept}>Use this destination</PrimaryButton><SecondaryButton onClick={back}>Cancel</SecondaryButton></div></div>
}

function RecognisedScreen({ destination, back, next, busy }: { destination: string; back: () => void; next: () => void; busy: boolean }) {
  return <div className="screen paper-screen plan-screen"><TopBar title="Plan a journey" back={back} /><section className="page-title"><h1>Where are you going?</h1><p className="success-text">Destination recognised!</p></section><div className="place-fields"><PlaceField label="From" value="Home in Bedok" icon={<Home />} listen={back} /><PlaceField label="To" value={destination} icon={<MapPin />} listen={back} /></div><AccessibleStrip /><div className="recognised-strip"><Check /><strong>Destination recognised</strong></div><div className="screen-actions"><PrimaryButton onClick={next} disabled={busy}>{busy ? 'Planning…' : 'Show my journey'}</PrimaryButton></div></div>
}

const MODE_LABEL: Record<api.Leg['mode'], string> = { walk: 'Walk', mrt: 'MRT', bus: 'Bus', taxi: 'Taxi' }
const ACTION_LABEL: Record<api.Advice['action'], string> = { proceed: 'All clear', wait: 'Wait', reroute: 'Change of plan', leave_earlier: 'Leave earlier', take_taxi: 'Take a taxi', cancel_trip: 'Do not travel' }

function AdviceBanner({ advice }: { advice: api.Advice }) {
  return <div className={`advice-banner action-${advice.action}`} role="status">
    <span className="advice-action">{ACTION_LABEL[advice.action]}</span>
    <strong>{advice.headline}</strong>
    <p>{advice.reason}</p>
    <small>Arrive {api.fmtTime(advice.eta_range[0])}–{api.fmtTime(advice.eta_range[1])}
      {advice.decide_by ? ` · decide by ${api.fmtTime(advice.decide_by)}` : ''} · confidence {advice.confidence}
      {advice.notify_family ? ' · family notified' : ''}</small>
    {api.anyFixture(advice) && <span className="replay-tag">REPLAY DATA — this disruption is a labelled fixture, not live</span>}
  </div>
}

function OverviewScreen({ advice, journey, scenario, switchScenario, busy, back, start, notice }: { advice: api.Advice | null; journey: api.Journey | null; scenario: api.ScenarioId; switchScenario: (s: api.ScenarioId) => void; busy: boolean; back: () => void; start: () => void; notice: string }) {
  if (!advice || !journey) return <div className="screen paper-screen overview-screen"><TopBar title="Your journey" back={back} /><section className="overview-heading"><h1>{busy ? 'Planning your journey…' : 'No journey yet'}</h1><p>{busy ? 'Checking live conditions.' : 'Plan a journey first.'}</p></section></div>
  const legs = advice.legs
  const total = Math.round((new Date(legs[legs.length - 1]?.arrive ?? journey.arrive_by).getTime() - new Date(legs[0]?.depart ?? journey.arrive_by).getTime()) / 60000)
  return <div className="screen paper-screen overview-screen"><TopBar title="Your journey" back={back} /><section className="overview-heading"><div><span>{journey.origin}</span><ArrowRight /><span>{journey.destination}</span></div><h1>{legs.length} step{legs.length === 1 ? '' : 's'}</h1><p>About {total} minutes at your walking pace, from live conditions.</p></section><div className="journey-badges"><span><Accessibility /> Step-free route</span><span><LocateFixed /> Walks on OSM footpaths</span></div><AdviceBanner advice={advice} /><ol className="journey-list">{legs.map((leg, index) => <li key={index}><b>{index + 1}</b><span><strong>{MODE_LABEL[leg.mode]}{leg.service ? ` ${leg.service}` : ''}: {leg.from_name} → {leg.to_name}</strong><small>{api.fmtTime(leg.depart)}–{api.fmtTime(leg.arrive)}{leg.crowding ? ` · crowd: ${leg.crowding}` : ''} · {leg.instruction}</small></span></li>)}</ol><ScenarioBar scenario={scenario} switchScenario={switchScenario} busy={busy} />{notice && <p className="overview-notice" role="status">{notice}</p>}<div className="screen-actions"><PrimaryButton onClick={start}><Navigation /> Start journey</PrimaryButton></div></div>
}

function GuideScreen({ locale, selectLocale, advice, scenario, switchScenario, busy, back, lost, sos }: { locale: Locale; selectLocale: (locale: Locale) => void; advice: api.Advice | null; scenario: api.ScenarioId; switchScenario: (s: api.ScenarioId) => void; busy: boolean; back: () => void; lost: () => void; sos: () => void }) {
  const copy = guideCopy[locale]; const [speaking, setSpeaking] = useState(false)
  const spokenText = advice ? `${advice.speech_text}. ${advice.reason}` : `${copy.title}. ${copy.instruction}.`
  const speak = () => { if (!('speechSynthesis' in window)) return; if (speaking) { speechSynthesis.cancel(); setSpeaking(false); return }; const utterance = new SpeechSynthesisUtterance(spokenText); utterance.lang = advice ? 'en-SG' : copy.speechLanguage; utterance.rate = .72; utterance.onend = () => setSpeaking(false); utterance.onerror = () => setSpeaking(false); speechSynthesis.cancel(); speechSynthesis.speak(utterance); setSpeaking(true) }
  useEffect(() => () => window.speechSynthesis?.cancel(), [])
  return <div className={`screen guide-screen locale-${locale}`}><img src={exitPhoto} alt="Illuminated yellow Exit 7 sign at Outram Park MRT" className="guide-photo" /><div className="photo-shade" /><div className="guide-top"><BackButton onClick={back} light /><strong>{advice ? 'Live guidance' : copy.station}</strong><label className="guide-language"><Languages /><select aria-label="Change language" value={locale} onChange={(event) => selectLocale(event.target.value as Locale)}>{languages.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label></div><button className="floating-sos" onClick={sos}>SOS</button><section className="guide-sheet">{advice ? <><AdviceBanner advice={advice} /><p className="illustrative-note">Station photo and exit-level wayfinding (“{copy.title}”, “{copy.distance} {copy.ahead}”) are illustrative — exit-level data is not in the backend yet.</p></> : <><div className="progress-row"><strong>{copy.step}</strong><span><i /></span></div><h1>{copy.title}</h1><p className="instruction">{copy.instruction}</p><div className="distance"><strong>{copy.distance}</strong><span>{copy.ahead}</span></div><p className="illustrative-note">Illustrative content — plan a journey to see live guidance.</p></>}<div className="guide-actions"><button className={speaking ? 'speaking' : ''} onClick={speak}>{speaking ? <Pause /> : <Volume2 />}<span>{speaking ? 'Playing…' : copy.hear}</span></button><button onClick={lost}><CircleHelp /><span>{copy.lost}</span></button></div><ScenarioBar scenario={scenario} switchScenario={switchScenario} busy={busy} /></section></div>
}

function WrongWayScreen({ journey, back, correct, call }: { journey: api.Journey | null; back: () => void; correct: () => void; call: () => void }) {
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
  return <div className="screen wrong-screen"><div className="warning-top"><BackButton onClick={back} /><strong>Check your direction</strong></div><RotateCcw className="turn-symbol" /><section className="wrong-sheet"><h1>Feeling lost?</h1>{journey ? <p role="status">{checking ? 'Sending your position to the journey service…' : ack ? (ack.wrong_direction ? `The service confirms you are heading away from the route. ${ack.notify_family ? 'Your family has been told.' : ''}` : 'Position received. The service has not seen enough movement to confirm a wrong turn — it alerts only after several readings away from the route, so one odd GPS point never worries your family.') : 'Could not reach the journey service. Use the buttons below.'}</p> : <p>Plan a journey first so the service can check your position.</p>}<div className="screen-actions two"><PrimaryButton onClick={correct}>Show the correct direction</PrimaryButton><SecondaryButton onClick={call}>Call my family</SecondaryButton></div></section></div>
}

function SosScreen({ back, record, confirm, setNotice }: { back: () => void; record: () => void; confirm: (value: { title: string; body: string; action: string; onConfirm?: () => void }) => void; setNotice: (value: string) => void }) {
  const contactFamily = async () => {
    try {
      const opened = await api.sosOpen()
      confirm({
        title: 'Alert trusted family?', body: 'Nothing has been sent yet. Your family is alerted only after you confirm.', action: 'Send SOS alert',
        onConfirm: () => { void api.sosConfirm(opened.sos_id).then((done) => setNotice(done.notified_user_ids.length ? `SOS sent. Notified: ${done.notified_user_ids.join(', ')}.` : 'SOS confirmed, but no family account is linked.')).catch(() => setNotice('Could not send the SOS. Try again or call directly.')) },
      })
    } catch { setNotice('Could not reach the SOS service. You can still call directly.') }
  }
  const option = (icon: React.ReactNode, title: string, detail: string | undefined, onClick: () => void) => <button className="help-option" onClick={onClick}><span>{icon}</span><span><strong>{title}</strong>{detail && <small>{detail}</small>}</span><ChevronRight /></button>
  return <div className="screen paper-screen sos-screen"><header className="simple-header"><BackButton onClick={back} /><strong>Get help</strong></header><span className="sos-mark">SOS</span><section className="sos-title"><h1>Who should we call?</h1><p>No call or recording has started.</p></section><div className="help-options">{option(<UserRound />, 'Trusted family', 'Sends a real alert via the app', () => { void contactFamily() })}{option(<Phone />, 'Emergency services', 'Use for immediate danger', () => confirm({ title: 'Call emergency services?', body: 'Call 995 only for an immediate emergency.', action: 'Call 995' }))}{option(<Mic />, 'Record an audio message', 'Optional; never starts automatically', record)}</div><p className="privacy-footer"><Check />Audio and location are shared only after confirmation.</p></div>
}

function RecordingScreen({ back }: { back: () => void }) {
  const [recording, setRecording] = useState(false); const [seconds, setSeconds] = useState(0); const [audioUrl, setAudioUrl] = useState(''); const [error, setError] = useState(''); const recorder = useRef<MediaRecorder | null>(null); const chunks = useRef<Blob[]>([])
  useEffect(() => { if (!recording) return; const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000); return () => window.clearInterval(timer) }, [recording])
  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl) }, [audioUrl])
  const start = async () => { try { const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); const next = new MediaRecorder(stream); chunks.current = []; next.ondataavailable = (event) => chunks.current.push(event.data); next.onstop = () => { setAudioUrl(URL.createObjectURL(new Blob(chunks.current, { type: next.mimeType }))); stream.getTracks().forEach((track) => track.stop()) }; next.start(); recorder.current = next; setSeconds(0); setRecording(true); setError('') } catch { setError('Microphone permission was not granted. You can go back without recording.') } }
  const stop = () => { recorder.current?.stop(); setRecording(false) }; const clear = () => { if (audioUrl) URL.revokeObjectURL(audioUrl); setAudioUrl(''); setSeconds(0) }
  return <div className="screen paper-screen recording-screen"><TopBar title="Audio message" back={back} /><section><span className={`recording-orb${recording ? ' active' : ''}`}>{recording ? <Square /> : <Mic />}</span><h1>{recording ? 'Recording…' : audioUrl ? 'Message ready' : 'Record a short message'}</h1><p>{recording ? 'Tell your family what happened and where you are.' : 'Nothing is shared until you confirm.'}</p><strong className="recording-time">{String(Math.floor(seconds / 60)).padStart(2, '0')}:{String(seconds % 60).padStart(2, '0')}</strong></section>{error && <p className="recording-error" role="alert">{error}</p>}{audioUrl && <audio className="audio-player" controls src={audioUrl} />}<div className="screen-actions two">{recording ? <PrimaryButton onClick={stop}><Square /> Stop recording</PrimaryButton> : !audioUrl ? <PrimaryButton onClick={start}><Mic /> Start recording</PrimaryButton> : <><PrimaryButton onClick={() => setError('Recording stays on this device in the demo — upload is not wired yet.')}>Confirm message</PrimaryButton><SecondaryButton onClick={clear}><Trash2 /> Delete and try again</SecondaryButton></>}</div><PreviewBadge /></div>
}

function FamilyAccessScreen({ back, next }: { back: () => void; next: () => void }) {
  const [code, setCode] = useState('LIM-7284')
  return <div className="screen paper-screen family-screen"><TopBar title="Family access" back={back} /><section className="family-intro"><span><HeartHandshake /></span><h1>Follow a shared journey.</h1><p>Mdm Lim must choose to share each active journey.</p></section><label className="code-field"><span>SHARING CODE</span><input value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} /></label><div className="family-consent"><LockKeyhole /><span><strong>Consent comes first</strong><small>Location sharing ends when the journey ends.</small></span></div><div className="screen-actions"><PrimaryButton onClick={next}>Open demo journey</PrimaryButton></div><PreviewBadge /></div>
}

function FamilyJourneyScreen({ back }: { back: () => void }) {
  return <div className="screen paper-screen family-journey"><TopBar title="Mdm Lim’s journey" back={back} /><section className="family-status"><span className="live-dot"><i /> Journey active</span><h1>On the way to SGH</h1><p>Design preview — not live data</p></section><div className="current-step"><span>6</span><div><small>CURRENT STEP</small><strong>Following the lift signs</strong><p>Outram Park MRT</p></div></div><dl><div><dt>Expected arrival</dt><dd>About 24 minutes</dd></div><div><dt>Direction</dt><dd className="positive"><Check /> On the right path</dd></div><div><dt>Sharing</dt><dd>Until journey ends</dd></div></dl><div className="family-note"><ShieldCheck /><span>No help is needed right now. You’ll be alerted if Mdm Lim asks for help.</span></div><div className="screen-actions"><SecondaryButton onClick={back}>Stop viewing demo</SecondaryButton></div><PreviewBadge /></div>
}

function ConfirmSheet({ title, body, action, onConfirm, close }: { title: string; body: string; action: string; onConfirm?: () => void; close: () => void }) {
  return <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><button className="modal-backdrop" onClick={close} aria-label="Close confirmation" /><section><button className="modal-close" onClick={close} aria-label="Close"><X /></button><span className="modal-icon"><Phone /></span><h2 id="confirm-title">{title}</h2><p>{body}</p><button className="danger-button" onClick={() => { onConfirm?.(); close() }}>{action}</button><SecondaryButton onClick={close}>Cancel</SecondaryButton></section></div>
}

export default App
