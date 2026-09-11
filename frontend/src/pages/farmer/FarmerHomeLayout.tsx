import { useFarmerDemo } from '../../demo/farmerContext'
import './workflows/workflows.css'
import './farmerHome.css'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Sprout, Globe, MapPin, Bell, Menu, House, Tickets, Activity, Grid2X2, UserRound, CircleHelp } from 'lucide-react'
import { useLanguage } from '../../i18n/languageState'
import { languages, isLanguage } from '../../i18n/translations'
import { demoLoginFarmer } from '../../data/demoData'
import { useDemoAuth } from '../../auth/authState'
import { FarmerLogout } from './FarmerLogout'
const navigation = [{ to: '/farmer', key: 'home', icon: House }, { to: '/farmer/bookings', key: 'bookingsNav', icon: Tickets }, { to: '/farmer/status', key: 'liveStatus', icon: Activity }, { to: '/farmer/more', key: 'more', icon: Grid2X2 }] as const
export function FarmerHomeLayout() {
  const { t, language, setLanguage, storageUnavailable } = useLanguage()
  const auth = useDemoAuth()
  const demo = useFarmerDemo()
  const { pathname } = useLocation()
  return <div className="fh-app"><a className="skip-link" href="#main">{t('skip')}</a><header className="fh-header"><Link className="brand" to="/farmer" aria-label="ProcureFlow"><span className="brand-mark"><Sprout aria-hidden="true" /></span><span>ProcureFlow<small>{t('farmerAccess')}</small></span></Link><div className="fh-header-controls"><label className="language"><Globe size={16} aria-hidden="true" /><select id="farmer-language" aria-label={t('language')} value={language} onChange={e => { if (isLanguage(e.target.value)) setLanguage(e.target.value) }}>{languages.map(item => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label><Link className="fh-icon-button" to="/farmer/services/notifications" aria-label={t('notificationLabel')}><Bell size={21} aria-hidden="true" />{demo.state.notificationsEnabled && demo.state.notifications.some(n=>!n.read) && <span className="wf-notification-count">{demo.state.notifications.filter(n=>!n.read).length}</span>}</Link><details className="fh-profile-menu" key={pathname}><summary className="fh-icon-button" aria-label={t('profileMenu')}><Menu size={21} aria-hidden="true" /></summary><div className="fh-menu"><Link to="/farmer/services/profile"><UserRound size={18} aria-hidden="true" />{t('profileDetails')}</Link><a href="#farmer-language" onClick={e => { e.preventDefault(); e.currentTarget.closest('details')?.removeAttribute('open'); document.getElementById('farmer-language')?.focus() }}><Globe size={18} aria-hidden="true" />{t('language')}</a><Link to="/farmer/services/support"><CircleHelp size={18} aria-hidden="true" />{t('help')}</Link><FarmerLogout /></div></details></div></header><div className="fh-frame"><aside className="fh-sidebar"><div className="fh-person"><span className="fh-avatar" aria-hidden="true">RK</span><strong>{demoLoginFarmer.name}</strong><span><MapPin size={13} aria-hidden="true" />{t('location')}</span></div><nav aria-label={t('navLabel')}>{navigation.map(({ to, key, icon: Icon }) => <NavLink end key={to} to={to}><Icon size={20} aria-hidden="true" />{t(key)}</NavLink>)}</nav><p className="fh-side-note">{t('demoNotice')}</p></aside><main className="fh-content" id="main" tabIndex={-1}>{(storageUnavailable || auth.storageUnavailable) && <p role="status" className="auth-error">{t('sessionWarning')}</p>}{demo.storageError && <p role="status" className="auth-error">{t('wfStorage')}</p>}<Outlet /></main></div><nav className="fh-bottom-nav" aria-label={t('navLabel')}>{navigation.map(({ to, key, icon: Icon }) => <NavLink end key={to} to={to}><Icon size={21} aria-hidden="true" /><span>{t(key)}</span></NavLink>)}</nav></div>
}


