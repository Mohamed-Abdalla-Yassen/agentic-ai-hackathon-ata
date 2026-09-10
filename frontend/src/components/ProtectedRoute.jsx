import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'

/**
 * Gate for authenticated routes. `role` additionally restricts to one of the
 * two roles in the spec — an owner hitting a booker route (or vice versa) is
 * bounced to their own home rather than shown a 403 page.
 */
export default function ProtectedRoute({ role }) {
  const { isAuthed, user } = useAuth()
  const location = useLocation()

  if (!isAuthed) {
    // Remember where they were headed so login can send them back.
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (role && user.role !== role) {
    return <Navigate to={user.role === 'owner' ? '/owner' : '/search'} replace />
  }

  return <Outlet />
}
