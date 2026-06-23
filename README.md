# Prism

> One entry point. Every angle of your API, visible.

Prism is a full-stack API gateway and developer platform. Developers register, get an API key, and register a proxy route pointing at any external API they want to call. Prism then validates every request, enforces rate limits and monthly quotas, forwards it to the real target, and logs the full transaction, all visible on a real-time analytics dashboard.

It's a mini [Kong](https://konghq.com/) (the gateway/proxy layer) plus a mini [Datadog](https://www.datadoghq.com/) (the analytics dashboard), built from scratch to understand how both actually work under the hood.

## Architecture

```
                  +-----------------+
                  |   Next.js UI    |  (dashboard: keys, routes,
                  | (localhost:3000)|   analytics, logs)
                  +--------+--------+
                           | REST (axios + Bearer JWT)
                           v
                  +-----------------+
                  |   FastAPI API   |  /v1/auth, /v1/api-keys,
                  | (localhost:8000)|  /v1/routes, /v1/analytics
                  +--------+--------+
                           |
            +--------------+--------------+
            v              v              v
     +------------+ +------------+ +-------------+
     | PostgreSQL | |   Redis    | |   httpx     |
     | (users,    | | (sliding-  | | (forwards   |
     |  keys,     | |  window    | |  to real    |
     |  routes,   | |  rate      | |  target API)|
     |  logs,     | |  limit)    | |             |
     |  quotas)   | +------------+ +-------------+
     +------------+

  Gateway flow: client -> /proxy/{slug} -> validate key (sha256 lookup)
                -> check Redis rate limit -> check Postgres quota
                -> look up route -> forward via httpx -> return response
                -> (background) write request_logs row + increment quota
```

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend API | FastAPI (Python) | Async-native, auto-generated OpenAPI docs (`/docs`), strong typing via Pydantic |
| Auth | JWT + bcrypt | Stateless tokens for the dashboard; bcrypt for slow, salted password hashing |
| Database | PostgreSQL + SQLAlchemy (async) + Alembic | Relational integrity for users/keys/routes/logs; Alembic gives version-controlled schema migrations |
| Rate Limiting | Redis (sliding window) | Sub-millisecond reads/writes at the volume a gateway needs; see "Key Design Decisions" below |
| HTTP Forwarding | httpx (async) | Async client matching FastAPI's async request lifecycle, avoids blocking the event loop while proxying |
| Frontend | Next.js (App Router) + React | File-based routing, easy API route co-location, large ecosystem |
| UI Components | Tailwind CSS + shadcn/ui | Utility-first styling + accessible, unstyled-by-default component primitives we can theme ourselves |
| Charts | Recharts | Simple declarative charts that compose well with React state |
| Data Fetching | TanStack Query + Axios | Caching, automatic refetching, and request/response interceptors (auth header injection, 401 handling) |
| Containerization | Docker + Docker Compose | One-command local environment matching production topology |
| Testing | Pytest (+ pytest-asyncio) | Async-native test support matching the async backend |
| Logging | Structlog (JSON) | Structured, queryable logs with per-request correlation IDs |
| CI/CD | GitHub Actions | Gate deploys on tests passing |
| Deployment | Vercel (frontend) + Render (backend) + Neon (Postgres) + Upstash (Redis) | Free-tier-friendly split across managed providers, each specialized for its piece (Vercel for Next.js specifically, Render for Dockerized services, Neon/Upstash as serverless managed DB/cache) |

## Local Setup

```bash
git clone <this-repo-url>
cd prism
docker compose up --build
```

That's it. Postgres, Redis, the FastAPI backend, and the Next.js frontend all come up together. Frontend: [http://localhost:3000](http://localhost:3000). Backend: [http://localhost:8000](http://localhost:8000).

**First-time setup note:** the database schema is created via Alembic migrations, not automatically on container start. After the containers are up, run migrations once:

```bash
docker exec -it project-prism-api-1 alembic upgrade head
```

(If you're developing locally outside Docker, see `backend/.env.example` for the required environment variables, and run the backend with `uvicorn app.main:app --reload` after `pip install -r requirements.txt` in a virtualenv.)

## API Documentation

FastAPI auto-generates interactive API docs. Once the backend is running, visit:
[http://localhost:8000/docs](http://localhost:8000/docs)

## Key Design Decisions

**1. Redis for rate limiting, not Postgres.**
Rate limiting needs a counter that's checked and incremented on *every single proxied request*, with sub-millisecond latency and automatic expiry. Redis's in-memory sorted sets (`ZADD`/`ZCARD`/`ZREMRANGEBYSCORE`) give us a true sliding window, counting only requests within the trailing 60 seconds, without the write-amplification and connection overhead of doing the same accounting in Postgres on every request.

**2. UUID primary keys, not auto-increment integers.**
API keys, routes, and users are UUIDs so IDs are globally unique and non-sequential. You can't infer how many users/keys exist or guess adjacent IDs by incrementing, which matters once IDs appear in URLs or client-visible payloads.

**3. Async SQLAlchemy (asyncpg) for the app, sync (psycopg2) for Alembic.**
The live FastAPI app needs to handle many concurrent requests without one slow query blocking others. That's what async buys it. Alembic migrations are a one-off, single-threaded CLI operation a developer runs manually; there's no concurrency to benefit from, so it uses the simpler, more mature sync driver.

**4. Background tasks for request logging, not inline writes.**
Writing a `request_logs` row and incrementing quota usage happen *after* the proxied response is already on its way back to the caller, via FastAPI's `BackgroundTasks`. The caller's latency reflects only the actual upstream round-trip, not our own bookkeeping.

**5. Store `key_hash`, never the raw API key.**
Raw API keys are shown to the user exactly once, at creation time, then only their SHA-256 hash is persisted. If the database were ever compromised, no usable credentials would leak. Every incoming request's key is hashed and compared against the stored hash, the same principle as password hashing but with a fast hash (not bcrypt) since API keys are already high-entropy random tokens, not low-entropy human passwords.

## Screenshots

_Add your own screenshots here (dashboard overview, API keys page, analytics charts, logs table)._

## Live Demo

- **Frontend (dashboard):** https://project-prism-eight.vercel.app
- **Backend (API + docs):** https://project-prism-n8d4.onrender.com/docs

**Deployment stack:** Vercel (frontend) + Render (backend, free tier — note: the free instance spins down after ~15 minutes of inactivity and may take 30-60 seconds to wake up on the first request) + Neon (PostgreSQL) + Upstash (Redis). Backend deploys are gated on the Pytest suite passing, via GitHub Actions calling a Render deploy hook.
