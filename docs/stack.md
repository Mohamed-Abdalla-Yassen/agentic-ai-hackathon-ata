# Stack

## Frontend
- React + Vite
- Plain CSS / Tailwind (no heavy component library)
- Fetch-based API client, JWT stored in a cookie

## Backend
- Node.js + Express
- REST API
- JWT auth (Authorization: Bearer header)
- bcrypt for password hashing

## Database
- SQLite (file-based, zero setup)
- Migration/seed script to create the 4 tables (User, Space, Room, Booking) and load demo data

## AI
- Claude (Anthropic API), single call per search request
- Input: filtered candidate rooms (structured fields + notes) + booker's free-text preference note
- Output: strict JSON — ranked room IDs + one-line reason each

## Repo layout
```
/backend    - Express app, DB access, routes, AI call
/frontend   - React + Vite app
/docs       - specification, stack, api-contract
```

## Environment variables
- `DATABASE_PATH` — path to the SQLite file (e.g. `./data/spacematch.db`)
- `JWT_SECRET`
- `ANTHROPIC_API_KEY`
