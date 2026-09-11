import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
export function RouteFocus() {
  const { pathname } = useLocation()
  useEffect(() => {
    const names: Record<string, string> = { '/': 'Welcome', '/farmer/login': 'Login / Register', '/farmer/otp': 'Verify your mobile', '/farmer': 'Farmer home', '/farmer/more': 'More services', '/farmer/bookings': 'My Bookings', '/farmer/status': 'Live Status', '/staff': 'Centre Operations', '/admin': 'Procurement Network' }
    document.title = `${names[pathname] || (pathname.startsWith('/farmer/services/') ? 'Farmer services' : pathname.startsWith('/staff/') ? 'Staff operations' : 'Page not found')} | ProcureFlow`
    window.scrollTo(0, 0)
    document.getElementById('main')?.focus({ preventScroll: true })
  }, [pathname])
  return null
}




