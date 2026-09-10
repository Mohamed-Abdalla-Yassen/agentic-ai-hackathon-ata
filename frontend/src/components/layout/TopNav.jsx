import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import { initials } from '../../lib/format'
import ThemeToggle from '../ThemeToggle'
import { Button, IconButton } from '../ui/primitives'

export default function TopNav() {
  const { user, isAuthed, isOwner, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="nav">
      <div className="container nav__inner">
        <Link to="/" className="brand">
          <span className="brand__mark">S</span>
          SpaceMatch
        </Link>

        <nav className="nav__links">
          {isAuthed &&
            (isOwner ? (
              <NavLink
                to="/owner"
                className={({ isActive }) =>
                  `nav__link ${isActive ? 'nav__link--active' : ''}`
                }
              >
                My spaces
              </NavLink>
            ) : (
              <NavLink
                to="/search"
                className={({ isActive }) =>
                  `nav__link ${isActive ? 'nav__link--active' : ''}`
                }
              >
                Find a space
              </NavLink>
            ))}
        </nav>

        <span className="spacer" />

        <ThemeToggle />

        {isAuthed ? (
          <div className="nav__user">
            <span className="avatar" title={`${user.name} · ${user.role}`}>
              {initials(user.name)}
            </span>
            <IconButton icon="logout" label="Sign out" onClick={handleLogout} />
          </div>
        ) : (
          <div className="row" style={{ gap: 'var(--s-2)' }}>
            <Link to="/login" className="nav__link">
              Sign in
            </Link>
            <Button size="sm" onClick={() => navigate('/register')}>
              Get started
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
