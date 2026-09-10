import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import BackLink from '../../components/BackLink'
import Icon from '../../components/ui/Icon'
import { Alert, Button, Card } from '../../components/ui/primitives'
import { AmenityPicker, Field, Input, Select, Textarea } from '../../components/ui/form'

const PRICE_UNITS = [
  { value: 'hour', label: 'per hour' },
  { value: 'day', label: 'per day' },
]

export default function NewRoom() {
  const { spaceId } = useParams()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    capacity: '',
    price: '',
    price_unit: 'hour',
    amenities: [],
    notes: '',
  })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [busy, setBusy] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  function validate() {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Give the room a name.'

    const capacity = Number(form.capacity)
    if (!form.capacity || !Number.isInteger(capacity) || capacity < 1)
      errs.capacity = 'Whole number, at least 1.'

    const price = Number(form.price)
    if (form.price === '' || Number.isNaN(price) || price < 0)
      errs.price = 'Enter a price (0 if free).'

    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!validate()) return

    setBusy(true)
    try {
      await api.createRoom(spaceId, {
        name: form.name.trim(),
        capacity: Number(form.capacity),
        price: Number(form.price),
        price_unit: form.price_unit,
        amenities: form.amenities,
        notes: form.notes.trim(),
      })
      navigate('/owner', { replace: true })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="container form-page fade-in">
      <BackLink to="/owner">Your spaces</BackLink>

      <div className="stack stack--sm" style={{ marginBottom: 'var(--s-6)' }}>
        <span className="eyebrow">Step 2 of 2</span>
        <h1 style={{ fontSize: 'var(--text-2xl)' }}>Add a room</h1>
        <p className="muted">
          Capacity, price and amenities are what search filters on — get these
          right and the room shows up for the right people.
        </p>
      </div>

      <Card pad>
        <form className="form-section" onSubmit={onSubmit} noValidate>
          <Alert>{error}</Alert>

          <Field label="Room name" error={fieldErrors.name} required>
            {(p) => (
              <Input
                {...p}
                placeholder="The Long Room"
                value={form.name}
                onChange={set('name')}
              />
            )}
          </Field>

          <div className="field-grid">
            <Field label="Capacity" error={fieldErrors.capacity} required>
              {(p) => (
                <Input
                  {...p}
                  type="number"
                  min="1"
                  step="1"
                  inputMode="numeric"
                  placeholder="12"
                  value={form.capacity}
                  onChange={set('capacity')}
                />
              )}
            </Field>

            <Field label="Price" error={fieldErrors.price} required>
              {(p) => (
                <Input
                  {...p}
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  placeholder="45"
                  value={form.price}
                  onChange={set('price')}
                />
              )}
            </Field>

            <Field label="Charged">
              {(p) => (
                <Select
                  {...p}
                  options={PRICE_UNITS}
                  value={form.price_unit}
                  onChange={set('price_unit')}
                />
              )}
            </Field>
          </div>

          <div className="field">
            <span className="field__label">Amenities</span>
            <AmenityPicker
              value={form.amenities}
              onChange={(amenities) => setForm((f) => ({ ...f, amenities }))}
            />
            <span className="field__hint">
              A fixed list, shared with search — only these are filterable.
            </span>
          </div>

          <Field
            label="Notes"
            hint="Everything that does not fit a checkbox. This text is read by the AI when ranking matches, so it is worth writing well."
          >
            {(p) => (
              <Textarea
                {...p}
                placeholder="Gets warm afternoon sun, so good for photography but bring blinds for screen work. Street noise drops off after 6pm."
                value={form.notes}
                onChange={set('notes')}
              />
            )}
          </Field>

          <p className="note note--ai">
            <Icon name="sparkles" size={15} />
            Notes are the single biggest lever on match quality — the structured
            fields decide whether a room is eligible, the notes decide where it
            ranks.
          </p>

          <div className="form-actions">
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/owner')}
            >
              Cancel
            </Button>
            <Button type="submit" loading={busy}>
              {busy ? 'Saving…' : 'Save room'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
