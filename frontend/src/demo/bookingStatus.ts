import { recommendation, type Booking, type FarmerState, type Stage } from './farmerModel'
export const bookingStages: Stage[] = ['booked', 'checkedIn', 'quality', 'weighing', 'complete']
/** Existing Farmer status estimate, shared by the status card and its compact ticker. */
export function bookingStatus(state: FarmerState, booking: Booking) {
 const centre = recommendation(state, booking.commodity).find(c => c.id === booking.centreId)!
 const index = bookingStages.indexOf(booking.stage)
 const done = ['complete', 'cancelled'].includes(booking.stage)
 const held = !!state.staff?.held.includes(booking.id)
 const ahead = done ? 0 : Math.max(0, centre.queue - index * 2)
 const wait = done ? 0 : Math.ceil(ahead * centre.service / centre.capacity) + centre.penalty
 const travel = !done && booking.stage === 'booked' ? centre.travel : 0
 const processing = done ? 0 : centre.service
 return { centre, index, done, held, ahead, wait, travel, processing, total: travel + wait + processing }
}
