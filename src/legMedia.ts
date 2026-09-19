import type { Leg } from './api'
import bedokPlatform from './assets/images/step-4-bedok-platform.jpg'
import outramLift from './assets/images/step-5-outram-lift.jpg'
import exitSeven from './assets/images/outram-exit-7.jpg'
import sghEntrance from './assets/images/step-8-sgh-entrance.jpg'
import guideLift from './assets/images/guide-step-1-lift.png'
import guideEscalator from './assets/images/guide-step-2-escalator.png'
import guideExitD from './assets/images/guide-step-3-exit-d.png'
import guideTaxiStand from './assets/images/guide-step-4-taxi-stand.png'

export type GuideStep = {
  title: string
  instruction: string
  speechText: string
  image: string
  alt: string
  arrowDirection: 'forward' | 'north' | 'upper-right' | 'upper-left' | 'right'
}

// Pitch guidance follows the four physical decisions in the supplied walkthrough.
// The Next button advances this sequence for the demo; production can advance it
// from location changes without changing the content model.
export const GUIDE_STEPS: GuideStep[] = [
  { title: 'Lift', instruction: 'The lift is on your right. Take the lift to level 2.', speechText: 'The lift is on your right. Take the lift to level 2.', image: guideLift, alt: 'Priority-use lift sign and lift lobby', arrowDirection: 'upper-right' },
  { title: 'Exit D', instruction: 'Turn left after the lift. Follow the signs to Exit D. Take the escalator.', speechText: 'Turn left after the lift. Follow the signs to Exit D. Take the escalator.', image: guideEscalator, alt: 'Station direction sign beside the escalator and Exit D', arrowDirection: 'upper-left' },
  { title: 'Taxi stand', instruction: 'Exit D is on your right. Follow the signs to the taxi stand.', speechText: 'Exit D is on your right. Follow the signs to the taxi stand.', image: guideExitD, alt: 'Bugis station Exit D sign', arrowDirection: 'upper-right' },
  { title: 'Arrived', instruction: 'You have arrived at the taxi stand.', speechText: 'You have arrived at the taxi stand.', image: guideTaxiStand, alt: 'Sheltered taxi stand beside the station entrance', arrowDirection: 'north' },
]

// Stage 2 transit guidance follows the confirmed planned-closure sequence.
// It is intentionally text-first: no landmark image is substituted for an MRT
// platform or interchange that has not been supplied and verified.
export const TRANSIT_GUIDE_STEPS: GuideStep[] = [
  { title: 'Ride to Bugis', instruction: 'Ride the East–West line to Bugis.', speechText: 'Ride the East–West line to Bugis.', image: '', alt: '', arrowDirection: 'forward' },
  { title: 'Get off at Bugis', instruction: 'Get off at Bugis.', speechText: 'Get off at Bugis.', image: '', alt: '', arrowDirection: 'forward' },
  { title: 'Take the Downtown line', instruction: 'Take the Downtown line toward Expo.', speechText: 'Take the Downtown line toward Expo.', image: '', alt: '', arrowDirection: 'forward' },
  { title: 'Get off at Chinatown', instruction: 'Get off at Chinatown.', speechText: 'Get off at Chinatown.', image: '', alt: '', arrowDirection: 'forward' },
]

// Landmark photos are ILLUSTRATIVE ONLY and are shown only when they match a
// real leg of the advice (the backend has no photo data; exit guidance comes
// from exit_hint, which is real OSM data). Legs
// with no matching landmark get no photo — never a wrong one.
export function legPhoto(leg: Leg): { image: string; alt: string } | null {
  if (leg.mode === 'mrt' && leg.from_name === 'Bedok')
    return { image: bedokPlatform, alt: 'Platform at Bedok MRT station' }
  if (leg.mode === 'mrt' && leg.to_name === 'Outram Park')
    return { image: outramLift, alt: 'Lift and wheelchair access area at Outram Park MRT station' }
  if (leg.mode === 'walk' && leg.from_name === 'Outram Park')
    return { image: exitSeven, alt: 'Yellow Exit 7 sign at Outram Park MRT station' }
  if (leg.mode === 'walk' && leg.to_name === 'Singapore General Hospital')
    return { image: sghEntrance, alt: 'Entrance to Singapore General Hospital' }
  return null
}
