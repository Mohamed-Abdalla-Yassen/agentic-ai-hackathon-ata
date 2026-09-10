import { useId } from 'react'
import Icon from './Icon'
import { AMENITIES } from '../../lib/amenities'

/* ----------------------------------------------------------------- Field */

/**
 * Wraps a control with a label, optional hint and error. Passes a generated
 * id down via render-prop so the label always points at the real input.
 */
export function Field({ label, hint, error, required, children }) {
  const id = useId()
  return (
    <div className="field">
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
          {required && <span aria-hidden="true" style={{ color: 'var(--danger)' }}> *</span>}
        </label>
      )}
      {children({ id, 'aria-invalid': error ? 'true' : undefined })}
      {error ? (
        <span className="field__error">{error}</span>
      ) : hint ? (
        <span className="field__hint">{hint}</span>
      ) : null}
    </div>
  )
}

/* ---------------------------------------------------------------- Inputs */

export function Input({ className = '', ...rest }) {
  return <input className={`input ${className}`.trim()} {...rest} />
}

export function Textarea({ className = '', ...rest }) {
  return <textarea className={`textarea ${className}`.trim()} {...rest} />
}

export function Select({ options = [], className = '', ...rest }) {
  return (
    <select className={`select ${className}`.trim()} {...rest}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  )
}

/* ---------------------------------------------------------------- Choice */

/** A pill-shaped checkbox. Used for the fixed amenity list. */
export function Choice({ checked, onChange, icon, children }) {
  return (
    <label className={`choice ${checked ? 'choice--on' : ''}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="choice__tick" aria-hidden="true">
        <Icon name="check" size={11} strokeWidth={2.6} />
      </span>
      {icon && <Icon name={icon} size={14} />}
      {children}
    </label>
  )
}

/**
 * The fixed amenity checkboxes from the API contract. `value` is an array of
 * amenity ids; emits a new array on every toggle.
 */
export function AmenityPicker({ value = [], onChange }) {
  const toggle = (id, on) =>
    onChange(on ? [...value, id] : value.filter((a) => a !== id))

  return (
    <div className="choice-group">
      {AMENITIES.map((a) => (
        <Choice
          key={a.id}
          icon={a.icon}
          checked={value.includes(a.id)}
          onChange={(on) => toggle(a.id, on)}
        >
          {a.label}
        </Choice>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------ OptionCard */

/** Large selectable panel — used for the owner/booker role picker. */
export function OptionCard({ selected, onSelect, title, description }) {
  return (
    <button
      type="button"
      className={`option-card ${selected ? 'option-card--on' : ''}`}
      onClick={onSelect}
      aria-pressed={selected}
    >
      <span className="option-card__title">{title}</span>
      <span className="option-card__desc">{description}</span>
    </button>
  )
}
