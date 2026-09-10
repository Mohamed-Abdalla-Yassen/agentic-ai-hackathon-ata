import { useState } from 'react'
import { api } from '../lib/api'
import Icon from './ui/Icon'

/**
 * Heart toggle for one room.
 *
 * Optimistic: the heart fills the instant it is clicked and rolls back if the
 * request fails. Saving something is a throwaway gesture — waiting on a round
 * trip to acknowledge it feels broken, and the cost of being wrong is one
 * heart briefly in the wrong state.
 *
 * `onChange` lets a parent react (the favourites page removes the card).
 */
export default function FavoriteButton({ roomId, favorite = false, onChange }) {
  const [saved, setSaved] = useState(favorite)
  const [busy, setBusy] = useState(false)

  async function toggle(e) {
    // Result cards are wrapped in a link to the listing; the heart is not
    // navigation, so it must not trigger one.
    e.preventDefault()
    e.stopPropagation()
    if (busy) return

    const next = !saved
    setSaved(next)
    setBusy(true)
    try {
      if (next) await api.addFavorite(roomId)
      else await api.removeFavorite(roomId)
      onChange?.(roomId, next)
    } catch {
      setSaved(!next)
    } finally {
      setBusy(false)
    }
  }

  return (
    <button
      type="button"
      className={`fav-btn ${saved ? 'is-saved' : ''}`}
      onClick={toggle}
      aria-pressed={saved}
      aria-label={saved ? 'Remove from favourites' : 'Save to favourites'}
      title={saved ? 'Saved' : 'Save'}
    >
      <Icon name="heart" size={18} fill={saved ? 'currentColor' : 'none'} />
    </button>
  )
}
