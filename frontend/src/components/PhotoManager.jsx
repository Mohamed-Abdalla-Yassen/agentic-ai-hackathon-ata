import { useRef, useState } from 'react'
import { api } from '../lib/api'
import Icon from './ui/Icon'
import { Alert, IconButton, Spinner } from './ui/primitives'

/** Mirrors the backend allowlist — anything else is refused server-side anyway,
 *  so match it here to fail fast instead of after a round trip. */
const ACCEPT = 'image/jpeg,image/png,image/webp'

/**
 * Photo strip for one room, owner side: shows what is uploaded, adds more,
 * removes one.
 *
 * Photos are held in local state rather than refetched after every change —
 * the server response for an upload already carries the new photo, and a
 * reload of the whole dashboard to add one image reads as a stutter.
 */
export default function PhotoManager({ roomId, photos: initial = [] }) {
  const [photos, setPhotos] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  async function onPick(e) {
    const files = Array.from(e.target.files ?? [])
    // Let the same file be picked again after a failure.
    e.target.value = ''
    if (files.length === 0) return

    setError('')
    setBusy(true)

    // Sequential rather than parallel: uploads are rate limited per owner, and
    // a burst of them is exactly the shape that trips the limit.
    for (const file of files) {
      try {
        const photo = await api.uploadPhoto(roomId, file)
        setPhotos((current) => [...current, photo])
      } catch (err) {
        setError(`${file.name}: ${err.message}`)
        break
      }
    }

    setBusy(false)
  }

  async function onRemove(photo) {
    setError('')
    try {
      await api.deletePhoto(photo.id)
      setPhotos((current) => current.filter((p) => p.id !== photo.id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="photo-manager">
      <div className="photo-manager__head">
        <span className="photo-manager__label">
          <Icon name="image" size={14} />
          Photos
        </span>
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          onClick={() => inputRef.current?.click()}
          disabled={busy}
        >
          {busy ? <Spinner size={14} /> : <Icon name="plus" size={14} />}
          {busy ? 'Uploading…' : 'Add photos'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          multiple
          hidden
          onChange={onPick}
        />
      </div>

      {error && <Alert>{error}</Alert>}

      {photos.length > 0 ? (
        <div className="photo-strip">
          {photos.map((photo) => (
            <div key={photo.id} className="photo-thumb">
              <img src={photo.url} alt="" loading="lazy" />
              <IconButton
                icon="x"
                label="Remove photo"
                size={14}
                className="photo-thumb__remove"
                onClick={() => onRemove(photo)}
              />
            </div>
          ))}
        </div>
      ) : (
        <p className="photo-manager__empty">
          No photos yet. Bookers skim listings visually — a room with a photo
          gets looked at.
        </p>
      )}
    </div>
  )
}
