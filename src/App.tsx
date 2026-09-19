import { useEffect, useRef, useState } from 'react'
import { Accessibility, ArrowLeft, ArrowRight, Check, ChevronRight, CircleHelp, HeartHandshake, Home, Languages, LocateFixed, LockKeyhole, MapPin, Mic, Navigation, Pause, Phone, RotateCcw, ShieldCheck, Square, Trash2, UserRound, Volume2, X } from 'lucide-react'
import { guideCopy, journeySteps, languages, screenLabels, type Locale, type ScreenId } from './data'
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
  const [confirm, setConfirm] = useState<{ title: string; body: string; action: string } | null>(null)
  useEffect(() => localStorage.setItem(storageKey, locale), [locale])
  const navigate = (next: ScreenId) => { setNotice(''); setConfirm(null); setScreen(next) }
  const selectLocale = (next: Locale) => setLocale(next)
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
      {screen === 'plan' && <PlanScreen destination={destination} setDestination={setDestination} back={() => navigate('profile')} listen={() => navigate('listening')} next={() => destination.trim() ? navigate('recognised') : setNotice('Enter a destination or use the microphone.')} />}
      {screen === 'listening' && <ListeningScreen transcript={transcript} setTranscript={setTranscript} back={() => navigate('plan')} accept={() => { setDestination(transcript || 'Singapore General Hospital'); navigate('recognised') }} notice={notice} setNotice={setNotice} />}
      {screen === 'recognised' && <RecognisedScreen destination={destination || 'Singapore General Hospital'} back={() => navigate('plan')} next={() => navigate('overview')} />}
      {screen === 'overview' && <OverviewScreen back={() => navigate('recognised')} start={startJourney} notice={notice} />}
      {screen === 'guide' && <GuideScreen locale={locale} selectLocale={selectLocale} back={() => navigate('overview')} lost={() => navigate('wrong-way')} sos={() => navigate('sos')} />}
      {screen === 'wrong-way' && <WrongWayScreen back={() => navigate('guide')} correct={() => navigate('guide')} call={() => setConfirm({ title: 'Call trusted family?', body: 'A call will only begin after you confirm.', action: 'Call family' })} />}
      {screen === 'sos' && <SosScreen back={() => navigate('guide')} record={() => navigate('recording')} confirm={setConfirm} />}
      {screen === 'recording' && <RecordingScreen back={() => navigate('sos')} />}
      {screen === 'family' && <FamilyAccessScreen back={() => navigate('profile')} next={() => navigate('family-journey')} />}
      {screen === 'family-journey' && <FamilyJourneyScreen back={() => navigate('family')} />}
      {notice && screen !== 'listening' && screen !== 'overview' && <div className="toast" role="status">{notice}</div>}
      {confirm && <ConfirmSheet {...confirm} close={() => setConfirm(null)} />}
    </div></section>
  </main>
}

function PrototypeNav({ screen, locale, navigate, selectLocale }: { screen: ScreenId; locale: Locale; navigate: (screen: ScreenId) => void; selectLocale: (locale: Locale) => void }) {
  return <aside className="prototype-nav" aria-label="Pitch demo navigation"><div className="prototype-brand"><span className="signal-mark"><i /><i /><i /></span><div><strong>Mdm Lim</strong><span>Commuter companion</span></div></div><p className="prototype-note">Jump to any judging moment. This panel is hidden on phones.</p><nav>{screenLabels.map((item, index) => <div key={item.id}>{item.group !== screenLabels[index - 1]?.group && <span className="nav-group">{item.group}</span>}<button className={screen === item.id ? 'active' : ''} onClick={() => navigate(item.id)}><span>{item.label}</span><ChevronRight size={18} /></button></div>)}</nav><div className="nav-languages"><span className="nav-group">Step 6 language</span><div>{languages.map((item) => <button key={item.id} className={locale === item.id ? 'active' : ''} onClick={() => { selectLocale(item.id); navigate('guide') }}>{item.code}</button>)}</div></div></aside>
}

