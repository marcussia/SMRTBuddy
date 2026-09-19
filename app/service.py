"""Glue: journey -> conditions -> facts -> ordered rules -> Advice.

This is the one place the whole pipeline is wired together, so the answer to
"where does a recommendation come from?" is always: gather (truthful statuses)
-> build_facts (typed, source-tagged) -> decide (first matching named rule)
-> assemble (localised, location-aware). Family notifications are logged here
(§7.3) when the decision says so."""
from datetime import datetime, timedelta

from app import conditions, store
from app.config import SGT
from app.engine import facts as F
from app.engine import rules
from app.models import Advice, Journey, UserProfile
from app.routing import stations as net
from app.routing.walk import _haversine_m


def _current_station(journey: Journey) -> str | None:
    """Where she is, for in-transit replanning: nearest corridor station to
    the latest ping. Without a ping we fall back to the plan's first station —
    we do not guess a position (assumption recorded in STATUS.md)."""
    ping = store.latest_ping(journey.journey_id)
    if ping is not None:
        stations = [s for s in net.BY_CODE.values() if s.lat is not None]
        nearest = min(stations,
                      key=lambda s: _haversine_m((ping.lat, ping.lon),
                                                 (s.lat, s.lon)))
        if _haversine_m((ping.lat, ping.lon), (nearest.lat, nearest.lon)) < 2000:
            return nearest.code
    for leg in journey.legs:
        if leg.mode == "mrt":
            match = net.station_for(leg.from_name)
            if match:
                return match[0].code
    return None


def check_wrong_direction(journey: Journey) -> tuple[bool, bool]:
    """Q4: wrong-direction = the last WRONG_DIRECTION_PINGS consecutive pings
    all move AWAY from the next expected waypoint, spanning >= 90 s, each with
    good GPS accuracy, while actually moving. Underground GPS is noise — poor
    accuracy or near-stationary readings suppress detection, never trigger it.
    Returns (wrong_direction, family_notified)."""
    from app.config import (GPS_ACCURACY_MAX_M, STATIONARY_SPEED_MPS,
                            WRONG_DIRECTION_PINGS, WRONG_DIRECTION_WINDOW_S)
    recent = (store.pings.get(journey.journey_id) or [])[-WRONG_DIRECTION_PINGS:]
    if len(recent) < WRONG_DIRECTION_PINGS:
        return False, False
    if any(p.accuracy_m is None or p.accuracy_m > GPS_ACCURACY_MAX_M
           for p in recent):
        return False, False
    span_s = (recent[-1].recorded_at - recent[0].recorded_at).total_seconds()
    if span_s < WRONG_DIRECTION_WINDOW_S or span_s <= 0:
        return False, False
    moved_m = _haversine_m((recent[0].lat, recent[0].lon),
                           (recent[-1].lat, recent[-1].lon))
    if moved_m / span_s < STATIONARY_SPEED_MPS:
        return False, False
    target = _next_waypoint(journey)
    if target is None:
        return False, False
    dists = [_haversine_m((p.lat, p.lon), target) for p in recent]
    if not all(b > a for a, b in zip(dists, dists[1:])):
        return False, False
    # notify family, but not more than once per 10 minutes per journey
    already = [n for n in store.notifications
               if n.journey_id == journey.journey_id
               and n.event == "wrong_direction"]
    now = datetime.now(SGT)
    if already and (now - already[-1].created_at).total_seconds() < 600:
        return True, False
    recipients = store.notify_family(
        journey.user_id, "wrong_direction",
        f"Heading away from the route to {journey.destination} "
        f"(moved {dists[-1] - dists[0]:.0f} m further over {span_s:.0f} s).",
        journey.journey_id)
    return True, bool(recipients)


def _next_waypoint(journey: Journey) -> tuple[float, float] | None:
    """The point she should currently be moving towards: the end of the leg
    in progress, else the start of the next future leg."""
    now = datetime.now(SGT)
    for leg in journey.legs:
        if not leg.geometry:
            continue
        if leg.depart <= now <= leg.arrive:
            return leg.geometry[-1]
        if leg.depart > now:
            return leg.geometry[0]
    return journey.legs[-1].geometry[-1] if journey.legs and \
        journey.legs[-1].geometry else None


def compute_advice(journey: Journey, profile: UserProfile) -> Advice:
    bus_leg = next((L for L in journey.legs if L.mode == "bus"), None)
    bus_stop = None
    if bus_leg is not None:
        bus_stop = net.BUS2["board"]["code"] \
            if bus_leg.from_name == net.BUS2["board"]["name"] else None
    results = conditions.gather(journey.scenario, bus_stop_code=bus_stop)

    boarding = journey.legs[0].depart if journey.legs else None
    facts = F.build_facts(results, boarding_time=boarding)

    # The clock: real time for live journeys. A scenario journey is a
    # labelled simulation, so its clock is simulated too — the latest ping's
    # recorded_at (the demo's "now"), else shortly before departure. Without
    # this, a replan at 15:00 real time would timestamp a morning demo's
    # advice in the afternoon.
    now = datetime.now(SGT)
    if journey.scenario:
        ping = store.latest_ping(journey.journey_id)
        if ping is not None:
            now = ping.recorded_at
        elif journey.legs:
            now = journey.legs[0].depart - timedelta(minutes=45)

    ctx = rules.Context(
        journey=journey, profile=profile, facts=facts, results=results,
        now=now,
        current_station_code=_current_station(journey))
    decision = rules.decide(ctx)
    advice = rules.assemble(ctx, decision, conditions.data_status(results))

    if advice.notify_family:
        recipients = store.notify_family(
            profile.user_id, decision.action,
            f"{advice.headline} — {advice.reason}", journey.journey_id)
        if not recipients:
            # honest: flag stays true (the EVENT warrants notifying), but the
            # log records nobody was linked to receive it.
            pass
    return advice
