import { Navigate, Route, Routes } from 'react-router-dom'
import Shell from './components/layout/Shell'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'
import OwnerDashboard from './pages/owner/OwnerDashboard'
import NewSpace from './pages/owner/NewSpace'
import NewRoom from './pages/owner/NewRoom'
import EditRoom from './pages/owner/EditRoom'
import Search from './pages/booker/Search'
import ListingDetail from './pages/booker/ListingDetail'

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
          <Route path="owner/rooms/:roomId/edit" element={<EditRoom />} />
        </Route>

        {/* Booker area */}
        <Route element={<ProtectedRoute role="booker" />}>
          <Route path="search" element={<Search />} />
          <Route path="listings/:roomId" element={<ListingDetail />} />
        </Route>

        <Route path="404" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  )
}
