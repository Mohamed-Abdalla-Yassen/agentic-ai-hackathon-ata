# SpaceMatch — frontend

React + Vite client for the SpaceMatch booking platform. Talks to the FastAPI
backend documented in [`../docs/api-contract.md`](../docs/api-contract.md).

## Running

```bash
npm install
npm run dev      # http://localhost:5173
```

Vite proxies `/api/*` to `http://127.0.0.1:8000` (the uvicorn default), so the
frontend stays origin-relative and no CORS config is needed. Point it elsewhere
with `VITE_BACKEND_URL`:

```bash
VITE_BACKEND_URL=http://127.0.0.1:9000 npm run dev
```

> **Why the scripts call `node node_modules/vite/bin/vite.js`** rather than just
> `vite`: this repo's path contains an `&`, which breaks npm's generated `.bin`
> shim on Windows. Invoking the entrypoint directly sidesteps the shim and works
> identically on macOS and Linux.

## Layout

```
src/
  lib/          API client, auth context, cookies, theme, shared constants
  components/
    ui/         Design-system primitives (Button, Field, Card, Icon, …)
    layout/     Nav + page shell
  pages/        Route components
  styles/       theme.css (design tokens) + global.css (component layer)
```

## Design system

`styles/theme.css` holds every colour, type, space, radius, shadow and motion
token. Light is the default; dark is applied via `[data-theme="dark"]` on
`<html>` and persisted in `localStorage`. An inline script in `index.html` sets
it before first paint so a dark reload never flashes white.

Two accent ramps: an evergreen for the product, and an iris/violet used **only**
for AI-generated content (match reasons, the preference note). Keeping that
second colour scarce is what makes AI output legible as AI output.

## Auth

Register/login return `{ token, user }`. The token is stored in a cookie (per
the stack doc) and replayed as `Authorization: Bearer <token>`. Since the
contract has no `GET /me`, the user object is cached in `localStorage` beside
it to restore sessions across reloads.
