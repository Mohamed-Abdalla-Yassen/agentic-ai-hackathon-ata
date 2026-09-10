# SpaceMatch — backend

FastAPI backend for the SpaceMatch workspace and venue booking platform. It
provides JWT-authenticated REST endpoints for owners and bookers, stores data in
SQLite, and optionally uses one AI call to rank search results.

## Running

This project uses [uv](https://docs.astral.sh/uv/) for its virtual environment,
dependencies, and lockfile.

```bash
cd backend
uv sync
cp .env.example .env
# Fill in DATABASE_PATH, JWT_SECRET, and the AI provider settings in .env
uv run python seed.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API is available at `http://127.0.0.1:8000`. FastAPI's interactive
documentation is available at `/docs`, with the OpenAPI schema at `/openapi.json`.

Run the test suite with:

```bash
uv run pytest
```

## Configuration

Copy `.env.example` to `.env` and set the required values:

```dotenv
DATABASE_PATH=./data/spacematch.db
JWT_SECRET=replace-with-a-random-secret
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
ANTHROPIC_MODEL=your-model
```

`AI_PROVIDER` defaults to `anthropic`. Set it to `openai` to use OpenAI or any
OpenAI-compatible `/chat/completions` endpoint:

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model
OPENAI_BASE_URL=https://backend.sovereigneg.com/v1
```

`ANTHROPIC_AUTH_TOKEN` can be used instead of `ANTHROPIC_API_KEY`, and both
providers support an optional custom base URL. Rate limits and photo upload
limits are also configurable; see `.env.example` for the complete list and
their defaults.

## Database and demo data

SQLite requires no separate database server. `seed.py` creates the schema when
needed and loads demo spaces, rooms, and users. It is safe to run repeatedly;
existing demo data is skipped.

Demo accounts:

```text
Owner:  owner@spacematch.demo  / password123
Booker: booker@spacematch.demo / password123
```

The database path is controlled by `DATABASE_PATH`. Uploaded room photos are
stored under `UPLOAD_DIR` (default: `./data/uploads`).

## API

The base URL is `/api`. Register and login return a JWT; all other protected
routes expect:

```http
Authorization: Bearer <token>
```

Main route groups:

- `/api/auth` — registration and login
- `/api/spaces` — owner spaces and room creation
- `/api/search` — structured filtering followed by optional AI ranking
- `/api/listings` — public room details
- `/api/bookings` — booking requests
- `/api/favorites` — saved rooms
- `/api/me` — the signed-in user's profile
- `/api/rooms` and `/api/photos` — room editing and photo management

The complete request and response shapes are documented in
[`../docs/api-contract.md`](../docs/api-contract.md).

## AI matching

Search first applies SQL filters for location, capacity, price, and amenities.
When a booker supplies a free-text preference note, the remaining candidates
and their room notes are sent in one call to the configured provider. The
provider returns strict JSON containing ranked room IDs and a one-line reason
for each result.

If the preference note is empty, no AI request is made and the SQL-filtered
results are returned in their default order with `reason: null`.

## Layout

```text
app/
  app/main.py       FastAPI app, middleware, and error handling
  app/routers/      Auth, spaces, rooms, search, bookings, photos, and profile routes
  app/ai.py         Pluggable Anthropic/OpenAI-compatible ranking
  app/config.py     Environment settings and shared constants
  app/db.py         SQLite connection and schema helpers
  app/security.py   Password hashing and JWT helpers
tests/              Pytest coverage for API and AI behavior
seed.py             Schema initialization and demo data
```
