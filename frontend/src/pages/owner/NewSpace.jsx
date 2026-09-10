import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'
import BackLink from '../../components/BackLink'
import { Alert, Button, Card } from '../../components/ui/primitives'
import { Field, Input, Textarea } from '../../components/ui/form'

export default function NewSpace() {
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    address: '',
    contact_info: '',
    description: '',
  })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [busy, setBusy] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  function validate() {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Give the space a name.'
    if (!form.address.trim()) errs.address = 'Bookers filter on location text.'
    if (!form.contact_info.trim())
      errs.contact_info = 'Bookers need a way to reach you.'
    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!validate()) return

    setBusy(true)
    try {
      const space = await api.createSpace({
        name: form.name.trim(),
        address: form.address.trim(),
        contact_info: form.contact_info.trim(),
        description: form.description.trim(),
      })
      // A space with no rooms is invisible to search, so go straight to
      // adding the first room rather than back to an empty card.
      navigate(`/owner/spaces/${space.id}/rooms/new`, { replace: true })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="container form-page fade-in">
      <BackLink to="/owner">Your spaces</BackLink>

      <div className="stack stack--sm" style={{ marginBottom: 'var(--s-6)' }}>
        <span className="eyebrow">Step 1 of 2</span>
        <h1 style={{ fontSize: 'var(--text-2xl)' }}>Add a space</h1>
        <p className="muted">
          The building or venue. You will add its individual rooms next.
        </p>
      </div>

      <Card pad>
        <form className="form-section" onSubmit={onSubmit} noValidate>
          <Alert>{error}</Alert>

          <Field label="Space name" error={fieldErrors.name} required>
            {(p) => (
              <Input
                {...p}
                placeholder="Northside Creative Hub"
                value={form.name}
                onChange={set('name')}
              />
            )}
          </Field>

          <Field
            label="Address"
            error={fieldErrors.address}
            hint="Plain text — search matches on substrings, so include the city."
            required
          >
            {(p) => (
              <Input
                {...p}
                placeholder="42 Mill Lane, Manchester"
                value={form.address}
                onChange={set('address')}
              />
            )}
          </Field>

          <Field
            label="Contact info"
            error={fieldErrors.contact_info}
            hint="Phone or email — shown to bookers on the listing."
            required
          >
            {(p) => (
              <Input
                {...p}
                placeholder="bookings@northside.co / +44 161 000 0000"
                value={form.contact_info}
                onChange={set('contact_info')}
              />
            )}
          </Field>

          <Field
            label="Description"
            hint="What the place is like overall. Optional."
          >
            {(p) => (
              <Textarea
                {...p}
                placeholder="A converted mill with six meeting rooms, natural light throughout and a café on the ground floor."
                value={form.description}
                onChange={set('description')}
              />
            )}
          </Field>

          <div className="form-actions">
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/owner')}
            >
              Cancel
            </Button>
            <Button type="submit" loading={busy}>
              {busy ? 'Saving…' : 'Save and add a room'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
