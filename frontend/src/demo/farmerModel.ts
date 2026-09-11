import { resourceSnapshot, validStaff, type StaffState } from './staffResources'
import { demoSlots, workflowCentres } from '../data/workflowData'
export type Stage = 'booked' | 'checkedIn' | 'quality' | 'weighing' | 'complete' | 'cancelled'
export interface Booking { completedOn?:string; id:string; token:string; commodity:string; quantity:number; centreId:string; date:string; slot:string; stage:Stage; group?:{name:string; farmers:number; contact:string} }
export interface Notice { id:string; kind:'confirmed'|'reminder'|'queue'|'delay'|'completed'|'grievance'|'cancelled'; reference:string; read:boolean }
export interface Grievance { id:string; category:string; reference:string; description:string; status:'submitted' }
export interface FarmerState { version:1; staff?:StaffState; commodity:string; centreId:string; bookings:Booking[]; notifications:Notice[]; grievances:Grievance[]; disruptions:Record<string,boolean>; notificationsEnabled:boolean; nextId:number }
export const STATE_KEY='procureflow.farmerWorkflows.v1'
export function dateOffset(days=1) { const date=new Date(); date.setDate(date.getDate()+days); return date.toLocaleDateString('en-CA',{timeZone:'Asia/Kolkata'}) }
export function initialFarmerState():FarmerState { return {version:1,commodity:'paddy',centreId:'kollam-east',bookings:[{id:'PF-1',token:'F001',commodity:'paddy',quantity:600,centreId:'kollam-east',date:dateOffset(),slot:'09:00',stage:'booked'}],notifications:[{id:'N1',kind:'reminder',reference:'F001',read:false}],grievances:[],disruptions:{'kollam-town':true},notificationsEnabled:true,nextId:2} }
export function centreById(id:string) { return workflowCentres.find(c=>c.id===id) }
export function recommendation(state:FarmerState,commodity=state.commodity) {
 return workflowCentres.filter(c=>(c.commodities as readonly string[]).includes(commodity)).map(c=>{
 const resources=resourceSnapshot(state.staff,c.id); const disrupted=!!state.disruptions[c.id] || resources.active.length>0; const capacity=Math.max(0.25,(c.resources-(state.disruptions[c.id] && c.resources>1?1:0))*resources.factor)
 const local=state.bookings.filter(b=>b.centreId===c.id && b.stage!=='cancelled' && b.stage!=='complete').length
 const wait=Math.ceil((c.queue+local)*c.service/capacity); const penalty=(state.disruptions[c.id]?Math.max(20,c.penalty):0)+resources.penalty
 return {...c,capacity,wait,penalty,total:c.travel+wait+c.service+penalty,disrupted}
 }).sort((a,b)=>a.total-b.total || a.id.localeCompare(b.id))
}
export function slotRemaining(state:FarmerState,centreId:string,date:string,slot:string) {
 const centre=centreById(centreId); if(!centre || !(demoSlots as readonly string[]).includes(slot)) return 0
 if(resourceSnapshot(state.staff,centreId).factor===0)return 0
 const base=slot==='14:00'?centre.slotCapacity:slot==='11:00'?Math.floor(centre.slotCapacity*.8):200
 const used=state.bookings.filter(b=>b.centreId===centreId&&b.date===date&&b.slot===slot&&b.stage!=='cancelled').reduce((sum,b)=>sum+b.quantity,0)
 return Math.max(0,centre.slotCapacity-base-used)
}
export type BookingDraft=Omit<Booking,'id'|'token'|'stage'>
export function bookingError(state:FarmerState,draft:BookingDraft):'wfInvalid'|'wfFull'|null {
 if(!centreById(draft.centreId)||!(centreById(draft.centreId)!.commodities as readonly string[]).includes(draft.commodity)||!Number.isInteger(draft.quantity)||draft.quantity<50||draft.quantity>20000||!/^\d{4}-\d{2}-\d{2}$/.test(draft.date)||draft.date<dateOffset()||draft.date>dateOffset(7)||!(demoSlots as readonly string[]).includes(draft.slot))return 'wfInvalid'
 if(draft.group&&(!draft.group.name.trim()||draft.group.name.length>60||!draft.group.contact.trim()||draft.group.contact.length>60||!Number.isInteger(draft.group.farmers)||draft.group.farmers<2||draft.group.farmers>20))return 'wfInvalid'
 if(draft.quantity>slotRemaining(state,draft.centreId,draft.date,draft.slot))return 'wfFull'
 return null
}
export function addBooking(state:FarmerState,draft:BookingDraft):FarmerState {
 const error=bookingError(state,draft); if(error)throw new Error(error)
 const booking:Booking={...draft,id:`PF-${state.nextId}`,token:`F${String(state.nextId).padStart(3,'0')}`,stage:'booked'}
 return {...state,nextId:state.nextId+1,commodity:draft.commodity,centreId:draft.centreId,bookings:[booking,...state.bookings],notifications:[{id:`N${state.nextId}`,kind:'confirmed',reference:booking.token,read:false},...state.notifications]}
}
function validState(value:unknown):value is FarmerState {
 if(!value||typeof value!=='object')return false
 const s=value as FarmerState
 const validBooking=(b:Booking)=>b&&typeof b.id==='string'&&typeof b.token==='string'&&['paddy','copra'].includes(b.commodity)&&!!centreById(b.centreId)&&(centreById(b.centreId)!.commodities as readonly string[]).includes(b.commodity)&&Number.isInteger(b.quantity)&&b.quantity>=50&&b.quantity<=20000&&/^\d{4}-\d{2}-\d{2}$/.test(b.date)&&!Number.isNaN(Date.parse(b.date))&&(demoSlots as readonly string[]).includes(b.slot)&&['booked','checkedIn','quality','weighing','complete','cancelled'].includes(b.stage)&&(!b.group||(typeof b.group.name==='string'&&typeof b.group.contact==='string'&&Number.isInteger(b.group.farmers)))
 return s.version===1&&(s.staff===undefined||validStaff(s.staff))&&['paddy','copra'].includes(s.commodity)&&!!centreById(s.centreId)&&Number.isSafeInteger(s.nextId)&&s.nextId>0&&typeof s.notificationsEnabled==='boolean'&&Array.isArray(s.bookings)&&s.bookings.every(validBooking)&&Array.isArray(s.notifications)&&s.notifications.every(n=>n&&typeof n.id==='string'&&typeof n.reference==='string'&&typeof n.read==='boolean'&&['confirmed','reminder','queue','delay','completed','grievance','cancelled'].includes(n.kind))&&Array.isArray(s.grievances)&&s.grievances.every(g=>g&&typeof g.id==='string'&&typeof g.category==='string'&&typeof g.reference==='string'&&typeof g.description==='string'&&g.status==='submitted')&&!!s.disruptions&&typeof s.disruptions==='object'&&Object.values(s.disruptions).every(v=>typeof v==='boolean')
}
export function readFarmerState() { try { const raw=localStorage.getItem(STATE_KEY); if(!raw)return {state:initialFarmerState(),storageError:false};const value:unknown=JSON.parse(raw);return validState(value)?{state:value,storageError:false}:{state:initialFarmerState(),storageError:true} }catch{return {state:initialFarmerState(),storageError:true}} }
export function persistFarmerState(state:FarmerState) { try{localStorage.setItem(STATE_KEY,JSON.stringify(state));return true}catch{return false} }
export const stageKeys={booked:'wfBooked',checkedIn:'wfCheckedIn',quality:'wfQuality',weighing:'wfWeighing',complete:'wfComplete',cancelled:'wfCancelled'} as const



