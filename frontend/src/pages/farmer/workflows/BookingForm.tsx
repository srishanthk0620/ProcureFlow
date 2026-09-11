import { useState,type FormEvent } from 'react'
import { useNavigate,useSearchParams } from 'react-router-dom'
import { useFarmerDemo } from '../../../demo/farmerContext'
import { addBooking,bookingError,dateOffset,recommendation,slotRemaining,type BookingDraft } from '../../../demo/farmerModel'
import { demoSlots } from '../../../data/workflowData'
import { maxDigits,validateRequired } from '../../../utils/validation'
import { useLanguage } from '../../../i18n/languageState'
import { Button } from '../../../components/ui/Primitives'
import { WorkflowHeader,CommoditySelect } from './Common'
export function BookingForm({group=false}:{group?:boolean}) {
 const {state,update}=useFarmerDemo();const {t}=useLanguage();const navigate=useNavigate();const [params]=useSearchParams()
 const [commodity,setCommodity]=useState(state.commodity);const [quantity,setQuantity]=useState('');const [centreId,setCentreId]=useState(params.get('centre')||state.centreId)
 const [date,setDate]=useState(dateOffset());const [slot,setSlot]=useState('');const [step,setStep]=useState(0);const [error,setError]=useState<'wfInvalid'|'wfFull'|null>(null)
 const [name,setName]=useState('');const [members,setMembers]=useState('');const [contact,setContact]=useState('')
 const centres=recommendation(state,commodity)
 const draft:BookingDraft={commodity,quantity:Number(quantity),centreId,date,slot,...(group?{group:{name:name.trim(),farmers:Number(members),contact:contact.trim()}}:{})}
 function submit(e:FormEvent){e.preventDefault();setError(null)
 if(step===0){if(!Number.isInteger(Number(quantity))||Number(quantity)<50||Number(quantity)>20000||(group&&(!validateRequired(name)||!validateRequired(contact)||Number(members)<2||Number(members)>20))){setError('wfInvalid');return}setStep(1);return}
 if(step===1){const problem=bookingError(state,draft);if(problem){setError(problem);return}setStep(2);return}
 let id='';let problem:'wfInvalid'|'wfFull'|null=null
 update(current=>{problem=bookingError(current,draft);if(problem)return current;const next=addBooking(current,draft);id=next.bookings[0].id;return next})
 if(problem){setError(problem);setStep(1)}else navigate(`/farmer/bookings?booking=${id}&confirmed=1`)
 }
 return <><WorkflowHeader title={group?'groupBooking':'bookSlot'}/>{group&&<p className="muted">Coordinate travel and processing together. Enter fictional demo contact names only.</p>}<ol className="wf-steps">{['commodity','wfSlot','wfReview'].map((key,i)=><li key={key} aria-current={step===i?'step':undefined}>{i+1}. {t(key as 'commodity'|'wfSlot'|'wfReview')}</li>)}</ol><form className="card wf-form" onSubmit={submit} noValidate>
 {step===0&&<><CommoditySelect value={commodity} onChange={value=>{setCommodity(value);setCentreId(recommendation(state,value)[0].id);setSlot('')}}/><label className="wf-field">{t('wfQuantity')}<input inputMode="numeric" value={quantity} maxLength={5} onChange={e=>setQuantity(maxDigits(e.target.value,5))} aria-describedby="qty-hint"/></label><p id="qty-hint" className="helper">50–20,000 kg · {t('wfAvailable')} {t('wfCapacity')}</p>{group&&<><label className="wf-field">{t('wfGroupName')}<input maxLength={60} value={name} onChange={e=>setName(e.target.value)}/></label><label className="wf-field">{t('wfMembers')}<input inputMode="numeric" maxLength={2} value={members} onChange={e=>setMembers(maxDigits(e.target.value,2))}/></label><label className="wf-field">{t('wfContact')}<input maxLength={60} value={contact} onChange={e=>setContact(e.target.value)}/></label></> }</>}
 {step===1&&<><label className="wf-field">{t('centres')}<select value={centreId} onChange={e=>{setCentreId(e.target.value);setSlot('')}}>{centres.map((c,i)=><option key={c.id} value={c.id}>{c.name} · {c.total} {t('minutes')}{i===0?` · ${t('bestOption')}`:''}</option>)}</select></label><details className="wf-details"><summary>{t('wfWhy')}</summary>{centres.map(c=><p key={c.id}>{c.name}: {c.travel} + {c.wait} + {c.service} + {c.penalty} = {c.total} {t('minutes')} ({t('travel')} + {t('currentWait')} + {t('wfService')} + {t('wfPenalty')})</p>)}</details><label className="wf-field">{t('wfDate')}<input type="date" value={date} min={dateOffset()} max={dateOffset(7)} onChange={e=>{setDate(e.target.value);setSlot('')}}/></label><fieldset><legend>{t('wfSlot')}</legend><div className="wf-slots">{demoSlots.map(time=>{const left=slotRemaining(state,centreId,date,time);return <label key={time} className={slot===time?'chosen':''}><input type="radio" name="slot" value={time} checked={slot===time} disabled={left<Number(quantity)} onChange={()=>setSlot(time)}/><strong>{time}</strong><span>{left===0?t('wfFullLabel'):left<Number(quantity)?t('wfLimited'):t('wfAvailable')} · {left} kg</span></label>})}</div></fieldset></>}
 {step===2&&<><h2>{t('wfReview')}</h2><dl className="wf-facts"><div><dt>{t('commodity')}</dt><dd>{t(commodity==='paddy'?'paddy':'wfCopra')}</dd></div><div><dt>{t('wfQuantity')}</dt><dd>{quantity} kg</dd></div><div><dt>{t('centres')}</dt><dd>{centres.find(c=>c.id===centreId)?.name}</dd></div><div><dt>{t('appointment')}</dt><dd>{date} · {slot}</dd></div>{group&&<><div><dt>{t('wfGroupName')}</dt><dd>{name}</dd></div><div><dt>{t('wfMembers')}</dt><dd>{members}</dd></div><div><dt>{t('wfContact')}</dt><dd>{contact}</dd></div></>}</dl></>}
 {error&&<p role="alert" className="auth-error">{t(error)}</p>}<div className="wf-actions">{step>0&&<Button className="secondary" type="button" onClick={()=>{setError(null);setStep(step-1)}}>{t('wfBack')}</Button>}<Button type="submit">{t(step===2?'wfConfirm':'wfNext')}</Button></div></form></>
}