function BackButton({ onClick, light = false }: { onClick: () => void; light?: boolean }) { return <button className={`back-button${light ? ' light' : ''}`} onClick={onClick} aria-label="Go back"><ArrowLeft /></button> }
function TopBar({ title, back }: { title: string; back: () => void }) { return <header className="top-bar"><BackButton onClick={back} /><strong>{title}</strong><span /></header> }
function PrimaryButton({ children, onClick, disabled = false }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean }) { return <button className="primary-button" onClick={onClick} disabled={disabled}>{children}</button> }
function SecondaryButton({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) { return <button className="secondary-button" onClick={onClick}>{children}</button> }

function LanguageScreen({ locale, selectLocale, next }: { locale: Locale; selectLocale: (locale: Locale) => void; next: () => void }) {
  return <div className="screen language-screen"><section className="language-sheet"><p className="welcome">Welcome!</p><h1>Choose your language.</h1><p className="helper">You can change this at any time.</p><div className="language-list" role="radiogroup" aria-label="Choose your language">{languages.map((item) => <button key={item.id} className={locale === item.id ? 'selected' : ''} onClick={() => selectLocale(item.id)} role="radio" aria-checked={locale === item.id}><span>{item.label}</span><b>{item.code}</b></button>)}</div><PrimaryButton onClick={next}>Continue</PrimaryButton></section></div>
}

function ProfileScreen({ back, traveller, family }: { back: () => void; traveller: () => void; family: () => void }) {
  return <div className="screen paper-screen profile-screen"><TopBar title="Choose your profile" back={back} /><h1>Who is using this app?</h1><div className="role-list"><button onClick={traveller}><b>A</b><span><strong>I am travelling</strong><small>Plan and follow my own journey.</small></span><ArrowRight /></button><button onClick={family}><b>B</b><span><strong>I am family</strong><small>Follow journeys that are shared with me.</small></span><ArrowRight /></button></div><p className="consent-copy">Location will never be shared automatically without your permission.</p></div>
}

function PlaceField({ label, value, placeholder, icon, onChange, listen }: { label: string; value: string; placeholder?: string; icon: React.ReactNode; onChange?: (value: string) => void; listen: () => void }) {
  return <label className="place-field"><span>{label}</span><div>{icon}<input value={value} placeholder={placeholder} onChange={(event) => onChange?.(event.target.value)} readOnly={!onChange} /><button onClick={listen} type="button" aria-label={`Speak ${label.toLowerCase()} location`}><Mic /></button></div></label>
}
function AccessibleStrip() { return <div className="accessible-strip"><Accessibility /><span><strong>Accessible route is on</strong><small>Lifts and sheltered paths preferred</small></span></div> }
function PlanScreen({ destination, setDestination, back, listen, next }: { destination: string; setDestination: (value: string) => void; back: () => void; listen: () => void; next: () => void }) {
  return <div className="screen paper-screen plan-screen"><TopBar title="Plan a journey" back={back} /><section className="page-title"><h1>Where are you going?</h1><p>Speak or type a place.</p></section><div className="place-fields"><PlaceField label="From" value="Home in Bedok" icon={<Home />} listen={listen} /><PlaceField label="To" value={destination} placeholder="Enter a place" icon={<MapPin />} onChange={setDestination} listen={listen} /></div><AccessibleStrip /><div className="screen-actions"><PrimaryButton onClick={next}>Show my journey</PrimaryButton></div></div>
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

function RecognisedScreen({ destination, back, next }: { destination: string; back: () => void; next: () => void }) {
  return <div className="screen paper-screen plan-screen"><TopBar title="Plan a journey" back={back} /><section className="page-title"><h1>Where are you going?</h1><p className="success-text">Destination recognised!</p></section><div className="place-fields"><PlaceField label="From" value="Home in Bedok" icon={<Home />} listen={back} /><PlaceField label="To" value={destination} icon={<MapPin />} listen={back} /></div><AccessibleStrip /><div className="recognised-strip"><Check /><strong>Destination recognised</strong></div><div className="screen-actions"><PrimaryButton onClick={next}>Show my journey</PrimaryButton></div></div>
}

function OverviewScreen({ back, start, notice }: { back: () => void; start: () => void; notice: string }) {
  return <div className="screen paper-screen overview-screen"><TopBar title="Your journey" back={back} /><section className="overview-heading"><div><span>Bedok</span><ArrowRight /><span>SGH</span></div><h1>8 simple steps</h1><p>About 48 minutes at your walking pace.</p></section><div className="journey-badges"><span><Accessibility /> Step-free</span><span><LocateFixed /> Sheltered paths</span></div><ol className="journey-list">{journeySteps.map((step) => <li key={step.number} className={step.number === 6 ? 'featured' : ''}><b>{step.number}</b><span><strong>{step.title}</strong><small>{step.detail}</small></span>{step.number === 6 && <ChevronRight />}</li>)}</ol>{notice && <p className="overview-notice" role="status">{notice}</p>}<div className="screen-actions"><PrimaryButton onClick={start}><Navigation /> Start journey</PrimaryButton></div></div>
}

function GuideScreen({ locale, selectLocale, back, lost, sos }: { locale: Locale; selectLocale: (locale: Locale) => void; back: () => void; lost: () => void; sos: () => void }) {
  const copy = guideCopy[locale]; const [speaking, setSpeaking] = useState(false)
  const speak = () => { if (!('speechSynthesis' in window)) return; if (speaking) { speechSynthesis.cancel(); setSpeaking(false); return }; const utterance = new SpeechSynthesisUtterance(`${copy.title}. ${copy.instruction}. ${copy.distance} ${copy.ahead}. ${copy.status}.`); utterance.lang = copy.speechLanguage; utterance.rate = .72; utterance.onend = () => setSpeaking(false); utterance.onerror = () => setSpeaking(false); speechSynthesis.cancel(); speechSynthesis.speak(utterance); setSpeaking(true) }
  useEffect(() => () => window.speechSynthesis?.cancel(), [])
  return <div className={`screen guide-screen locale-${locale}`}><img src={exitPhoto} alt="Illuminated yellow Exit 7 sign at Outram Park MRT" className="guide-photo" /><div className="photo-shade" /><div className="guide-top"><BackButton onClick={back} light /><strong>{copy.station}</strong><label className="guide-language"><Languages /><select aria-label="Change language" value={locale} onChange={(event) => selectLocale(event.target.value as Locale)}>{languages.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label></div><button className="floating-sos" onClick={sos}>SOS</button><section className="guide-sheet"><div className="progress-row"><strong>{copy.step}</strong><span><i /></span></div><h1>{copy.title}</h1><p className="instruction">{copy.instruction}</p><div className="distance"><strong>{copy.distance}</strong><span>{copy.ahead}</span></div><div className="right-path"><Check /><strong>{copy.status}</strong></div><div className="guide-actions"><button className={speaking ? 'speaking' : ''} onClick={speak}>{speaking ? <Pause /> : <Volume2 />}<span>{speaking ? 'Playing…' : copy.hear}</span></button><button onClick={lost}><CircleHelp /><span>{copy.lost}</span></button></div></section></div>
}

function WrongWayScreen({ back, correct, call }: { back: () => void; correct: () => void; call: () => void }) {
  return <div className="screen wrong-screen"><div className="warning-top"><BackButton onClick={back} /><strong>Check your direction</strong></div><RotateCcw className="turn-symbol" /><section className="wrong-sheet"><h1>Stop!<br />Turn around.</h1><p>Follow the yellow Exit 7 signs in the opposite direction.</p><div className="screen-actions two"><PrimaryButton onClick={correct}>Show the correct direction</PrimaryButton><SecondaryButton onClick={call}>Call my family</SecondaryButton></div></section></div>
}

function SosScreen({ back, record, confirm }: { back: () => void; record: () => void; confirm: (value: { title: string; body: string; action: string }) => void }) {
  const option = (icon: React.ReactNode, title: string, detail: string | undefined, onClick: () => void) => <button className="help-option" onClick={onClick}><span>{icon}</span><span><strong>{title}</strong>{detail && <small>{detail}</small>}</span><ChevronRight /></button>
  return <div className="screen paper-screen sos-screen"><header className="simple-header"><BackButton onClick={back} /><strong>Get help</strong></header><span className="sos-mark">SOS</span><section className="sos-title"><h1>Who should we call?</h1><p>No call or recording has started.</p></section><div className="help-options">{option(<UserRound />, 'Trusted family', undefined, () => confirm({ title: 'Call trusted family?', body: 'Your location will be shared only after you confirm.', action: 'Call family' }))}{option(<Phone />, 'Emergency services', 'Use for immediate danger', () => confirm({ title: 'Call emergency services?', body: 'Call 995 only for an immediate emergency.', action: 'Call 995' }))}{option(<Mic />, 'Record an audio message', 'Optional; never starts automatically', record)}</div><p className="privacy-footer"><Check />Audio and location are shared only after confirmation.</p></div>
}

function RecordingScreen({ back }: { back: () => void }) {
  const [recording, setRecording] = useState(false); const [seconds, setSeconds] = useState(0); const [audioUrl, setAudioUrl] = useState(''); const [error, setError] = useState(''); const recorder = useRef<MediaRecorder | null>(null); const chunks = useRef<Blob[]>([])
  useEffect(() => { if (!recording) return; const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000); return () => window.clearInterval(timer) }, [recording])
  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl) }, [audioUrl])
  const start = async () => { try { const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); const next = new MediaRecorder(stream); chunks.current = []; next.ondataavailable = (event) => chunks.current.push(event.data); next.onstop = () => { setAudioUrl(URL.createObjectURL(new Blob(chunks.current, { type: next.mimeType }))); stream.getTracks().forEach((track) => track.stop()) }; next.start(); recorder.current = next; setSeconds(0); setRecording(true); setError('') } catch { setError('Microphone permission was not granted. You can go back without recording.') } }
  const stop = () => { recorder.current?.stop(); setRecording(false) }; const clear = () => { if (audioUrl) URL.revokeObjectURL(audioUrl); setAudioUrl(''); setSeconds(0) }
  return <div className="screen paper-screen recording-screen"><TopBar title="Audio message" back={back} /><section><span className={`recording-orb${recording ? ' active' : ''}`}>{recording ? <Square /> : <Mic />}</span><h1>{recording ? 'Recording…' : audioUrl ? 'Message ready' : 'Record a short message'}</h1><p>{recording ? 'Tell your family what happened and where you are.' : 'Nothing is shared until you confirm.'}</p><strong className="recording-time">{String(Math.floor(seconds / 60)).padStart(2, '0')}:{String(seconds % 60).padStart(2, '0')}</strong></section>{error && <p className="recording-error" role="alert">{error}</p>}{audioUrl && <audio className="audio-player" controls src={audioUrl} />}<div className="screen-actions two">{recording ? <PrimaryButton onClick={stop}><Square /> Stop recording</PrimaryButton> : !audioUrl ? <PrimaryButton onClick={start}><Mic /> Start recording</PrimaryButton> : <><PrimaryButton onClick={() => setError('Demo message saved locally. Connect the backend to send it.')}>Confirm message</PrimaryButton><SecondaryButton onClick={clear}><Trash2 /> Delete and try again</SecondaryButton></>}</div></div>
}

