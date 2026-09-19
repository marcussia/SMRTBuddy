"""The decision engine (PRD §7): an explicit, ordered rules list — first match
wins for `action`. Each rule is a named function whose docstring states its
trigger and rationale, taking a Context and returning a Decision or None.

The engine DECIDES; the commuter confirms. One recommended action, one plain
sentence of reason, a deadline where one exists. Alternatives ride along for
transparency (Advice.alternatives), never to push the choice back onto her."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.config import (ASSUMED_DISRUPTION_DELAY_MIN, CROWD_HIGH_BAND,
                        ETA_UNCERTAINTY_DISRUPTED_MIN,
                        ETA_UNCERTAINTY_NORMAL_MIN, LEAVE_EARLIER_STEP_MIN,
                        RAIN_ROAD_BUFFER_MIN, REROUTE_BENEFIT_THRESHOLD_MIN)
from app.engine import facts as F
from app.i18n import resolve
from app.models import Advice, Journey, Leg, SourceResult, UserProfile
from app.routing import stations as net
from app.routing.planner import RouteOption, plan_options

# Physical-station grouping: an interchange is ONE place with several codes.
_PHYSICAL: dict[str, set[str]] = {}
for _a, _b in net.INTERCHANGES:
    group = {_a, _b}
    _PHYSICAL[_a] = group
    _PHYSICAL[_b] = group


def physical(codes: set[str]) -> set[str]:
    """Expand codes to every code of the same physical station."""
    out: set[str] = set()
    for c in codes:
        out |= _PHYSICAL.get(c, {c})
    return out


@dataclass
class Context:
    journey: Journey
    profile: UserProfile
    facts: F.Facts
    results: dict[str, SourceResult]
    now: datetime
    current_station_code: str | None = None   # where she is, if in transit


@dataclass
class Decision:
    action: str
    reason: str                      # plain English, always
    triggered_by: list[str]
    chosen: RouteOption | None = None      # None = keep current plan
    keep_legs: list[Leg] | None = None
    alternatives: list[RouteOption] = field(default_factory=list)
    decide_by: datetime | None = None
    notify_family: bool = False
    headline_params: dict = field(default_factory=dict)
    extra_uncertainty_min: float = 0.0
    affected_codes: set[str] = field(default_factory=set)


# --- shared helpers ------------------------------------------------------------

def _route_codes(ctx: Context) -> set[str]:
    return physical(set(F.stations_of(ctx.journey.legs)))


def _mobility_ok(opt: RouteOption, ctx: Context) -> bool:
    """Reroute constraints (§7.2): every walk leg within max_walk_metres, and
    step-free when the profile requires it."""
    mob = ctx.profile.mobility
    if mob is None:
        return True
    needs_step_free = mob.wheelchair or not mob.can_use_stairs
    for leg in opt.legs:
        # Only a known-bad leg blocks the route; "unverified" walks are allowed
        # (rejecting them would leave no walking at all) but carry their status
        # into the response so the UI shows the caveat.
        if needs_step_free and leg.step_free == "not_step_free":
            return False
    walk_per_leg = [
        sum(F._haversine_m(a, b) for a, b in zip(L.geometry, L.geometry[1:]))
        for L in opt.legs if L.mode == "walk"]
    return all(w <= mob.max_walk_metres for w in walk_per_leg)


def _replan_literal(ctx: Context, avoid: set[str],
                    in_transit: bool) -> list[RouteOption]:
    """Replan avoiding exactly these codes (no physical expansion)."""
    try:
        return plan_options(
            ctx.journey.origin, ctx.journey.destination, ctx.now,
            ctx.profile.mobility, ctx.profile.locale, avoid=avoid,
            start_station_code=ctx.current_station_code if in_transit else None)
    except ValueError:
        return []


def _replan(ctx: Context, avoid: set[str],
            in_transit: bool) -> list[RouteOption]:
    try:
        opts = plan_options(
            ctx.journey.origin, ctx.journey.destination, ctx.now,
            ctx.profile.mobility, ctx.profile.locale,
            avoid=physical(avoid),
            start_station_code=ctx.current_station_code if in_transit else None)
    except ValueError:
        return []
    return opts


def _split_taxi(opts: list[RouteOption]
                ) -> tuple[list[RouteOption], RouteOption | None]:
    """§7.6: taxi is the LAST resort — never chosen while public transport
    exists, but kept as a priced alternative."""
    pt = [o for o in opts if o.kind != "taxi"]
    taxi = next((o for o in opts if o.kind == "taxi"), None)
    return pt, taxi


def _in_transit(ctx: Context) -> bool:
    return ctx.journey.location_state in ("walking", "on_bus", "on_train",
                                          "on_platform")


# --- the ordered rules (PRD §7.1) ----------------------------------------------

def rule_1_safety_stop(ctx: Context) -> Decision | None:
    """Trigger: widespread flooding (3+ active alerts), or a flood alert whose
    circle covers the origin or destination. Rationale: no journey plan beats
    not being caught in a flash flood; some disruptions mean 'don't travel
    today' and the app must be willing to say so."""
    origin = net.place_for(ctx.journey.origin) or _first_coord(ctx.journey.legs)
    dest = net.place_for(ctx.journey.destination) or _last_coord(ctx.journey.legs)
    hit = None
    where = None
    if len(ctx.facts.floods) >= 3:
        hit, where = ctx.facts.floods[0], "across the island"
    elif dest and F.flood_near(ctx.facts, dest):
        hit, where = F.flood_near(ctx.facts, dest), "at your destination"
    elif origin and F.flood_near(ctx.facts, origin):
        hit, where = F.flood_near(ctx.facts, origin), "where you are"
    if hit is None:
        return None
    return Decision(
        action="cancel_trip",
        reason=f"PUB flood alert ({hit.severity}) {where}: {hit.description} "
               f"Travelling into a flood zone is not safe; your family has "
               f"been notified.",
        triggered_by=["flood_alerts"],
        notify_family=True,
        headline_params={"reason_short": resolve("short.flood",
                                                 ctx.profile.locale)})


