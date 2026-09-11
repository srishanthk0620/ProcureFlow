import { useState, type ReactNode } from 'react'
import { DemoAuthContext } from './authState'
import { clearDemoSession, farmerSession, readDemoSession, RESEND_SECONDS, saveDemoSession, verifyDemoOtp } from './demoAuth'
import { validateIndianMobile } from '../utils/validation'
export function DemoAuthProvider({ children }: { children: ReactNode }) {
  const [saved, setSaved] = useState(readDemoSession)
  const [mobile, setMobile] = useState('')
  const [resendAt, setResendAt] = useState(0)
  function begin(value: string) {
    if (!validateIndianMobile(value)) return false
    setMobile(value)
    setResendAt(Date.now() + RESEND_SECONDS * 1000)
    return true
  }
  function verify(otp: string) {
    if (!validateIndianMobile(mobile) || !verifyDemoOtp(otp)) return false
    setSaved({ state: farmerSession(), storageUnavailable: !saveDemoSession() })
    setMobile('')
    return true
  }
  function resend() {
    if (!validateIndianMobile(mobile) || Date.now() < resendAt) return false
    setResendAt(Date.now() + RESEND_SECONDS * 1000)
    return true
  }
  function logout() {
    if (!clearDemoSession()) return false
    setSaved({ state: { status: 'inactive' }, storageUnavailable: false })
    setMobile('')
    setResendAt(0)
    return true
  }
  return <DemoAuthContext.Provider value={{ ...saved, mobile, resendAt, begin, verify, resend, logout }}>{children}</DemoAuthContext.Provider>
}

