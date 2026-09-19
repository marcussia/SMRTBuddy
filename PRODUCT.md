# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated by the user: React + Vite + TypeScript, structured as an installable, PWA-ready mobile web application. This stack is chosen for hackathon-speed iteration, accessible component development, and graceful offline support without introducing a native-app build.

## Users

The primary user is Mdm Lim, an older, accessibility-constrained occasional traveller who journeys from Bedok to Singapore General Hospital for fortnightly appointments. She walks slowly, avoids stairs, depends on lifts and sheltered paths, and should not need to improvise a reroute while already in transit.

A secondary user is a trusted family member who wants consent-based awareness of Mdm Lim's active journey, meaningful route changes, persistent wrong-direction events, and genuine requests for help.

Two profile roles are required:

- **Traveller:** records mobility needs such as ability to use stairs or wheelchair use, preferred walking pace, language, and trusted contacts.
- **Family:** follows an explicitly shared active journey and receives agreed safety notifications.

## Product Purpose

The product is a mobile-first smart commuter companion that gives Mdm Lim a route she can confidently follow from door to door. It plans around her actual mobility and walking speed, checks for planned and unplanned disruption before departure, explains changes in simple language, and continues guiding her with slow spoken and landmark-based instructions during the journey.

Success means Mdm Lim can understand what to do next without improvising, while her family receives useful awareness without taking away her independence or privacy.

## Positioning

Unlike a generic journey planner that optimises primarily for average travel time, this product acts as a confidence and safety layer for an accessibility-constrained traveller. Its recommendation is shaped by lift and exit availability, stairs, sheltered walking, personal walking speed, route plausibility, upcoming network changes, and whether the traveller is still moving in the expected direction. It proactively rechecks the journey 24 hours and 1 hour before departure and can keep a trusted family member informed with the traveller's consent.

## Operating Context

- The hackathon deliverable is a web app designed mobile-first and judged on a real phone.
- The core demonstration is Mdm Lim's end-to-end journey from Bedok to Singapore General Hospital, including walking legs at both ends.
- The interface will be used outdoors, in bright light, with one hand, while walking or riding public transport, and sometimes with weak or no connectivity underground.
- Guidance must continue from cached journey information when live data is unavailable and must clearly identify stale information.
- The app should check a planned journey 24 hours and 1 hour before departure, then notify the traveller and opted-in family members when an actionable change occurs.
- Live guidance includes slow spoken instructions and landmark-based cues such as “Turn left after the lift.”
- If movement suggests the traveller is going in the opposite direction, the app warns the traveller first and escalates to family according to an agreed rule rather than treating one noisy location reading as an emergency.

## Capabilities and Constraints

### Required hackathon capabilities

- Plan an actual, revised, door-to-door journey with realistic timing and visible uncertainty.
- Use OpenStreetMap as the geospatial base and display “© OpenStreetMap contributors” wherever map or derived map data appears.
- Provide a phone-readable visualisation of the journey and its current state.
- Respond to planned and unplanned disruptions, crowding, weather, lift or exit outages, and other conditions relevant to the chosen route.
- Do not depend on a real disruption occurring during judging; replayed or injected test events must be labelled as simulations.

### Confirmed product capabilities

- Large, readable text and large interaction targets.
- High-contrast presentation and an in-app visibility or luminance control. Mobile web cannot reliably control the device's hardware brightness.
- English, Chinese, Malay, and Tamil localisation. One additional dialect is desired but remains undecided.
- Voice input or audio capture where it materially reduces typing.
- Slow text-to-speech journey instructions similar in purpose to spoken map guidance.
- Image- and landmark-supported instructions, while retaining enough text and speech for users who cannot interpret an image.
- A prominent SOS action with a secondary confirmation step and an audio-capture option.
- Consent-based location sharing for trusted family awareness during an active journey.
- Wrong-direction detection, traveller correction, and rule-based family notification.
- ETA calculated using the traveller's walking speed rather than a generic average.
- Tolerant origin and destination search that recognises likely misspellings, ranks similar station names, and checks whether the resulting journey is plausible before accepting a correction.
- First-run profile creation with Traveller and Family roles. Traveller profiles include relevant mobility capability such as stair use and wheelchair use.
- Automatic route checks 24 hours and 1 hour before a scheduled journey.
- Landmark-based, lift-aware, exit-aware, and step-by-step guidance.

