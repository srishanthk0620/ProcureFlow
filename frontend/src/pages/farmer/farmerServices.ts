import { CalendarPlus, Tickets, MapPin, Users, IndianRupee, Landmark, BookOpen, CircleHelp, Newspaper, MessageSquareWarning, MessagesSquare, Settings, UserRound, Bell, Warehouse, Activity } from 'lucide-react'
import type { HomeKey } from '../../i18n/homeTranslations'
import type { LucideIcon } from 'lucide-react'
export interface FarmerService { id: string; key: HomeKey; icon: LucideIcon }
export const primaryServices: FarmerService[] = [
  { id: 'book-slot', key: 'bookSlot', icon: CalendarPlus },
  { id: 'bookings', key: 'myBookings', icon: Tickets },
  { id: 'find-centre', key: 'findCentre', icon: MapPin },
  { id: 'group-booking', key: 'groupBooking', icon: Users },
]
export const informationServices: FarmerService[] = [
  { id: 'prices', key: 'prices', icon: IndianRupee },
  { id: 'schemes', key: 'schemes', icon: Landmark },
  { id: 'guide', key: 'guide', icon: BookOpen },
  { id: 'support', key: 'support', icon: CircleHelp },
]
export const moreServices: FarmerService[] = [primaryServices[3], primaryServices[2], informationServices[0], { id: 'market', key: 'market', icon: Newspaper }, ...informationServices.slice(1), { id: 'grievance', key: 'grievance', icon: MessageSquareWarning }, { id: 'chat', key: 'chat', icon: MessagesSquare }, { id: 'settings', key: 'settings', icon: Settings }]
export const farmerServices: FarmerService[] = [...primaryServices, ...moreServices.filter(item => !primaryServices.some(primary => primary.id === item.id)), { id: 'profile', key: 'profileDetails', icon: UserRound }, { id: 'notifications', key: 'notificationLabel', icon: Bell }, { id: 'centre-details', key: 'viewCentre', icon: Warehouse }, { id: 'status', key: 'liveStatus', icon: Activity }]
export function servicePath(id: string) {
  if (id === 'bookings' || id === 'status') return `/farmer/${id}`
  return `/farmer/services/${id}`
}
