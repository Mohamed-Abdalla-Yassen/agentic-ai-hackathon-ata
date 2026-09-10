import { getCookie } from './cookies'

export const TOKEN_COOKIE = 'spacematch_token'
const BASE = '/api'

/** Errors from the API surface as this, so callers can read `.status`. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  if (auth) {
    const token = getCookie(TOKEN_COOKIE)
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    // Network-level failure: backend not running, DNS, offline.
    throw new ApiError(
      "Can't reach the server. Is the backend running on port 8000?",
      0
    )
  }

  if (res.status === 204) return null

  const raw = await res.text()
  let data = null
  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      // Non-JSON body (proxy error page, stack trace) — keep the text.
      data = { error: raw.slice(0, 200) }
    }
  }

  if (!res.ok) {
    // The contract specifies `{ "error": string }` for every failure.
    throw new ApiError(data?.error || `Request failed (${res.status})`, res.status)
  }

  return data
}

/** Build a query string, dropping empty/absent values. */
function qs(params) {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v)) {
      if (v.length === 0) continue
      sp.set(k, v.join(','))
    } else {
      sp.set(k, String(v))
    }
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export const api = {
  // ---- Auth ----
  register: (payload) =>
    request('/auth/register', { method: 'POST', body: payload, auth: false }),
  login: (payload) =>
    request('/auth/login', { method: 'POST', body: payload, auth: false }),

  // ---- Owner ----
  createSpace: (payload) => request('/spaces', { method: 'POST', body: payload }),
  mySpaces: () => request('/spaces/mine'),
  createRoom: (spaceId, payload) =>
    request(`/spaces/${spaceId}/rooms`, { method: 'POST', body: payload }),

  // ---- Booker ----
  search: (params) => request(`/search${qs(params)}`),
  listing: (roomId) => request(`/listings/${roomId}`),
  createBooking: (payload) =>
    request('/bookings', { method: 'POST', body: payload }),
}
