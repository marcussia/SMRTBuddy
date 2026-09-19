"""LTA DataMall adapters (AccountKey from .env). Endpoint paths follow guide
v6.8 — note contradiction B6: the crowd APIs are PCDRealTime / PCDForecast,
not the PlatformCrowdDensity* names in the spec .docx.

Each function returns SourceResult; on any failure it returns status
"unavailable" with the error recorded — it never fabricates a response."""
from typing import Any

from app.adapters.base import AdapterError, fetch_json, live, unavailable
from app.config import DATAMALL_BASE, LTA_DATAMALL_KEY

# Live response shapes verified against the real API on 2026-09-19:
#   TrainServiceAlerts   value = {Status, AffectedSegments[], Message[]}
#   PCDRealTime          value = [{Station, StartTime, EndTime, CrowdLevel}]
#   PCDForecast          value = [{Date, Stations:[{Station, Interval:[{Start, CrowdLevel}]}]}]
#   v2/FacilitiesMaintenance value = [{Line, StationCode, StationName, LiftID, LiftDesc}]
#   TaxiStands           value = [{TaxiCode, Latitude, Longitude, Bfa, Ownership, Type, Name}]
#   Taxi-Availability    value = [{Latitude, Longitude}]
#   PubFloodAlerts       value = [] on a dry day; fields per guide §2.30 (CAP-style)


def _get(endpoint: str) -> Any:
    if not LTA_DATAMALL_KEY:
        raise AdapterError("LTA_DATAMALL_KEY is not set (.env)")
    return fetch_json(f"{DATAMALL_BASE}/{endpoint}",
                      headers={"AccountKey": LTA_DATAMALL_KEY})


def train_service_alerts() -> Any:
    return _get("TrainServiceAlerts")["value"]


def crowd_density_realtime(lines: list[str]) -> Any:
    """One call per line (API requirement); returns {line: [rows]}."""
    return {line: _get(f"PCDRealTime?TrainLine={line}")["value"] for line in lines}


def crowd_density_forecast(lines: list[str]) -> Any:
    return {line: _get(f"PCDForecast?TrainLine={line}")["value"] for line in lines}


def bus_arrival(bus_stop_code: str) -> Any:
    return _get(f"v3/BusArrival?BusStopCode={bus_stop_code}")


def lift_maintenance() -> Any:
    return _get("v2/FacilitiesMaintenance")["value"]


def flood_alerts() -> Any:
    return _get("PubFloodAlerts")["value"]


def traffic_incidents() -> Any:
    return _get("TrafficIncidents")["value"]


def taxi_availability() -> Any:
    return _get("Taxi-Availability")["value"]


def taxi_stands() -> Any:
    return _get("TaxiStands")["value"]


# name -> zero-arg callable returning raw data (line-parameterised ones bound
# to the demo-corridor lines by the caller)
def fetchers(lines: list[str]) -> dict[str, Any]:
    return {
        "train_service_alerts": train_service_alerts,
        "crowd_density_realtime": lambda: crowd_density_realtime(lines),
        "crowd_density_forecast": lambda: crowd_density_forecast(lines),
        "lift_maintenance": lift_maintenance,
        "flood_alerts": flood_alerts,
        "traffic_incidents": traffic_incidents,
        "taxi_availability": taxi_availability,
        "taxi_stands": taxi_stands,
    }


def fetch_source(name: str, lines: list[str]):
    fn = fetchers(lines).get(name)
    if fn is None:
        return unavailable(name, f"no such DataMall source: {name}")
    try:
        return live(name, fn())
    except (AdapterError, KeyError, TypeError) as exc:
        return unavailable(name, str(exc))
