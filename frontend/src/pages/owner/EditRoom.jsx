import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import BackLink from '../../components/BackLink'
import Icon from '../../components/ui/Icon'
import { Alert, Button, Card, Loading } from '../../components/ui/primitives'
import { AmenityPicker, Field, Input, Select, Textarea } from '../../components/ui/form'

const PRICE_UNITS = [
  { value: 'hour', label: 'per hour' },
  { value: 'day', label: 'per day' },
]

/**
 * Edit a published room.
 *
 * Deliberately close to NewRoom in layout so the fields sit where an owner
 * already expects them, but it sends a PATCH with only what actually changed —
 * an owner fixing a price should not rewrite the notes they carefully wrote.
 */
export default function EditRoom() {
  const { roomId } = useParams()
  const navigate = useNavigate()

  const { data: room, error: loadError, loading } = useAsync(
    () => api.room(roomId),
    [roomId]
  )

  const [form, setForm] = useState(null)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [busy, setBusy] = useState(false)

  // Populate the form once the room arrives. Keeping the loaded room around
  // separately is what lets the save compare against the stored values.
  useEffect(() => {
    if (!room) return
    setForm({
      name: room.name ?? '',
      capacity: String(room.capacity ?? ''),
      price: String(room.price ?? ''),
      price_unit: room.price_unit ?? 'hour',
      amenities: room.amenities ?? [],
      notes: room.notes ?? '',
    })
  }, [room])

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  function validate() {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Give the room a name.'

    const capacity = Number(form.capacity)
    if (!form.capacity || !Number.isInteger(capacity) || capacity < 1)
      errs.capacity = 'Whole number, at least 1.'

    const price = Number(form.price)
    if (form.price === '' || Number.isNaN(price) || price <= 0)
      errs.price = 'Enter a price above zero.'

    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  /** Only the fields that actually differ from what was loaded. */
  function changedFields() {
    const next = {
      name: form.name.trim(),
      capacity: Number(form.capacity),
      price: Number(form.price),
      price_unit: form.price_unit,
      amenities: form.amenities,
      notes: form.notes.trim(),
    }
    const changes = {}
    for (const [key, value] of Object.entries(next)) {
      const before = room[key]
      const same = Array.isArray(value)
        ? value.length === before.length && value.every((v) => before.includes(v))
        : value === before
      if (!same) changes[key] = value
    }
    return changes
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!validate()) return

    const changes = changedFields()
    if (Object.keys(changes).length === 0) {
      navigate('/owner', { replace: true })
      return
    }

    setBusy(true)
    try {
      await api.updateRoom(roomId, changes)
      navigate('/owner', { replace: true })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  if (loading || (!form && !loadError)) {
    return (
      <div className="container">
        <Loading label="Loading room…" />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="container container--narrow stack">
        <BackLink to="/owner">Your spaces</BackLink>
        <Alert>{loadError}</Alert>
      </div>
    )
  }

  return (
    <div className="container form-page fade-in">
      <BackLink to="/owner">Your spaces</BackLink>

      <div className="stack stack--sm" style={{ marginBottom: 'var(--s-6)' }}>
        <span className="eyebrow">Edit room</span>
        <h1 style={{ fontSize: 'var(--text-2xl)' }}>{room.name}</h1>
        <p className="muted">
          Changes go live immediately — bookers see the updated room the next
          time they search.
        </p>
      </div>

      <Card pad>
        <form className="form-section" onSubmit={onSubmit} noValidate>
          <Alert>{error}</Alert>

          <Field label="Room name" error={fieldErrors.name} required>
            {(p) => <Input {...p} value={form.name} onChange={set('name')} />}
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
          </div>

          <Field
            label="Notes"
            hint="Read by the AI when ranking matches, so it is worth keeping current."
          >
            {(p) => (
              <Textarea {...p} value={form.notes} onChange={set('notes')} />
            )}
          </Field>

          <p className="note">
            <Icon name="image" size={15} />
            Photos are managed from your spaces list, under this room.
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
              {busy ? 'Saving…' : 'Save changes'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
