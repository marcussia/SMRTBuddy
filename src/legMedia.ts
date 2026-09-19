import type { Leg } from './api'
import bedokPlatform from './assets/images/step-4-bedok-platform.jpg'
import outramLift from './assets/images/step-5-outram-lift.jpg'
import exitSeven from './assets/images/outram-exit-7.jpg'
import sghEntrance from './assets/images/step-8-sgh-entrance.jpg'

// Landmark photos are ILLUSTRATIVE ONLY and are shown only when they match a
// real leg of the advice (the backend has no exit-level or photo data). Legs
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
