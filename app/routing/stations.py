"""Demo-corridor network (Q1: hand-built graph, corridor only — Bedok to
Outram Park / Singapore General Hospital and its alternatives).

Sources, per file:
- Station coordinates: app/reference/stations.json — centroids computed from
  the organisers' AmendmenttoMP2014RailStation.geojson (WGS84, verified).
- Line sequences and interchange pairings: the public MRT network map
  (stable, well-known); recorded as an assumption in STATUS.md.
- Bus 2 segment: data/replay/bus2_bedok_outram.json — captured live from
  DataMall BusRoutes/BusStops on 2026-09-19.
- Places: data/replay/places_geocoded.json — OSM Nominatim, captured.

DT17 (Downtown) is absent from the 2017 GeoJSON: it stays in the sequence for
hop timing, with no coordinate; geometry skips it."""
import json
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REF = json.loads((_HERE.parent / "reference" / "stations.json").read_text())["stations"]
_REPLAY = _HERE.parent.parent / "data" / "replay"


@dataclass(frozen=True)
class Station:
    code: str            # e.g. "EW5"
    name: str            # e.g. "Bedok"
    line: str            # "EWL" | "DTL" | "NEL"
    lat: float | None
    lon: float | None


def _coord(name: str) -> tuple[float | None, float | None]:
    entry = _REF.get(name.upper())
    if entry is None:
        return None, None
    return entry["lat"], entry["lon"]


def _line(line: str, codes_names: list[tuple[str, str]]) -> list[Station]:
    out = []
    for code, name in codes_names:
        lat, lon = _coord(name)
        out.append(Station(code, name, line, lat, lon))
    return out


# Order matters: adjacent entries are adjacent stations.
EWL = _line("EWL", [
    ("EW4", "Tanah Merah"), ("EW5", "Bedok"), ("EW6", "Kembangan"),
    ("EW7", "Eunos"), ("EW8", "Paya Lebar"), ("EW9", "Aljunied"),
    ("EW10", "Kallang"), ("EW11", "Lavender"), ("EW12", "Bugis"),
    ("EW13", "City Hall"), ("EW14", "Raffles Place"), ("EW15", "Tanjong Pagar"),
    ("EW16", "Outram Park"),
])
DTL = _line("DTL", [
    ("DT14", "Bugis"), ("DT15", "Promenade"), ("DT16", "Bayfront"),
    ("DT17", "Downtown"), ("DT18", "Telok Ayer"), ("DT19", "Chinatown"),
])
NEL = _line("NEL", [
    ("NE3", "Outram Park"), ("NE4", "Chinatown"),
    ("NE5", "Clarke Quay"), ("NE6", "Dhoby Ghaut"),
])

LINES: dict[str, list[Station]] = {"EWL": EWL, "DTL": DTL, "NEL": NEL}

# Same physical station, different line codes.
INTERCHANGES: list[tuple[str, str]] = [
    ("EW12", "DT14"),   # Bugis
    ("EW16", "NE3"),    # Outram Park
    ("DT19", "NE4"),    # Chinatown
]

# Direction shown to the commuter = terminus of travel direction (public
# network knowledge; only the directions the corridor actually uses).
DIRECTION_TOWARDS: dict[tuple[str, str], str] = {
    ("EWL", "west"): "Tuas Link",
    ("EWL", "east"): "Pasir Ris",
    ("DTL", "toward_expo"): "Expo",
    ("NEL", "toward_harbourfront"): "HarbourFront",
    ("NEL", "toward_punggol"): "Punggol",
}

BY_CODE: dict[str, Station] = {s.code: s for line in LINES.values() for s in line}
BY_NAME: dict[str, list[Station]] = {}
for _s in BY_CODE.values():
    BY_NAME.setdefault(_s.name.lower(), []).append(_s)

# Verified bus alternative (replay capture).
BUS2 = json.loads((_REPLAY / "bus2_bedok_outram.json").read_text())
PLACES: dict[str, dict] = json.loads(
    (_REPLAY / "places_geocoded.json").read_text())["places"]


def station_for(name_or_code: str) -> list[Station]:
    """All stations matching a name or exact code (no silent auto-correct)."""
    key = name_or_code.strip()
    if key.upper() in BY_CODE:
        return [BY_CODE[key.upper()]]
    return BY_NAME.get(key.lower(), [])


def place_for(name: str) -> tuple[float, float] | None:
    p = PLACES.get(name)
    if p:
        return p["lat"], p["lon"]
    return None
