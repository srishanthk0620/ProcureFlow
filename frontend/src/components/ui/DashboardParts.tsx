import { ArrowRight, CalendarDays, Ticket, Users, Route, ScanLine, ListOrdered, Settings2, Workflow } from 'lucide-react'
import { Card } from './Primitives'
export function QuickActions({ staff = false }: { staff?: boolean }) {
  const actions = staff ? [{ label: 'Check in farmer', icon: ScanLine }, { label: 'View queue', icon: ListOrdered }, { label: 'Resource status', icon: Settings2 }, { label: 'Procurement workflow', icon: Workflow }] : [{ label: 'Book procurement', icon: CalendarDays }, { label: 'My token', icon: Ticket }, { label: 'Farmer Circle', icon: Users }, { label: 'Track procurement', icon: Route }]
  return <section id="operations"><div className="section-heading"><h2>{staff ? 'Quick operations' : 'Quick actions'}</h2><span className="muted text-sm">Available in a later phase</span></div><div className="quick-grid">{actions.map(({ label, icon: Icon }) => <button className="quick-action" disabled key={label}><Icon size={23} aria-hidden="true" /><span>{label}</span><ArrowRight size={16} aria-hidden="true" /></button>)}</div></section>
}
export function Summary({ labels }: { labels: string[] }) {
  return <div className="summary-grid">{labels.map(label => <Card key={label}><p className="muted">{label}</p><p className="metric" aria-label={`${label}: not connected`}>—</p><span className="placeholder-label">Not connected yet</span></Card>)}</div>
}

