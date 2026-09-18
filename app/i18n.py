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
    # --- leg instructions ---
    "leg.walk.instruction": {
        "en": "Walk to {to}. {landmark}",
        "zh": "步行前往{to}。{landmark}"},
    "leg.mrt.instruction": {
        "en": "Take the {line} line from {from_} towards {direction}. Get off at {to} ({stops} stops).",
        "zh": "在{from_}乘搭{line}线（{direction}方向），在{to}下车（{stops}站）。"},
    "leg.taxi.instruction": {
        "en": "Taxi from {from_} to {to}. Show the driver the card on screen.",
        "zh": "从{from_}乘德士到{to}。请向司机出示屏幕上的乘车卡。"},
    "leg.bus.instruction": {
        "en": "Take bus {service} from {from_} to {to}.",
        "zh": "在{from_}乘搭{service}号巴士到{to}。"},
    # --- landmarks (station-specific, keyed) ---
    "landmark.lift": {
        "en": "Use the lift, not the escalator.",
        "zh": "请使用电梯，不要使用扶梯。"},
    "landmark.sheltered": {
        "en": "The walkway is sheltered the whole way.",
        "zh": "沿途步道全程有遮盖。"},
    "landmark.none": {"en": "", "zh": ""},
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
