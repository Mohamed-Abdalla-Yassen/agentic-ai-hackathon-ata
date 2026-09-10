# API Contract

Base URL: `/api`
Auth: JWT via `Authorization: Bearer <token>` header (all routes except register/login).

Fixed amenities list (used by both Room creation and search filters):
`wifi, parking, whiteboard, projector, kitchen, ac`

---

## Auth

### POST /api/auth/register
Request:
```json
{ "name": "string", "email": "string", "password": "string", "role": "owner | booker" }
```
Response `201`:
```json
{ "token": "string", "user": { "id": "number", "name": "string", "email": "string", "role": "owner | booker" } }
```

### POST /api/auth/login
Request:
```json
{ "email": "string", "password": "string" }
```
Response `200`: same shape as register.

---

## Owner

### POST /api/spaces
Request:
```json
{ "name": "string", "address": "string", "contact_info": "string", "description": "string" }
```
Response `201`: created Space object.

### GET /api/spaces/mine
Response `200`: array of Space objects owned by the logged-in owner, each with nested `rooms: []`.

### POST /api/spaces/:spaceId/rooms
Request:
```json
{
  "name": "string",
  "capacity": "number",
  "price": "number",
  "price_unit": "hour | day",
  "amenities": ["wifi", "parking"],
  "notes": "string"
}
```
Response `201`: created Room object.

---

## Booker

### GET /api/search
Query params:
- `location` (string, substring match)
- `capacity` (number, min)
- `priceMax` (number)
- `amenities` (comma-separated, e.g. `wifi,projector`)
- `note` (string, free-text preference — passed to the AI ranking step)

Response `200`:
```json
{
  "results": [
    {
      "roomId": "number",
      "spaceName": "string",
      "roomName": "string",
      "address": "string",
      "capacity": "number",
      "price": "number",
      "price_unit": "string",
      "amenities": ["wifi"],
      "reason": "string"
    }
  ]
}
```
Results are hard-filtered by SQL first, then re-ranked by a single Claude call using `note` + candidate fields/notes. `reason` is the one-line AI explanation for that match. If `note` is empty, skip the AI call and return SQL-filtered results in default order with `reason: null`.

### GET /api/listings/:roomId
Response `200`: full Room + parent Space details (no `reason` field — this is a direct lookup, not a ranked search result).

---

## Errors

All error responses:
```json
{ "error": "string" }
```
Status codes: `400` validation, `401` missing/invalid token, `403` wrong role for action, `404` not found.

---

## Photos

Photos belong to a **room**. Image bytes are stored on the server's filesystem;
the API only ever exchanges metadata and URLs.

Allowed formats: `image/jpeg`, `image/png`, `image/webp`. The format is decided
by the file's own leading bytes, not by the `Content-Type` the client sends, so
a non-image renamed to `.png` is refused. Default limits: 5 MB per file, 8
photos per room (`MAX_PHOTO_BYTES`, `MAX_PHOTOS_PER_ROOM`).

### POST /api/rooms/{room_id}/photos
Owner only, and only for a room in a space they own.
Request: `multipart/form-data` with a single `file` part.
Response `201`:
```json
{ "id": "number", "url": "string", "content_type": "string", "size": "number" }
```
Errors: `400` unsupported format / empty / too large / room already at the cap,
`403` not your room, `404` no such room, `429` upload rate limit.

### GET /api/rooms/{room_id}/photos
Response `200`: array of the same Photo object.

### GET /api/photos/{photo_id}
Returns the image bytes with the stored content type. **Unauthenticated** — a
browser loading `<img src>` sends no Authorization header, and listing photos
are public information. Served with a long immutable cache lifetime, since a
photo id always maps to the same bytes.

### DELETE /api/photos/{photo_id}
Owner only. Response `204`. Errors: `403` not your photo, `404` no such photo.

### Where photos appear
* `GET /api/search` — each result carries `photos: string[]` (URLs); the first
  is the card thumbnail.
* `GET /api/listings/{room_id}` — `photos: string[]`, shown as a gallery.
* `GET /api/spaces/mine` — each room carries `photos: Photo[]` (full objects,
  since the owner UI needs ids to delete with).
