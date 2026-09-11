import { dateOffset,centreById, type FarmerState, type Stage } from './farmerModel'
import { emptyStaffState, resourceSnapshot, type OperationalDisruption } from './staffResources'
export type QueueAction='checkIn'|'advance'|'hold'|'resume'|'complete'
export function changeQueue(s:FarmerState,id:string,action:QueueAction):FarmerState {
 const booking=s.bookings.find(b=>b.id===id);const staff=s.staff||emptyStaffState()
 if(!booking||['complete','cancelled'].includes(booking.stage))return s
 const held=staff.held.includes(id)
 if(action==='hold'||action==='resume')return {...s,staff:{...staff,held:action==='hold'?[...new Set([...staff.held,id])]:staff.held.filter(x=>x!==id)}}
 if(held)return s
 const stages:Stage[]=['booked','checkedIn','quality','weighing','complete']
 if(action==='checkIn'&&booking.stage!=='booked'||action==='complete'&&booking.stage!=='weighing')return s
 const stage=action==='checkIn'?'checkedIn':stages[Math.min(4,stages.indexOf(booking.stage)+1)]
 return {...s,nextId:s.nextId+1,bookings:s.bookings.map(b=>b.id===id?{...b,stage,...(stage==='complete'?{completedOn:dateOffset(0)}:{})}:b),notifications:[{id:`N${s.nextId}`,kind:stage==='complete'?'completed':'queue',reference:booking.token,read:false},...s.notifications]}
}
export function reportDisruption(s:FarmerState,draft:Omit<OperationalDisruption,'id'|'resolved'>):FarmerState {
 if(!centreById(draft.centreId)||!draft.note.trim()||draft.note.length>300||!Number.isInteger(draft.recovery)||draft.recovery<5||draft.recovery>480)throw Error('stInvalid')
 const staff=s.staff||emptyStaffState();const incident={...draft,id:`D${s.nextId}`,resolved:false}
 const snapshot=resourceSnapshot(staff,draft.centreId)
 if(draft.type!=='other'&&snapshot.available[draft.type]===0)throw Error('stNoResource')
 return {...s,nextId:s.nextId+1,staff:{...staff,incidents:[incident,...staff.incidents]},notifications:[{id:`N${s.nextId}`,kind:'delay',reference:`${incident.id} · ${centreById(draft.centreId)!.name}`,read:false},...s.notifications]}
}
export function resolveDisruption(s:FarmerState,id:string):FarmerState {
 const staff=s.staff||emptyStaffState();if(!staff.incidents.some(d=>d.id===id&&!d.resolved))return s
 return {...s,nextId:s.nextId+1,staff:{...staff,incidents:staff.incidents.map(d=>d.id===id?{...d,resolved:true}:d)},notifications:[{id:`N${s.nextId}`,kind:'queue',reference:`${id} · resolved`,read:false},...s.notifications]}
}

