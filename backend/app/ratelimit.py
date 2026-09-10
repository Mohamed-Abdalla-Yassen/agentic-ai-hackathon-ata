"""In-process rate limiting.

The asset actually worth protecting here is the Anthropic API budget: every
search that carries a `note` costs real tokens, and nothing else in the API
spends money. So the limits are layered rather than flat:

1. **Per-IP limits on auth** — registration is open, so without this an
   attacker just mints accounts in a loop and walks around any per-user quota.
2. **Per-user limits on AI search** — the ordinary abuse ceiling for a single
   logged-in account.
3. **A global daily AI budget** — the backstop. Per-user quotas are only as
   strong as the cost of getting another user, and on an open-registration app
   that cost is one HTTP request. The global cap is what actually bounds the
   worst-case spend for the day, no matter how many identities are involved.

Free (non-AI) reads are limited too, but only loosely — enough to blunt a
scripted hammering without getting in a real user's way.

State is in-process memory: one uvicorn worker, matching the SQLite-in-a-file
scale of the rest of the app. Running multiple workers gives each its own
counters, so effective limits multiply by worker count — move the counters to
Redis before scaling out.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

# Keys are (bucket_name, identity). Identity is a user id for per-user buckets,
# a client IP for per-IP ones, and a constant for the global budget.
_Key = tuple[str, str]

# Above this many distinct keys in one bucket we drop the idle ones. A limiter
# keyed by client IP is memory an unauthenticated attacker can allocate, so it
# needs a ceiling; the eviction is oldest-activity-first, which means the keys
# discarded are the ones already at zero recent hits and therefore not being
# rate limited anyway.
_MAX_KEYS_PER_BUCKET = 20_000


@dataclass(frozen=True)
class Limit:
    """`count` requests allowed per `window_seconds`, rolling."""

    count: int
    window_seconds: int


class SlidingWindowLimiter:
    """Rolling-window counter: remembers hit timestamps per key.

    A rolling window rather than a fixed calendar window, because a fixed one
    lets a caller spend the whole quota at 11:59 and the whole next quota at
    12:00 — twice the intended rate across the boundary, which for an AI budget
    is twice the intended spend.
    """

    def __init__(self) -> None:
        self._hits: dict[_Key, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, bucket: str, identity: str, limit: Limit) -> float | None:
        """Record a hit and return None, or return seconds-to-wait if over limit.

        A rejected call does *not* consume quota — otherwise a client that keeps
        retrying while blocked would keep pushing its own reset further away.
        """
        key = (bucket, identity)
        now = time.monotonic()
        cutoff = now - limit.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit.count:
                # Quota frees up when the oldest hit in the window expires.
                return max(0.0, hits[0] + limit.window_seconds - now)

            hits.append(now)
            if len(self._hits) > _MAX_KEYS_PER_BUCKET:
                self._evict_idle_locked(cutoff)
            return None

    def _evict_idle_locked(self, cutoff: float) -> None:
        """Drop keys whose every hit has aged out. Caller must hold the lock."""
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]

    def reset(self) -> None:
        """Clear all counters. For tests and for a deliberate operator reset."""
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()
