import { createContext, useContext } from 'react'
import type { FarmerState } from './farmerModel'
export interface FarmerDemoValue {state:FarmerState;storageError:boolean;update:(change:(current:FarmerState)=>FarmerState)=>void}
export const FarmerDemoContext=createContext<FarmerDemoValue|undefined>(undefined)
export function useFarmerDemo(){const context=useContext(FarmerDemoContext);if(!context)throw Error('FarmerDemoProvider required');return context}
