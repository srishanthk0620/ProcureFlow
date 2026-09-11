import type { ReactNode } from 'react'
import { Sprout, Globe, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { languages, isLanguage } from '../../i18n/translations'
import { useLanguage } from '../../i18n/languageState'
export function FarmerAuthLayout({ children, otp = false }: { children: ReactNode; otp?: boolean }) {
  const { language, setLanguage, t, storageUnavailable } = useLanguage()
  return <div className="auth-page"><a className="skip-link" href="#main">{t('skip')}</a><header className="auth-header"><Link to="/" className="brand" aria-label="ProcureFlow"><span className="brand-mark"><Sprout aria-hidden="true" /></span><span>ProcureFlow<small>{t('farmerAccess')}</small></span></Link><label className="language"><Globe size={16} aria-hidden="true" /><select aria-label={t('language')} value={language} onChange={e => { if (isLanguage(e.target.value)) setLanguage(e.target.value) }}>{languages.map(item => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label></header><main id="main" tabIndex={-1} className="auth-main"><Link className="auth-back" to="/"><ArrowLeft size={17} aria-hidden="true" />{t('backHome')}</Link><section className="auth-panel"><div className="auth-progress" aria-label={t('farmerAccess')}><span aria-current={!otp ? 'step' : undefined}>{t('stepMobile')}</span><span aria-current={otp ? 'step' : undefined}>{t('stepOtp')}</span></div>{children}</section><p className="auth-disclaimer">{t('demoNotice')}</p>{storageUnavailable && <p className="auth-error" role="status">{t('sessionWarning')}</p>}</main></div>
}
