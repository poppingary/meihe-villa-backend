# Meihe Villa Backend - Development Guide

This is a FastAPI backend for **Meihe Villa** (梅鶴山莊) - a Taiwan heritage/historic sites website (台灣古蹟網站). Provides REST APIs for the Next.js frontend and CMS admin panel.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Package Manager**: uv
- **Database**: PostgreSQL with SQLAlchemy ORM (async)
- **Migrations**: Alembic
- **Auth**: JWT tokens (httpOnly cookies)
- **Storage**: AWS S3 + CloudFront CDN
- **Testing**: pytest + pytest-asyncio

## Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings/environment config
│   ├── database.py       # Database connection
│   ├── models/           # SQLAlchemy models
│   │   ├── heritage.py   # HeritageSite, Category
│   │   ├── news.py       # News
│   │   ├── timeline.py   # TimelineEvent
│   │   ├── visit_info.py # VisitInfo
│   │   ├── media.py      # MediaFile
│   │   └── user.py       # User (admin)
│   ├── schemas/          # Pydantic schemas
│   ├── api/              # API routes
│   │   ├── deps.py       # Dependencies (auth, db session)
│   │   └── v1/           # API version 1
│   │       ├── heritage.py
│   │       ├── news.py
│   │       ├── timeline.py
│   │       ├── visit_info.py
│   │       ├── media.py
│   │       └── auth.py
│   ├── core/             # Core utilities
│   │   └── security.py   # JWT, password hashing
│   └── crud/             # Database operations
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
│   ├── create_admin.py   # Create admin user
│   └── sync_s3_media.py  # Sync S3 files to database
├── tests/                # Test files
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Common Commands

### Development

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --all-extras

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs
open http://localhost:8000/docs

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>
```

### Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Downgrade one revision
uv run alembic downgrade -1
```

### Admin User Management

```bash
# Create an admin user
uv run python scripts/create_admin.py <email> <password> <name>

# Example
uv run python scripts/create_admin.py admin@example.com mypassword "Admin User"
```

### Media Sync

```bash
# Sync existing S3 files to database
uv run python scripts/sync_s3_media.py
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_main.py -v

# Run with coverage
uv run pytest --cov=app tests/
```

### Docker

```bash
# Build and start containers (includes PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Start only database (for local development)
docker-compose up -d db
```

### Linting

```bash
# Check code style
uv run ruff check .

# Format code
uv run ruff format .
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/meihe_villa

# Auth
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=meihe-villa-media
CLOUDFRONT_DOMAIN=d3e6xq549z85ve.cloudfront.net

# Environment (dev or prod)
ENVIRONMENT=dev
```

### Environment-specific S3 Buckets

- **Development**: `meihe-villa-media-dev`
- **Production**: `meihe-villa-media`

The `ENVIRONMENT` variable determines which bucket is used.

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/api/v1/heritage/sites` | List heritage sites |
| GET | `/api/v1/heritage/sites/{id}` | Get site by ID |
| GET | `/api/v1/heritage/sites/slug/{slug}` | Get site by slug |
| GET | `/api/v1/heritage/categories` | List categories |
| GET | `/api/v1/news` | List news articles |
| GET | `/api/v1/news/{id}` | Get news by ID |
| GET | `/api/v1/news/slug/{slug}` | Get news by slug |
| GET | `/api/v1/timeline` | List timeline events |
| GET | `/api/v1/timeline/{id}` | Get timeline event by ID |
| GET | `/api/v1/visit-info` | List visit information |
| GET | `/api/v1/visit-info/{id}` | Get visit info by ID |
| GET | `/api/v1/media` | List media files |

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login (sets JWT cookie) |
| POST | `/api/v1/auth/logout` | Logout (clears cookie) |
| GET | `/api/v1/auth/me` | Get current user |

### Protected Endpoints (require authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/heritage/sites` | Create heritage site |
| PATCH | `/api/v1/heritage/sites/{id}` | Update heritage site |
| DELETE | `/api/v1/heritage/sites/{id}` | Delete heritage site |
| POST | `/api/v1/heritage/categories` | Create category |
| PATCH | `/api/v1/heritage/categories/{id}` | Update category |
| DELETE | `/api/v1/heritage/categories/{id}` | Delete category |
| POST | `/api/v1/news` | Create news article |
| PATCH | `/api/v1/news/{id}` | Update news article |
| DELETE | `/api/v1/news/{id}` | Delete news article |
| POST | `/api/v1/timeline` | Create timeline event |
| PATCH | `/api/v1/timeline/{id}` | Update timeline event |
| DELETE | `/api/v1/timeline/{id}` | Delete timeline event |
| POST | `/api/v1/visit-info` | Create visit info |
| PATCH | `/api/v1/visit-info/{id}` | Update visit info |
| DELETE | `/api/v1/visit-info/{id}` | Delete visit info |
| POST | `/api/v1/media/upload` | Upload file to S3 |
| DELETE | `/api/v1/media/{id}` | Delete media file |

## Authentication

The API uses JWT tokens stored in httpOnly cookies for authentication:

```python
# Login sets a cookie
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
username=admin@example.com&password=mypassword

# Response sets cookie: access_token=<jwt>; HttpOnly; Path=/; SameSite=Lax

# Protected endpoints read the cookie automatically
GET /api/v1/auth/me
Cookie: access_token=<jwt>
```

### CORS Configuration

The backend is configured to allow credentials (cookies) from the frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## AWS S3 Media Storage

Media files are uploaded to S3 and served via CloudFront CDN:

1. Frontend uploads file to `/api/v1/media/upload`
2. Backend stores file in S3 with unique key
3. Backend saves metadata to database (MediaFile model)
4. CloudFront URL is returned for display

### Media File Structure

```
s3://meihe-villa-media/
├── images/
│   ├── heritage/
│   ├── news/
│   └── gallery/
└── videos/
```

## Development Notes

- Use async SQLAlchemy for all database operations
- Pydantic schemas in `/app/schemas/` match frontend TypeScript interfaces
- All dates are stored in UTC
- Images should include `width` and `height` metadata when possible
- The `sync_s3_media.py` script can populate the database from existing S3 files
