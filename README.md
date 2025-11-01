# AlmaLead - Lead Management System

A production-ready lead management API built with FastAPI, featuring complete Docker orchestration, comprehensive testing, and detailed design documentation.

## Features

- **Public Lead Submission**: REST API for prospects to submit applications with resume upload
- **Email Notifications**: Automated emails to both prospects and attorneys
- **Attorney Management**: Secure JWT-based API for managing leads
- **Lead State Management**: Track leads through PENDING → REACHED_OUT states
- **File Storage**: MinIO S3-compatible storage for resumes
- **Authentication**: JWT-based authentication for attorneys
- **Comprehensive Testing**: Unit tests, integration tests, and E2E CLI tool
- **API Documentation**: Auto-generated Swagger/ReDoc documentation

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with async support
- **PostgreSQL**: Relational database with UUID primary keys
- **SQLAlchemy 2.0**: ORM with Alembic migrations
- **MinIO**: S3-compatible object storage for resume files
- **MailHog**: SMTP email testing (development)
- **uv**: Fast Python package manager
- **pytest**: Testing framework with async support

### Infrastructure
- **Docker & Docker Compose**: Container orchestration
- **JWT**: Stateless authentication
- **Bcrypt**: Password hashing

## Quick Start

> **📘 New to the project?** See [SETUP.md](SETUP.md) for a complete step-by-step setup guide with troubleshooting.

### Prerequisites

