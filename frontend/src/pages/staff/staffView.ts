import { useFarmerDemo } from '../../demo/farmerContext'
import { recommendation,stageKeys,type Booking } from '../../demo/farmerModel'
import { emptyStaffState,resourceSnapshot } from '../../demo/staffResources'
export const modules=[['','stDashboard'],['operations','stLive'],['queue','stQueue'],['bookings','myBookings'],['farmers','stFarmers'],['groups','groupBooking'],['disruptions','stDisruptions'],['messages','stMessages'],['reports','stReports'],['help','help']] as const
export const resourceKeys={gate:'stGate',quality:'stQuality',weighing:'stWeigh',staff:'stStaff',other:'stOther'} as const
export function useOperations(){const demo=useFarmerDemo();const staff=demo.state.staff||emptyStaffState();const bookings=demo.state.bookings.filter(b=>b.centreId===staff.centreId);const estimate=recommendation(demo.state,'paddy').find(c=>c.id===staff.centreId)!;return {...demo,staff,bookings,estimate,resources:resourceSnapshot(staff,staff.centreId)}}
export function bookingStatus(b:Booking,held:string[]){return held.includes(b.id)&&!['complete','cancelled'].includes(b.stage)?'stHeld':stageKeys[b.stage]}
