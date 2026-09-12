import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { useFarmerLanguage } from './useFarmerLanguage'
import './publicFarmerV2.css'
import harvestPhoto from '../../assets/farmer-harvest.jpg'
import circlePhoto from '../../assets/farmer-circle.jpg'

const slides = [
  { title: 'bookSlot', copy: 'vHeadline', to: '/farmer/services/book-slot', scene: 'visit', image: harvestPhoto },
  { title: 'circle', copy: 'vTogether', to: '/farmer/services/group-booking', scene: 'circle', image: circlePhoto },
  { title: 'liveStatus', copy: 'vQueue', to: '/farmer/status', scene: 'queue', image: harvestPhoto },
  { title: 'bestOption', copy: 'vCentre', to: '/farmer/services/find-centre', scene: 'centre', image: circlePhoto },
] as const

export function ServiceCarousel({ publicEntry = false }: { publicEntry?: boolean }) {
  const { t } = useFarmerLanguage()
  const items = publicEntry ? slides : slides.slice(1)
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [engaged, setEngaged] = useState(false)
  const touch = useRef<number | null>(null)
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const change = () => setReduced(media.matches)
    media.addEventListener('change', change)
    return () => media.removeEventListener('change', change)
  }, [])
  useEffect(() => {
    if (paused || reduced || engaged) return
    const timer = window.setInterval(() => { if (!document.hidden) setIndex(i => (i + 1) % items.length) }, 8000)
    return () => window.clearInterval(timer)
  }, [paused, reduced, engaged, items.length])
  function move(delta: number) { setPaused(true); setIndex(i => (i + delta + items.length) % items.length) }
  return <section className={`pf-carousel ${publicEntry ? 'pf-hero' : ''}`} aria-roledescription="carousel" aria-label={t('vDiscover')}
    onMouseEnter={() => setEngaged(true)} onMouseLeave={() => setEngaged(false)} onFocusCapture={() => setEngaged(true)} onBlurCapture={e => { if (!e.currentTarget.contains(e.relatedTarget)) setEngaged(false) }}
    onKeyDown={e => { if(e.key==='ArrowLeft'){ e.preventDefault(); move(-1) } if(e.key==='ArrowRight'){ e.preventDefault(); move(1) } }} onTouchCancel={()=>{touch.current=null}} onTouchStart={e => { touch.current = e.touches[0].clientX }} onTouchEnd={e => { if (touch.current !== null) { const delta = touch.current - e.changedTouches[0].clientX; if (Math.abs(delta) > 45) move(delta > 0 ? 1 : -1); touch.current = null } }}>
    <div className="pf-slides">{items.map((slide, i) => <div key={slide.scene} className={`pf-slide pf-photo-${slide.scene}`} hidden={i !== index} role="group" aria-roledescription="slide" aria-label={`${i + 1} / ${items.length}`}>
      <div className="pf-slide-copy"><p className="eyebrow">{t(slide.title)}</p><h2>{t(slide.copy)}</h2><Link className="button" to={slide.to}>{t(slide.title)}<ArrowRight size={18} aria-hidden="true" /></Link></div><img className="pf-scene" src={slide.image} alt="" width={1200} height={800} fetchPriority={i===0?'high':'auto'} loading={i===0?'eager':'lazy'}/>
    </div>)}</div>
    <div className="pf-carousel-controls"><span aria-live={paused ? 'polite' : 'off'}>{String(index + 1).padStart(2, '0')} / {String(items.length).padStart(2, '0')}</span><div className="pf-dots">{items.map((slide, i) => <button key={slide.scene} aria-label={t(slide.title)} aria-current={i === index ? 'true' : undefined} onClick={() => { setPaused(true); setIndex(i) }}><span /></button>)}</div><button className="pf-prev" aria-label={t('vPrevious')} onClick={() => move(-1)}><ArrowLeft size={18} /></button><button className="pf-next" aria-label={t('vNext')} onClick={() => move(1)}><ArrowRight size={18} /></button>{!reduced && <button className="pf-motion-access" onClick={() => setPaused(!paused)}>{t(paused ? 'vPlay' : 'vPause')}</button>}</div>
  </section>
}
