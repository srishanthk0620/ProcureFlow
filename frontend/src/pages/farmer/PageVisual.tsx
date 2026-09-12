import type { TranslationKey } from '../../i18n/translations'
import harvest from '../../assets/farmer-harvest.jpg'
import community from '../../assets/farmer-circle.jpg'
import { useFarmerLanguage } from './useFarmerLanguage'
/** A compact photographic heading, shared by each secondary Farmer page. */
export function PageVisual({ title }: { title: TranslationKey }) {
 const { t } = useFarmerLanguage()
 const group = ['groupBooking','services','support','chat','grievance','schemes'].includes(title)
 return <div className={`pf-page-visual ${group?'pf-page-community':''}`}><div><p>ProcureFlow</p><h1>{t(title)}</h1></div><img src={group?community:harvest} alt="" width="1200" height="800"/></div>
}
