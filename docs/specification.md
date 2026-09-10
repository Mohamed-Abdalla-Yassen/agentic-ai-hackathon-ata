# SpaceMatch — AI-Powered Workspace & Venue Booking Platform

### Hackathon Build Spec (couple-hours scope, real backend + DB + accounts)

## 1. What We're Actually Building

A working two-sided app with real accounts and a real database:
- **Owners** register, log in, and add listings (spaces + rooms with structured attributes + free-text notes)
- **Bookers** register, log in, search with filters + a free-text preference note, and get an AI-ranked list of matches with a "why this matches" explanation
- Booking is a **request** stored in the DB (status: requested) — no payments, no calendar sync, no real confirmation flow

Everything else from the original concept (claim flow, admin/unclaimed listings, reviews, messaging, payments, calendar sync) is explicitly **out of scope** — listed at the bottom as future work so it's still in the pitch, just not in the build.

---

## 2. User Roles (hackathon scope)

| Role | Can do |
|---|---|
| **Owner** | Register, log in, create/edit listings + rooms |
| **Booker** | Register, log in, search, view listing detail, submit a booking request |

No admin/moderator role for the demo — cut it.

---

## 3. Feature Set

### 3.1 Auth
- Basic email + password registration/login for both roles
- Session or JWT — whichever your stack does fastest, don't overthink it
- No email verification, no password reset flow — skip for time

### 3.2 Owner Features
- After login: "Add a space" form → name, address (just a text field, skip geocoding unless a coding agent can wire up a free geocoding API fast), contact info
- "Add a room" under a space → capacity, price, amenities (checkboxes from a fixed list — this is what makes filtering work), description, notes (free text)
- List/edit their own spaces and rooms
- Skip: photo upload (use a placeholder image or a single image URL field if there's time), availability calendar (just assume everything's requestable)

### 3.3 Booker Features
- Search form: location (simple text match, not geo-radius), capacity, price range, amenity checkboxes, plus a **free-text preference note**
- Results: hard-filtered by structured fields (SQL query), then re-ranked by one LLM call that takes the filtered candidates + the user's note and returns an ordered list with a one-line reason per match
- Click a result → detail page with full listing info
- "Request to book" button → creates a booking record (status: requested), no payment, no owner-side confirmation UI needed unless time allows

---

## 4. Data Model (hackathon-scoped)

```
User
 ├─ id, name, email, password_hash, role (owner | booker)

Space
 ├─ id, owner_id, name, address, contact_info, description

Room
 ├─ id, space_id, name, capacity, price, price_unit
 ├─ amenities[] (from a fixed shared list — enum or join table)
 └─ notes (free text)

Booking
 ├─ id, room_id, booker_id, requested_start, requested_end
 └─ status (requested)
```

Four tables. That's it. Keep amenities as a **fixed list** (checkboxes, not free text) — that's the one modeling decision that has to be right, since it's what makes both the hard filter and the demo work.

---

## 5. AI Matching — Keep It to One LLM Call

Don't build embeddings or a vector DB — no time, no payoff at this scale.

1. Run the hard-filter SQL query (location match, capacity ≥, price ≤, required amenities present) → gets you 5-15 candidate rooms
2. Send those candidates (structured fields + notes) + the user's free-text preference note to an LLM in a single call
3. Ask it to return **strict JSON**: ranked room IDs + a one-line reason each
4. Render that ranked list with the reasons shown as the "AI match" explanation

This is a genuinely real AI matching feature, it's honest about what it's doing, and it's maybe 30-45 minutes of backend work.

---

## 9. Explicitly Out of Scope (mention as roadmap, don't build)

- Admin-added / unclaimed listings + claim flow
- Payments / Stripe Connect
- Calendar sync
- Reviews & ratings
- In-app messaging
- Instant booking / owner confirmation workflow
- Photo uploads (unless trivially fast with your stack)
- Geo-radius search (plain text location match is fine for a demo)

These are worth naming out loud in the pitch — it shows you scoped deliberately rather than ran out of time.