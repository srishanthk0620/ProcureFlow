import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useDemoAuth } from '../../auth/authState'
import { useFarmerLanguage as useLanguage } from './useFarmerLanguage'
export function FarmerLogout() {
  const { logout } = useDemoAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [error, setError] = useState(false)
  return <div className="fh-logout"><button onClick={() => { if (logout()) navigate('/farmer/login', { replace: true }); else setError(true) }}><LogOut size={19} aria-hidden="true" />{t('logout')}</button>{error && <p role="alert" className="auth-error">{t('logoutError')}</p>}</div>
}
