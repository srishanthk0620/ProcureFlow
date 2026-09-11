import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '../../components/ui/Primitives'
import { useLanguage } from '../../i18n/languageState'
import { useDemoAuth } from '../../auth/authState'
import { DEMO_OTP, OTP_LENGTH } from '../../auth/demoAuth'
import { otpInputValue, validateOtp } from '../../utils/validation'
import { FarmerAuthLayout } from './FarmerAuthLayout'
export function FarmerOtp() {
  const auth = useDemoAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [otp, setOtp] = useState('')
  const [wrong, setWrong] = useState(false)
  const [resent, setResent] = useState(false)
  const [now, setNow] = useState(Date.now)
  useEffect(() => { const timer = window.setInterval(() => setNow(Date.now()), 500); return () => window.clearInterval(timer) }, [])
  const remaining = Math.max(0, Math.ceil((auth.resendAt - now) / 1000))
  if (auth.state.status === 'active') return <Navigate to="/farmer" replace />
  if (!auth.mobile) return <Navigate to="/farmer/login" replace />
  function submit(event: FormEvent) {
    event.preventDefault()
    if (!validateOtp(otp, OTP_LENGTH)) return
    if (auth.verify(otp)) navigate('/farmer', { replace: true })
    else setWrong(true)
  }
  function change(value: string) { setOtp(otpInputValue(value, OTP_LENGTH)); setWrong(false) }
  return <FarmerAuthLayout otp><h1>{t('otpTitle')}</h1><p className="auth-intro">{t('otpIntro')}<strong className="masked-mobile" dir="ltr">+91 •••••• {auth.mobile.slice(-4)}</strong></p><Link className="auth-edit" to="/farmer/login">{t('editMobile')}</Link><form onSubmit={submit} noValidate><label className="auth-label" htmlFor="otp">{t('otpLabel')}</label><div className="otp-entry"><div className="otp-cells" aria-hidden="true">{Array.from({ length: OTP_LENGTH }, (_, index) => <span key={index}>{otp[index] || ''}</span>)}</div><input className="otp-field" id="otp" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={OTP_LENGTH} value={otp} onChange={e => change(e.target.value)} onPaste={e => { e.preventDefault(); change(e.clipboardData.getData('text')) }} aria-invalid={wrong} aria-describedby="otp-error demo-code" /></div><p className="auth-error" id="otp-error" role="alert">{wrong ? t('wrongOtp') : ''}</p><Button type="submit" className="auth-submit" disabled={!validateOtp(otp, OTP_LENGTH)}>{t('verify')}<ArrowRight size={18} aria-hidden="true" /></Button></form><div className="auth-resend"><Button className="secondary" disabled={remaining > 0} onClick={() => { if (auth.resend()) { setNow(Date.now()); setResent(true); change('') } }}>{t('resend')}</Button><span>{remaining > 0 ? `${t('resendIn')} ${remaining} ${t('seconds')}` : ''}</span></div><p role="status" className="helper">{resent ? t('resent') : ''}</p><p className="demo-code" id="demo-code">{t('demoCode')}<strong dir="ltr">{DEMO_OTP}</strong></p></FarmerAuthLayout>
}

