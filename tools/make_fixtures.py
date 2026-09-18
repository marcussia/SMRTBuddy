"""Generates data/fixtures/<scenario>.json — one file per PRD §9 scenario.

ALL OF THIS IS INJECTED TEST DATA (PRD §2.6 allows it "provided it is labelled
as such"). Every file carries `_fixture: true` and a banner comment; the API
serves it with data_status = "fixture", never "live". Shapes mirror the real
endpoints, verified live on 2026-09-19 (see app/adapters/datamall.py header).

Run:  .venv/bin/python tools/make_fixtures.py
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "fixtures"

BANNER = ("FIXTURE — injected test data for the demo, labelled per PS2 brief "
          "§2.6. Not real transport data. Shapes mirror the live APIs.")

# Corridor forecast areas (data.gov.sg two-hr forecast area names).
AREAS = ["Bedok", "Geylang", "Kallang", "City", "Bukit Merah", "Queenstown"]


def weather(condition: str) -> dict:
    return {"items": [{
        "update_timestamp": "2026-09-19T08:00:00+08:00",
        "timestamp": "2026-09-19T08:00:00+08:00",
        "valid_period": {"start": "2026-09-19T08:00:00+08:00",
                         "end": "2026-09-19T10:00:00+08:00",
                         "text": "8.00 am to 10.00 am"},
        "forecasts": [{"area": a, "forecast": condition} for a in AREAS],
    }]}


def crowd_rt(level_by_station: dict[str, str], default: str = "l") -> dict:
    """PCDRealTime shape per line: {line: [{Station, ..., CrowdLevel}]}."""
    lines = {"EWL": [f"EW{i}" for i in range(1, 34)],
             "DTL": [f"DT{i}" for i in range(1, 36)],
             "NEL": [f"NE{i}" for i in range(1, 18)]}
    return {line: [{"Station": s,
                    "StartTime": "2026-09-19T08:00:00+08:00",
                    "EndTime": "2026-09-19T08:10:00+08:00",
                    "CrowdLevel": level_by_station.get(s, default)}
                   for s in stations]
            for line, stations in lines.items()}


def crowd_fc(station_levels: dict[str, str]) -> dict:
    """PCDForecast shape: 30-min intervals, 06:00–23:30."""
    def intervals(level: str) -> list[dict]:
        out = []
        for h in range(6, 24):
            for m in (0, 30):
                out.append({"Start": f"2026-09-19T{h:02d}:{m:02d}:00+08:00",
                            "CrowdLevel": level})
        return out
    return {"EWL": [{"Date": "2026-09-19T00:00:00+08:00",
                     "Stations": [{"Station": s, "Interval": intervals(lv)}
                                  for s, lv in station_levels.items()]}],
            "DTL": [], "NEL": []}


TSA_NORMAL = {"Status": 1, "AffectedSegments": [], "Message": []}

# Scenario 3: EWL down between Bugis (EW12) and Outram Park (EW16).
TSA_DISRUPTED = {
    "Status": 2,
    "AffectedSegments": [{
        "Line": "EWL",
        "Direction": "Both",
        "Stations": "EW12,EW13,EW14,EW15,EW16",
        "FreePublicBus": "EW12,EW13,EW14,EW15,EW16",
        "FreeMRTShuttle": "EW12,EW13,EW14,EW15,EW16",
        "MRTShuttleDirection": "Both",
    }],
    "Message": [{
        "Content": "[FIXTURE] EWL: No train service between Bugis and Outram "
                   "Park due to a signalling fault. Free bus rides and shuttle "
                   "services are available at designated stops.",
        "CreatedDate": "2026-09-19 08:05:00"}],
}

SCENARIOS: dict[str, dict] = {
    # 1. Clear day -> proceed, no family notification
    "clear_day": {
        "train_service_alerts": TSA_NORMAL,
        "weather": weather("Partly Cloudy (Day)"),
        "crowd_density_realtime": crowd_rt({}),
        "lift_maintenance": [],
        "flood_alerts": [],
    },
    # 2. Rain -> road/exposed legs deprioritised, shelter required, buffer added
    "rain": {
        "train_service_alerts": TSA_NORMAL,
        "weather": weather("Heavy Thundery Showers"),
        "crowd_density_realtime": crowd_rt({}),
        "lift_maintenance": [],
        "flood_alerts": [],
    },
    # 3. THE DEMO: disruption mid-journey, she is on_train
    "disruption_on_train": {
        "train_service_alerts": TSA_DISRUPTED,
        "weather": weather("Partly Cloudy (Day)"),
        "crowd_density_realtime": crowd_rt(
            {"EW8": "h", "EW9": "h", "EW10": "h", "EW11": "h", "EW12": "h"}),
        "lift_maintenance": [],
        "flood_alerts": [],
    },
    # 4. Lift out at the destination interchange, wheelchair profile
    "lift_outage": {
        "train_service_alerts": TSA_NORMAL,
        "weather": weather("Partly Cloudy (Day)"),
        "crowd_density_realtime": crowd_rt({}),
        "lift_maintenance": [{
            "Line": "EWL", "StationCode": "EW16",
            "StationName": "Outram Park", "LiftID": "FIXTURE-L1",
            "LiftDesc": "EXIT A STREET LEVEL - CONCOURSE - PLATFORM"}],
        "flood_alerts": [],
    },
    # 5. Flash flood at the destination -> cancel_trip
    "flood_destination": {
        "train_service_alerts": TSA_NORMAL,
        "weather": weather("Heavy Thundery Showers"),
        "crowd_density_realtime": crowd_rt({}),
        "lift_maintenance": [],
        "flood_alerts": [{
            "alertId": "FIXTURE-FLOOD-1",
            "dateTime": "2026-09-19T08:10:00+08:00",
            "msgType": "Alert", "event": "Flood", "responseType": "Avoid",
            "urgency": "Immediate", "severity": "Severe",
            "expires": "2026-09-20T08:10:00+08:00", "senderName": "PUB",
            "headline": "[FIXTURE] Flash Flood Alert",
            "description": "Flash flood at Outram Rd near Singapore General "
                           "Hospital. Please avoid the area.",
            "instruction": "Please avoid this area.",
            "areaDesc": "Outram Rd",
            "circle": {"latitude": 1.2802, "longitude": 103.8394,
                       "radius_km": 1.0},
            "status": "Actual"}],
    },
    # 6. Crowding forecast at the origin station -> leave_earlier
    "crowding_forecast": {
        "train_service_alerts": TSA_NORMAL,
        "weather": weather("Partly Cloudy (Day)"),
        "crowd_density_realtime": crowd_rt({}),
        "crowd_density_forecast": crowd_fc({"EW5": "h"}),
        "lift_maintenance": [],
        "flood_alerts": [],
    },
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, sources in SCENARIOS.items():
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(
            {"_fixture": True, "_comment": BANNER, "scenario": name,
             "sources": sources}, indent=1) + "\n")
        print(f"wrote {path.relative_to(OUT.parent.parent)}"
              f" ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
