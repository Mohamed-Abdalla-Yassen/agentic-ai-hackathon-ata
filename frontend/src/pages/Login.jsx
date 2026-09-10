import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Alert, Button, Card } from '../components/ui/primitives'
import { Field, Input } from '../components/ui/form'

export default function Login() {
  const { login, isAuthed, isOwner } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (isAuthed) return <Navigate to={isOwner ? '/owner' : '/search'} replace />

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const user = await login(form)
      const fallback = user.role === 'owner' ? '/owner' : '/search'
      navigate(location.state?.from || fallback, { replace: true })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="auth fade-in">
      <div className="auth__panel">
        <div className="auth__head">
          <h1>Welcome back</h1>
          <p className="muted">Sign in to keep matching spaces.</p>
        </div>

        <Card pad>
          <form className="stack stack--lg" onSubmit={onSubmit} noValidate>
            <Alert>{error}</Alert>

            <Field label="Email" required>
              {(p) => (
                <Input
                  {...p}
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={set('email')}
                  required
                />
              )}
            </Field>

            <Field label="Password" required>
              {(p) => (
                <Input
                  {...p}
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={set('password')}
                  required
                />
              )}
            </Field>

            <Button type="submit" block size="lg" loading={busy}>
              {busy ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </Card>

        <p className="auth__foot">
          New to SpaceMatch? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