def rule_2_hard_mobility_block(ctx: Context) -> Decision | None:
    """Trigger: a lift is out of service at a station on the route AND the
    profile cannot use stairs (or uses a wheelchair). Rationale: for this
    commuter a dead lift is a wall, not an inconvenience — reroute around the
    station; if nothing step-free remains within her walking limit, taxi."""
    mob = ctx.profile.mobility
    if mob is None or (mob.can_use_stairs and not mob.wheelchair):
        return None
    blocked = physical(set(ctx.facts.lift_out)) & _route_codes(ctx)
    if not blocked:
        return None
    names = sorted({net.BY_CODE[c].name for c in blocked if c in net.BY_CODE})
    opts = _replan(ctx, avoid=blocked, in_transit=_in_transit(ctx))
    pt, taxi = _split_taxi(opts)
    viable = [o for o in pt if o.kind == "rail" and _mobility_ok(o, ctx)] \
        or [o for o in pt if _mobility_ok(o, ctx)]
    lift_desc = "; ".join(f"{net.BY_CODE.get(c) and net.BY_CODE[c].name}: "
                          f"{ctx.facts.lift_out.get(c, '')}"
                          for c in sorted(set(ctx.facts.lift_out) & blocked))
    if viable:
        return Decision(
            action="reroute", chosen=viable[0],
            alternatives=[o for o in opts if o is not viable[0]][:2],
            reason=f"The lift at {', '.join(names)} is out of service "
                   f"({lift_desc}). This route avoids that station and stays "
                   f"step-free.",
            triggered_by=["lift_maintenance"], notify_family=True,
            affected_codes=blocked,
            headline_params={"summary": _summary_of(viable[0], ctx)})
    if taxi is None:
        return None
    return Decision(
        action="take_taxi", chosen=taxi,
        reason=f"The lift at {', '.join(names)} is out of service "
               f"({lift_desc}) and no step-free route within your walking "
               f"range remains. A taxi is the reliable option; show the "
               f"driver the card.",
        triggered_by=["lift_maintenance"], notify_family=True,
        affected_codes=blocked,
        headline_params={"stand": taxi.legs[0].from_name})


