import { useEffect,useRef,useState,type ReactNode } from 'react'
import { FarmerDemoContext } from './farmerContext'
import { readFarmerState,persistFarmerState,STATE_KEY,type FarmerState } from './farmerModel'
export function FarmerDemoProvider({children}:{children:ReactNode}) {
 const [saved,setSaved]=useState(readFarmerState); const current=useRef(saved.state)
 useEffect(()=>{
  function sync(event:StorageEvent){if(event.key!==STATE_KEY)return;const next=readFarmerState();if(next.storageError){setSaved(previous=>({...previous,storageError:true}));return}current.current=next.state;setSaved(next)}
  window.addEventListener('storage',sync);return ()=>window.removeEventListener('storage',sync)
 },[])
 function update(change:(state:FarmerState)=>FarmerState){const state=change(current.current);current.current=state;setSaved({state,storageError:!persistFarmerState(state)})}
 return <FarmerDemoContext.Provider value={{...saved,update}}>{children}</FarmerDemoContext.Provider>
}
