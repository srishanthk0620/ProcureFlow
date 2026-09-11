import { createContext, useContext } from 'react'
import type { DemoSessionState } from '../types/session'
export interface DemoAuthValue {
  state: DemoSessionState
  mobile: string
  resendAt: number
  storageUnavailable: boolean
  begin: (mobile: string) => boolean
  verify: (otp: string) => boolean
  resend: () => boolean
  logout: () => boolean
}
export const DemoAuthContext = createContext<DemoAuthValue | undefined>(undefined)
export function useDemoAuth() {
  const context = useContext(DemoAuthContext)
  if (!context) throw new Error('useDemoAuth requires DemoAuthProvider')
  return context
}

