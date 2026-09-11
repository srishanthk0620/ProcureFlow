import { Link,NavLink,Outlet,useLocation } from 'react-router-dom'
import { useLanguage } from '../../i18n/languageState'
import { languages,isLanguage } from '../../i18n/translations'
import { workflowCentres } from '../../data/workflowData'
import { modules,useOperations } from './staffView'
import { StaffLogout } from './StaffAuth'
import './staff.css'
export function StaffLayout(){const {t,language,setLanguage,storageUnavailable}=useLanguage();const {staff,update,storageError}=useOperations();const {pathname}=useLocation();const nav=<nav aria-label={t('staff')}>{modules.map(([path,key])=><NavLink end to={'/staff'+(path?'/'+path:'')} key={path}>{t(key)}</NavLink>)}</nav>
 return <div className="st-app"><a className="skip-link" href="#main">{t('skip')}</a><header className="st-header"><Link className="brand" to="/staff">ProcureFlow <small>{t('staff')}</small></Link><label className="wf-field">{t('centres')}<select value={staff.centreId} onChange={e=>update(s=>({...s,staff:{...(s.staff||staff),centreId:e.target.value}}))}>{workflowCentres.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label className="wf-field">{t('language')}<select value={language} onChange={e=>{if(isLanguage(e.target.value))setLanguage(e.target.value)}}>{languages.map(l=><option key={l.code} value={l.code}>{l.label}</option>)}</select></label><Link to="/staff/messages">{t('notificationLabel')}</Link><Link to="/staff/help">{t('help')}</Link><Link to="/staff/profile">Anitha S.</Link></header><div className="st-frame"><aside className="st-sidebar"><p><strong>Anitha S.</strong></p><p>{t('stInspector')}</p><p>Kollam Procurement Centre</p>{nav}<StaffLogout/></aside><div className="st-body"><details className="st-mobile-nav" key={pathname}><summary>{t('staff')} · {t('more')}</summary>{nav}<StaffLogout/></details><main id="main" tabIndex={-1}>{(storageError||storageUnavailable)&&<p role="status" className="st-alert">{t('wfStorage')}</p>}<p className="st-demo">{t('wfDemo')}</p><Outlet/></main></div></div></div>
}

