/** Fictional, deterministic Kerala demonstration data. Not official capacity or prices. */
export const workflowCentres = [
 { id: 'kollam-town', name: 'Kollam Town Demo Centre', area: 'Kollam', distance: 5, travel: 12, queue: 9, resources: 1, service: 10, penalty: 20, commodities: ['paddy','copra'], slotCapacity: 1800 },
 { id: 'kollam-east', name: 'Kollam East Demo Centre', area: 'Kollam', distance: 8.4, travel: 18, queue: 6, resources: 3, service: 10, penalty: 0, commodities: ['paddy','copra'], slotCapacity: 3000 },
 { id: 'karunagappally', name: 'Karunagappally Demo Centre', area: 'Kollam', distance: 22, travel: 38, queue: 4, resources: 2, service: 12, penalty: 0, commodities: ['paddy'], slotCapacity: 2400 },
] as const
export const demoSlots = ['09:00','11:00','14:00'] as const
export const workflowPrices = [{ commodity:'paddy', rate:28.5 },{commodity:'copra',rate:112}]
export const demoSchemes = [
 { title:'Produce preparation support', text:'Ask about local support for drying and preparing produce. Ask the centre about available equipment.', documents:'Preparation checklist: farmer profile and produce details. This is not an official eligibility requirement.' },
 { title:'Community transport coordination', text:'Ask about assistance for farmer groups sharing a vehicle to the procurement centre.', documents:'Preparation checklist: group contact, member count and planned quantity. Availability must be verified locally.' },
 { title:'Farmer registration guidance', text:'Information on getting help with procurement registration through an assisted service desk.', documents:'Carry only the documents requested by the actual centre. Never share OTPs with unknown callers.' },
]
export const guideSections = [
 { title:'Before booking', text:'Choose a commodity and enter the total quantity. Compare completion estimates, not just distance.' },
 { title:'Documents to carry', text:'Keep your booking token and farmer profile ready. Confirm actual document requirements with your centre.' },
 { title:'Preparing produce', text:'Keep lots separated and clearly labelled. Ask the centre about drying, packaging and quality requirements.' },
 { title:'Reaching the centre', text:'Check your slot and centre location. Estimates may change; travel guidance does not use live GPS or maps.' },
 { title:'Quality inspection', text:'Staff check the produce before weighing. Follow the stage updates in Live Status.' },
 { title:'Weighing', text:'Review the recorded quantity with staff. Confirm the weight on the centre’s equipment.' },
 { title:'Payment and status', text:'Track completion with your token. Payment processing is not connected.' },
]
export const chatQuestions = [
 { key:'wfChatBooking', answer:'Open My Bookings to see your tokens. Select a booking to view its centre, quantity and date.', route:'/farmer/bookings' },
 { key:'wfChatChange', answer:'Open the booking details, cancel an upcoming booking, then book a new available slot. Checked-in bookings cannot be cancelled after arrival.', route:'/farmer/bookings' },
 { key:'wfChatDocs', answer:'Keep your token and farmer profile ready. Confirm official documents directly with your centre.', route:'/farmer/services/guide' },
 { key:'wfChatWhy', answer:'We compare travel time, queued workload divided by working resources, your service time, and disruption delay. A farther centre can finish sooner.', route:'/farmer/services/find-centre' },
] as const
