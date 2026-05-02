# backend-template-repository

A FastAPI backend template with [Auth0](https://auth0.com) JWT authentication.

## Project structure

```
app/
  config.py        # Settings loaded from environment variables
  auth.py          # Auth0 JWT verification (FastAPI dependency)
  main.py          # Application entry point
  routers/
    public.py      # Unauthenticated endpoints
    private.py     # Protected endpoints (require valid Auth0 token)
tests/
  conftest.py      # Shared fixtures (RSA key pair, JWKS mock, test client)
  test_public.py   # Tests for public endpoints
  test_private.py  # Tests for protected endpoints
.env.example       # Example environment variables
requirements.txt
```

## Quick start

### 1. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set AUTH0_DOMAIN and AUTH0_AUDIENCE
```

| Variable | Description | Example |
|---|---|---|
| `AUTH0_DOMAIN` | Your Auth0 tenant domain | `your-tenant.auth0.com` |
| `AUTH0_AUDIENCE` | API identifier configured in Auth0 | `https://your-api/` |

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`. Interactive docs at `/docs`.

## Endpoints

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/public` | No | Public data |
| GET | `/api/private` | **Yes** | Protected data |

### Authenticating

Obtain an access token from Auth0 and pass it as a Bearer token:

```bash
curl http://localhost:8000/api/private \
  -H "Authorization: Bearer <access_token>"
```

## Running tests

```bash
pytest
```