### Safety, privacy, and feasibility constraints

- Browser page zoom must not be disabled. The team's “no zoom” request is interpreted as avoiding a route experience that requires manual map zooming; essential directions must be available without pinch-zoom gestures.
- Location sharing and audio recording are opt-in, visible while active, revocable, and limited by a stated retention policy. Family access must not silently override traveller consent.
- The SOS feature is an assistive escalation pathway, not a guaranteed replacement for Singapore emergency services.
- Images, colour, audio, and location signals must each have a non-exclusive fallback; no critical instruction may rely on only one sensory channel or one uncertain sensor reading.
- Underground connectivity is unreliable. Cache the current route, essential landmarks, next actions, emergency information, and last-known status.
- Credentials must remain outside the repository. External data use must respect licensing, attribution, and rate limits.
- Product name is undecided. “SMRTBuddy” is only the current repository name and is not yet a confirmed public brand.
- Deployment target is undecided.

## Evidence on Hand

- Hackathon challenge brief: `/Users/germaine/.codex/attachments/d6014352-955c-4c3a-9bde-9b39f05e3da4/pasted-text.txt`.
- The brief identifies LTA DataMall, data.gov.sg, OneMap, and OpenStreetMap as relevant sources and requires OpenStreetMap as the geospatial base.
- The brief specifically identifies LTA's `v2/FacilitiesMaintenance`, `TrainStationExit`, and `CoveredLinkWay` data as relevant to Mdm Lim.
- The team's confirmed feature list is recorded in this document.
- There is no implemented application, validated user research, production data, logo, public product name, or approved brand system yet. Future work must not fabricate these as evidence.

## Product Principles

1. **Recommend one safe next action.** Status is secondary to a clear instruction Mdm Lim can follow immediately.
2. **Prevent platform improvisation.** Anticipate lift, exit, route, weather, and timing problems before departure whenever possible.
3. **Protect independence with consent.** Family awareness should reassure and assist, not become invisible surveillance.
4. **Design for degraded conditions.** Core guidance remains useful with poor connectivity, imperfect GPS, noisy audio, or incomplete live feeds.
5. **Make confidence visible.** Clearly distinguish confirmed facts, estimates, stale information, auto-corrections, and simulated hackathon events.

## Core Demonstration Journey

The pitch follows one coherent eight-step journey rather than mixing planning and live navigation states:

1. Leave home.
2. Walk to Bedok MRT.
3. Enter Bedok station using the accessible entrance.
4. Board the East West Line towards Tuas Link.
5. Alight at Outram Park.
6. Take the lift towards Exit 7, using a large real landmark photograph of the yellow Exit 7 sign.
7. Follow the sheltered SGH connection or shuttle instruction.
8. Arrive at Singapore General Hospital.

Pre-trip route checks occur before these eight live journey steps. When the traveller's saved mobility preferences already rule out stairs or inaccessible exits, the app automatically updates to the safest valid route and explains the change. It does not ask the traveller to opt into safety again. The primary pre-trip action is “View updated journey” or “Got it,” with “Hear update” available as a secondary action.

## Accessibility & Inclusion

The product is designed around an older traveller with reduced walking speed and possible mobility constraints rather than treating accessibility as an optional mode. It must support large text, large touch targets, clear hierarchy, strong contrast, slow spoken guidance, plain language, multilingual content, stairs and wheelchair preferences, lift- and exit-aware routing, sheltered paths, and adequate time to understand and act.

Critical meaning must never depend on colour alone. Text alternatives must accompany images; visual instructions must accompany audio; controls must retain browser zoom and work with assistive technology. Motion should be restrained and respect reduced-motion settings. The eventual interface should be evaluated for WCAG 2.2 AA conformance, including reflow, zoom, focus visibility, contrast, target size, error prevention, and accessible authentication.
