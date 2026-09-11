# SpaceMatch

SpaceMatch is an AI-assisted workspace and venue booking platform. Owners list
spaces and bookable rooms; bookers search by practical constraints and describe
what they need in plain language. The backend filters rooms structurally, then
uses one AI ranking call to return the best matches with a short explanation.

> Hackathon project. The current build focuses on the core owner, booker, search,
> favorites, booking-request, profile, and room-photo workflows.

You can watch the demo [here](https://drive.google.com/file/d/1LFMU-CeeowpEabO9mvRn8NnYGmDaEYmc/view?usp=sharing)!

## Highlights

- Owner accounts with spaces, rooms, structured attributes, and notes
- Booker accounts with location, capacity, price, and amenity filters
- AI-ranked search results with a one-line reason for each match
- Optional Anthropic or OpenAI-compatible AI provider
- JWT authentication and bcrypt password hashing
- SQLite storage with a repeatable demo-data seed
- Room photo uploads with type, size, count, and rate limits
- Responsive React interface with light and dark themes

## Stack

- **Frontend:** React 19, Vite, React Router, plain CSS
- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic
- **Database:** SQLite
- **Authentication:** JWT bearer tokens and bcrypt
- **AI:** Anthropic Claude or an OpenAI-compatible `/chat/completions` endpoint

## Quick start

### 1. Start the backend

From the repository root:

```bash
cd backend
uv sync
cp .env.example .env
```

Set at least `DATABASE_PATH` and `JWT_SECRET` in `backend/.env`. To enable
AI-ranked searches, also configure the provider variables described in
[`backend/README.md`](backend/README.md).

```bash
uv run python seed.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API runs at `http://127.0.0.1:8000`. FastAPI's interactive documentation
is at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to the backend's
port 8000 by default. To use another backend URL:

```bash
VITE_BACKEND_URL=http://127.0.0.1:9000 npm run dev
```

## Demo accounts

The backend seed creates these accounts:

```text
Owner:  owner@spacematch.demo  / password123
Booker: booker@spacematch.demo / password123
```

Use the owner account to create spaces and rooms. Use the booker account to
search, save favorites, and submit booking requests.

## How AI matching works

1. SQL applies the structured filters: location, capacity, price, and required
   amenities.
2. If the booker entered a preference note, the remaining room candidates and
   their notes are sent in one request to the configured AI provider.
3. The provider returns strict JSON containing ranked room IDs and one-line
   matching reasons.

When the preference note is empty, the AI call is skipped and the filtered
results keep their default order with `reason: null`.

## Repository layout

```text
backend/   FastAPI application, SQLite access, auth, AI ranking, and tests
frontend/  React + Vite client
 docs/     Product specification, stack notes, and API contract
```

## Development commands

Backend tests:

```bash
cd backend
uv run pytest
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Documentation

- [Backend README](backend/README.md) — backend configuration, API routes, and testing
- [Frontend README](frontend/README.md) — frontend setup, layout, auth, and design system
- [API contract](docs/api-contract.md) — request and response shapes
- [Product specification](docs/specification.md) — scope, workflows, and data model
- [Stack notes](docs/stack.md) — technology and environment overview
- [Initial concept](docs/initial-concept.md) — original product direction

## Scope

The booking flow creates a request with `status: requested`. Payments, calendar
sync, reviews, messaging, geo-radius search, and admin listing claims are
outside the current hackathon scope.
