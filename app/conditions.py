"""Assemble the SourceResults a journey's advice is computed from.

Fixture overlay (PRD §9): a journey created with `scenario` set loads
data/fixtures/<scenario>.json. Sources present in that file come back with
status "fixture" — labelled test data, never presented as live. Sources the
fixture does not override are fetched live as usual. No scenario = all live."""
import json
from typing import Any

from app.adapters import datamall, weather
from app.adapters.base import fixture as fixture_result
from app.adapters.base import live as live_result
from app.adapters.base import unavailable
from app.config import FIXTURES_DIR
from app.models import SourceResult

# Lines serving the demo corridor (Bedok -> Outram Park and its alternatives).
CORRIDOR_LINES = ["EWL", "DTL", "NEL"]

# Sources gathered for every advice computation. Tier 1 + the Tier 2 sources
# the §7.1 rules need (floods for rule 1, lifts for rule 2).
SOURCES = [
    "train_service_alerts",
    "weather",
    "crowd_density_realtime",
    "crowd_density_forecast",
    "lift_maintenance",
    "flood_alerts",
    "traffic_incidents",
    "taxi_availability",
    "taxi_stands",
]

SCENARIOS = ["clear_day", "rain", "disruption_on_train", "lift_outage",
             "flood_destination", "crowding_forecast"]


def load_fixture(scenario: str) -> dict[str, Any] | None:
    path = FIXTURES_DIR / f"{scenario}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def gather(scenario: str | None = None,
           bus_stop_code: str | None = None) -> dict[str, SourceResult]:
    """`bus_stop_code`: when the journey plan boards a bus, its stop's live
    arrival/Load feed is gathered too (rule 6)."""
    overrides: dict[str, Any] = {}
    if scenario is not None:
        fx = load_fixture(scenario)
        if fx is None:
            # Unknown scenario: no data rather than wrong data.
            return {name: unavailable(name, f"unknown scenario '{scenario}' — "
                                            f"no fixture file") for name in SOURCES}
        overrides = fx.get("sources", {})

    results: dict[str, SourceResult] = {}
    for name in SOURCES:
        if name in overrides:
            results[name] = fixture_result(name, overrides[name])
        elif name == "weather":
            results[name] = weather.two_hour_forecast()
        else:
            results[name] = datamall.fetch_source(name, CORRIDOR_LINES)
    if bus_stop_code:
        name = "bus_arrival"
        if name in overrides:
            results[name] = fixture_result(name, overrides[name])
        else:
            try:
                results[name] = live_result(name,
                                            datamall.bus_arrival(bus_stop_code))
            except Exception as exc:  # noqa: BLE001 — truthful unavailability
                results[name] = unavailable(name, str(exc))
    return results


def data_status(results: dict[str, SourceResult]) -> dict[str, str]:
    return {name: r.status for name, r in results.items()}
