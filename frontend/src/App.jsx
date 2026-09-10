import { Navigate, Route, Routes } from 'react-router-dom'
import Shell from './components/layout/Shell'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'
import Placeholder from './pages/Placeholder'
import OwnerDashboard from './pages/owner/OwnerDashboard'
import NewSpace from './pages/owner/NewSpace'
import NewRoom from './pages/owner/NewRoom'

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Landing />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />

        {/* Owner area */}
        <Route element={<ProtectedRoute role="owner" />}>
          <Route path="owner" element={<OwnerDashboard />} />
          <Route path="owner/spaces/new" element={<NewSpace />} />
          <Route path="owner/spaces/:spaceId/rooms/new" element={<NewRoom />} />
        </Route>

        {/* Booker area — filled in by part 3 */}
        <Route element={<ProtectedRoute role="booker" />}>
          <Route
            path="search"
            element={
              <Placeholder
                icon="search"
                title="Search is on its way"
                description="Filters, the free-text preference note and AI-ranked results arrive in the final part of the build."
              />
            }
          />
        </Route>

        <Route path="404" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  )
}
