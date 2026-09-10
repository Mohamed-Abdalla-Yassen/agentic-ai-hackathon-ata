import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { useAuth } from '../../lib/auth'
import { pluralize } from '../../lib/format'
import Icon from '../../components/ui/Icon'
import RoomRow from '../../components/RoomRow'
import { Alert, Button, Card, EmptyState, Loading } from '../../components/ui/primitives'

function SpaceCard({ space }) {
  const rooms = space.rooms ?? []

  return (
    <Card className="space-card">
      <div className="space-card__head">
        <div className="stack stack--sm" style={{ minWidth: 0 }}>
          <span className="space-card__title">{space.name}</span>
          <div className="meta-row">
            {space.address && (
              <span className="meta">
                <Icon name="pin" size={15} />
                {space.address}
              </span>
            )}
            {space.contact_info && (
              <span className="meta">
                <Icon name="mail" size={15} />
                {space.contact_info}
              </span>
            )}
            <span className="meta">
              <Icon name="door" size={15} />
              {pluralize(rooms.length, 'room')}
            </span>
          </div>
          {space.description && (
            <p className="muted" style={{ fontSize: 'var(--text-base)', maxWidth: '68ch' }}>
              {space.description}
            </p>
          )}
        </div>

        <Link
          to={`/owner/spaces/${space.id}/rooms/new`}
          className="btn btn--secondary btn--sm"
        >
          <Icon name="plus" size={15} />
          Add room
        </Link>
      </div>

      {rooms.length > 0 ? (
        <div className="room-list">
          {rooms.map((room) => (
            <RoomRow key={room.id} room={room} />
          ))}
        </div>
      ) : (
        <p className="room-empty">
          No rooms yet — a space needs at least one room before bookers can find it.
        </p>
      )}
    </Card>
  )
}

export default function OwnerDashboard() {
  const { user } = useAuth()
  const { data, error, loading, reload } = useAsync(() => api.mySpaces(), [])

  const spaces = data ?? []

  return (
    <div className="container fade-in">
      <div className="page-head">
        <div>
          <span className="eyebrow">Owner</span>
          <h1 style={{ marginTop: 'var(--s-2)' }}>
            {user.name.split(' ')[0]}&rsquo;s spaces
          </h1>
        </div>
        <Link to="/owner/spaces/new" className="btn btn--primary">
          <Icon name="plus" size={16} />
          Add a space
        </Link>
      </div>

      {loading ? (
        <Loading label="Loading your spaces…" />
      ) : error ? (
        <div className="stack">
          <Alert>{error}</Alert>
          <div>
            <Button variant="secondary" onClick={reload}>
              Try again
            </Button>
          </div>
        </div>
      ) : spaces.length === 0 ? (
        <EmptyState
          icon="building"
          title="No spaces yet"
          description="Add your first space, then give it rooms with their capacity, price and amenities. Bookers search against exactly those fields."
          action={
            <Link to="/owner/spaces/new" className="btn btn--primary">
              Add your first space
            </Link>
          }
        />
      ) : (
        <div>
          {spaces.map((space) => (
            <SpaceCard key={space.id} space={space} />
          ))}
        </div>
      )}
    </div>
  )
}
