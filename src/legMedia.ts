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
}

// Pitch guidance follows the four physical decisions in the supplied walkthrough.
// The Next button advances this sequence for the demo; production can advance it
// from location changes without changing the content model.
export const GUIDE_STEPS: GuideStep[] = [
  { title: 'Find the lift', instruction: 'Turn left and walk towards the lift. Take the lift to level 2.', speechText: 'Turn left and walk towards the lift. Take the lift to level 2.', image: guideLift, alt: 'Priority-use lift sign and lift lobby' },
  { title: 'Leave the lift', instruction: 'After exiting the lift, turn left. Follow the signs towards Exit D and take the escalator.', speechText: 'After exiting the lift, turn left. Follow the signs towards Exit D and take the escalator.', image: guideEscalator, alt: 'Station direction sign beside the escalator and Exit D' },
  { title: 'Follow Exit D', instruction: 'Exit D is on your right. Follow the signs to the taxi stand.', speechText: 'Exit D is on your right. Follow the signs to the taxi stand.', image: guideExitD, alt: 'Bugis station Exit D sign' },
  { title: 'Reach the taxi stand', instruction: 'You have arrived at the taxi stand.', speechText: 'You have arrived at the taxi stand.', image: guideTaxiStand, alt: 'Sheltered taxi stand beside the station entrance' },
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
