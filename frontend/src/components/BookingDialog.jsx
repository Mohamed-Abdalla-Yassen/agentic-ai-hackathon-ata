import { useState } from 'react'
import { api } from '../lib/api'
import Modal from './ui/Modal'
import Icon from './ui/Icon'
import { Alert, Button } from './ui/primitives'
import { Field, Input } from './ui/form'

/** `datetime-local` gives "YYYY-MM-DDTHH:mm" in local time; the contract
 *  wants ISO 8601, so widen it through Date. */
function toISO(localValue) {
  return new Date(localValue).toISOString()
}

/** Now + `hoursFromNow`, formatted for a datetime-local input. */
function defaultSlot(hoursFromNow) {
  const d = new Date(Date.now() + hoursFromNow * 3600_000)
  d.setMinutes(0, 0, 0)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`
}

export default function BookingDialog({ open, onClose, room, onBooked }) {
  const [start, setStart] = useState(() => defaultSlot(24))
  const [end, setEnd] = useState(() => defaultSlot(26))
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [busy, setBusy] = useState(false)

  function validate() {
    const errs = {}
    if (!start) errs.start = 'Pick a start time.'
    if (!end) errs.end = 'Pick an end time.'

    if (start && end) {
      const s = new Date(start)
      const e = new Date(end)
      if (e <= s) errs.end = 'End has to be after the start.'
      if (s.getTime() < Date.now()) errs.start = 'Pick a time in the future.'
    }

    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!validate()) return

    setBusy(true)
    try {
      const booking = await api.createBooking({
        roomId: room.id,
        requested_start: toISO(start),
        requested_end: toISO(end),
      })
      onBooked(booking)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={`Request ${room.name}`}>
      <form className="stack stack--lg" onSubmit={onSubmit} noValidate>
        <Alert>{error}</Alert>

        <Field label="From" error={fieldErrors.start} required>
          {(p) => (
            <Input
              {...p}
              type="datetime-local"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          )}
        </Field>

        <Field label="Until" error={fieldErrors.end} required>
          {(p) => (
            <Input
              {...p}
              type="datetime-local"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          )}
        </Field>

        <p className="note">
          <Icon name="alert" size={15} />
          This sends a request, not a confirmed booking. The owner follows up
          using the contact details on the listing.
        </p>

        <div className="form-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={busy}>
            {busy ? 'Sending…' : 'Send request'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
