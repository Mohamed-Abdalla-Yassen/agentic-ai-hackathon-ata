import Icon from './ui/Icon'
import { Badge } from './ui/primitives'
import { AMENITIES, amenityLabel } from '../lib/amenities'
import { formatPrice, pluralize } from '../lib/format'

const ICON_BY_AMENITY = Object.fromEntries(AMENITIES.map((a) => [a.id, a.icon]))

/** One room inside an owner's space card. */
export default function RoomRow({ room }) {
  const amenities = room.amenities ?? []

  return (
    <div className="room-row">
      <div className="room-row__main">
        <span className="room-row__name">{room.name}</span>

        <div className="meta-row">
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

        {room.notes && (
          <p className="note">
            <Icon name="tag" size={14} />
            {room.notes}
          </p>
        )}
      </div>

      <span className="room-row__price">
        {formatPrice(room.price)}
        <small>/{room.price_unit}</small>
      </span>
    </div>
  )
}
