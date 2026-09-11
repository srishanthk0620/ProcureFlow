/** Entirely fictional Kerala fixtures. Not live bookings, capacity, or operational records. */
export interface DemoFarmer { id: string; name: string; village: string; district: string }
export interface DemoCentre { id: string; name: string; district: string; commodityIds: string[] }
export interface DemoCommodity { id: string; name: string; unit: 'kg' }
export interface DemoBooking { id: string; farmerId: string; centreId: string; commodityId: string; quantityKg: number; status: 'draft'; requestedDate: string }
export interface DemoQueueEntry { id: string; bookingId: string; centreId: string; status: 'preview'; token: string }
export interface DemoResource { id: string; centreId: string; name: string; stage: 'quality' | 'weighing' | 'unloading'; status: 'not_connected' }
export interface DemoDisruption { id: string; centreId: string; resourceId: string; type: 'equipment_outage'; status: 'scenario_only'; description: string }
export interface DemoNotification { id: string; farmerId: string; bookingId: string; channel: 'in_app'; status: 'preview'; message: string }
export const procurementStages = ['Booking', 'Arrival', 'Quality', 'Weighing', 'Procurement', 'Payment'] as const
export const farmers: DemoFarmer[] = [
  { id: 'demo-farmer-1', name: 'Anitha K.', village: 'Kuzhalmannam', district: 'Palakkad' },
  { id: 'demo-farmer-2', name: 'Suresh P.', village: 'Nedumudi', district: 'Alappuzha' },
]
export const commodities: DemoCommodity[] = [{ id: 'paddy', name: 'Paddy', unit: 'kg' }, { id: 'copra', name: 'Copra', unit: 'kg' }]
export const procurementCentres: DemoCentre[] = [
  { id: 'demo-centre-1', name: 'Kuzhalmannam Demo Centre', district: 'Palakkad', commodityIds: ['paddy', 'copra'] },
  { id: 'demo-centre-2', name: 'Nedumudi Demo Centre', district: 'Alappuzha', commodityIds: ['paddy'] },
]
export const bookings: DemoBooking[] = [{ id: 'demo-booking-1', farmerId: 'demo-farmer-1', centreId: 'demo-centre-1', commodityId: 'paddy', quantityKg: 750, status: 'draft', requestedDate: '2026-10-15' }]
export const queueEntries: DemoQueueEntry[] = [{ id: 'demo-queue-1', bookingId: 'demo-booking-1', centreId: 'demo-centre-1', status: 'preview', token: 'DEMO-001' }]
export const centreResources: DemoResource[] = [
  { id: 'demo-quality-1', centreId: 'demo-centre-1', name: 'Quality station A', stage: 'quality', status: 'not_connected' },
  { id: 'demo-scale-1', centreId: 'demo-centre-1', name: 'Weighbridge A', stage: 'weighing', status: 'not_connected' },
  { id: 'demo-bay-1', centreId: 'demo-centre-1', name: 'Unloading bay A', stage: 'unloading', status: 'not_connected' },
]
export const disruptions: DemoDisruption[] = [{ id: 'demo-disruption-1', centreId: 'demo-centre-1', resourceId: 'demo-scale-1', type: 'equipment_outage', status: 'scenario_only', description: 'Practice scenario: weighbridge unavailable for maintenance.' }]
export const notifications: DemoNotification[] = [{ id: 'demo-notification-1', farmerId: 'demo-farmer-1', bookingId: 'demo-booking-1', channel: 'in_app', status: 'preview', message: 'Demo request draft prepared. No appointment has been confirmed.' }]

export const demoLoginFarmer: DemoFarmer = { id: 'demo-ravi', name: 'Ravi Kumar', village: 'Kollam', district: 'Kollam' }

/** Home-only sample scenario. These figures are illustrative, not calculated or live. */
export const farmerHomeDemo = {
  centre: { id: 'demo-kollam', nameKey: 'centreKollam', distanceKm: 8.4, travelMinutes: 18, waitMinutes: 30, recommendationKey: 'bestOption' },
  booking: { id: 'demo-ravi-booking', farmerId: demoLoginFarmer.id, centreId: 'demo-kollam', token: 'F001', commodityKey: 'paddy', startsAt: '2026-10-15T09:30:00+05:30', endsAt: '2026-10-15T10:00:00+05:30', statusKey: 'onSchedule', sample: true },
} as const
