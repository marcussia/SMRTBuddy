"""Adapter plumbing. Every fetch returns a SourceResult whose `status` is
truthful (PRD §4): "live" only for data that actually came from the network
just now, "fixture" only for labelled test data, "unavailable" when a source
could not be reached. Nothing in here invents data."""
import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from app.config import HTTP_TIMEOUT_S, SGT
from app.models import SourceResult


class AdapterError(Exception):
    pass


def fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    # data.gov.sg returns 403 to the default Python-urllib User-Agent; identify
    # this app honestly instead.
    req = urllib.request.Request(url, headers={"accept": "application/json",
                                               "User-Agent": "smrtbuddy/0.1 (NEBULA X PS2 entry)",
                                               **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise AdapterError(f"{url}: {exc}") from exc


def _now() -> datetime:
    return datetime.now(SGT)


def live(name: str, data: Any) -> SourceResult:
    return SourceResult(name=name, status="live", fetched_at=_now(), data=data)


def fixture(name: str, data: Any) -> SourceResult:
    return SourceResult(name=name, status="fixture", fetched_at=_now(), data=data)


def unavailable(name: str, note: str) -> SourceResult:
    # The error note travels in `data` so a judge can see WHY it is unavailable.
    return SourceResult(name=name, status="unavailable", fetched_at=_now(),
                        data={"error": note})
