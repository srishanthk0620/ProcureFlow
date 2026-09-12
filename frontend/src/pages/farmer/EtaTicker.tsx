import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useFarmerDemo } from '../../demo/farmerContext'
import { bookingStatus } from '../../demo/bookingStatus'
import { stageKeys } from '../../demo/farmerModel'
import { centreLabel, useFarmerLanguage } from './useFarmerLanguage'
export function EtaTicker({ bookingId }: { bookingId?: string }) {
 const { state } = useFarmerDemo()
 const { t, language } = useFarmerLanguage()
 const booking = bookingId ? state.bookings.find(b => b.id === bookingId) : state.bookings.find(b => !['complete','cancelled'].includes(b.stage))
 if (!booking || ['complete','cancelled'].includes(booking.stage)) return null
 const status = bookingStatus(state, booking)
 return <Link className="pf-eta-ticker" to={`/farmer/status?booking=${booking.id}`}><strong className="pf-live-label">{t('vLive')}</strong><span><b>{booking.token} · {t(status.held?'stHeld':stageKeys[booking.stage])}</b><span aria-live="polite">{centreLabel(status.centre.name)} · {t('vWait')}: {new Intl.NumberFormat(language).format(status.wait)} {t('minutes')}</span></span><ArrowRight size={17} aria-hidden="true"/></Link>
}
