# AlmaLead - Lead Management System - Implementation Approach

## Table of Contents
1. [Original Requirements](#original-requirements)
2. [Technology Stack](#technology-stack)
3. [Architecture Decisions](#architecture-decisions)
4. [Project Structure](#project-structure)
5. [Docker Services](#docker-services)
6. [API Design](#api-design)
7. [Testing Strategy](#testing-strategy)
8. [Configuration](#configuration)
9. [User Setup Experience](#user-setup-experience)
10. [Implementation Checklist](#implementation-checklist)

---

## Original Requirements

### Functional Requirements
- Develop an application to support creating, getting and updating leads
- Lead is a **publicly available** form for prospects to fill in
- **Required fields**:
  - First name
  - Last name
  - Email
  - Resume / CV (file upload)

### Email Notifications
- When lead is submitted, send emails to:
  1. **Prospect**: Confirmation email
  2. **Attorney**: Notification of new lead

### Internal Lead Management
- Internal UI guarded by **authentication**
- List all leads with prospect information
- Each lead has a **state**:
  - Initial: `PENDING`
  - Transitions to: `REACHED_OUT` (manual action by attorney)

### Tech Requirements
- Use **FastAPI** for the application
- Implement all necessary APIs (no UI requirement in original spec)
- Add storage to persist data
- Properly structure code for production-level repo
- Create system design document
- 6-hour timeline

---

## Technology Stack

### Backend
- **FastAPI**: Python web framework
- **PostgreSQL**: Relational database
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations
- **Pydantic**: Data validation and serialization
- **uv**: Python package manager (fast, modern)
- **JWT**: Authentication tokens
- **Pytest**: Testing framework

### Frontend (Bonus - For Testing)
- **Next.js**: React framework with SSR
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling (optional, can use plain CSS)

### Infrastructure (Docker)
- **PostgreSQL**: Database container
- **MinIO**: S3-compatible object storage for resume files
- **MailHog**: SMTP server for testing emails
- **FastAPI**: Backend application container
- **Next.js**: Frontend application container

### Development Tools
- **Docker & Docker Compose**: Container orchestration
- **uv**: Python dependency management
- **.env**: Configuration management

---

## Architecture Decisions

### 1. Local Development with Docker
**Decision**: All services run in Docker containers orchestrated by Docker Compose

**Rationale**:
- Easy one-command setup for reviewers
- Environment consistency
- No need to install PostgreSQL, SMTP server locally
- Production-like environment

### 2. MinIO for Object Storage
**Decision**: Use MinIO (S3-compatible) instead of local filesystem

**Rationale**:
- Abstraction layer allows switching to real S3 in production
- Same API as AWS S3
- Professional approach to file storage
- Resumes stored as objects with proper access control

**Implementation**:
```python
# Storage abstraction (Protocol/Interface)
class StorageInterface(Protocol):
    def upload_file(self, file, bucket, key) -> str: ...
    def get_file_url(self, bucket, key) -> str: ...
    def delete_file(self, bucket, key) -> bool: ...

# MinIO implementation
class MinIOStorage(StorageInterface):
    # Implements interface using MinIO client
    pass

# Easy to swap with S3Storage in production
```

### 3. Layered Architecture
**Decision**: Separate code into Controller → Service → Repository layers

**Rationale**:
- Clear separation of concerns
- Testable components
- Business logic isolated from HTTP and data access
- Industry best practice

**Layers**:
- **API/Controllers**: Handle HTTP requests, validation, responses
- **Services**: Business logic, orchestration, email sending
- **Repositories**: Database queries, data access
- **Models**: SQLAlchemy database models
- **Schemas**: Pydantic DTOs for validation

### 4. Next.js for UI
**Decision**: Build simple UI even though not required

**Rationale**:
- Easy to test the application end-to-end
- Validate JWT authentication flow
- Test both personas (customer and attorney)
- Better demo experience

**Pages**:
- `/`: Public lead submission form
- `/attorney/login`: Attorney login
- `/attorney/dashboard`: List all leads
- `/attorney/leads/[id]`: Lead details + state update

### 5. MailHog for Email Testing
**Decision**: Use MailHog instead of real SMTP

**Rationale**:
- No need for real email credentials
- Web UI to view sent emails (localhost:8025)
- Perfect for local development and testing
- No spam/deliverability concerns

### 6. Extensible Lead States
**Decision**: Use Python Enum for states, designed for future expansion

```python
class LeadState(str, Enum):
    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"
    # Future extensibility:
    # QUALIFIED = "QUALIFIED"
    # REJECTED = "REJECTED"
    # CONVERTED = "CONVERTED"
```

### 7. File Upload Restrictions
**Decision**: Restrict to PDF, DOC, DOCX only

**Validation**:
- MIME type checking
- File extension validation
- Max file size: 10MB
- Proper error messages

### 8. Authentication Strategy
**Decision**: Hardcoded attorney account, JWT tokens

**Rationale**:
- No user registration needed for this scope
- JWT standard for API auth
- Attorney credentials in `.env` for flexibility

---

## Project Structure

```
almalead/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # Controller layer (routes)
│   │   │   ├── __init__.py
│   │   │   ├── deps.py        # Dependencies (get_db, get_current_user)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py    # POST /auth/login
│   │   │       └── leads.py   # Lead CRUD endpoints
│   │   │
│   │   ├── core/              # Core configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py      # Settings (from .env)
│   │   │   ├── security.py    # JWT creation, password hashing
│   │   │   └── enums.py       # LeadState enum
│   │   │
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── lead.py        # Lead model
│   │   │   └── user.py        # User model (attorney)
│   │   │
│   │   ├── schemas/           # Pydantic schemas (DTOs)
│   │   │   ├── __init__.py
│   │   │   ├── lead.py        # LeadCreate, LeadResponse, LeadUpdate
│   │   │   ├── user.py        # UserResponse
│   │   │   └── auth.py        # LoginRequest, TokenResponse
│   │   │
│   │   ├── services/          # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── lead_service.py       # Lead business logic
│   │   │   ├── auth_service.py       # Authentication logic
│   │   │   ├── email_service.py      # Email sending
│   │   │   └── storage_service.py    # File storage abstraction
│   │   │
│   │   ├── repositories/      # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── lead_repository.py    # Lead DB operations
│   │   │   └── user_repository.py    # User DB operations
│   │   │
│   │   ├── db/                # Database setup
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # Import all models
│   │   │   ├── session.py     # Database session
│   │   │   └── init_db.py     # Initialize DB, seed attorney
│   │   │
│   │   ├── utils/             # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── storage.py     # Storage protocol/interface
│   │   │   ├── minio_storage.py  # MinIO implementation
│   │   │   └── email.py       # Email utilities
│   │   │
│   │   └── main.py            # FastAPI application entry
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py        # Pytest fixtures
│   │   ├── unit/              # Unit tests (run on host)
│   │   │   ├── test_services/
│   │   │   │   ├── test_lead_service.py
│   │   │   │   ├── test_auth_service.py
│   │   │   │   └── test_email_service.py
│   │   │   ├── test_repositories/
│   │   │   │   └── test_lead_repository.py
│   │   │   └── test_utils/
│   │   │       └── test_storage.py
│   │   └── integration/       # Integration tests (Docker)
│   │       └── test_api/
│   │           ├── test_auth.py
│   │           └── test_leads.py
│   │
│   ├── alembic/               # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── Dockerfile
│   ├── pyproject.toml         # uv project configuration
│   ├── uv.lock                # Locked dependencies
│   └── .dockerignore
│
├── frontend/                   # Next.js application
│   ├── app/
│   │   ├── page.tsx           # Home - public lead form
│   │   ├── layout.tsx         # Root layout
│   │   ├── attorney/
│   │   │   ├── login/
│   │   │   │   └── page.tsx   # Attorney login
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx   # Lead list
│   │   │   └── leads/
│   │   │       └── [id]/
│   │   │           └── page.tsx  # Lead detail
│   │   └── api/               # Next.js API routes (optional)
│   │
│   ├── components/
│   │   ├── LeadForm.tsx       # Public lead submission
│   │   ├── LeadList.tsx       # Attorney lead list
│   │   ├── LeadDetail.tsx     # Lead detail view
│   │   └── LoginForm.tsx      # Login form
│   │
│   ├── lib/
│   │   ├── api.ts             # API client for FastAPI
│   │   └── auth.ts            # JWT token management
│   │
│   ├── types/
│   │   └── index.ts           # TypeScript types
│   │
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── .dockerignore
│
├── docs/
│   ├── DESIGN.md              # Architecture decisions
│   ├── API.md                 # API documentation
│   └── TESTING.md             # Testing guide
│
├── docker-compose.yml         # Main docker compose
├── docker-compose.test.yml    # Testing docker compose
├── .env.example               # Environment template
├── .gitignore
├── README.md                  # Quick start guide
└── Approach.md                # This document
```

---

## Docker Services

### docker-compose.yml

```yaml
services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: almalead-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio:latest
    container_name: almalead-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  # MailHog (Email testing)
  mailhog:
    image: mailhog/mailhog:latest
    container_name: almalead-mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8025"]
      interval: 5s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: almalead-backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      JWT_SECRET: ${JWT_SECRET}
      ATTORNEY_EMAIL: ${ATTORNEY_EMAIL}
      ATTORNEY_PASSWORD: ${ATTORNEY_PASSWORD}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
      mailhog:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Next.js Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: almalead-frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  postgres_data:
  minio_data:
```

### Access Points
- **Public Form**: http://localhost:3000
- **Attorney Dashboard**: http://localhost:3000/attorney
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **MinIO Console**: http://localhost:9001
- **MailHog UI**: http://localhost:8025

---

## API Design

### Authentication Endpoints

#### POST /api/v1/auth/login
```json
Request:
{
  "email": "attorney@company.com",
  "password": "securepassword123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Lead Endpoints

#### POST /api/v1/leads (Public - No Auth)
```
Content-Type: multipart/form-data

Fields:
- first_name: string (required)
- last_name: string (required)
- email: string (required, valid email)
- resume: file (required, .pdf/.doc/.docx, max 10MB)

Response:
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "resume_url": "http://minio:9000/resumes/uuid-filename.pdf",
  "state": "PENDING",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:00:00Z"
}
```

#### GET /api/v1/leads (Protected)
```
Headers:
Authorization: Bearer <token>

Query Params (optional):
- skip: int (default 0)
- limit: int (default 100)
- state: PENDING | REACHED_OUT

Response:
{
  "total": 42,
  "leads": [
    {
      "id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "resume_url": "...",
      "state": "PENDING",
      "created_at": "...",
      "updated_at": "..."
    },
    ...
  ]
}
```

#### GET /api/v1/leads/{lead_id} (Protected)
```
Headers:
Authorization: Bearer <token>

Response:
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "resume_url": "...",
  "state": "PENDING",
  "created_at": "...",
  "updated_at": "..."
}
```

#### PATCH /api/v1/leads/{lead_id}/state (Protected)
```
Headers:
Authorization: Bearer <token>

Request:
{
  "state": "REACHED_OUT"
}

Response:
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "resume_url": "...",
  "state": "REACHED_OUT",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Testing Strategy

### Unit Tests (Run on Host - No Docker)
**Command**: `cd backend && uv run pytest tests/unit -v`

**Coverage**:
- **Services**:
  - `test_lead_service.py`: Create lead, update state, get leads
  - `test_auth_service.py`: Login, token creation
  - `test_email_service.py`: Email sending logic
  - `test_storage_service.py`: File upload/download

- **Repositories**:
  - `test_lead_repository.py`: DB operations with mocked session
  - `test_user_repository.py`: User DB operations

- **Utils**:
  - `test_storage.py`: Storage abstraction
  - `test_security.py`: JWT, password hashing

**Approach**:
- Mock external dependencies (DB, MinIO, SMTP)
- Fast execution
- Test business logic in isolation

### Integration Tests (Run in Docker)
**Command**: `docker-compose -f docker-compose.test.yml up --abort-on-container-exit`

**Coverage**:
- **API Tests**:
  - `test_auth.py`: Login flow, invalid credentials, JWT validation
  - `test_leads.py`:
    - Create lead (with file upload)
    - List leads (auth required)
    - Get lead detail
    - Update lead state
    - File validation (invalid types, size)

**Approach**:
- Real database (test PostgreSQL instance)
- Real MinIO instance
- Real MailHog instance
- Test full request → response cycle
- Cleanup between tests

### Test Coverage Goals
- **Unit Tests**: >80% coverage
- **Integration Tests**: All API endpoints
- **Critical Paths**: 100% coverage (auth, lead creation, email sending)

### Running Tests

```bash
# Unit tests (fast, no Docker)
cd backend
uv run pytest tests/unit -v --cov=app --cov-report=html

# Integration tests (Docker required)
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# All tests
uv run pytest tests/ -v
```

---

## Configuration

### .env.example
```bash
# Database
POSTGRES_USER=almalead
POSTGRES_PASSWORD=almalead_password
POSTGRES_DB=almalead
DATABASE_URL=postgresql://almalead:almalead_password@postgres:5432/almalead

# MinIO (S3-compatible storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=resumes
MINIO_SECURE=false

# Email (MailHog)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_FROM_EMAIL=noreply@almalead.com
SMTP_FROM_NAME=AlmaLead

# JWT Authentication
JWT_SECRET=your-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Attorney Account (Seeded on startup)
ATTORNEY_EMAIL=attorney@company.com
ATTORNEY_PASSWORD=SecurePassword123!
ATTORNEY_FIRST_NAME=John
ATTORNEY_LAST_NAME=Attorney

# Application
APP_NAME=AlmaLead
APP_VERSION=1.0.0
DEBUG=true

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=.pdf,.doc,.docx
```

### Configuration Loading (backend/app/core/config.py)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "resumes"
    MINIO_SECURE: bool = False

    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # Attorney
    ATTORNEY_EMAIL: str
    ATTORNEY_PASSWORD: str
    ATTORNEY_FIRST_NAME: str = "John"
    ATTORNEY_LAST_NAME: str = "Attorney"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".doc", ".docx"]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## User Setup Experience

### For Reviewers/Users

```bash
# 1. Clone repository
git clone <repository-url>
cd almalead

# 2. Copy environment template
cp .env.example .env

# 3. (Optional) Edit .env if needed
# Most defaults work out of the box
nano .env

# 4. Start all services
docker-compose up -d

# 5. Wait for services to be healthy (~30 seconds)
docker-compose ps

# 6. Access the application
# - Public form: http://localhost:3000
# - Attorney login: http://localhost:3000/attorney/login
#   - Email: attorney@company.com
#   - Password: SecurePassword123!
# - API docs: http://localhost:8000/docs
# - Email inbox: http://localhost:8025

# 7. Stop services
docker-compose down

# 8. Run tests
cd backend
uv run pytest tests/unit -v
```

### First-Time Setup (Development)
```bash
# Backend setup
cd backend
uv sync  # Install dependencies

# Frontend setup
cd frontend
npm install

# Database migrations
cd backend
uv run alembic upgrade head

# Seed attorney account
uv run python -m app.db.init_db
```

---

## Implementation Checklist

### Phase 1: Project Setup
- [ ] Initialize project structure
- [ ] Setup backend with uv (`pyproject.toml`)
- [ ] Setup frontend with Next.js
- [ ] Create Dockerfiles for backend and frontend
- [ ] Create docker-compose.yml
- [ ] Create .env.example
- [ ] Setup .gitignore

### Phase 2: Backend - Core Setup
- [ ] Configure FastAPI app (`main.py`)
- [ ] Setup database connection (`db/session.py`)
- [ ] Create base models (`db/base.py`)
- [ ] Setup Alembic for migrations
- [ ] Configure settings (`core/config.py`)
- [ ] Implement security utilities (`core/security.py`)
- [ ] Create enums (`core/enums.py`)

### Phase 3: Backend - Database Models
- [ ] Create User model (`models/user.py`)
- [ ] Create Lead model (`models/lead.py`)
- [ ] Create initial migration
- [ ] Setup database initialization (`db/init_db.py`)

### Phase 4: Backend - Schemas
- [ ] Create auth schemas (`schemas/auth.py`)
- [ ] Create user schemas (`schemas/user.py`)
- [ ] Create lead schemas (`schemas/lead.py`)

### Phase 5: Backend - Repositories
- [ ] Implement UserRepository (`repositories/user_repository.py`)
- [ ] Implement LeadRepository (`repositories/lead_repository.py`)

### Phase 6: Backend - Services
- [ ] Implement storage abstraction (`utils/storage.py`)
- [ ] Implement MinIO storage (`utils/minio_storage.py`)
- [ ] Implement email service (`services/email_service.py`)
- [ ] Implement auth service (`services/auth_service.py`)
- [ ] Implement lead service (`services/lead_service.py`)

### Phase 7: Backend - API Endpoints
- [ ] Create auth endpoints (`api/v1/auth.py`)
  - [ ] POST /login
- [ ] Create lead endpoints (`api/v1/leads.py`)
  - [ ] POST /leads (public)
  - [ ] GET /leads (protected)
  - [ ] GET /leads/{id} (protected)
  - [ ] PATCH /leads/{id}/state (protected)
- [ ] Setup dependencies (`api/deps.py`)

### Phase 8: Frontend - Setup
- [ ] Configure Next.js project
- [ ] Setup TypeScript types
- [ ] Create API client (`lib/api.ts`)
- [ ] Create auth utilities (`lib/auth.ts`)

### Phase 9: Frontend - Components
- [ ] Create LeadForm component
- [ ] Create LoginForm component
- [ ] Create LeadList component
- [ ] Create LeadDetail component

### Phase 10: Frontend - Pages
- [ ] Create home page (public form)
- [ ] Create attorney login page
- [ ] Create attorney dashboard page
- [ ] Create lead detail page

### Phase 11: Testing - Unit Tests
- [ ] Setup pytest configuration
- [ ] Write service tests
- [ ] Write repository tests
- [ ] Write utility tests
- [ ] Generate coverage report

### Phase 12: Testing - Integration Tests
- [ ] Setup test docker-compose
- [ ] Write auth API tests
- [ ] Write lead API tests
- [ ] Test file upload validation
- [ ] Test email sending

### Phase 13: Documentation
- [ ] Write README.md with setup instructions
- [ ] Write DESIGN.md with architecture decisions
- [ ] Write API.md with endpoint documentation
- [ ] Write TESTING.md with testing guide
- [ ] Add inline code documentation

### Phase 14: Polish & Validation
- [ ] Test complete user flow
- [ ] Verify email sending
- [ ] Verify file upload to MinIO
- [ ] Verify JWT authentication
- [ ] Verify state transitions
- [ ] Test with fresh .env setup
- [ ] Run all tests
- [ ] Code cleanup and formatting

---

## Key Success Criteria

1. **One-command setup**: `docker-compose up` works on first try
2. **All tests pass**: Both unit and integration tests green
3. **Email verification**: Emails visible in MailHog
4. **File storage**: Resumes uploaded to MinIO
5. **Authentication**: JWT working for protected endpoints
6. **State transitions**: PENDING → REACHED_OUT works
7. **Documentation**: Clear, comprehensive, accurate
8. **Code quality**: Clean, well-structured, production-ready

---

## Timeline Estimate

Based on 6-hour constraint:

- **Phase 1-2**: Project setup (30 min)
- **Phase 3-4**: Models & Schemas (30 min)
- **Phase 5-7**: Repositories, Services, APIs (2 hours)
- **Phase 8-10**: Frontend (1.5 hours)
- **Phase 11-12**: Testing (1 hour)
- **Phase 13-14**: Documentation & Polish (30 min)

Total: ~6 hours

---

## Notes & Considerations

### Production Enhancements (Not in Scope)
- Rate limiting on public endpoint
- CAPTCHA for lead submission
- Email templates with HTML
- File virus scanning
- Advanced lead search/filtering
- Lead assignment to multiple attorneys
- Audit logs
- Soft deletes
- More lead states (QUALIFIED, REJECTED, etc.)
- Real S3 integration
- Real email service (SendGrid, SES)
- CI/CD pipeline
- Kubernetes deployment

### Security Considerations Implemented
- JWT for authentication
- Password hashing (bcrypt)
- File type validation
- File size limits
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Environment variable secrets

### Assumptions
- Single attorney user (hardcoded)
- No lead deletion endpoint
- No prospect authentication
- Resume files stay in MinIO (no cleanup)
- Emails are fire-and-forget (no retry logic)
- No pagination on frontend (backend supports it)

---

**Last Updated**: 2025-11-01
**Status**: Ready for implementation
