import { Outlet } from 'react-router-dom'
import TopNav from './TopNav'

export default function Shell() {
  return (
    <div className="app-shell">
      <TopNav />
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="container footer__inner">
          <span>SpaceMatch — AI-matched workspaces & venues</span>
          <span>Hackathon build</span>
        </div>
      </footer>
    </div>
  )
}
