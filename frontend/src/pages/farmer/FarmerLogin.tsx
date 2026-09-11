import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight, Fingerprint } from 'lucide-react'
import { Button } from '../../components/ui/Primitives'
import { useLanguage } from '../../i18n/languageState'
import { useDemoAuth } from '../../auth/authState'
import { mobileInputValue, validateIndianMobile } from '../../utils/validation'
import { FarmerAuthLayout } from './FarmerAuthLayout'
export function FarmerLogin() {
  const auth = useDemoAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [mobile, setMobile] = useState(auth.mobile)
  const [touched, setTouched] = useState(false)
  const valid = validateIndianMobile(mobile)
  if (auth.state.status === 'active') return <Navigate to="/farmer" replace />
  function submit(event: FormEvent) {
    event.preventDefault()
    setTouched(true)
    if (auth.begin(mobile)) navigate('/farmer/otp')
  }
  return <FarmerAuthLayout><h1>{t('loginTitle')}</h1><p className="auth-intro">{t('loginIntro')}</p><form onSubmit={submit} noValidate><label className="auth-label" htmlFor="mobile">{t('mobile')}</label><div className="mobile-field"><span aria-hidden="true">+91</span><input id="mobile" type="tel" inputMode="numeric" autoComplete="tel-national" value={mobile} onChange={e => setMobile(mobileInputValue(e.target.value))} onPaste={e => { e.preventDefault(); setMobile(mobileInputValue(e.clipboardData.getData('text'))) }} onBlur={() => setTouched(true)} maxLength={10} aria-invalid={touched && !valid} aria-describedby="mobile-hint mobile-error" /></div><p id="mobile-hint" className="helper">{t('mobileHint')}</p><p id="mobile-error" className="auth-error" aria-live="polite">{touched && !valid ? t('invalidMobile') : ''}</p><Button className="auth-submit" type="submit" disabled={!valid}>{t('sendOtp')}<ArrowRight size={18} aria-hidden="true" /></Button></form><p className="auth-new-user">{t('newUser')}</p><div className="auth-assisted"><Button className="secondary auth-submit" disabled aria-describedby="aadhaar-note"><Fingerprint size={20} aria-hidden="true" />{t('aadhaar')}</Button><p id="aadhaar-note" className="helper">{t('notConnected')}</p></div></FarmerAuthLayout>
}
