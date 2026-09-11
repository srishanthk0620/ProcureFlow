/** Local demonstration resources only; no production scheduling decisions. */
export type ResourceType = 'quality' | 'weighing' | 'gate' | 'staff' | 'other'
export interface OperationalDisruption { id:string; centreId:string; type:ResourceType; severity:'low'|'medium'|'high'; recovery:number; note:string; resolved:boolean }
export interface StaffState { centreId:string; held:string[]; read:string[]; incidents:OperationalDisruption[] }
export const emptyStaffState = ():StaffState => ({centreId:'kollam-east',held:[],read:[],incidents:[]})
export const resourceTotals = {gate:3,quality:2,weighing:2,staff:7} as const
export function resourceSnapshot(staff:StaffState|undefined, centreId:string) {
 const active=(staff?.incidents||[]).filter(d=>d.centreId===centreId&&!d.resolved)
 const available={...resourceTotals} as Record<keyof typeof resourceTotals,number>
 for(const incident of active) if(incident.type!=='other')available[incident.type]=Math.max(0,available[incident.type]-1)
 const factor=Math.min(...Object.keys(available).map(k=>available[k as keyof typeof available]/resourceTotals[k as keyof typeof resourceTotals]))
 const penalty=active.reduce((n,d)=>n+({low:5,medium:15,high:30}[d.severity]),0)
 return {active,available,factor,penalty}
}
export function validStaff(value:unknown):value is StaffState {
 if(!value||typeof value!=='object')return false
 const s=value as StaffState
 return ['kollam-east','kollam-town','karunagappally'].includes(s.centreId)&&Array.isArray(s.held)&&s.held.every(x=>typeof x==='string')&&Array.isArray(s.read)&&s.read.every(x=>typeof x==='string')&&Array.isArray(s.incidents)&&s.incidents.every(d=>d&&typeof d.id==='string'&&['kollam-east','kollam-town','karunagappally'].includes(d.centreId)&&['quality','weighing','gate','staff','other'].includes(d.type)&&['low','medium','high'].includes(d.severity)&&Number.isInteger(d.recovery)&&d.recovery>=5&&d.recovery<=480&&typeof d.note==='string'&&d.note.length<=300&&typeof d.resolved==='boolean')
}

