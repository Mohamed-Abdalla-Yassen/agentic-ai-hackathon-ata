import Icon from './Icon'

/* ---------------------------------------------------------------- Button */

export function Button({
  variant = 'primary',
  size,
  block = false,
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...rest
}) {
  const classes = [
    'btn',
    `btn--${variant}`,
    size ? `btn--${size}` : '',
    block ? 'btn--block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <Spinner size={14} /> : icon ? <Icon name={icon} size={16} /> : null}
      {children}
    </button>
  )
}

export function IconButton({ icon, label, size = 18, ...rest }) {
  return (
    <button className="icon-btn" aria-label={label} title={label} {...rest}>
      <Icon name={icon} size={size} />
    </button>
  )
}

/* --------------------------------------------------------------- Spinner */

export function Spinner({ size = 18 }) {
  return (
    <span
      className="spinner"
      style={{ width: size, height: size }}
      role="status"
      aria-label="Loading"
    />
  )
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="center-pad">
      <Spinner size={22} />
      <span className="muted">{label}</span>
    </div>
  )
}

/* ------------------------------------------------------------------ Card */

export function Card({ pad = false, hover = false, className = '', ...rest }) {
  const classes = [
    'card',
    pad ? 'card--pad' : '',
    hover ? 'card--hover' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return <div className={classes} {...rest} />
}

/* ----------------------------------------------------------------- Badge */

export function Badge({ variant, icon, children, className = '' }) {
  const classes = ['badge', variant ? `badge--${variant}` : '', className]
    .filter(Boolean)
    .join(' ')
  return (
    <span className={classes}>
      {icon && <Icon name={icon} size={12} />}
      {children}
    </span>
  )
}

/* ----------------------------------------------------------------- Alert */

export function Alert({ variant = 'error', children }) {
  if (!children) return null
  const icon = variant === 'success' ? 'check' : 'alert'
  return (
    <div className={`alert alert--${variant}`} role={variant === 'error' ? 'alert' : 'status'}>
      <Icon name={icon} size={17} className="alert__icon" />
      <span>{children}</span>
    </div>
  )
}

/* ------------------------------------------------------------ EmptyState */

export function EmptyState({ icon = 'inbox', title, description, action }) {
  return (
    <div className="empty">
      <span className="empty__icon">
        <Icon name={icon} size={20} />
      </span>
      <span className="empty__title">{title}</span>
      {description && <p className="empty__desc">{description}</p>}
      {action}
    </div>
  )
}
