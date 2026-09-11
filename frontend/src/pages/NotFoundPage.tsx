import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Header } from '../components/layout/AppShell'
export function NotFoundPage() {
  return <><Header /><main id="main" tabIndex={-1} className="not-found"><p className="eyebrow">Page not found · 404</p><h1>Let’s get you back on track.</h1><p className="muted">This page is not part of the ProcureFlow demo.</p><Link className="button" to="/">Back home <ArrowRight size={18} aria-hidden="true" /></Link></main></>
}

