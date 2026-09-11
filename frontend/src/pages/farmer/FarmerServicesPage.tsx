import { Link, useParams } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useLanguage } from '../../i18n/languageState'
import { farmerServices, moreServices, servicePath } from './farmerServices'
import { FarmerLogout } from './FarmerLogout'
import { CentreDiscovery } from './workflows/Centres'
import { BookingForm } from './workflows/BookingForm'
import { BookingsPage,LiveStatus,NotificationsPage } from './workflows/BookingViews'
import { ChatPage,GrievanceForm,InformationPage,SettingsPage } from './workflows/Secondary'
export function FarmerMore() {
  const { t } = useLanguage()
  return <><p className="eyebrow">{t('farmerHome')}</p><h1>{t('services')}</h1><div className="fh-service-list">{moreServices.map(({ id, key, icon: Icon }) => <Link key={id} to={servicePath(id)}><Icon size={22} aria-hidden="true" /><span>{t(key)}</span><ArrowRight size={17} aria-hidden="true" /></Link>)}<FarmerLogout /></div></>
}
export function FarmerServicePage({ serviceId }: { serviceId?: string }) {
  const params = useParams()
  const { t } = useLanguage()
  const service = farmerServices.find(item => item.id === (serviceId ?? params.serviceId))
  if (!service) return <section className="fh-placeholder"><h1>404</h1><Link className="button" to="/farmer">{t('home')}</Link></section>
  const id=service.id
  if(id==='book-slot'||id==='group-booking')return <BookingForm key={id} group={id==='group-booking'}/>
  if(id==='find-centre'||id==='centre-details')return <CentreDiscovery detail={id==='centre-details'}/>
  if(id==='bookings')return <BookingsPage/>
  if(id==='status')return <LiveStatus/>
  if(id==='notifications')return <NotificationsPage/>
  if(id==='grievance')return <GrievanceForm/>
  if(id==='chat')return <ChatPage/>
  if(id==='settings'||id==='profile')return <SettingsPage profile={id==='profile'}/>
  return <InformationPage kind={id}/>
}
