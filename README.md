# Backend Template Repository

A production-ready FastAPI backend template with async SQLAlchemy, JWT auth, Redis caching, Celery tasks, and a full test suite.

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Primary DB | PostgreSQL 16 |
| Test DB | SQLite + aiosqlite |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Cache / queue | Redis 7 |
| Background tasks | Celery 5 |
| Settings | Pydantic Settings v2 + `.env` |
| Logging | structlog (JSON in prod, pretty in dev) |
| Validation | Pydantic v2 |
| Rate limiting | slowapi |
| Python | 3.12+ |
| Package manager | Poetry |
| Linter / formatter | Ruff |
| Testing | pytest + pytest-asyncio + factory-boy + httpx |
| CI | GitHub Actions |
| Containers | Docker + docker-compose |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry (`pip install poetry`)
- Docker & docker-compose (optional, for full stack)

### Local development (SQLite)

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd backend-template-repository

# 2. Install dependencies
make install
# or: poetry install

# 3. Copy and edit environment file
cp .env.example .env
# Edit SECRET_KEY and DATABASE_URL at minimum

# 4. Run database migrations
make migrate

# 5. Start the dev server
make dev
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
# → http://localhost:8000/redoc (ReDoc)
```

### Docker Compose (full stack)

```bash
# Start Postgres, Redis, API server, and Celery worker
docker-compose up -d

# Apply migrations inside the container
docker-compose exec web alembic upgrade head

# View logs
make docker-logs
```

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py        # register, login, refresh, /me
│   │       │   ├── users.py       # CRUD (superuser-protected)
│   │       │   └── health.py      # /api/v1/health/
│   │       └── router.py
│   ├── core/
│   │   ├── config.py              # Pydantic Settings + lru_cache
│   │   ├── security.py            # JWT helpers, password hashing
│   │   ├── redis.py               # Async Redis client
│   │   ├── celery_app.py          # Celery factory
│   │   └── logging.py             # structlog setup
│   ├── db/
│   │   ├── base.py                # DeclarativeBase + BaseModel (UUID PK, timestamps)
│   │   ├── session.py             # init_db(), get_db(), close_db()
│   │   └── migrations/            # Alembic env + versions
│   ├── models/
│   │   └── user.py                # User SQLAlchemy model
│   ├── schemas/
│   │   ├── auth.py                # LoginRequest, TokenResponse, ...
│   │   ├── user.py                # UserCreate, UserResponse, ...
│   │   └── common.py              # PaginationParams, PagedResponse
│   ├── repositories/
│   │   ├── base.py                # Generic CRUD repository
│   │   └── user.py                # UserRepository
│   ├── services/
│   │   ├── auth.py                # AuthService (register, login, refresh)
│   │   └── user.py                # UserService (CRUD)
│   ├── tasks/
│   │   └── email.py               # Celery email tasks
│   ├── middleware/
│   │   └── logging.py             # Request/response logging + X-Request-ID
│   ├── dependencies/
│   │   ├── db.py                  # get_db re-export
│   │   └── auth.py                # get_current_user, require_superuser
│   ├── exceptions/
│   │   ├── base.py                # AppException hierarchy
│   │   └── handlers.py            # FastAPI exception handlers
│   └── main.py                    # App factory, lifespan, middleware
├── tests/
│   ├── conftest.py                # Fixtures: db_session, client, test_user, ...
│   ├── factories/user.py          # factory_boy UserFactory
│   ├── unit/                      # Pure unit tests (mocked deps)
│   └── integration/               # End-to-end HTTP tests (SQLite)
├── Dockerfile                     # Multi-stage production image
├── docker-compose.yml             # Dev stack
├── docker-compose.prod.yml        # Production stack
├── pyproject.toml                 # Poetry + Ruff + pytest config
├── alembic.ini                    # Alembic config
├── Makefile                       # Common tasks
└── .env.example                   # Environment template
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` / `testing` / `production` |
| `SECRET_KEY` | *(required)* | HS256 signing key (min 32 chars) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `DATABASE_URL` | postgres URL | Async SQLAlchemy URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery results |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated CORS origins |
| `RATE_LIMIT_TIMES` | `100` | Requests allowed per window |
| `RATE_LIMIT_SECONDS` | `60` | Rate limit window in seconds |