function FamilyAccessScreen({ back, next }: { back: () => void; next: () => void }) {
  const [code, setCode] = useState('LIM-7284')
  return <div className="screen paper-screen family-screen"><TopBar title="Family access" back={back} /><section className="family-intro"><span><HeartHandshake /></span><h1>Follow a shared journey.</h1><p>Mdm Lim must choose to share each active journey.</p></section><label className="code-field"><span>SHARING CODE</span><input value={code} onChange={(event) => setCode(event.target.value.toUpperCase())} /></label><div className="family-consent"><LockKeyhole /><span><strong>Consent comes first</strong><small>Location sharing ends when the journey ends.</small></span></div><div className="screen-actions"><PrimaryButton onClick={next}>Open demo journey</PrimaryButton></div></div>
}

function FamilyJourneyScreen({ back }: { back: () => void }) {
  return <div className="screen paper-screen family-journey"><TopBar title="Mdm Lim’s journey" back={back} /><section className="family-status"><span className="live-dot"><i /> Journey active</span><h1>On the way to SGH</h1><p>Last updated just now · Demo data</p></section><div className="current-step"><span>6</span><div><small>CURRENT STEP</small><strong>Following Exit 7</strong><p>Outram Park MRT</p></div></div><dl><div><dt>Expected arrival</dt><dd>About 24 minutes</dd></div><div><dt>Direction</dt><dd className="positive"><Check /> On the right path</dd></div><div><dt>Sharing</dt><dd>Until journey ends</dd></div></dl><div className="family-note"><ShieldCheck /><span>No help is needed right now. You’ll be alerted if Mdm Lim asks for help.</span></div><div className="screen-actions"><SecondaryButton onClick={back}>Stop viewing demo</SecondaryButton></div></div>
}

function ConfirmSheet({ title, body, action, close }: { title: string; body: string; action: string; close: () => void }) {
  return <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><button className="modal-backdrop" onClick={close} aria-label="Close confirmation" /><section><button className="modal-close" onClick={close} aria-label="Close"><X /></button><span className="modal-icon"><Phone /></span><h2 id="confirm-title">{title}</h2><p>{body}</p><button className="danger-button" onClick={close}>{action}</button><SecondaryButton onClick={close}>Cancel</SecondaryButton></section></div>
}

export default App
