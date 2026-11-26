# Backend Template Repository

A reusable, fully typed FastAPI backend to start new web platforms from. Features live in self-contained modules under `app/modules/`, so a new project keeps what it needs and deletes the rest.

The roadmap (Auth0, multi-tenancy, partner API gateway, secure key exchange, WebSockets, TCP/UDP, QRIS and international payments via Xendit, and more) is built one module at a time.

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ORM / migrations | SQLAlchemy 2 (async) / Alembic |
| Database | PostgreSQL 16 (SQLite for tests) |
| Auth | JWT (PyJWT) + bcrypt |
| Cache, rate-limit store, broker | Redis 7 |
| Background jobs | Celery |
| Rate limiting | slowapi (Redis-backed, shared across workers) |
| Settings | Pydantic Settings, validated at startup |
| Logging | structlog (JSON in production, pretty in dev) with request IDs |
| Python / packaging | Python 3.12+, [uv](https://docs.astral.sh/uv/) with a committed `uv.lock` |
| Quality | Ruff (lint + format), mypy `--strict`, pytest |
| CI / containers | GitHub Actions, Docker, docker compose |

## Quick start

```bash
# 1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
# 2. Install dependencies (creates .venv from uv.lock)
make install

# 3. Configure
cp .env.example .env        # set SECRET_KEY and DATABASE_URL at minimum

# 4. Create the schema and run
make migrate
make dev                    # http://localhost:8000/docs
```

Full stack with Postgres, Redis and a Celery worker:

```bash
docker compose up -d
docker compose exec web alembic upgrade head
```

## Project structure

```
app/
├── main.py                 # App factory: middleware, exception handlers, routers
├── api/router.py           # Mounts each module's router under /api/v1
├── core/                   # Cross-cutting infrastructure
│   ├── config.py           # Settings + production safety checks
│   ├── clock.py            # utc_now() and frozen_clock() for tests
│   ├── security/           # passwords.py (bcrypt), tokens.py (JWT)
│   ├── rate_limit.py       # Global limiter, typed limit()/exempt() helpers
│   ├── redis.py, celery_app.py, logging.py
├── common/                 # Shared building blocks
│   ├── repository.py       # Generic async CRUD repository
│   ├── schemas.py          # Pagination, PagedResponse
│   ├── exceptions.py       # AppException hierarchy
│   ├── exception_handlers.py
│   └── middleware.py       # Request ID + logging, security headers
├── db/                     # Declarative base, session, Alembic migrations
├── modules/                # One folder per feature
│   ├── auth/               # Register, login, refresh, current-user dependencies
│   ├── users/              # User model, repository, service, CRUD routes
│   ├── health/             # Liveness and readiness probes
│   └── notifications/      # Email tasks (provider integration coming)
└── utils/                  # Date/time, currency (Decimal), text helpers
tests/
├── unit/                   # No I/O
└── integration/            # HTTP + SQLite, migrations, rate limits
```

### Adding a module

1. Create `app/modules/<name>/` with `models.py`, `schemas.py`, `repository.py` (extend `BaseRepository`), `service.py`, `router.py`.
2. Mount the router in `app/api/router.py`.
3. Import the models in `app/db/migrations/env.py`, then `make migrate-create msg="add <name>"`.
4. Put Celery tasks in `app/modules/<name>/tasks.py` and add the module to `autodiscover_tasks` in `app/core/celery_app.py`.
5. Add unit and integration tests. `make check` must pass.

To remove a module, delete its folder and its line in `app/api/router.py`.

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Notes |
|---|---|---|
| `APP_ENV` | `development` | `development`, `testing`, `staging`, `production` |
| `SECRET_KEY` | dev placeholder | 32+ chars. Staging/production refuse to start with the default |
| `ALGORITHM` | `HS256` | `HS256`, `HS384` or `HS512` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | `30` / `7` | |
| `DATABASE_URL` | local Postgres | SQLite is rejected in staging/production |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` | `10` / `20` | |
| `REDIS_URL` | `redis://localhost:6379/0` | |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis DB 1 / 2 | |
| `ALLOWED_ORIGINS` | localhost | Comma-separated. `*` is rejected in staging/production |
| `RATE_LIMIT_ENABLED` | `true` | |
| `RATE_LIMIT_TIMES` / `RATE_LIMIT_SECONDS` | `100` / `60` | Default limit for every route |
| `RATE_LIMIT_STORAGE_URL` | empty (= `REDIS_URL`) | `memory://` for a single process |

## API

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | none | Register (10/min per client) |
| POST | `/api/v1/auth/login` | none | Returns access + refresh tokens (10/min) |
| POST | `/api/v1/auth/refresh` | none | New token pair from a refresh token (10/min) |
| GET | `/api/v1/auth/me` | Bearer | Current user |
| GET | `/api/v1/users/` | Superuser | Paginated list |
| GET | `/api/v1/users/me` | Bearer | Current user |
| GET | `/api/v1/users/{id}` | Superuser | Get user |
| PATCH | `/api/v1/users/{id}` | Self or superuser | Update (only superusers can change `is_active`) |
| DELETE | `/api/v1/users/{id}` | Superuser | Delete |
| GET | `/api/v1/health/live` | none | Process is up |
| GET | `/api/v1/health/ready` | none | Database and Redis reachable, else 503 |

Every response carries `X-Request-ID` (an incoming safe value is reused). Rate-limited responses include `X-RateLimit-*` headers; a 429 includes `Retry-After`.

### Rate limits per route

```python
from app.core import rate_limit

@router.post("/expensive")
@rate_limit.limit("5/minute")          # the route must accept request and response
async def expensive(request: Request, response: Response) -> ...: ...

@router.get("/ping")
@rate_limit.exempt
async def ping() -> ...: ...
```

## Development

```bash
make check            # ruff check, ruff format --check, mypy --strict, pytest (what CI runs)
make test             # tests with coverage
make format           # auto-format and fix lint
make migrate-create msg="add_table"
uv add <package>      # add a dependency (updates pyproject.toml and uv.lock)
uv run pre-commit install
```

Tests use SQLite and in-memory rate limits; no Postgres or Redis needed. Use `app.core.clock.frozen_clock()` to pin time in tests, and `utc_now()` instead of `datetime.now()` in code.

## Production checklist

- Set `APP_ENV=production`, a random `SECRET_KEY`, a managed Postgres `DATABASE_URL` and your real `ALLOWED_ORIGINS`.
- Run `alembic upgrade head` before starting new app versions.
- Terminate TLS at your proxy; HSTS is sent when `APP_ENV=production`.
- Point load balancer health checks at `/api/v1/health/ready`.

## License

MIT
