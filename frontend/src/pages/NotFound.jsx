import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container container--narrow fade-in" style={{ textAlign: 'center', paddingBlock: 'var(--s-20)' }}>
      <p className="eyebrow">Error 404</p>
      <h1 className="display" style={{ fontSize: 'var(--text-4xl)', margin: 'var(--s-3) 0' }}>
        Nothing here
      </h1>
      <p className="muted" style={{ marginBottom: 'var(--s-6)' }}>
        That page does not exist — or it moved somewhere better.
      </p>
      <Link to="/" className="btn btn--secondary">
        Back to home
      </Link>
    </div>
  )
}
