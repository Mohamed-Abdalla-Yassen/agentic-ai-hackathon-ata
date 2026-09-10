import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { AMENITIES, amenityLabel } from '../../lib/amenities'
import { formatPrice, pluralize } from '../../lib/format'
import Icon from '../../components/ui/Icon'
import FavoriteButton from '../../components/FavoriteButton'
import { Alert, Badge, Button, Card, EmptyState, Loading } from '../../components/ui/primitives'

const ICON_BY_AMENITY = Object.fromEntries(AMENITIES.map((a) => [a.id, a.icon]))

function SavedCard({ room, onUnsave }) {
  const amenities = room.amenities ?? []
  const thumb = (room.photos ?? [])[0]

  return (
    <Card hover className="result">
      <Link to={`/listings/${room.roomId}`} style={{ color: 'inherit', display: 'block' }}>
        <div className="result__top">
          {thumb && <img className="result__thumb" src={thumb} alt="" loading="lazy" />}

          <div className="result__body">
            <span className="result__name">
              {room.roomName} <span className="result__space">· {room.spaceName}</span>
            </span>

            <div className="meta-row">
              {room.address && (
                <span className="meta">
                  <Icon name="pin" size={15} />
                  {room.address}
                </span>
              )}
              <span className="meta">
                <Icon name="users" size={15} />
                {pluralize(room.capacity, 'seat')}
              </span>
            </div>

            {amenities.length > 0 && (
              <div className="row row--wrap" style={{ gap: 'var(--s-2)' }}>
                {amenities.map((a) => (
                  <Badge key={a} icon={ICON_BY_AMENITY[a]}>
                    {amenityLabel(a)}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <span className="result__price">
            <strong>{formatPrice(room.price)}</strong>
            <small>per {room.price_unit}</small>
          </span>

          <FavoriteButton roomId={room.roomId} favorite onChange={onUnsave} />
        </div>
      </Link>
    </Card>
  )
}

export default function Favorites() {
  const { data, error, loading, reload } = useAsync(() => api.favorites(), [])
  const [rooms, setRooms] = useState([])

  useEffect(() => {
    if (data) setRooms(data)
  }, [data])

  /* Drop the card locally rather than refetching: unsaving from this page
     always means "remove this one", and a full reload would make the row the
     user just clicked flicker before disappearing. */
  function onUnsave(roomId, saved) {
    if (!saved) setRooms((current) => current.filter((r) => r.roomId !== roomId))
  }

  return (
    <div className="container fade-in">
      <div className="page-head">
        <div>
          <span className="eyebrow">Saved</span>
          <h1 style={{ marginTop: 'var(--s-2)' }}>Your favourites</h1>
        </div>
      </div>

      {loading ? (
        <Loading label="Loading your favourites…" />
      ) : error ? (
        <div className="stack">
          <Alert>{error}</Alert>
          <div>
            <Button variant="secondary" onClick={reload}>
              Try again
            </Button>
          </div>
        </div>
      ) : rooms.length === 0 ? (
        <EmptyState
          icon="heart"
          title="Nothing saved yet"
          description="Tap the heart on any room to keep it here for later. Favourites are private to you."
          action={
            <Link to="/search" className="btn btn--primary">
              Find a space
            </Link>
          }
        />
      ) : (
        <div className="stack">
          {rooms.map((room) => (
            <SavedCard key={room.roomId} room={room} onUnsave={onUnsave} />
          ))}
        </div>
      )}
    </div>
  )
}