- **Docker Desktop** (required) - includes Docker Compose
- **Python 3.11+** (optional, only for E2E CLI testing)
- **uv** (optional, only for E2E CLI testing) - [Install guide](https://github.com/astral-sh/uv#installation)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AlmaLead
   ```

2. **Configure environment variables**
   ```bash
   cp .env-local .env
   ```

3. **Start all services**
   ```bash
   docker-compose up
   ```

   This will start:
   - Backend (FastAPI) on http://localhost:8000
   - PostgreSQL database
   - MinIO object storage
   - MailHog email server

4. **Wait for services to be ready** (~30-60 seconds)
   - Watch the logs for "Application startup complete"
   - Database migrations run automatically
   - Attorney account is seeded automatically

5. **Install uv (if testing with E2E CLI or running tests)**
   ```bash
   # Mac/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

6. **Test the API**
   ```bash
   cd backend
   uv sync --all-extras  # Installs all dependencies including E2E tools
   cd e2e
   python test.py e2e
   ```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | Swagger UI for API testing |
| **API Documentation** | http://localhost:8000/redoc | ReDoc alternative UI |
| **MinIO Console** | http://localhost:9001 | Object storage management |
| **MailHog UI** | http://localhost:8025 | View sent emails |

## Default Credentials

**Attorney API Access:**
- Email: `attorney@almalead.com`
- Password: `attorney123`

**MinIO Console:**
- Username: `minioadmin`
- Password: `minioadmin`

## Testing the API

### Option 1: E2E CLI Tool (Recommended)

```bash
cd backend/e2e

# Interactive mode
python test.py

# Run full E2E workflow
python test.py e2e

# Create test leads
python test.py create --count 5

# Login
python test.py login

# List leads
python test.py list

# Get specific lead
python test.py get <lead-id>

# Update lead state
python test.py update <lead-id> --state REACHED_OUT
```

See [backend/e2e/README.md](backend/e2e/README.md) for detailed CLI documentation.

### Option 2: Swagger UI

Navigate to http://localhost:8000/docs for interactive API testing with a visual interface.

### Option 3: curl

```bash
# Create lead
curl -X POST http://localhost:8000/api/v1/leads \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john@example.com" \
  -F "resume=@resume.pdf"

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"attorney@almalead.com","password":"attorney123"}' \
  | jq -r '.access_token')

# List leads
curl -X GET "http://localhost:8000/api/v1/leads" \
  -H "Authorization: Bearer $TOKEN"

# Get specific lead
curl -X GET "http://localhost:8000/api/v1/leads/<lead-id>" \
  -H "Authorization: Bearer $TOKEN"

# Update lead state
curl -X PATCH "http://localhost:8000/api/v1/leads/<lead-id>/state" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state":"REACHED_OUT"}'
```

## API Endpoints

### Public Endpoints

#### Create Lead
```http
POST /api/v1/leads
Content-Type: multipart/form-data

first_name: string
last_name: string
email: string (email format)
resume: file (.pdf, .doc, .docx, max 10MB)

Response: 201 Created
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "resume_url": "http://...",
  "state": "PENDING",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "attorney@almalead.com",
  "password": "attorney123"
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Protected Endpoints (Require JWT Token)

All protected endpoints require `Authorization: Bearer <token>` header.

#### Get All Leads
```http
GET /api/v1/leads?skip=0&limit=100&state=PENDING
Authorization: Bearer <token>

Response: 200 OK
{
  "total": 42,
  "skip": 0,
  "limit": 100,
  "leads": [...]
}
```

#### Get Lead by ID
```http
GET /api/v1/leads/{lead_id}
Authorization: Bearer <token>

Response: 200 OK
{ ...lead details... }
```

#### Update Lead State
```http
PATCH /api/v1/leads/{lead_id}/state
Authorization: Bearer <token>
Content-Type: application/json

{
  "state": "REACHED_OUT"
}

Response: 200 OK
{ ...updated lead... }
```

## Development

### Running Locally Without Docker

#### Backend
```bash
cd backend

# Install dependencies
uv sync --extra dev

# Run migrations (includes seed data)
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

### Package Manager: uv

This project uses **`uv`** as the standard package manager for both backend and E2E testing.

**Why uv?**
- Modern, fast Python package manager (10-100x faster than pip)
- Better dependency resolution
- Automatic virtual environment management
- Consistent across the entire project

**Installation:**
```bash
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (if you already have Python)
pip install uv
```

**Note:** `uv` is automatically installed in Docker containers, so you only need it locally if running tests outside Docker.

### Running Tests

#### Unit Tests (Backend)
```bash
cd backend
uv run pytest tests/unit -v
# Note: 'uv' is required for backend development, but Docker handles this automatically
```

#### Integration Tests (Backend)
```bash
cd backend
uv run pytest tests/integration -v
```

#### All Tests with Coverage
```bash
cd backend
uv run pytest tests/ -v --cov=app --cov-report=html
```

View coverage report at `backend/htmlcov/index.html`

#### E2E Workflow Test
```bash
cd backend/e2e
python test.py e2e
```

## Project Structure

```
AlmaLead/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API endpoints (routes)
│   │   │   ├── deps.py  # Dependencies (auth, DB)
│   │   │   └── v1/      # API version 1
│   │   ├── core/        # Config, security, enums
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── schemas/     # Pydantic validation schemas
│   │   ├── services/    # Business logic layer
│   │   ├── repositories/# Data access layer
│   │   ├── db/          # Database setup & migrations
│   │   └── utils/       # Storage, email utilities
│   ├── tests/           # Test suite
│   │   ├── unit/        # Unit tests (services)
│   │   ├── integration/ # Integration tests (API)
│   │   └── conftest.py  # Pytest fixtures
│   ├── e2e/             # End-to-end testing CLI
│   │   ├── test.py      # Python CLI testing tool
│   │   ├── sample_resume.pdf # Test resume file
│   │   └── README.md    # CLI documentation
│   ├── alembic/         # Database migrations
│   └── pyproject.toml   # Python dependencies (uv)
├── docs/                # Additional documentation
├── DESIGN.md            # System design document
├── PROGRESS.md          # Implementation progress
├── docker-compose.yml   # Docker orchestration
├── .env.example         # Environment template
└── README.md            # This file
```

## Architecture

See [DESIGN.md](DESIGN.md) for comprehensive system design documentation covering:
- Layered architecture patterns
- Technology stack rationale
- Security considerations
- Scalability strategies
- Deployment architecture
- And much more

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│              API/Controller Layer                    │
│         (FastAPI routes, validation)                 │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              Service Layer                           │
│      (Business logic, orchestration)                 │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│            Repository Layer                          │
│        (Data access abstraction)                     │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              Database Layer                          │
│         (PostgreSQL, SQLAlchemy)                     │
└─────────────────────────────────────────────────────┘

     External Services: MinIO, SMTP (MailHog)
```

### Key Design Patterns

- **Layered Architecture**: Separation of concerns with API, Service, and Repository layers
- **Repository Pattern**: Data access abstraction
- **Service Layer Pattern**: Business logic orchestration
- **Protocol-based Storage**: Easy swap between MinIO and AWS S3
- **Dependency Injection**: FastAPI's Depends() for clean code

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `MINIO_*`: Object storage configuration
- `SMTP_*`: Email server configuration
- `JWT_SECRET`: Secret key for JWT tokens (change in production!)
- `ATTORNEY_*`: Attorney account credentials
- `MAX_UPLOAD_SIZE`: Maximum resume file size (bytes)
- `ALLOWED_EXTENSIONS`: Permitted file types

## Troubleshooting

### Services won't start
```bash
# Check if ports are already in use
docker-compose down
docker-compose up --force-recreate
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker-compose ps
# Wait for health checks to pass
```

### MinIO bucket errors
```bash
# Restart MinIO service
docker-compose restart minio
```

### Can't see emails
- Check MailHog UI at http://localhost:8025
- Emails are captured, not sent to real addresses

### Tests failing
```bash
# Make sure dependencies are installed
cd backend
uv sync --all-extras

# Run tests with verbose output
uv run pytest tests/ -v --tb=short
```

### E2E CLI connection errors
```bash
# Make sure backend is running
docker-compose up backend

# Check health
cd backend
uv sync --all-extras  # Make sure dependencies are installed
cd e2e
python test.py health
```

### uv not found
```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh  # Mac/Linux
# or
pip install uv  # Alternative method
```

## Production Deployment

For production deployment:

1. **Update environment variables**
   - Generate strong `JWT_SECRET` (min 32 characters)
   - Change all passwords and secrets
   - Use real email SMTP (SendGrid, AWS SES, etc.)
   - Use AWS S3 or production MinIO cluster
   - Set secure `ATTORNEY_PASSWORD`

2. **Security hardening**
   - Enable HTTPS/TLS with proper certificates
   - Configure CORS for your domain only
   - Implement rate limiting (SlowAPI)
   - Use secure password policies
   - Regular security audits

3. **Infrastructure**
   - Use managed PostgreSQL (AWS RDS, etc.)
   - Use AWS S3 for file storage
   - Add load balancer for backend scaling
   - Configure monitoring and alerting
   - Set up automated backups

4. **Deployment options**
   - AWS ECS/Fargate
   - Kubernetes
   - Traditional VMs with systemd

See [DESIGN.md - Deployment Architecture](DESIGN.md#deployment-architecture) for detailed deployment strategies.

## Testing Coverage

- **Unit Tests**: 11 tests (service layer logic)
- **Integration Tests**: 22 tests (API endpoints)
- **Total**: 33 tests, all passing ✅
- **Coverage**: >90% of core business logic

## Documentation

- **[SETUP.md](SETUP.md)**: Complete setup guide with troubleshooting (for first-time setup)

- **[DESIGN.md](DESIGN.md)**: Comprehensive system design document (1700+ lines)
  - Architecture patterns and rationale
  - Technology stack decisions
  - Security considerations
  - Scalability strategies
  - Performance benchmarks
  - And much more

- **[PROGRESS.md](PROGRESS.md)**: Implementation status and quick start guide

- **[backend/e2e/README.md](backend/e2e/README.md)**: E2E CLI tool documentation

- **[Requirements.md](Requirements.md)**: Original assignment requirements

- **API Docs**: Auto-generated at http://localhost:8000/docs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`cd backend && uv run pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

[Your License Here]

## Support

For issues or questions:
- Check [DESIGN.md](DESIGN.md) for architecture details
- Review API docs at http://localhost:8000/docs
- Check logs: `docker-compose logs -f backend`
- Run E2E tests: `cd backend/e2e && python test.py e2e`

---

**Built for AlmaLead Assignment**

*A production-ready API demonstrating modern FastAPI development practices, clean architecture, comprehensive testing, and detailed documentation.*
