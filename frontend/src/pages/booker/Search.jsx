import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { useAsync } from '../../lib/useAsync'
import { AMENITIES, amenityLabel } from '../../lib/amenities'
import { formatPrice, pluralize } from '../../lib/format'
import Icon from '../../components/ui/Icon'
import { Alert, Badge, Card, EmptyState, Button, Loading } from '../../components/ui/primitives'
import { AmenityPicker, Field, Input, Textarea } from '../../components/ui/form'

const ICON_BY_AMENITY = Object.fromEntries(AMENITIES.map((a) => [a.id, a.icon]))

const BLANK = { location: '', capacity: '', priceMax: '', amenities: [], note: '' }

function formFromParams(sp) {
  const amenities = sp.get('amenities')
  return {
    location: sp.get('location') ?? '',
    capacity: sp.get('capacity') ?? '',
    priceMax: sp.get('priceMax') ?? '',
    amenities: amenities ? amenities.split(',').filter(Boolean) : [],
    note: sp.get('note') ?? '',
  }
}

/** Drop blanks so the URL only carries filters that are actually set. */
function paramsFromForm(form) {
  const out = {}
  if (form.location.trim()) out.location = form.location.trim()
  if (form.capacity) out.capacity = form.capacity
  if (form.priceMax) out.priceMax = form.priceMax
  if (form.amenities.length) out.amenities = form.amenities.join(',')
  if (form.note.trim()) out.note = form.note.trim()
  return out
}

function ResultCard({ result, rank, aiRanked }) {
  const amenities = result.amenities ?? []
  const thumb = (result.photos ?? [])[0]

  return (
    <Card hover className="result">
      <Link
        to={`/listings/${result.roomId}`}
        style={{ color: 'inherit', display: 'block' }}
      >
        <div className="result__top">
          <span className={`result__rank ${aiRanked ? 'result__rank--ai' : ''}`}>
            {rank}
          </span>

          {thumb && (
            <img className="result__thumb" src={thumb} alt="" loading="lazy" />
          )}

          <div className="result__body">
            <span className="result__name">
              {result.roomName}{' '}
              <span className="result__space">· {result.spaceName}</span>
            </span>

            <div className="meta-row">
              {result.address && (
                <span className="meta">
                  <Icon name="pin" size={15} />
                  {result.address}
                </span>
              )}
              <span className="meta">
                <Icon name="users" size={15} />
                {pluralize(result.capacity, 'seat')}
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

            {result.reason && (
              <p className="note note--ai">
                <Icon name="sparkles" size={15} />
                {result.reason}
              </p>
            )}
          </div>

          <span className="result__price">
            <strong>{formatPrice(result.price)}</strong>
            <small>per {result.price_unit}</small>
          </span>
        </div>
      </Link>
    </Card>
  )
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [form, setForm] = useState(() => formFromParams(searchParams))

  // Keyed on the serialised URL params, so every committed search — including
  // back/forward navigation — refetches, but typing in the form does not.
  const key = searchParams.toString()
  const { data, error, loading, reload } = useAsync(
    () => api.search(Object.fromEntries(searchParams)),
    [key]
  )

  const results = data?.results ?? []
  const aiRanked = results.some((r) => r.reason)
  const hasFilters = key.length > 0

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  function onSubmit(e) {
    e.preventDefault()
    setSearchParams(paramsFromForm(form))
  }

  function onClear() {
    setForm(BLANK)
    setSearchParams({})
  }

  return (
    <div className="container fade-in">
      <div className="page-head">
        <div>
          <span className="eyebrow">Find a space</span>
          <h1 style={{ marginTop: 'var(--s-2)' }}>Search</h1>
        </div>
      </div>

      <div className="search-layout">
        <Card className="filters">
          <form className="filters__body" onSubmit={onSubmit}>
            <span className="filters__title">
              <Icon name="sliders" size={16} />
              Filters
            </span>

            <Field label="Location" hint="Matches anywhere in the address.">
              {(p) => (
                <Input
                  {...p}
                  placeholder="Manchester"
                  value={form.location}
                  onChange={set('location')}
                />
              )}
            </Field>

            <Field label="Minimum capacity">
              {(p) => (
                <Input
                  {...p}
                  type="number"
                  min="1"
                  step="1"
                  inputMode="numeric"
                  placeholder="Any"
                  value={form.capacity}
                  onChange={set('capacity')}
                />
              )}
            </Field>

            <Field label="Maximum price">
              {(p) => (
                <Input
                  {...p}
                  type="number"
                  min="0"
                  step="1"
                  inputMode="decimal"
                  placeholder="Any"
                  value={form.priceMax}
                  onChange={set('priceMax')}
                />
              )}
            </Field>

            <div className="field">
              <span className="field__label">Must have</span>
              <AmenityPicker
                value={form.amenities}
                onChange={(amenities) => setForm((f) => ({ ...f, amenities }))}
              />
            </div>

            <div className="note-field">
              <span className="note-field__label">
                <Icon name="sparkles" size={15} />
                What are you looking for?
              </span>
              <Textarea
                rows={4}
                placeholder="A quiet room for a six-person client workshop. We'll run a demo, so a projector matters more than the price."
                value={form.note}
                onChange={set('note')}
              />
              <span className="note-field__hint">
                Optional. Add a note and the shortlist gets re-ranked against it,
                with a reason on every match.
              </span>
            </div>

            <div className="stack stack--sm">
              <Button type="submit" block loading={loading} icon="search">
                {loading ? 'Searching…' : 'Search'}
              </Button>
              {hasFilters && (
                <Button type="button" variant="ghost" block onClick={onClear}>
                  Clear filters
                </Button>
              )}
            </div>
          </form>
        </Card>

        <section>
          {loading ? (
            <Loading
              label={
                searchParams.get('note')
                  ? 'Ranking matches against your note…'
                  : 'Finding spaces…'
              }
            />
          ) : error ? (
            <div className="stack">
              <Alert>{error}</Alert>
              <div>
                <Button variant="secondary" onClick={reload}>
                  Try again
                </Button>
              </div>
            </div>
          ) : results.length === 0 ? (
            <EmptyState
              icon="search"
              title={hasFilters ? 'No rooms match those filters' : 'No spaces listed yet'}
              description={
                hasFilters
                  ? 'Filters are matched exactly before any ranking happens. Try widening the capacity or price, or dropping an amenity.'
                  : 'Once owners list their rooms they will show up here.'
              }
              action={
                hasFilters && (
                  <Button variant="secondary" onClick={onClear}>
                    Clear filters
                  </Button>
                )
              }
            />
          ) : (
            <>
              <div className="results-head">
                <span className="muted">
                  {pluralize(results.length, 'space')} found
                </span>
                {aiRanked && (
                  <Badge variant="ai" icon="sparkles">
                    Ranked against your note
                  </Badge>
                )}
              </div>

              {results.map((r, i) => (
                <ResultCard
                  key={r.roomId}
                  result={r}
                  rank={i + 1}
                  aiRanked={Boolean(r.reason)}
                />
              ))}
            </>
          )}
        </section>
      </div>
    </div>
  )
}
