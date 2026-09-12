import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate, useLocation } from 'react-router-dom'
import { ArrowRight, Fingerprint } from 'lucide-react'
import { Button } from '../../components/ui/Primitives'
import { useFarmerLanguage as useLanguage } from './useFarmerLanguage'
import { useDemoAuth } from '../../auth/authState'
import { mobileInputValue, validateIndianMobile } from '../../utils/validation'
import { FarmerAuthLayout } from './FarmerAuthLayout'
export function FarmerLogin() {
  const auth = useDemoAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const requested = location.state?.returnTo
  const returnTo = typeof requested === 'string' && /^\/farmer(?:\/services\/[a-z-]+|\/bookings|\/status|\/more)?(?:\?.*)?$/.test(requested) ? requested : '/farmer'
  const [mobile, setMobile] = useState(auth.mobile)
  const [aadhaarOpen, setAadhaarOpen] = useState(false)
  const [touched, setTouched] = useState(false)
  const valid = validateIndianMobile(mobile)
  if (auth.state.status === 'active') return <Navigate to={returnTo} replace />
  function submit(event: FormEvent) {
    event.preventDefault()
    setTouched(true)
    if (auth.begin(mobile)) navigate('/farmer/otp', { state: { returnTo } })
  }
  return <FarmerAuthLayout><h1>{t('loginTitle')}</h1><p className="auth-intro">{t('loginIntro')}</p><form onSubmit={submit} noValidate><label className="auth-label" htmlFor="mobile">{t('mobile')}</label><div className="mobile-field"><span aria-hidden="true">+91</span><input id="mobile" type="tel" inputMode="numeric" autoComplete="tel-national" value={mobile} onChange={e => setMobile(mobileInputValue(e.target.value))} onPaste={e => { e.preventDefault(); setMobile(mobileInputValue(e.clipboardData.getData('text'))) }} onBlur={() => setTouched(true)} maxLength={10} aria-invalid={touched && !valid} aria-describedby="mobile-hint mobile-error" /></div><p id="mobile-hint" className="helper">{t('mobileHint')}</p><p id="mobile-error" className="auth-error" aria-live="polite">{touched && !valid ? t('invalidMobile') : ''}</p><Button className="auth-submit" type="submit" disabled={!valid}>{t('sendOtp')}<ArrowRight size={18} aria-hidden="true" /></Button></form><div className="pf-aadhaar"><Button className="secondary auth-submit" aria-expanded={aadhaarOpen} aria-controls="aadhaar-availability" onClick={()=>setAadhaarOpen(!aadhaarOpen)}><Fingerprint size={23} aria-hidden="true"/>{t('aadhaar')}</Button>{aadhaarOpen&&<p id="aadhaar-availability" role="status">{t('vAadhaarUnavailable')}</p>}</div></FarmerAuthLayout>
}
