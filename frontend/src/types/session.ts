/** Demo display roles only. Never use these types as an authorization boundary. */
export type Role = 'farmer' | 'staff' | 'centre_manager' | 'delegate' | 'district_admin' | 'state_admin' | 'super_admin'
export interface DemoSession {
  mode: 'demo'
  role: Role
  displayName: string
  farmerId?: string
  centreId?: string
}
export type DemoSessionState = { status: 'inactive' } | { status: 'active'; session: DemoSession }
