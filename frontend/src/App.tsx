import { StaffSessionProvider,StaffGate,StaffLogin } from './pages/staff/StaffAuth'
import { StaffLayout } from './pages/staff/StaffLayout'
import { StaffBookings,StaffFarmers } from './pages/staff/StaffBookings'
import { StaffDisruptions,StaffHelp } from './pages/staff/StaffDisruptions'
import { StaffMessages,StaffReports } from './pages/staff/StaffReports'
import { FarmerDemoProvider } from './demo/FarmerDemoProvider'
import { FarmerHomeLayout } from './pages/farmer/FarmerHomeLayout'
import { FarmerMore, FarmerServicePage } from './pages/farmer/FarmerServicesPage'
import { DemoAuthProvider } from './auth/DemoAuthProvider'
import { FarmerDemoGate } from './auth/FarmerDemoGate'
import { FarmerLogin } from './pages/farmer/FarmerLogin'
import { FarmerOtp } from './pages/farmer/FarmerOtp'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import { FarmerDashboard } from './pages/farmer/FarmerDashboard'
import { StaffDashboard } from './pages/staff/StaffDashboard'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { NotFoundPage } from './pages/NotFoundPage'
import { RouteFocus } from './app/RouteFocus'
import { LanguageProvider } from './i18n/LanguageContext'
import './App.css'

function App() {
  return <LanguageProvider><DemoAuthProvider><FarmerDemoProvider><StaffSessionProvider><BrowserRouter><RouteFocus /><Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/farmer" element={<FarmerDemoGate><FarmerHomeLayout /></FarmerDemoGate>}>
      <Route index element={<FarmerDashboard />} />
      <Route path="bookings" element={<FarmerServicePage serviceId="bookings" />} />
      <Route path="status" element={<FarmerServicePage serviceId="status" />} />
      <Route path="more" element={<FarmerMore />} />
      <Route path="services/:serviceId" element={<FarmerServicePage />} />
    </Route>
    <Route path="/farmer/login" element={<FarmerLogin />} />
    <Route path="/farmer/otp" element={<FarmerOtp />} />
    <Route path="/staff/login" element={<StaffLogin />} />
    <Route path="/staff" element={<StaffGate><StaffLayout /></StaffGate>}>
      <Route index element={<StaffDashboard />} />
      <Route path="operations" element={<StaffDashboard live />} />
      <Route path="queue" element={<StaffBookings mode="queue" />} />
      <Route path="bookings" element={<StaffBookings />} />
      <Route path="groups" element={<StaffBookings mode="groups" />} />
      <Route path="farmers" element={<StaffFarmers />} />
      <Route path="disruptions" element={<StaffDisruptions />} />
      <Route path="messages" element={<StaffMessages />} />
      <Route path="reports" element={<StaffReports />} />
      <Route path="help" element={<StaffHelp />} />
      <Route path="profile" element={<StaffHelp profile />} />
    </Route>
    <Route path="/admin" element={<AdminDashboard />} />
    <Route path="*" element={<NotFoundPage />} />
  </Routes></BrowserRouter></StaffSessionProvider></FarmerDemoProvider></DemoAuthProvider></LanguageProvider>
}
export default App




