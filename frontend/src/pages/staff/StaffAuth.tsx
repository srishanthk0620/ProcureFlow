import { createContext,useContext,useState,type ReactNode,type FormEvent } from 'react'
import { Navigate,Link,useNavigate } from 'react-router-dom'
import { useLanguage } from '../../i18n/languageState'
import { maxDigits,validateOtp } from '../../utils/validation'
import { Button } from '../../components/ui/Primitives'
import './staff.css'
const key='procureflow.staffDemoSession'
const Context=createContext({active:false,warning:false,login:()=>{},logout:()=>{}})
export function StaffSessionProvider({children}:{children:ReactNode}) {
 const [session,setSession]=useState(()=>{try{return {active:localStorage.getItem(key)==='STF001',warning:false}}catch{return {active:false,warning:true}}})
 const change=(active:boolean)=>{let warning=false;try{if(active)localStorage.setItem(key,'STF001');else localStorage.removeItem(key)}catch{warning=true}setSession({active,warning})}
 return <Context.Provider value={{...session,login:()=>change(true),logout:()=>change(false)}}>{children}</Context.Provider>
}
export function StaffGate({children}:{children:ReactNode}){return useContext(Context).active?<>{children}</>:<Navigate to="/staff/login" replace/>}
export function StaffLogout(){const session=useContext(Context);const {t}=useLanguage();return <Button className="secondary" onClick={session.logout}>{t('logout')}</Button>}
export function StaffLogin(){
 const {t}=useLanguage();const session=useContext(Context);const navigate=useNavigate()
 const [id,setId]=useState('');const [password,setPassword]=useState('');const [otp,setOtp]=useState('');const [step,setStep]=useState(false);const [error,setError]=useState(false)
 function submit(e:FormEvent){e.preventDefault();if(id.trim()!=='STF001'||password!=='demo123'||step&&(!validateOtp(otp,6)||otp!=='123456')){setError(true);return}setError(false);if(!step){setStep(true);return}session.login();navigate('/staff')}
 if(session.active)return <Navigate to="/staff" replace/>
 return <main id="main" tabIndex={-1} className="st-login"><Link to="/">ProcureFlow</Link><h1>{t('stLogin')}</h1><p>{t('wfDemo')}</p><form className="card wf-form" onSubmit={submit} noValidate>{!step?<><label className="wf-field">{t('stId')}<input autoComplete="username" value={id} maxLength={12} onChange={e=>setId(e.target.value)}/></label><label className="wf-field">{t('stPassword')}<input type="password" autoComplete="current-password" value={password} maxLength={32} onChange={e=>setPassword(e.target.value)}/></label></>:<label className="wf-field">{t('stOtp')}<input inputMode="numeric" autoComplete="one-time-code" value={otp} maxLength={6} onChange={e=>setOtp(maxDigits(e.target.value,6))}/></label>}{error&&<p role="alert">{t('stInvalid')}</p>}{session.warning&&<p role="status">{t('wfStorage')}</p>}<div className="wf-actions">{step&&<Button type="button" className="secondary" onClick={()=>{setStep(false);setOtp('');setError(false)}}>{t('wfBack')}</Button>}<Button type="submit">{t(step?'stVerify':'wfNext')}</Button></div></form><p>Demo credentials: STF001 / demo123 · OTP 123456. Local simulation only; no real authentication or messages.</p></main>
}

