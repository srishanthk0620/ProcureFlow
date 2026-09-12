import { useServiceUpdates } from './serviceUpdates'
import { EtaTicker } from './EtaTicker'
import { ServiceCarousel } from './ServiceCarousel'
import { EtaPanel } from './EtaPanel'
import { centreLabel } from './useFarmerLanguage'
import { useFarmerDemo } from '../../demo/farmerContext'
import { recommendation,centreById } from '../../demo/farmerModel'
import { stageKeys } from '../../demo/farmerModel'
import { Link } from 'react-router-dom'
import { ArrowRight, MapPin, Clock3, Warehouse, Ticket, CircleCheck, Activity, Leaf } from 'lucide-react'
import { Card } from '../../components/ui/Primitives'
import { useFarmerLanguage as useLanguage } from './useFarmerLanguage'
import { demoLoginFarmer } from '../../data/demoData'
import { primaryServices, informationServices, servicePath } from './farmerServices'
export function FarmerDashboard() {
  const hasUpdate = useServiceUpdates()
  const { t, language } = useLanguage()
  const { state } = useFarmerDemo()
  const centre = recommendation(state)[0]
  const booking = state.bookings.find(b=>!['cancelled','complete'].includes(b.stage))
  const date = booking ? new Intl.DateTimeFormat(language + '-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' }).format(new Date(booking.date+'T'+booking.slot+':00+05:30')) : ''
  const time = new Intl.DateTimeFormat(language + '-IN', { hour: 'numeric', minute: '2-digit', timeZone: 'Asia/Kolkata' })
  return <><div className="fh-welcome"><div><p className="eyebrow">{t('farmerHome')}</p><h1>{t('welcomeFarmer')}</h1><p className="muted">{t('homeIntro')}</p></div><div className="fh-mobile-person"><strong>{demoLoginFarmer.name}</strong><span><MapPin size={14} aria-hidden="true" />{t('location')}</span></div></div><ServiceCarousel /><div className="fh-services">{[...primaryServices, {id:'status',key:'liveStatus' as const,icon:Activity},{id:'guide',key:'vCropInfo' as const,icon:Leaf}].map(({ id, key, icon: Icon }, index) => <Link key={id} to={servicePath(id)} className={index === 0 ? 'fh-service primary' : 'fh-service'}><span className="pf-icon-wrap"><Icon size={27} strokeWidth={1.7} aria-hidden="true" />{hasUpdate(id)&&<small className="pf-new-badge">{t('vNew')}</small>}</span><span>{t(key)}</span><ArrowRight size={17} aria-hidden="true" /></Link>)}</div><EtaTicker /><div className="fh-card-grid"><Card className="fh-recommendation"><div className="fh-section-top"><h2>{t('recommended')}</h2><span className="fh-status"><CircleCheck size={14} aria-hidden="true" />{t('bestOption')}</span></div><div className="fh-centre-title"><span className="icon-tile"><Warehouse size={27} aria-hidden="true" /></span><div><h3>{centreLabel(centre.name || '')}</h3><p><MapPin size={13} aria-hidden="true" />{new Intl.NumberFormat(language).format(centre.distance)} {t('kilometres')} · {t('location')}</p></div></div><EtaPanel travel={centre.travel} wait={centre.wait+centre.penalty} processing={centre.service}/><details className="wf-details"><summary>{t('wfWhy')}</summary><p>{t('vReason')}</p><p>{t('vNearest')}: {centreLabel([...recommendation(state)].sort((a,b)=>a.distance-b.distance)[0].name)}</p></details><div className="fh-card-actions"><Link className="button secondary" to={'/farmer/services/centre-details?centre=' + centre.id}>{t('viewCentre')}<ArrowRight size={16} aria-hidden="true" /></Link><Link className="fh-text-link" to={servicePath('find-centre')}>{t('otherCentres')}</Link></div></Card>{booking ? <Card className="fh-booking"><div className="fh-section-top"><h2>{t('upcoming')}</h2><Ticket size={21} aria-hidden="true" /></div><div className="fh-token"><div><span>{t('tokenLabel')}</span><strong>{booking.token}</strong></div><span className="fh-status"><CircleCheck size={14} aria-hidden="true" />{t(stageKeys[booking.stage])}</span></div><dl className="fh-booking-details"><div><dt>{t('commodity')}</dt><dd>{t(booking.commodity==='paddy'?'paddy':'wfCopra')}</dd></div><div><dt>{t('centres')}</dt><dd>{centreLabel(centreById(booking.centreId)?.name || '')}</dd></div><div><dt><Clock3 size={14} aria-hidden="true" />{t('appointment')}</dt><dd><time dateTime={booking.date+'T'+booking.slot+':00+05:30'}>{date}<br />{time.format(new Date(booking.date+'T'+booking.slot+':00+05:30'))}</time></dd></div></dl><div className="fh-card-actions"><Link className="button secondary" to={`/farmer/status?booking=${booking.id}`}>{t('viewStatus')}<ArrowRight size={16} aria-hidden="true" /></Link><Link className="fh-text-link" to="/farmer/bookings">{t('myBookings')}</Link></div></Card> : <Card className="pf-empty-booking"><Ticket size={34} aria-hidden="true"/><h2>{t('upcoming')}</h2><p>{t('wfEmpty')}</p><Link className="button" to='/farmer/services/book-slot'>{t('bookSlot')}</Link><Link className="fh-text-link" to='/farmer/bookings?view=history'>{t('vHistory')}</Link></Card>}</div><section className="fh-info"><div className="fh-section-top"><h2>{t('quickInfo')}</h2><Link className="fh-text-link" to="/farmer/more">{t('allServices')}<ArrowRight size={15} aria-hidden="true" /></Link></div><div>{informationServices.map(({ id, key, icon: Icon }) => <Link key={id} to={servicePath(id)}><Icon size={20} aria-hidden="true" /><span>{t(key)}</span><ArrowRight size={15} aria-hidden="true" /></Link>)}</div></section></>
}



