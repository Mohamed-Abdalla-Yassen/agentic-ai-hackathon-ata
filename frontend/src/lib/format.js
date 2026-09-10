export function formatPrice(price, unit) {
  if (price === null || price === undefined) return '—'
  const n = Number(price)
  const amount = Number.isInteger(n)
    ? `$${n}`
    : `$${n.toFixed(2)}`
  return unit ? `${amount}/${unit}` : amount
}

export function initials(name) {
  if (!name) return '?'
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')
}

export function pluralize(n, singular, plural = `${singular}s`) {
  return `${n} ${n === 1 ? singular : plural}`
}
