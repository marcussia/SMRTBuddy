"""data.gov.sg real-time weather (no key needed; verified live 2026-09-19)."""
from app.adapters.base import AdapterError, fetch_json, live, unavailable
from app.config import WEATHER_BASE
from app.models import SourceResult


def two_hour_forecast() -> SourceResult:
    name = "weather"
    try:
        payload = fetch_json(f"{WEATHER_BASE}/two-hr-forecast")
        return live(name, payload.get("data", payload))
    except (AdapterError, AttributeError) as exc:
        return unavailable(name, str(exc))


def rainfall() -> SourceResult:
    name = "rainfall"
    try:
        payload = fetch_json(f"{WEATHER_BASE}/rainfall")
        return live(name, payload.get("data", payload))
    except (AdapterError, AttributeError) as exc:
        return unavailable(name, str(exc))
