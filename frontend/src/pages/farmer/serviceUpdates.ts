import { useFarmerDemo } from '../../demo/farmerContext'
/** Highlight only real unread activity, using the existing notification preference. */
export function useServiceUpdates() {
 const { state } = useFarmerDemo()
 return (id: string) => state.notificationsEnabled && state.notifications.some(n => {
  if (n.read) return false
  if (id === 'notifications') return true
  if (id === 'bookings') return ['confirmed','reminder','cancelled','completed'].includes(n.kind)
  if (id === 'status' || id === 'find-centre') return ['queue','delay'].includes(n.kind)
  if (id === 'grievance') return n.kind === 'grievance'
  if (id === 'group-booking') return state.bookings.some(b => b.group && b.token === n.reference)
  return false
 })
}
