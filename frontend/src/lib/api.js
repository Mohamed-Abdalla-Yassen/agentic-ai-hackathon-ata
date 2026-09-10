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
  // FormData sets its own multipart Content-Type, including the boundary the
  // server needs to parse the parts. Setting it by hand would strip that.
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'

  if (auth) {
    const token = getCookie(TOKEN_COOKIE)
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
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

  // ---- Profile ----
  me: () => request('/me'),
  updateProfile: (changes) => request('/me', { method: 'PATCH', body: changes }),

  // ---- Owner ----
  createSpace: (payload) => request('/spaces', { method: 'POST', body: payload }),
  mySpaces: () => request('/spaces/mine'),
  createRoom: (spaceId, payload) =>
    request(`/spaces/${spaceId}/rooms`, { method: 'POST', body: payload }),
  room: (roomId) => request(`/rooms/${roomId}`),
  updateRoom: (roomId, changes) =>
    request(`/rooms/${roomId}`, { method: 'PATCH', body: changes }),
  uploadPhoto: (roomId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/rooms/${roomId}/photos`, { method: 'POST', body: form })
  },
  roomPhotos: (roomId) => request(`/rooms/${roomId}/photos`),
  deletePhoto: (photoId) => request(`/photos/${photoId}`, { method: 'DELETE' }),

  // ---- Booker ----
  search: (params) => request(`/search${qs(params)}`),
  listing: (roomId) => request(`/listings/${roomId}`),
  favorites: () => request('/favorites'),
  addFavorite: (roomId) => request(`/rooms/${roomId}/favorite`, { method: 'PUT' }),
  removeFavorite: (roomId) =>
    request(`/rooms/${roomId}/favorite`, { method: 'DELETE' }),
  createBooking: (payload) =>
    request('/bookings', { method: 'POST', body: payload }),
}