def rule_3_route_broken(ctx: Context) -> Decision | None:
    """Trigger: TrainServiceAlerts names closed stations that the current
    plan passes through. Rationale: the leg is impossible — replan around it
    now, from where she actually is, and say why."""
    broken = physical(ctx.facts.broken_stations) & _route_codes(ctx)
    if not broken:
        return None
    # Avoid the LITERAL closed codes: the alert names one line's platforms —
    # an interchange's other line keeps running (e.g. NE3 when EW13–16 close).
    opts = _replan_literal(ctx, avoid=set(ctx.facts.broken_stations),
                           in_transit=_in_transit(ctx))
    plan_lines = {leg.service for leg in ctx.journey.legs if leg.mode == "mrt"}
    broken_on_line = {c for c in ctx.facts.broken_stations
                      if c in net.BY_CODE and net.BY_CODE[c].line in plan_lines}
    broken = broken | broken_on_line
    pt, taxi = _split_taxi(opts)
    viable = [o for o in pt if _mobility_ok(o, ctx)]
    mitigation = ""
    if ctx.facts.free_shuttle_stations & broken:
        mitigation = (" LTA is running free MRT shuttles at the affected "
                      "stations (in the alert feed), but the sheltered rail "
                      "route below avoids the closure entirely.")
    advisory = f" Operator notice: {ctx.facts.advisories[0]}" \
        if ctx.facts.advisories else ""
    if viable:
        return Decision(
            action="reroute", chosen=viable[0],
            alternatives=([o for o in pt if o is not viable[0]] +
                          ([taxi] if taxi else []))[:2],
            reason=f"Train service is suspended at "
                   f"{_names(broken)} on your usual route."
                   f"{advisory}{mitigation}",
            triggered_by=["train_service_alerts"], notify_family=True,
            affected_codes=broken_on_line or broken,
            headline_params={"summary": _summary_of(viable[0], ctx)})
    if taxi is None:
        return None
    return Decision(
        action="take_taxi", chosen=taxi,
        reason=f"Train service is suspended at {_names(broken)} and no "
               f"public-transport alternative fits your mobility profile."
               f"{advisory}",
        triggered_by=["train_service_alerts"], notify_family=True,
        affected_codes=broken,
        headline_params={"stand": taxi.legs[0].from_name})


