import { useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { initials } from '../lib/format'
import Icon from '../components/ui/Icon'
import { Alert, Badge, Button, Card } from '../components/ui/primitives'
import { Field, Input } from '../components/ui/form'

const MIN_PASSWORD = 8

/**
 * Manage your own account.
 *
 * Split into two forms on purpose. Changing a display name and changing the
 * credentials you sign in with are different acts with different stakes, and
 * the second needs the current password — folding them together would demand a
 * password from someone who only wanted to fix a typo in their name.
 */
export default function Profile() {
  const { user, updateUser, logout } = useAuth()

  const [name, setName] = useState(user.name)
  const [nameBusy, setNameBusy] = useState(false)
  const [nameNote, setNameNote] = useState('')
  const [nameError, setNameError] = useState('')

  const [creds, setCreds] = useState({
    email: user.email,
    password: '',
    confirm: '',
    current_password: '',
  })
  const [credsBusy, setCredsBusy] = useState(false)
  const [credsNote, setCredsNote] = useState('')
  const [credsError, setCredsError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})

  const setCred = (key) => (e) =>
    setCreds((c) => ({ ...c, [key]: e.target.value }))

  async function saveName(e) {
    e.preventDefault()
    setNameError('')
    setNameNote('')

    const trimmed = name.trim()
    if (!trimmed) return setNameError('Your name cannot be empty.')
    if (trimmed === user.name) return setNameNote('That is already your name.')

    setNameBusy(true)
    try {
      updateUser(await api.updateProfile({ name: trimmed }))
      setNameNote('Name updated.')
    } catch (err) {
      setNameError(err.message)
    } finally {
      setNameBusy(false)
    }
  }

  async function saveCreds(e) {
    e.preventDefault()
    setCredsError('')
    setCredsNote('')

    const errs = {}
    const emailChanged = creds.email.trim() !== user.email
    const wantsNewPassword = creds.password.length > 0

    if (!creds.email.trim()) errs.email = 'Enter an email address.'
    if (wantsNewPassword && creds.password.length < MIN_PASSWORD)
      errs.password = `At least ${MIN_PASSWORD} characters.`
    if (wantsNewPassword && creds.password !== creds.confirm)
      errs.confirm = 'The two passwords do not match.'
    if ((emailChanged || wantsNewPassword) && !creds.current_password)
      errs.current_password = 'Required to change your email or password.'

    setFieldErrors(errs)
    if (Object.keys(errs).length > 0) return

    if (!emailChanged && !wantsNewPassword) {
      setCredsNote('Nothing to change.')
      return
    }

    const changes = { current_password: creds.current_password }
    if (emailChanged) changes.email = creds.email.trim()
    if (wantsNewPassword) changes.password = creds.password

    setCredsBusy(true)
    try {
      updateUser(await api.updateProfile(changes))
      setCreds((c) => ({ ...c, password: '', confirm: '', current_password: '' }))
      setCredsNote(
        wantsNewPassword
          ? 'Saved. Your new password is active — existing sessions stay signed in.'
          : 'Saved. Sign in with your new email from now on.'
      )
    } catch (err) {
      setCredsError(err.message)
    } finally {
      setCredsBusy(false)
    }
  }

  return (
    <div className="container form-page fade-in">
      <div className="stack stack--sm" style={{ marginBottom: 'var(--s-6)' }}>
        <span className="eyebrow">Account</span>
        <h1 style={{ fontSize: 'var(--text-2xl)' }}>Your profile</h1>
      </div>

      <Card pad className="profile-head">
        <span className="avatar avatar--lg">{initials(user.name)}</span>
        <div className="stack stack--sm" style={{ minWidth: 0 }}>
          <strong style={{ fontSize: 'var(--text-lg)' }}>{user.name}</strong>
          <span className="meta muted">
            <Icon name="mail" size={15} />
            {user.email}
          </span>
        </div>
        <Badge icon={user.role === 'owner' ? 'building' : 'search'}>
          {user.role === 'owner' ? 'Space owner' : 'Booker'}
        </Badge>
      </Card>

      <Card pad style={{ marginTop: 'var(--s-6)' }}>
        <form className="form-section" onSubmit={saveName} noValidate>
          <h2 className="section-title">Display name</h2>
          {nameError && <Alert>{nameError}</Alert>}
          {nameNote && <Alert variant="success">{nameNote}</Alert>}

          <Field label="Name" required>
            {(p) => (
              <Input {...p} value={name} onChange={(e) => setName(e.target.value)} />
            )}
          </Field>

          <div className="form-actions">
            <Button type="submit" loading={nameBusy}>
              {nameBusy ? 'Saving…' : 'Save name'}
            </Button>
          </div>
        </form>
      </Card>

      <Card pad style={{ marginTop: 'var(--s-6)' }}>
        <form className="form-section" onSubmit={saveCreds} noValidate>
          <h2 className="section-title">Sign-in details</h2>
          <p className="muted" style={{ fontSize: 'var(--text-sm)' }}>
            Changing either of these needs your current password, so a
            forgotten open session cannot be used to take the account over.
          </p>

          {credsError && <Alert>{credsError}</Alert>}
          {credsNote && <Alert variant="success">{credsNote}</Alert>}

          <Field label="Email" error={fieldErrors.email} required>
            {(p) => (
              <Input {...p} type="email" value={creds.email} onChange={setCred('email')} />
            )}
          </Field>

          <Field
            label="New password"
            hint={`Leave blank to keep your current password. At least ${MIN_PASSWORD} characters.`}
            error={fieldErrors.password}
          >
            {(p) => (
              <Input
                {...p}
                type="password"
                autoComplete="new-password"
                value={creds.password}
                onChange={setCred('password')}
              />
            )}
          </Field>

          {creds.password.length > 0 && (
            <Field label="Confirm new password" error={fieldErrors.confirm} required>
              {(p) => (
                <Input
                  {...p}
                  type="password"
                  autoComplete="new-password"
                  value={creds.confirm}
                  onChange={setCred('confirm')}
                />
              )}
            </Field>
          )}

          <Field
            label="Current password"
            error={fieldErrors.current_password}
            required
          >
            {(p) => (
              <Input
                {...p}
                type="password"
                autoComplete="current-password"
                value={creds.current_password}
                onChange={setCred('current_password')}
              />
            )}
          </Field>

          <div className="form-actions">
            <Button type="submit" loading={credsBusy}>
              {credsBusy ? 'Saving…' : 'Save sign-in details'}
            </Button>
          </div>
        </form>
      </Card>

      <Card pad style={{ marginTop: 'var(--s-6)' }}>
        <div className="row row--between row--wrap">
          <div className="stack stack--sm">
            <strong>Sign out</strong>
            <span className="muted" style={{ fontSize: 'var(--text-sm)' }}>
              Ends this session on this device.
            </span>
          </div>
          <Button variant="secondary" onClick={logout}>
            Sign out
          </Button>
        </div>
      </Card>
    </div>
  )
}