---

## API Endpoints

### Auth (`/api/v1/auth`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | — | Register a new user |
| POST | `/login` | — | Login, returns JWT pair |
| POST | `/refresh` | — | Issue new access token |
| GET | `/me` | Bearer | Current user profile |

### Users (`/api/v1/users`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | Superuser | List all users (paginated) |
| GET | `/me` | Bearer | Current user profile |
| GET | `/{user_id}` | Superuser | Get user by ID |
| PATCH | `/{user_id}` | Bearer | Update user (own or superuser) |
| DELETE | `/{user_id}` | Superuser | Delete user |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Basic health (env) |
| GET | `/api/v1/health/` | Detailed health + version |

---

## Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

Tests use SQLite — no external services (Redis, PostgreSQL) required.
Each test creates fresh tables and drops them on teardown for full isolation.

---

## Makefile Reference

```bash
make install          # Install Poetry dependencies
make dev              # Run dev server with hot-reload
make test             # Run all tests + coverage
make test-unit        # Unit tests only
make test-integration # Integration tests only
make lint             # ruff check
make format           # ruff format + fix
make clean            # Remove __pycache__, .pytest_cache, test DB
make migrate          # alembic upgrade head
make migrate-create msg="add_table"  # autogenerate migration
make docker-up        # Start docker-compose
make docker-down      # Stop docker-compose
make docker-logs      # Tail container logs
```

---

## Database Migrations

```bash
# Create a new migration (auto-generates from model changes)
make migrate-create msg="add_users_table"

# Apply all pending migrations
make migrate

# Downgrade one step
poetry run alembic downgrade -1
```

---

## Background Tasks (Celery)

```bash
# Start a worker (requires Redis)
celery -A app.core.celery_app.celery_app worker --loglevel=info

# Trigger a task from Python
from app.tasks.email import send_welcome_email
send_welcome_email.delay("user@example.com", "username")
```

Add new tasks in `app/tasks/`. Decorate with `@celery_app.task`.

---

## Adding a New Resource

1. **Model** — add `app/models/myresource.py` (extends `BaseModel`)
2. **Schema** — add `app/schemas/myresource.py` (Pydantic v2)
3. **Repository** — add `app/repositories/myresource.py` (extends `BaseRepository`)
4. **Service** — add `app/services/myresource.py`
5. **Endpoints** — add `app/api/v1/endpoints/myresource.py`
6. **Router** — include in `app/api/v1/router.py`
7. **Migration** — `make migrate-create msg="add_myresource"`
8. **Tests** — add unit + integration tests under `tests/`

---

## Pre-commit Hooks

```bash
# Install hooks
poetry run pre-commit install

# Run manually against all files
poetry run pre-commit run --all-files
```

Hooks run: ruff (lint + format), trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files.

---

## Production Deployment

1. Build the image:
   ```bash
   docker build -t backend-template:latest .
   ```

2. Set all required environment variables (see `.env.example`).

3. Run migrations before starting:
   ```bash
   docker run --env-file .env backend-template:latest alembic upgrade head
   ```

4. Start with docker-compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

**Security checklist for production:**
- [ ] Set a strong, random `SECRET_KEY` (32+ chars)
- [ ] Set `APP_ENV=production`
- [ ] Use a managed PostgreSQL instance
- [ ] Enable TLS termination in your reverse proxy
- [ ] Restrict `ALLOWED_ORIGINS` to your frontend domain(s)
- [ ] Rotate JWT secrets regularly

---

## License

MIT