def rule_4_wait_vs_reroute(ctx: Context) -> Decision | None:
    """Trigger: a line the plan uses reports major delay (Status 2) but her
    stations are still open. Rationale (§7.2): switching costs HER more than
    it costs a fast commuter — reroute only when it wins by
    REROUTE_BENEFIT_THRESHOLD_MIN minutes after walking at her speed."""
    if ctx.facts.tsa_status != 2:
        return None
    plan_lines = {leg.service for leg in ctx.journey.legs if leg.mode == "mrt"}
    hit_lines = ctx.facts.affected_lines & plan_lines
    if not hit_lines:
        return None
    planned_arrival = ctx.journey.legs[-1].arrive if ctx.journey.legs else ctx.now
    t_wait = planned_arrival + timedelta(minutes=ASSUMED_DISRUPTION_DELAY_MIN)
    avoid = {s.code for ln in hit_lines for s in net.LINES.get(ln, [])}
    opts = _replan(ctx, avoid=avoid, in_transit=_in_transit(ctx))
    pt, _taxi = _split_taxi(opts)
    viable = [o for o in pt if _mobility_ok(o, ctx)]
    t_switch = (ctx.now + timedelta(minutes=viable[0].total_min)) if viable else None
    saving_min = ((t_wait - t_switch).total_seconds() / 60) if t_switch else 0.0
    if t_switch is None or saving_min < REROUTE_BENEFIT_THRESHOLD_MIN:
        return Decision(
            action="wait",
            reason=(f"{'/'.join(sorted(hit_lines))} reports major delays, but "
                    f"switching would "
                    + (f"only save about {saving_min:.0f} min"
                       if t_switch else "leave no viable route")
                    + f" once your walking pace and transfers are counted "
                      f"(assumed delay {ASSUMED_DISRUPTION_DELAY_MIN:.0f} min). "
                      f"Staying put is the better option."),
            triggered_by=["train_service_alerts"],
            decide_by=ctx.now + timedelta(minutes=10),
            extra_uncertainty_min=ASSUMED_DISRUPTION_DELAY_MIN,
            alternatives=viable[:2])
    return Decision(
        action="reroute", chosen=viable[0],
        alternatives=[o for o in viable[1:]][:2],
        reason=f"{'/'.join(sorted(hit_lines))} reports major delays (assumed "
               f"{ASSUMED_DISRUPTION_DELAY_MIN:.0f} min). Switching now "
               f"arrives about {saving_min:.0f} min earlier, walking at your "
               f"pace, within your limits.",
        triggered_by=["train_service_alerts"], notify_family=True,
        decide_by=ctx.now + timedelta(minutes=10),
        headline_params={"summary": _summary_of(viable[0], ctx)})


def rule_5_platform_crowding(ctx: Context) -> Decision | None:
    """Trigger: crowd level 'h' now (or forecast 'h' before departure) at the
    boarding station. Rationale: proactive comfort/safety — leave earlier, or
    use another line, rather than stand in a crush."""
    first_mrt = next((L for L in ctx.journey.legs if L.mode == "mrt"), None)
    if first_mrt is None:
        return None
    board_codes = {s.code for s in net.station_for(first_mrt.from_name)}
    departed = _in_transit(ctx)
    if not departed:
        fc_hit = {c for c in board_codes
                  if ctx.facts.crowd_forecast.get(c) == CROWD_HIGH_BAND}
        rt_hit = {c for c in board_codes
                  if ctx.facts.crowd.get(c) == CROWD_HIGH_BAND}
        hit = fc_hit or rt_hit
        if hit:
            src = "crowd_density_forecast" if fc_hit else "crowd_density_realtime"
            kind = "is forecast to be" if fc_hit else "is"
            return Decision(
                action="leave_earlier",
                reason=f"{first_mrt.from_name} station {kind} at the highest "
                       f"crowd level ('h' band) around your departure. "
                       f"Leaving {LEAVE_EARLIER_STEP_MIN:.0f} min earlier "
                       f"avoids the crush at almost no cost to you.",
                triggered_by=[src],
                headline_params={"minutes": f"{LEAVE_EARLIER_STEP_MIN:.0f}"})
        return None
    # In transit: recommend an alternative line only if one exists.
    rt_hit = {c for c in physical(_next_boardings(ctx))
              if ctx.facts.crowd.get(c) == CROWD_HIGH_BAND}
    if not rt_hit:
        return None
    opts = _replan(ctx, avoid=rt_hit, in_transit=True)
    viable = [o for o in _split_taxi(opts)[0] if _mobility_ok(o, ctx)]
    if not viable:
        return None
    return Decision(
        action="reroute", chosen=viable[0],
        reason=f"{_names(rt_hit)} is at the highest crowd level right now. "
               f"This alternative avoids the crush.",
        triggered_by=["crowd_density_realtime"],
        affected_codes=rt_hit,
        headline_params={"summary": _summary_of(viable[0], ctx)})


