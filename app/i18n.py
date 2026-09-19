"""Table-driven i18n (Q6): en + zh shipped; adding ms/ta = adding entries to
STRINGS, no code change. Every user-facing string in a response is produced
here from an i18n_key + params; `resolve` falls back to English when a locale
has no entry (fallbacks are counted so gaps are visible, never silent)."""
from typing import Any

FALLBACKS_USED: dict[str, int] = {}  # i18n_key -> count (visibility, not logic)

STRINGS: dict[str, dict[str, str]] = {
    # --- advice headlines ---
    "advice.proceed.headline": {
        "en": "All clear — leave as planned.",
        "zh": "一切正常——按原计划出发。"},
    "advice.wait.headline": {
        "en": "Stay where you are — waiting is faster.",
        "zh": "请留在原地——等待更快。"},
    "advice.reroute.headline": {
        "en": "Change of plan: {summary}",
        "zh": "计划有变：{summary}"},
    "advice.leave_earlier.headline": {
        "en": "Leave {minutes} minutes earlier today.",
        "zh": "今天请提早{minutes}分钟出发。"},
    "advice.take_taxi.headline": {
        "en": "Take a taxi from {stand} — show the driver the card.",
        "zh": "请到{stand}乘坐德士——向司机出示乘车卡。"},
    "advice.cancel_trip.headline": {
        "en": "Do not travel today — {reason_short}",
        "zh": "今天请不要出行——{reason_short}"},
    # --- alight instruction (§7.5 on_train) ---
    "advice.alight.headline": {
        "en": "Get off at {station}, then {next_step}",
        "zh": "请在{station}下车，然后{next_step}"},
    # --- leg instructions (screen text) ---
    "leg.walk.instruction": {
        "en": "Walk to {to}. {landmark}",
        "zh": "步行前往{to}。{landmark}",
        "ms": "Jalan kaki ke {to}. {landmark}",
        "ta": "{to}க்கு நடந்து செல்லுங்கள். {landmark}"},
    "leg.mrt.instruction": {
        "en": "Take the {line} line from {from_} towards {direction}. Get off at {to} ({stops} stops).",
        "zh": "在{from_}乘搭{line}线（{direction}方向），在{to}下车（{stops}站）。",
        "ms": "Naik laluan {line} dari {from_} menuju {direction}. Turun di {to} ({stops} perhentian).",
        "ta": "{from_}லிருந்து {direction} நோக்கிச் செல்லும் {line} ரயிலில் ஏறுங்கள். {to}இல் இறங்குங்கள் ({stops} நிலையங்கள்)."},
    "leg.taxi.instruction": {
        "en": "Taxi from {from_} to {to}. Show the driver the card on screen.",
        "zh": "从{from_}乘德士到{to}。请向司机出示屏幕上的乘车卡。",
        "ms": "Naik teksi dari {from_} ke {to}. Tunjukkan kad pada skrin kepada pemandu.",
        "ta": "{from_}லிருந்து {to}க்கு டாக்சியில் செல்லுங்கள். திரையில் உள்ள அட்டையை ஓட்டுநரிடம் காட்டுங்கள்."},
    "leg.bus.instruction": {
        "en": "Take bus {service} from {from_} to {to}.",
        "zh": "在{from_}乘搭{service}号巴士到{to}。",
        "ms": "Naik bas {service} dari {from_} ke {to}.",
        "ta": "{from_}இல் {service} பேருந்தில் ஏறி {to}க்குச் செல்லுங்கள்."},
    # --- leg speech (same information, said the way a person would say it) ---
    "leg.walk.speech": {
        "en": "Next, walk to {to}. Take your time. {landmark}",
        "zh": "接下来，请慢慢步行前往{to}。{landmark}",
        "ms": "Seterusnya, jalan perlahan-lahan ke {to}. {landmark}",
        "ta": "அடுத்து, {to}க்கு நிதானமாக நடந்து செல்லுங்கள். {landmark}"},
    "leg.mrt.speech": {
        "en": "You're at {from_}. Take the {line} line towards {direction}, ride {stops} stops, and get off at {to}.",
        "zh": "您现在在{from_}。请乘搭{line}线，往{direction}方向，坐{stops}站，在{to}下车。",
        "ms": "Anda di {from_}. Naik laluan {line} menuju {direction}, {stops} perhentian, dan turun di {to}.",
        "ta": "நீங்கள் {from_}இல் இருக்கிறீர்கள். {direction} நோக்கி {line} ரயிலில் ஏறி, {stops} நிலையங்கள் பயணித்து, {to}இல் இறங்குங்கள்."},
    "leg.taxi.speech": {
        "en": "Take a taxi from {from_} to {to}. When you board, show the driver the card on your screen.",
        "zh": "请从{from_}乘德士前往{to}。上车后，请向司机出示屏幕上的乘车卡。",
        "ms": "Naik teksi dari {from_} ke {to}. Selepas menaiki, tunjukkan kad pada skrin anda kepada pemandu.",
        "ta": "{from_}லிருந்து {to}க்கு டாக்சியில் செல்லுங்கள். ஏறியதும், திரையில் உள்ள அட்டையை ஓட்டுநரிடம் காட்டுங்கள்."},
    "leg.bus.speech": {
        "en": "Take bus {service} from {from_}. It will take you to {to}.",
        "zh": "请在{from_}乘搭{service}号巴士，它会带您前往{to}。",
        "ms": "Naik bas {service} dari {from_}. Ia akan membawa anda ke {to}.",
        "ta": "{from_}இல் {service} பேருந்தில் ஏறுங்கள். அது உங்களை {to}க்கு அழைத்துச் செல்லும்."},
    # --- landmarks (station-specific, keyed) ---
    "landmark.lift": {
        "en": "Use the lift, not the escalator.",
        "zh": "请使用电梯，不要使用扶梯。",
        "ms": "Gunakan lif, bukan eskalator.",
        "ta": "மின்தூக்கியைப் பயன்படுத்துங்கள், எஸ்கலேட்டரை அல்ல."},
    "landmark.sheltered": {
        "en": "The walkway is sheltered the whole way.",
        "zh": "沿途步道全程有遮盖。",
        "ms": "Laluan ini berbumbung sepanjang jalan.",
        "ta": "நடைபாதை முழுவதும் மூடப்பட்டுள்ளது."},
    "landmark.none": {"en": "", "zh": "", "ms": "", "ta": ""},
    # --- station exit hints (from captured OSM entrances) ---
    "exit.nearest.yes": {
        "en": "Exit {ref} is nearest to this route and OSM tags it step-free.",
        "zh": "{ref} 号出口离这条路线最近，OSM 标注为无障碍。",
        "ms": "Pintu keluar {ref} paling dekat dengan laluan ini dan OSM menandakannya bebas tangga.",
        "ta": "வெளியேறும் வழி {ref} இந்தப் பாதைக்கு மிக அருகில் உள்ளது; OSM இதை படிக்கட்டு இல்லாதது எனக் குறித்துள்ளது."},
    "exit.nearest.no": {
        "en": "Exit {ref} is nearest to this route. OSM tags it as not wheelchair-accessible.",
        "zh": "{ref} 号出口离这条路线最近。OSM 标注为不适合轮椅。",
        "ms": "Pintu keluar {ref} paling dekat dengan laluan ini. OSM menandakannya tidak sesuai untuk kerusi roda.",
        "ta": "வெளியேறும் வழி {ref} இந்தப் பாதைக்கு மிக அருகில் உள்ளது. OSM இதை சக்கர நாற்காலிக்கு ஏற்றதல்ல எனக் குறித்துள்ளது."},
    "exit.nearest.untagged": {
        "en": "Exit {ref} is nearest to this route (OpenStreetMap; wheelchair access not tagged).",
        "zh": "{ref} 号出口离这条路线最近（OpenStreetMap；未标注轮椅通行情况）。",
        "ms": "Pintu keluar {ref} paling dekat dengan laluan ini (OpenStreetMap; akses kerusi roda tidak ditanda).",
        "ta": "வெளியேறும் வழி {ref} இந்தப் பாதைக்கு மிக அருகில் உள்ளது (OpenStreetMap; சக்கர நாற்காலி அணுகல் குறிக்கப்படவில்லை)."},
    "exit.preferred.untagged": {
        "en": "Exit {ref} is tagged step-free (OpenStreetMap). It is slightly further than Exit {other}, which has no accessibility tag.",
        "zh": "{ref} 号出口标注为无障碍（OpenStreetMap）。它比 {other} 号出口稍远，后者没有无障碍标注。",
        "ms": "Pintu keluar {ref} ditanda bebas tangga (OpenStreetMap). Ia sedikit lebih jauh daripada pintu keluar {other}, yang tiada tanda kebolehcapaian.",
        "ta": "வெளியேறும் வழி {ref} படிக்கட்டு இல்லாதது எனக் குறிக்கப்பட்டுள்ளது (OpenStreetMap). இது {other}-ஐ விட சற்று தொலைவில் உள்ளது; {other}-க்கு அணுகல் குறியீடு இல்லை."},
    "exit.preferred.no": {
        "en": "Exit {ref} is tagged step-free (OpenStreetMap). It is slightly further than Exit {other}, which OSM tags as not wheelchair-accessible.",
        "zh": "{ref} 号出口标注为无障碍（OpenStreetMap）。它比 {other} 号出口稍远，后者被 OSM 标注为不适合轮椅。",
        "ms": "Pintu keluar {ref} ditanda bebas tangga (OpenStreetMap). Ia sedikit lebih jauh daripada pintu keluar {other}, yang ditanda OSM sebagai tidak sesuai untuk kerusi roda.",
        "ta": "வெளியேறும் வழி {ref} படிக்கட்டு இல்லாதது எனக் குறிக்கப்பட்டுள்ளது (OpenStreetMap). இது {other}-ஐ விட சற்று தொலைவில் உள்ளது; {other}-ஐ OSM சக்கர நாற்காலிக்கு ஏற்றதல்ல எனக் குறித்துள்ளது."},
    # --- reroute summaries / short reasons ---
    "summary.take_line": {
        "en": "take the {line} line to {to}.",
        "zh": "改乘{line}线前往{to}。"},
    "summary.head_to": {
        "en": "head to {to} instead.",
        "zh": "请改前往{to}。"},
    "short.flood": {
        "en": "flash flooding on your route.",
        "zh": "您的路线上出现淹水。"},
}


def resolve(key: str, locale: str, **params: Any) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        # Unknown key is a bug we want to see, not hide.
        return f"[missing i18n: {key}]"
    if locale not in entry:
        FALLBACKS_USED[key] = FALLBACKS_USED.get(key, 0) + 1
        locale = "en"
    try:
        return entry[locale].format(**params)
    except (KeyError, IndexError):
        return entry[locale]


# Destination names for the taxi driver card (en + zh). Demo corridor only;
# a destination missing here gets destination_zh = the English name, so the
# card never silently shows a wrong translation.
PLACE_NAMES_ZH: dict[str, str] = {
    "Singapore General Hospital": "新加坡中央医院",
    "Outram Park": "欧南园",
    "Bedok": "勿洛",
    "Bugis": "武吉士",
    "Chinatown": "牛车水",
}


def place_zh(name_en: str) -> str:
    return PLACE_NAMES_ZH.get(name_en, name_en)
