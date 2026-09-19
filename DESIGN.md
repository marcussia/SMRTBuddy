---
name: Commuter Companion
description: Calm, landmark-led wayfinding for an older Singapore commuter.
colors:
  direction-navy: "#0d2136"
  warm-paper: "#f5f1e8"
  clear-white: "#fffdfa"
  supporting-slate: "#52606d"
  divider-stone: "#cbc6ba"
  transit-yellow: "#ffd400"
  confirmation-green: "#0f6f55"
  emergency-red: "#b63831"
typography:
  display:
    fontFamily: "Atkinson Next, Avenir Next, sans-serif"
    fontSize: "43px"
    fontWeight: 750
    lineHeight: 1.04
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Atkinson Next, Avenir Next, sans-serif"
    fontSize: "38px"
    fontWeight: 750
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Atkinson Next, Avenir Next, sans-serif"
    fontSize: "20px"
    fontWeight: 450
    lineHeight: 1.4
  label:
    fontFamily: "Atkinson Next, Avenir Next, sans-serif"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.2
rounded:
  control: "12px"
  surface: "14px"
  sheet: "22px"
  circle: "50%"
spacing:
  xs: "8px"
  sm: "12px"
  md: "18px"
  lg: "28px"
  xl: "36px"
components:
  button-primary:
    backgroundColor: "{colors.direction-navy}"
    textColor: "{colors.clear-white}"
    rounded: "{rounded.control}"
    padding: "14px 20px"
    height: "64px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.direction-navy}"
    rounded: "{rounded.control}"
    padding: "14px 20px"
    height: "64px"
  field:
    backgroundColor: "{colors.clear-white}"
    textColor: "{colors.direction-navy}"
    rounded: "{rounded.control}"
    padding: "0 12px 0 18px"
    height: "72px"
---

# Design System: Commuter Companion

<!-- APPROVAL STATUS: Only the Step 6 landmark-guidance screen and its navy/cream/yellow/green visual direction are approved. Other screens and component applications remain proposals until the user explicitly approves them. The earlier React screens are rejected and must not be used as visual reference. -->

## Overview

**Creative North Star: "Landmark Editorial"**

Only the Step 6 landmark-guidance composition is currently locked. Apply its principles to proposed screens, but do not treat any other screen structure as approved until the static HTML/CSS review is complete.

The interface combines the authority of Singapore transit wayfinding with the warmth and pace needed by an older traveller. A real landmark image leads whenever recognition is more useful than a map; the interface beneath it behaves like a carefully typeset instruction sheet. The result is calm, direct and recognisable rather than decorative or futuristic.

Every screen should answer one question first: “What should Mdm Lim do next?” Status, route mechanics and secondary choices support that instruction instead of competing with it. The product uses strong typography, large controls and visible confirmation while avoiding the card-heavy appearance of generic generated interfaces.

**Key Characteristics:**

- Real landmark photography paired with one dominant instruction.
- Warm cream surfaces and deep navy structure, with yellow used as a wayfinding signal.
- Large humanist type and large touch targets intended for use outdoors and in motion.
- Flat, restrained composition with selective depth only when it communicates layering.
- Language-specific reflow instead of shrinking every translation into the English layout.

## Colors

The palette is drawn from physical transit signs: dark structural navy, warm paper, signal yellow and confirmation green.

### Primary

- **Direction Navy** (`#0d2136`): Primary text, navigation structure and dominant actions.
- **Transit Yellow** (`#ffd400`): Current steps, wayfinding landmarks and rare high-salience markers.

### Secondary

- **Confirmation Green** (`#0f6f55`): Reassurance and verified positive status.
- **Emergency Red** (`#b63831`): Reserved for SOS and immediate danger actions.

### Neutral

- **Warm Paper** (`#f5f1e8`): Default app surface.
- **Clear White** (`#fffdfa`): Raised fields and route surfaces.
- **Supporting Slate** (`#52606d`): Secondary explanatory text.
- **Divider Stone** (`#cbc6ba`): Rules and quiet boundaries.

**The Signal Rarity Rule.** Yellow marks the current route instruction or an important transit object; it does not become general decoration.

