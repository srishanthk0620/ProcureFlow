import { demoLoginFarmer } from '../data/demoData'
import type { DemoSessionState } from '../types/session'
import { validateOtp } from '../utils/validation'

// Deliberately insecure demo adapter. Replace with a server-backed provider for real authentication.
export const DEMO_OTP = '123456'
export const OTP_LENGTH = 6
export const RESEND_SECONDS = 30
export const SESSION_KEY = 'procureflow.demoFarmerSession'
export const verifyDemoOtp = (code: string) => validateOtp(code, OTP_LENGTH) && code === DEMO_OTP
export function farmerSession(): DemoSessionState {
  return { status: 'active', session: { mode: 'demo', role: 'farmer', farmerId: demoLoginFarmer.id, displayName: demoLoginFarmer.name } }
}
export function readDemoSession(): { state: DemoSessionState; storageUnavailable: boolean } {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY)
    const value: unknown = raw ? JSON.parse(raw) : null
    if (value && typeof value === 'object' && 'mode' in value && value.mode === 'demo' && 'farmerId' in value && value.farmerId === demoLoginFarmer.id && 'role' in value && value.role === 'farmer') return { state: farmerSession(), storageUnavailable: false }
    return { state: { status: 'inactive' }, storageUnavailable: false }
  } catch { return { state: { status: 'inactive' }, storageUnavailable: true } }
}
export function saveDemoSession(): boolean {
  try {
    // Never persist mobile numbers or OTP input.
    window.localStorage.setItem(SESSION_KEY, JSON.stringify({ mode: 'demo', role: 'farmer', farmerId: demoLoginFarmer.id }))
    return true
  } catch { return false }
}
export function clearDemoSession(): boolean {
  try { window.localStorage.removeItem(SESSION_KEY); return true }
  catch { return false }
}