def rule_6_bus_crowding(ctx: Context) -> Decision | None:
    """Trigger: plan has a bus leg, she has not departed, the next bus reports
    LSD (limited standing) and there is slack. Rationale: with time in hand,
    waiting one bus beats standing in a packed one."""
    bus_leg = next((L for L in ctx.journey.legs if L.mode == "bus"), None)
    if bus_leg is None or _in_transit(ctx):
        return None
    ba = ctx.results.get("bus_arrival")
    if ba is None or ba.status == "unavailable" or not isinstance(ba.data, dict):
        return None   # no load signal -> no advice from this rule
    slack_min = (ctx.journey.arrive_by - ctx.journey.legs[-1].arrive
                 ).total_seconds() / 60
    for svc in ba.data.get("Services", []):
        if svc.get("ServiceNo") != bus_leg.service:
            continue
        nxt, nxt2 = svc.get("NextBus", {}), svc.get("NextBus2", {})
        if nxt.get("Load") == "LSD" and slack_min > 15 \
                and nxt2.get("Load") in ("SEA", "SDA"):
            return Decision(
                action="wait",
                reason=f"The next bus {bus_leg.service} is packed (limited "
                       f"standing), the one behind it has seats, and you have "
                       f"{slack_min:.0f} min in hand. Wait for the second bus.",
                triggered_by=["bus_arrival"],
                decide_by=_parse_eta(nxt2.get("EstimatedArrival")) or
                          ctx.now + timedelta(minutes=10))
    return None


def rule_7_weather(ctx: Context) -> Decision | None:
    """Trigger: rain forecast on the route. Rationale: rain turns exposed
    legs into a problem for a slow-walking commuter — prefer MRT over bus,
    treat shelter as required, and buffer any road/exposed leg."""
    codes = F.stations_of(ctx.journey.legs) or ["EW5", "EW16"]
    if not F.raining_at(ctx.facts, codes) and not (
            ctx.facts.rain_areas and any(L.mode in ("bus", "walk")
                                         for L in ctx.journey.legs)):
        return None
    has_bus = any(L.mode == "bus" for L in ctx.journey.legs)
    if has_bus:
        opts = _replan(ctx, avoid=set(), in_transit=_in_transit(ctx))
        rail = [o for o in _split_taxi(opts)[0]
                if o.kind == "rail" and _mobility_ok(o, ctx)]
        if rail:
            return Decision(
                action="reroute", chosen=rail[0],
                alternatives=[o for o in opts if o is not rail[0]][:2],
                notify_family=True,
                reason="Heavy rain is forecast on your route. The bus leg is "
                       "exposed at the stops; the MRT keeps you under shelter "
                       f"the whole way. Road legs would also need a "
                       f"{RAIN_ROAD_BUFFER_MIN:.0f}-min buffer in this rain.",
                triggered_by=["weather"],
                extra_uncertainty_min=RAIN_ROAD_BUFFER_MIN,
                headline_params={"summary": _summary_of(rail[0], ctx)})
    if ctx.facts.rain_areas and not has_bus:
        # Already on rail: no mode change, but the walk needs a buffer —
        # fold it into timing advice rather than interrupting her (7.3).
        return None
    return None


def rule_8_road_conditions(ctx: Context) -> Decision | None:
    """Trigger: live road incidents near a bus leg of the plan. Rationale: a
    blocked road delays the bus unpredictably — leave earlier or go by rail."""
    bus_leg = next((L for L in ctx.journey.legs if L.mode == "bus"), None)
    ti = ctx.results.get("traffic_incidents")
    if bus_leg is None or ti is None or ti.status == "unavailable" \
            or not isinstance(ti.data, list):
        return None
    near = [row for row in ti.data
            if _near_leg(bus_leg, row.get("Latitude"), row.get("Longitude"))]
    if not near:
        return None
    opts = _replan(ctx, avoid=set(), in_transit=_in_transit(ctx))
    rail = [o for o in _split_taxi(opts)[0]
            if o.kind == "rail" and _mobility_ok(o, ctx)]
    what = near[0].get("Message", near[0].get("Type", "incident"))
    if rail:
        return Decision(
            action="reroute", chosen=rail[0],
            reason=f"Road incident on the bus route: {what}. Rail avoids it.",
            triggered_by=["traffic_incidents"], notify_family=True,
            headline_params={"summary": _summary_of(rail[0], ctx)})
    return Decision(
        action="leave_earlier",
        reason=f"Road incident on the bus route: {what}. No rail alternative "
               f"here — leave {LEAVE_EARLIER_STEP_MIN:.0f} min earlier.",
        triggered_by=["traffic_incidents"],
        headline_params={"minutes": f"{LEAVE_EARLIER_STEP_MIN:.0f}"})


