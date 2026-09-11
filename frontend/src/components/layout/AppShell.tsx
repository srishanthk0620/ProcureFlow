import { useLanguage } from '../../i18n/languageState'
import { languages, isLanguage, type TranslationKey } from '../../i18n/translations'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, CircleHelp, Globe, LayoutDashboard, Leaf, Sprout, Ticket, Users, Route } from 'lucide-react'
import { Badge, Button } from '../ui/Primitives'

export function Header({ role }: { role?: string }) {
  const { language, setLanguage, t, storageUnavailable } = useLanguage()
  const roleKey = role === 'Farmer' ? 'farmer' : role === 'Centre Staff' ? 'staff' : 'admin'
  const [helpOpen, setHelpOpen] = useState(false)
  return <><a className="skip-link" href="#main">{t('skip')}</a><header className="topbar"><Link className="brand" to="/" aria-label="ProcureFlow home"><span className="brand-mark"><Sprout aria-hidden="true" /></span><span>ProcureFlow<small>{role ? t(roleKey) : 'Smart Procurement. Less Waiting.'}</small></span></Link><div className="header-actions">{role && <Badge>{t('demo')}</Badge>}<label className="language"><Globe size={16} aria-hidden="true" /><select aria-label={t('language')} value={language} onChange={event => { if (isLanguage(event.target.value)) setLanguage(event.target.value) }}>{languages.map(item => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>{role ? <Link className="home-link" to="/" aria-label={t('backHome')}><ArrowLeft size={17} aria-hidden="true" /><span>{t('home')}</span></Link> : <Button className="secondary" aria-expanded={helpOpen} aria-controls="help-panel" onClick={() => setHelpOpen(!helpOpen)}><CircleHelp size={17} aria-hidden="true" /> {t('help')}</Button>}</div></header>{storageUnavailable && <p className="help-panel" role="status">{t('storageWarning')}</p>}{helpOpen && <aside id="help-panel" className="help-panel"><strong>Explore the prototype</strong><p>Choose Farmer, Centre Staff or Administrator below. This demo shows the interface; procurement actions are not connected yet.</p></aside>}</>
}
export function AppShell({ role, children }: { role: string; children: ReactNode }) {
  const { t } = useLanguage()
  const navKeys: Record<string, TranslationKey> = { Overview: 'overview', 'My token': 'token', 'Farmer Circle': 'circle', Journey: 'journey', Operations: 'operations', Resources: 'resources', Centres: 'centres', Monitoring: 'monitoring' }
  const farmer = role === 'Farmer'
  const items = farmer ? [{ label: 'Overview', icon: LayoutDashboard, href: '#main' }, { label: 'My token', icon: Ticket, href: '#current-status' }, { label: 'Farmer Circle', icon: Users, href: '#farmer-circle' }, { label: 'Journey', icon: Route, href: '#journey' }] : role === 'Centre Staff' ? [{ label: 'Overview', icon: LayoutDashboard, href: '#main' }, { label: 'Operations', icon: Route, href: '#operations' }, { label: 'Resources', icon: Leaf, href: '#resources' }] : [{ label: 'Overview', icon: LayoutDashboard, href: '#main' }, { label: 'Centres', icon: Leaf, href: '#centres' }, { label: 'Monitoring', icon: Route, href: '#monitoring' }]
  return <><Header role={role} /><div className={`workspace ${farmer ? 'farmer-workspace' : ''}`}><aside className="sidebar"><p className="eyebrow">{role} workspace</p><nav aria-label={`${role} sections`}>{items.map(({ label, icon: Icon, href }) => <a key={label} href={href}><Icon size={19} aria-hidden="true" />{t(navKeys[label])}</a>)}</nav><div className="sidebar-note"><Sprout size={24} aria-hidden="true" /><strong>A smoother procurement day.</strong><p>From planning your visit to tracking its progress.</p><Badge>SIH 2026 Prototype</Badge></div></aside><main id="main" tabIndex={-1} className="dashboard">{children}<p className="demo-note">Prototype workspace · Live services are not connected yet.</p></main></div>{farmer && <nav className="bottom-nav" aria-label="Farmer mobile sections">{items.map(({ label, icon: Icon, href }) => <a key={label} href={href}><Icon size={20} aria-hidden="true" />{t(navKeys[label])}</a>)}</nav>}</>
}



