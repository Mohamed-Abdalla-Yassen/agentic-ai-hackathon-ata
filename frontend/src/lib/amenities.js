// The fixed amenity list from docs/api-contract.md. It has to stay exactly
// in sync with the backend: these strings are both the room-creation values
// and the search filter values.
export const AMENITIES = [
  { id: 'wifi', label: 'Wi-Fi', icon: 'wifi' },
  { id: 'parking', label: 'Parking', icon: 'car' },
  { id: 'whiteboard', label: 'Whiteboard', icon: 'board' },
  { id: 'projector', label: 'Projector', icon: 'projector' },
  { id: 'kitchen', label: 'Kitchen', icon: 'kitchen' },
  { id: 'ac', label: 'Air conditioning', icon: 'ac' },
]

export const AMENITY_IDS = AMENITIES.map((a) => a.id)

const BY_ID = Object.fromEntries(AMENITIES.map((a) => [a.id, a]))

export function amenityLabel(id) {
  return BY_ID[id]?.label ?? id
}
