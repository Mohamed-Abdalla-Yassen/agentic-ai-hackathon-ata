import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import Icon from '../components/ui/Icon'
import { Badge } from '../components/ui/primitives'

const STEPS = [
  {
    n: '01',
    title: 'Filter on what is measurable',
    body: 'Location, capacity, price ceiling and the amenities you actually need — matched exactly, in the database, before any AI is involved.',
  },
  {
    n: '02',
    title: 'Describe what is not',
    body: '“Quiet enough for client calls, and we will need the projector after six.” The things that never fit into a checkbox go in a sentence.',
  },
  {
    n: '03',
    title: 'Get a ranked shortlist',
    body: 'The shortlist is re-ordered against your note, and every result arrives with one line explaining why it earned its place.',
  },
]

export default function Landing() {
  const { isAuthed, isOwner } = useAuth()

  // Signed-in users have a home; the marketing page is not it.
  if (isAuthed) return <Navigate to={isOwner ? '/owner' : '/search'} replace />

  return (
    <div className="fade-in">
      <section className="container hero">
        <Badge variant="ai" icon="sparkles">
          AI-ranked matching
        </Badge>
        <h1 className="display hero__title" style={{ marginTop: 'var(--s-5)' }}>
          Find the room that <em>fits</em>.
        </h1>
        <p className="hero__sub">
          Every workspace listing looks the same on paper. SpaceMatch reads the
          detail behind the filters — the notes, the quirks, the way you plan to
          use the room — and ranks what is genuinely right for you.
        </p>
        <div className="hero__cta">
          <Link to="/register" className="btn btn--primary btn--lg">
            Get started
            <Icon name="arrowRight" size={16} />
          </Link>
          <Link to="/login" className="btn btn--secondary btn--lg">
            Sign in
          </Link>
        </div>
      </section>

      <section className="container">
        <div className="feature-grid">
          {STEPS.map((s) => (
            <article key={s.n} className="feature">
              <span className="feature__num">{s.n}</span>
              <h2 className="feature__title">{s.title}</h2>
              <p className="feature__body">{s.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="container" style={{ paddingBottom: 'var(--s-16)' }}>
        <div
          className="card card--pad"
          style={{ display: 'flex', gap: 'var(--s-6)', flexWrap: 'wrap', alignItems: 'center' }}
        >
          <div style={{ flex: '1 1 320px' }}>
            <span className="eyebrow">For venue owners</span>
            <h2 style={{ fontSize: 'var(--text-xl)', margin: 'var(--s-2) 0' }}>
              List a space in about a minute
            </h2>
            <p className="muted" style={{ maxWidth: '52ch' }}>
              Add your rooms with their real attributes and a free-text note about
              how the space actually behaves. That note is what puts you in front
              of the right bookers.
            </p>
          </div>
          <Link to="/register" className="btn btn--secondary btn--lg">
            List your space
          </Link>
        </div>
      </section>
    </div>
  )
}