def rule_9_default(ctx: Context) -> Decision:
    """Trigger: nothing above fired. Rationale: interrupt-only-when-it-matters
    — the strongest advice on a normal day is quiet confidence."""
    checked = [n for n, r in ctx.results.items() if r.status != "unavailable"]
    return Decision(
        action="proceed",
        reason="No disruption, flood, lift outage, heavy rain or unusual "
               "crowding on your route right now "
               f"(checked: {', '.join(sorted(checked))}).",
        triggered_by=sorted(checked) or ["none"])


RULES = [rule_1_safety_stop, rule_2_hard_mobility_block, rule_3_route_broken,
         rule_4_wait_vs_reroute, rule_5_platform_crowding, rule_6_bus_crowding,
         rule_7_weather, rule_8_road_conditions]


def decide(ctx: Context) -> Decision:
    for rule in RULES:
        decision = rule(ctx)
        if decision is not None:
            return decision
    return rule_9_default(ctx)


# --- small helpers --------------------------------------------------------------

def _names(codes: set[str]) -> str:
    return ", ".join(sorted({net.BY_CODE[c].name for c in codes
                             if c in net.BY_CODE})) or ", ".join(sorted(codes))


def _first_coord(legs: list[Leg]) -> tuple[float, float] | None:
    for leg in legs:
        if leg.geometry:
            return leg.geometry[0]
    return None


def _last_coord(legs: list[Leg]) -> tuple[float, float] | None:
    for leg in reversed(legs):
        if leg.geometry:
            return leg.geometry[-1]
    return None


def _next_boardings(ctx: Context) -> set[str]:
    """Stations where she still has to board/transfer on the current plan."""
    out = set()
    for leg in ctx.journey.legs:
        if leg.mode == "mrt" and leg.arrive > ctx.now:
            out |= {s.code for s in net.station_for(leg.from_name)}
    return out


def _summary_of(opt: RouteOption, ctx: Context) -> str:
    first_mrt = next((L for L in opt.legs if L.mode == "mrt"), None)
    if first_mrt is None:
        leg = opt.legs[0]
        return resolve("summary.head_to", ctx.profile.locale, to=leg.to_name)
    from app.routing.planner import LINE_NAMES
    code = first_mrt.service or ""
    names = LINE_NAMES.get(code, {})
    line = names.get(ctx.profile.locale, names.get("en", code))
    return resolve("summary.take_line", ctx.profile.locale,
                   line=line, to=first_mrt.to_name)


