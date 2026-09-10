import { useEffect, useRef } from 'react'
import { IconButton } from './primitives'

/**
 * Minimal accessible dialog: Escape to close, click-outside to close,
 * focus moved in on open and body scroll locked while open.
 */
export default function Modal({ open, onClose, title, children }) {
  const panelRef = useRef(null)

  useEffect(() => {
    if (!open) return

    function onKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', onKeyDown)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    panelRef.current?.focus()

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        // Only close on a press that starts on the backdrop itself, so a
        // drag-select inside the panel that ends outside doesn't dismiss it.
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        ref={panelRef}
      >
        <div className="modal__head">
          <span className="modal__title">{title}</span>
          <IconButton icon="x" label="Close" onClick={onClose} />
        </div>
        <div className="modal__body">{children}</div>
      </div>
    </div>
  )
}
