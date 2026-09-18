"""Normalises raw SourceResults into typed Facts the rules read.

Parsing is defensive: a malformed or missing source yields an EMPTY fact (no
signal), never an invented one. Every fact knows which source produced it, so
Advice.triggered_by is auditable end to end."""
from dataclasses import dataclass, field
from datetime import datetime

from app.models import SourceResult
from app.routing import stations as net
from app.routing.walk import _haversine_m

# The line-code trap (PS2_README §2.4): the same line has different codes in
# TrainServiceAlerts vs Station Crowd Density. Everything maps through this
# canonical table (crowd-density naming) before use. Corridor lines are
# identical in both, but the table exists so a non-corridor code never slips
# through unmapped.
CANONICAL_LINE = {
    "EWL": "EWL", "NSL": "NSL", "CCL": "CCL", "NEL": "NEL", "DTL": "DTL",
    "TEL": "TEL", "BPL": "BPL",
    "STL": "SLRT", "SLRT": "SLRT",       # Sengkang LRT
    "PTL": "PLRT", "PLRT": "PLRT",       # Punggol LRT
    "CEL": "CCL",                        # Circle extension -> CCL
    "CGL": "EWL",                        # Changi extension -> EWL
}

RAIN_TERMS = ("rain", "showers", "thundery")

# Corridor station -> data.gov.sg two-hr forecast area (assumption, STATUS.md).
STATION_AREA = {
    "EW4": "Bedok", "EW5": "Bedok", "EW6": "Bedok", "EW7": "Geylang",
    "EW8": "Geylang", "EW9": "Geylang", "EW10": "Kallang", "EW11": "Kallang",
    "EW12": "City", "EW13": "City", "EW14": "City", "EW15": "City",
    "EW16": "Bukit Merah", "DT14": "City", "DT15": "City", "DT16": "City",
    "DT17": "City", "DT18": "City", "DT19": "City",
    "NE3": "Bukit Merah", "NE4": "City", "NE5": "City", "NE6": "City",
}


@dataclass
class FloodFact:
    severity: str
    description: str
    lat: float | None
    lon: float | None
    radius_m: float


@dataclass
class Facts:
    tsa_status: int = 1
    broken_stations: set[str] = field(default_factory=set)   # canonical codes
    affected_lines: set[str] = field(default_factory=set)
    free_bus_stations: set[str] = field(default_factory=set)
    free_shuttle_stations: set[str] = field(default_factory=set)
    advisories: list[str] = field(default_factory=list)
    rain_areas: set[str] = field(default_factory=set)
    crowd: dict[str, str] = field(default_factory=dict)          # code -> l/m/h
    crowd_forecast: dict[str, str] = field(default_factory=dict) # code -> worst level 06:00-10:00
    lift_out: dict[str, str] = field(default_factory=dict)       # code -> LiftDesc
    floods: list[FloodFact] = field(default_factory=list)