def _parse_eta(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _near_leg(leg: Leg, lat, lon, within_m: float = 500) -> bool:
    if lat is None or lon is None:
        return False
    return any(F._haversine_m((lat, lon), p) <= within_m for p in leg.geometry)


# --- Advice assembly (incl. §7.5 location context) ------------------------------

_UNCERTAIN = {"proceed": ETA_UNCERTAINTY_NORMAL_MIN,
              "leave_earlier": ETA_UNCERTAINTY_NORMAL_MIN}


def assemble(ctx: Context, decision: Decision,
             data_status: dict[str, str]) -> Advice:
    locale = ctx.profile.locale
    legs = (decision.chosen.legs if decision.chosen
            else (decision.keep_legs or ctx.journey.legs))
    arrive = legs[-1].arrive if legs else ctx.now
    width = decision.extra_uncertainty_min + _UNCERTAIN.get(
        decision.action, ETA_UNCERTAINTY_DISRUPTED_MIN)
    state = ctx.journey.location_state

    # §7.5: the same action means something different in each location state.
    headline_key = f"advice.{decision.action}.headline"
    params = dict(decision.headline_params)
    decide_by = decision.decide_by
    if decision.action == "reroute" and decision.chosen:
        if state == "on_train" and decision.chosen.legs:
            first = decision.chosen.legs[0]
            alight = first.to_name if first.mode == "mrt" else first.from_name
            nxt = decision.chosen.legs[1].instruction \
                if len(decision.chosen.legs) > 1 else first.instruction
            nxt = nxt[:1].lower() + nxt[1:] if nxt else nxt
            headline_key = "advice.alight.headline"
            params = {"station": alight, "next_step": nxt}
            decide_by = decide_by or (first.arrive if first.mode == "mrt"
                                      else None)
        elif state == "on_platform":
            params.setdefault("summary", _summary_of(decision.chosen, ctx))
            decision.reason = ("Stay on the platform — do not board. "
                               + decision.reason)
        elif state == "walking":
            first = decision.chosen.legs[0]
            params.setdefault("summary", resolve(
                "summary.head_to", locale, to=first.to_name))

    headline = resolve(headline_key, locale, **params)

    # walking-route provenance rides along honestly
    ds = dict(data_status)
    if decision.chosen:
        srcs = decision.chosen.walk_sources
        if "straightline_estimate" in srcs:
            ds["walk_routing"] = "estimate (OSM router unreachable)"
        elif srcs:
            ds["walk_routing"] = "live"

    # Confidence reflects only the sources this DECISION rests on
    # (triggered_by) plus the walking-route provenance of the chosen option.
    # An unused source being down is honestly visible in data_status but does
    # not shake a decision that never consulted it.
    relevant = set(decision.triggered_by)
    unavailable_relevant = [n for n in relevant
                            if ds.get(n, "").startswith("unavailable")]
    confidence = ("low" if unavailable_relevant or
                  (decision.chosen and
                   "straightline_estimate" in decision.chosen.walk_sources)
                  else "high" if decision.action == "proceed" else "medium")

    # crowding painted onto legs (visualisation: readable in one second)
    level = {"l": "low", "m": "medium", "h": "high"}
    lift_out_names = {net.BY_CODE[c].name for c in physical(set(ctx.facts.lift_out))
                      if c in net.BY_CODE}
    for leg in legs:
        if leg.mode == "mrt":
            codes = [s.code for s in net.station_for(leg.from_name)]
            worst = max((ctx.facts.crowd.get(c, "l") for c in codes),
                        key=lambda v: "lmh".index(v), default="l")
            leg.crowding = level[worst]
        # A known lift outage is the one step-free fact we HAVE: any leg
        # touching that station is positively not step-free right now.
        if leg.mode in ("mrt", "walk") and                 ({leg.from_name, leg.to_name} & lift_out_names):
            leg.step_free = "not_step_free"

    affected = None
    if decision.affected_codes:
        pts = [(net.BY_CODE[c].lat, net.BY_CODE[c].lon)
               for c in sorted(decision.affected_codes)
               if c in net.BY_CODE and net.BY_CODE[c].lat is not None]
        affected = pts if len(pts) >= 2 else None

    return Advice(
        action=decision.action,
        headline=headline,
        speech_text=headline,
        reason=decision.reason,
        triggered_by=decision.triggered_by,
        decide_by=decide_by,
        eta_range=(arrive, arrive + timedelta(minutes=width)),
        confidence=confidence,
        notify_family=decision.notify_family,
        data_status=ds,
        legs=legs,
        affected_segment=affected,
        alternatives=[o.legs for o in decision.alternatives][:2],
        driver_card=(decision.chosen.driver_card
                     if decision.chosen and decision.action == "take_taxi"
                     else None),
    )
