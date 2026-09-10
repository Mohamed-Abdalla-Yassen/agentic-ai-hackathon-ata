import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Alert, Button, Card } from '../components/ui/primitives'
import { Field, Input, OptionCard } from '../components/ui/form'

const MIN_PASSWORD = 8

export default function Register() {
  const { register, isAuthed, isOwner } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'booker',
  })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [busy, setBusy] = useState(false)

  if (isAuthed) return <Navigate to={isOwner ? '/owner' : '/search'} replace />

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  function validate() {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Tell us what to call you.'
    if (!form.email.includes('@')) errs.email = 'That does not look like an email.'
    if (form.password.length < MIN_PASSWORD)
      errs.password = `At least ${MIN_PASSWORD} characters.`
    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!validate()) return

    setBusy(true)
    try {
      const user = await register({ ...form, name: form.name.trim() })
      navigate(user.role === 'owner' ? '/owner' : '/search', { replace: true })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="auth fade-in">
      <div className="auth__panel">
        <div className="auth__head">
          <h1>Create your account</h1>
          <p className="muted">Two roles, one platform. Pick the one that fits.</p>
        </div>

        <Card pad>
          <form className="stack stack--lg" onSubmit={onSubmit} noValidate>
            <Alert>{error}</Alert>

            <div className="field">
              <span className="field__label">I want to…</span>
              <div className="row row--wrap" style={{ alignItems: 'stretch' }}>
                <OptionCard
                  selected={form.role === 'booker'}
                  onSelect={() => setForm((f) => ({ ...f, role: 'booker' }))}
                  title="Book a space"
                  description="Search venues and send booking requests."
                />
                <OptionCard
                  selected={form.role === 'owner'}
                  onSelect={() => setForm((f) => ({ ...f, role: 'owner' }))}
                  title="List a space"
                  description="Publish your rooms and reach the right bookers."
                />
              </div>
            </div>

            <Field label="Full name" error={fieldErrors.name} required>
              {(p) => (
                <Input
                  {...p}
                  autoComplete="name"
                  placeholder="Ada Lovelace"
                  value={form.name}
                  onChange={set('name')}
                />
              )}
            </Field>

            <Field label="Email" error={fieldErrors.email} required>
              {(p) => (
                <Input
                  {...p}
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={set('email')}
                />
              )}
            </Field>

            <Field
              label="Password"
              error={fieldErrors.password}
              hint={`At least ${MIN_PASSWORD} characters.`}
              required
            >
              {(p) => (
                <Input
                  {...p}
                  type="password"
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={set('password')}
                />
              )}
            </Field>

            <Button type="submit" block size="lg" loading={busy}>
              {busy ? 'Creating account…' : 'Create account'}
            </Button>
          </form>
        </Card>

        <p className="auth__foot">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