def _stations_list(raw: str | list) -> list[str]:
    if isinstance(raw, list):
        return [s.strip() for s in raw]
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def build_facts(results: dict[str, SourceResult],
                boarding_time: datetime | None = None) -> Facts:
    f = Facts()

    tsa = results.get("train_service_alerts")
    if tsa and tsa.status != "unavailable" and isinstance(tsa.data, dict):
        f.tsa_status = int(tsa.data.get("Status", 1))
        for seg in tsa.data.get("AffectedSegments") or []:
            line = CANONICAL_LINE.get(str(seg.get("Line", "")).upper(),
                                      str(seg.get("Line", "")).upper())
            f.affected_lines.add(line)
            f.broken_stations |= set(_stations_list(seg.get("Stations", "")))
            f.free_bus_stations |= set(_stations_list(seg.get("FreePublicBus", "")))
            f.free_shuttle_stations |= set(_stations_list(seg.get("FreeMRTShuttle", "")))
        for msg in tsa.data.get("Message") or []:
            content = msg.get("Content") if isinstance(msg, dict) else str(msg)
            if content:
                f.advisories.append(content)

    wx = results.get("weather")
    if wx and wx.status != "unavailable" and isinstance(wx.data, dict):
        for item in wx.data.get("items") or []:
            for fc in item.get("forecasts") or []:
                text = str(fc.get("forecast", "")).lower()
                if any(t in text for t in RAIN_TERMS):
                    f.rain_areas.add(fc.get("area", ""))

    crt = results.get("crowd_density_realtime")
    if crt and crt.status != "unavailable" and isinstance(crt.data, dict):
        for _line, rows in crt.data.items():
            for row in rows or []:
                code = row.get("Station")
                level = row.get("CrowdLevel")
                if code and level in ("l", "m", "h"):
                    f.crowd[code] = level

    cfc = results.get("crowd_density_forecast")
    if cfc and cfc.status != "unavailable" and isinstance(cfc.data, dict):
        # Forecast matching is by TIME OF DAY (30-min slots), not date, so a
        # fixture dated differently from the demo day still matches
        # (assumption recorded in STATUS.md).
        want = boarding_time.strftime("%H:%M") if boarding_time else None
        for _line, days in cfc.data.items():
            for day in days or []:
                for st in day.get("Stations") or []:
                    code = st.get("Station")
                    worst = None
                    for iv in st.get("Interval") or []:
                        start = str(iv.get("Start", ""))
                        hhmm = start[11:16] if len(start) >= 16 else ""
                        lv = iv.get("CrowdLevel")
                        if lv not in ("l", "m", "h"):
                            continue
                        if want is None or hhmm == want or \
                           (want and abs(_min_of_day(hhmm) - _min_of_day(want)) <= 30):
                            order = {"l": 0, "m": 1, "h": 2}
                            if worst is None or order[lv] > order[worst]:
                                worst = lv
                    if code and worst:
                        f.crowd_forecast[code] = worst

    lift = results.get("lift_maintenance")
    if lift and lift.status != "unavailable" and isinstance(lift.data, list):
        for row in lift.data:
            code = row.get("StationCode")
            if code:
                f.lift_out[code] = row.get("LiftDesc", "")

    fl = results.get("flood_alerts")
    if fl and fl.status != "unavailable" and isinstance(fl.data, list):
        for row in fl.data:
            if str(row.get("msgType", "Alert")) == "Cancel":
                continue
            circle = row.get("circle") or {}
            f.floods.append(FloodFact(
                severity=str(row.get("severity", "Unknown")),
                description=str(row.get("description", row.get("headline", ""))),
                lat=circle.get("latitude"), lon=circle.get("longitude"),
                radius_m=float(circle.get("radius_km", 1.0)) * 1000))
    return f


def _min_of_day(hhmm: str) -> int:
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except ValueError:
        return -10_000


def flood_near(facts: Facts, coord: tuple[float, float],
               margin_m: float = 400) -> FloodFact | None:
    for fd in facts.floods:
        if fd.lat is None or fd.lon is None:
            continue
        if _haversine_m(coord, (fd.lat, fd.lon)) <= fd.radius_m + margin_m:
            return fd
    return None


def raining_at(facts: Facts, station_codes: list[str]) -> bool:
    if not facts.rain_areas:
        return False
    areas = {STATION_AREA.get(c) for c in station_codes} - {None}
    if areas & facts.rain_areas:
        return True
    # Fallback: island-wide rain (many areas reporting) counts everywhere.
    return len(facts.rain_areas) >= 15


def stations_of(legs) -> list[str]:
    """Station codes an MRT plan passes through (from uses_stations when the
    engine has it; else derived from leg endpoints by name)."""
    codes = []
    for leg in legs:
        if leg.mode != "mrt":
            continue
        for name in (leg.from_name, leg.to_name):
            for s in net.station_for(name):
                codes.append(s.code)
    return codes
