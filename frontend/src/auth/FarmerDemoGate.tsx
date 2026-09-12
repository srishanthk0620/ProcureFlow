import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useDemoAuth } from './authState'
export function FarmerDemoGate({ children }: { children: ReactNode }) {
  const { state } = useDemoAuth()
  const location = useLocation()
  return state.status === 'active' && state.session.role === 'farmer' ? children : <Navigate to="/farmer/login" state={{ returnTo: location.pathname + location.search }} replace />
}
