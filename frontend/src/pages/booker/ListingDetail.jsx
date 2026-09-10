import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { AMENITIES, amenityLabel } from '../../lib/amenities'
import { formatPrice, pluralize } from '../../lib/format'
import BackLink from '../../components/BackLink'
import BookingDialog from '../../components/BookingDialog'
import Icon from '../../components/ui/Icon'
import { Alert, Badge, Button, Card, Loading } from '../../components/ui/primitives'

const ICON_BY_AMENITY = Object.fromEntries(AMENITIES.map((a) => [a.id, a.icon]))

/**
 * The contract says this endpoint returns "full Room + parent Space details"
 * without pinning the shape, so accept either a nested `space` object or the
 * space fields flattened onto the room.
 */
function normalize(raw) {
  if (!raw) return null
  const space = raw.space ?? {}
  return {
    id: raw.id ?? raw.roomId,
    name: raw.name ?? raw.roomName,
    capacity: raw.capacity,
    price: raw.price,
    price_unit: raw.price_unit,
    amenities: raw.amenities ?? [],
    notes: raw.notes,
    spaceName: space.name ?? raw.spaceName,
    address: space.address ?? raw.address,
    contactInfo: space.contact_info ?? raw.contact_info,
    spaceDescription: space.description ?? raw.description,
  }
}

export default function ListingDetail() {
  const { roomId } = useParams()
  const navigate = useNavigate()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [booking, setBooking] = useState(null)

  const { data, error, loading, reload } = useAsync(
    () => api.listing(roomId),
    [roomId]
  )

  const room = normalize(data)

  if (loading) {
    return (
      <div className="container">
        <Loading label="Loading listing…" />
      </div>
    )
  }

  if (error || !room) {
    return (
      <div className="container container--narrow stack">
        <BackLink to="/search">Back to search</BackLink>
        <Alert>{error || 'That listing could not be found.'}</Alert>
        <div className="row">
          <Button variant="secondary" onClick={reload}>
            Try again
          </Button>
          <Button variant="ghost" onClick={() => navigate('/search')}>
            Back to search
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container fade-in">
      <BackLink to="/search">Back to search</BackLink>

      <div className="detail-layout">
        <div>
          {/* No photo uploads in scope — a tinted panel beats a broken image. */}
          <div className="detail-hero">
            <Icon name="door" size={34} />
          </div>

          <div className="stack stack--sm" style={{ marginBottom: 'var(--s-6)' }}>
            <span className="eyebrow">{room.spaceName}</span>
            <h1 className="detail-title">{room.name}</h1>
            {room.address && (
              <span className="meta muted">
                <Icon name="pin" size={16} />
                {room.address}
              </span>
            )}
          </div>

          <div className="spec-grid" style={{ marginBottom: 'var(--s-8)' }}>
            <div className="spec">
              <span className="spec__label">Capacity</span>
              <span className="spec__value">{pluralize(room.capacity, 'seat')}</span>
            </div>
            <div className="spec">
              <span className="spec__label">Price</span>
              <span className="spec__value">
                {formatPrice(room.price)}
                <small
                  style={{ fontWeight: 400, color: 'var(--text-subtle)' }}
                >
                  {' '}
                  /{room.price_unit}
                </small>
              </span>
            </div>
            <div className="spec">
              <span className="spec__label">Amenities</span>
              <span className="spec__value">{room.amenities.length}</span>
            </div>
          </div>

          {room.amenities.length > 0 && (
            <section style={{ marginBottom: 'var(--s-8)' }}>
              <h2 className="section-title">What is included</h2>
              <div className="row row--wrap" style={{ gap: 'var(--s-2)' }}>
                {room.amenities.map((a) => (
                  <Badge key={a} icon={ICON_BY_AMENITY[a]}>
                    {amenityLabel(a)}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          {room.notes && (
            <section style={{ marginBottom: 'var(--s-8)' }}>
              <h2 className="section-title">Notes from the owner</h2>
              <p className="note">
                <Icon name="tag" size={15} />
                {room.notes}
              </p>
            </section>
          )}

          {room.spaceDescription && (
            <section>
              <h2 className="section-title">About {room.spaceName}</h2>
              <p className="muted" style={{ maxWidth: '68ch' }}>
                {room.spaceDescription}
              </p>
            </section>
          )}
        </div>

        <Card pad className="booking-panel">
          {booking ? (
            <div className="stack">
              <Alert variant="success">
                Request sent — the owner will be in touch.
              </Alert>
              <div className="stack stack--sm">
                <span className="field__hint">
                  Status: <strong>{booking.status}</strong>
                </span>
                {room.contactInfo && (
                  <span className="field__hint">
                    Chase it up directly: {room.contactInfo}
                  </span>
                )}
              </div>
              <Button variant="secondary" block onClick={() => navigate('/search')}>
                Back to search
              </Button>
            </div>
          ) : (
            <div className="stack">
              <div>
                <span className="result__price" style={{ textAlign: 'left' }}>
                  <strong style={{ fontSize: 'var(--text-2xl)' }}>
                    {formatPrice(room.price)}
                  </strong>
                  <small>per {room.price_unit}</small>
                </span>
              </div>

              <Button block size="lg" onClick={() => setDialogOpen(true)}>
                Request to book
              </Button>

              {room.contactInfo && (
                <div className="stack stack--sm">
                  <span className="eyebrow">Contact</span>
                  <span className="meta muted">
                    <Icon name="mail" size={15} />
                    {room.contactInfo}
                  </span>
                </div>
              )}

              <p className="field__hint">
                Requests are not confirmed bookings — no payment is taken.
              </p>
            </div>
          )}
        </Card>
      </div>

      <BookingDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        room={room}
        onBooked={(b) => {
          setBooking(b)
          setDialogOpen(false)
        }}
      />
    </div>
  )
}