**The Emergency Reserve Rule.** Red appears only when the user is entering an actual help or emergency flow.

## Typography

**Display Font:** Atkinson Hyperlegible Next, with Avenir Next and sans-serif fallbacks  
**Body Font:** Atkinson Hyperlegible Next, with Avenir Next and sans-serif fallbacks  
**Chinese Font:** Noto Sans SC  
**Tamil Font:** Noto Sans Tamil

**Character:** Friendly, highly differentiated letterforms with enough weight to remain readable in bright light. Type is confident but not promotional.

### Hierarchy

- **Display** (750, 43px, 1.04): The single live instruction.
- **Headline** (750, 38px, 1.04): Page titles and important state changes.
- **Title** (700–760, 19–26px): Route and component titles.
- **Body** (450, 20–23px, 1.35–1.4): Directions and explanations.
- **Label** (700, 17px): Step, status and field labels.

**The Translation Reflow Rule.** Preserve meaning and touch-target size first. Tamil and other longer scripts may increase the sheet height and use a smaller—but still accessible—type tier rather than clipping or truncating critical text.

## Layout

The primary target is a 430 × 932 mobile viewport. Screens use 28px content margins, 18–28px vertical group spacing and 64px minimum dominant actions. Live guidance places a real photograph in the upper field and overlaps it with a warm instruction sheet rising from the bottom. Other operational screens use one continuous warm surface and avoid nested card grids.

On desktop, the phone remains the canonical interface and is accompanied by a navy prototype navigator for the team. Below 800px the navigator disappears and the app fills the browser viewport.

## Elevation & Depth

The system is flat by default. Tonal contrast and rules create most separation. A single diffuse shadow is used only for a clearly raised journey surface or emergency control; borders and shadows are not combined on the same ordinary container.

**The Flat-by-Default Rule.** If hierarchy can be communicated with spacing, type or tone, do not add a shadow.

## Shapes

Controls use 12px corners and content surfaces use 14px corners. The landmark instruction sheet uses one 22px leading corner to feel like a physical page entering over the photograph. Circles are reserved for step markers, icon controls, user identity and SOS—not text chips.

## Components

### Buttons

- **Shape:** Rectangular with 12px corners and a 64px minimum height.
- **Primary:** Direction Navy with white text; one dominant action per screen.
- **Secondary:** Transparent warm surface with a 1.5px navy border.
- **Focus:** A visible 4px translucent Transit Yellow outline.

### Cards / Containers

- **Corner Style:** 14px for rare raised route surfaces.
- **Background:** Clear White on Warm Paper.
- **Shadow Strategy:** Diffuse and low-contrast; only when the surface is meaningfully raised.
- **Internal Padding:** Usually 20–22px.

### Inputs / Fields

- **Style:** Clear White, 1.5px navy stroke, 12px radius and 72px minimum height.
- **Voice action:** A separate circular target inside the field, always labelled for assistive technology.
- **Focus:** The global yellow focus outline; never remove browser focus without replacing it.

### Navigation

Mobile task screens use a centred title and circular back action. The live journey deliberately removes generic bottom navigation so the next instruction and safety actions remain dominant.

### Landmark Guidance Sheet

The photograph occupies the upper field. The warm sheet contains step progress, one headline, supporting instruction, distance, reassurance and two large actions. The progress indicator carries text and geometry so its meaning never depends on colour alone.

## Do's and Don'ts

### Do:

- **Do** use real, route-validated landmark photography for live instructions.
- **Do** keep one primary instruction and one dominant action on each operational screen.
- **Do** label simulated disruption data explicitly.
- **Do** display unknown times, contacts and route details as unresolved rather than inventing values.
- **Do** keep browser zoom enabled and make the interface readable without manual map zooming.

### Don't:

- **Don't** return to the rejected pink and purple palette.
- **Don't** use gradients, glassmorphism, decorative blobs or a dashboard grid.
- **Don't** ask the traveller to opt into an accessible route after her saved mobility needs have already determined it.
- **Don't** shrink translated text until it becomes inaccessible; reflow the composition.
- **Don't** present simulated outages, location readings or notifications as live facts.
