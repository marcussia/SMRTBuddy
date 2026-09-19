"""Named constants and environment. Every tunable the PRD or the resolved
open-questions list names lives here, once."""
import os
from datetime import timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"
REPLAY_DIR = REPO_ROOT / "data" / "replay"

SGT = timezone(timedelta(hours=8), "SGT")

# --- Secrets (never committed; .env at repo root) ----------------------------

def _load_dotenv() -> None:
    env = REPO_ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_load_dotenv()
LTA_DATAMALL_KEY = os.environ.get("LTA_DATAMALL_KEY", "")

# --- External endpoints -------------------------------------------------------

DATAMALL_BASE = "https://datamall2.mytransport.sg/ltaodataservice"
WEATHER_BASE = "https://api-open.data.gov.sg/v2/real-time/api"
# OSRM public demo (Q1: walking legs; 30-min budget, else straight-line x1.3)
OSRM_BASE = "https://router.project-osrm.org"

HTTP_TIMEOUT_S = 10

# --- Decision constants (resolved open questions) -----------------------------

# Q3: minutes of saving that justify an unfamiliar reroute.
REROUTE_BENEFIT_THRESHOLD_MIN = 10

# Q4: wrong-direction detection.
WRONG_DIRECTION_PINGS = 3            # consecutive divergent pings
WRONG_DIRECTION_WINDOW_S = 90        # spanning at least this long
GPS_ACCURACY_MAX_M = 50              # suppress when accuracy is worse
STATIONARY_SPEED_MPS = 0.2           # suppress when near-stationary

# Q5: crowd bands are DataMall's own: l / m / h / NA (LTA guide v6.8).
CROWD_HIGH_BAND = "h"                # the band that triggers crowding rules

# --- Timing assumptions (recorded in STATUS.md; no timetable data in repo) ----

MRT_HOP_MIN = 2.0                    # minutes between adjacent stations
TRANSFER_MIN = 6.0                   # line-change penalty at an interchange
                                     # (generous for a slow-walking commuter)
BOARDING_WAIT_MIN = 4.0              # average wait for the next train
ASSUMED_DISRUPTION_DELAY_MIN = 20.0  # delay assumed when a line reports major
                                     # delay (Status 2) but is still passable —
                                     # the feed carries no delay-minutes field
ETA_UNCERTAINTY_NORMAL_MIN = 5.0     # eta_range width on a normal day
ETA_UNCERTAINTY_DISRUPTED_MIN = 15.0 # eta_range width during disruption
TAXI_SPEED_KMH = 30.0                # city average for taxi leg estimate
WALK_DETOUR_FACTOR = 1.3             # straight-line -> street distance, used
                                     # only when OSRM is unreachable (labelled)

RAIN_ROAD_BUFFER_MIN = 8.0           # §7.1 rule 7: buffer added to road legs
LEAVE_EARLIER_STEP_MIN = 20.0        # §7.1 rule 5: how much earlier to leave
