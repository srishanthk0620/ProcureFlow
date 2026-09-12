import { useEffect, useState } from 'react'
import { useFarmerLanguage } from './useFarmerLanguage'
function RefreshStamp() {
 const {t,language}=useFarmerLanguage()
 const [now,setNow]=useState(()=>new Date())
 useEffect(()=>{const timer=window.setInterval(()=>setNow(new Date()),30000);return()=>window.clearInterval(timer)},[])
 return <span>{t('vUpdated')} · <time dateTime={now.toISOString()}>{new Intl.DateTimeFormat(language,{hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(now)}</time></span>
}
export function EtaPanel({travel,wait,processing}:{travel:number;wait:number;processing:number}) {
 const {t,language}=useFarmerLanguage()
 const total=travel+wait+processing
 return <div className="pf-eta"><dl aria-live="polite" aria-atomic="true">{[{label:'vTravel',value:travel},{label:'vWait',value:wait},{label:'vProcess',value:processing},{label:'vCompletion',value:total}].map(({label,value})=><div key={label}><dt>{t(label as 'vTravel')}</dt><dd>{new Intl.NumberFormat(language).format(value)} <small>{t('minutes')}</small></dd></div>)}</dl><p className="pf-eta-fresh"><span aria-hidden="true" className="pf-live-dot"/><RefreshStamp key={`${travel}-${wait}-${processing}`}/></p><p className="pf-eta-note">{t('vEstimate')}</p></div>
}
