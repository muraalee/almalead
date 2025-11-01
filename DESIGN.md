# AlmaLead - System Design Document

> **Design Philosophy**: Self-contained, production-ready, works out-of-the-box

## Overview

AlmaLead is a lead management system for law firms. Prospects submit applications with resumes via a public form, and attorneys manage leads through a protected API.

**Core Requirements**:
- Public lead submission (no auth)
- Protected lead management (JWT auth)
- Resume file storage
- Email notifications
- Lead state tracking (PENDING → REACHED_OUT)

---

## Architecture

### Layered Architecture

```
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database (PostgreSQL + MinIO)
```

**Why?**
- **Testability**: Each layer can be tested independently
- **Flexibility**: Easy to swap implementations (e.g., MinIO → S3)
- **Maintainability**: Changes are isolated to specific layers

---

## Key Design Decisions

### 1. Self-Contained Docker Setup

**Decision**: All services run in Docker with docker-compose
- PostgreSQL (database)
- MinIO (file storage)
- MailHog (email server)
- Backend (FastAPI)

**Rationale**:
- **Out-of-box experience**: `docker-compose up` and everything works
- **No external dependencies**: No AWS account, no email service signup
- **Consistent environments**: Same setup for dev, testing, and demo
- **Easy onboarding**: New developers can start in minutes

**Trade-off**: Production will need real services, but code is designed for easy swap (see below).

---

### 2. Checked-in `.env` File

**Decision**: `.env` file is committed to Git with working defaults

**Rationale**:
- **Works immediately**: No manual configuration needed
- **Example and defaults combined**: One file serves both purposes
- **Developer experience**: Clone → `docker-compose up` → done
- **Safe defaults**: Uses localhost-only services, fake SMTP, test credentials

**Security Note**: Production deployments MUST replace:
- `JWT_SECRET` (currently a placeholder)
- `ATTORNEY_PASSWORD` (currently `attorney123`)
- Database passwords
- Storage credentials

The `.env` is explicitly documented as "development defaults" in comments.

---

### 3. MinIO for Object Storage

**Decision**: Use MinIO instead of AWS S3 for local development

**Rationale**:
- **Self-contained**: No AWS account required
- **S3-compatible API**: MinIO implements the S3 protocol
- **Easy production swap**: Change 3 lines of code to use real S3
- **Local development**: Faster, no network latency, no costs

**Production Path**:
```python
# Current (MinIO)
MINIO_ENDPOINT=minio:9000

# Production (AWS S3)
MINIO_ENDPOINT=s3.amazonaws.com
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

The storage abstraction (`StorageInterface` Protocol) allows swapping storage backends without changing business logic.

---

### 4. MailHog for Email Testing

**Decision**: Use MailHog instead of a real SMTP server

**Rationale**:
- **Self-contained**: No external email service needed (SendGrid, AWS SES, etc.)
- **Development-friendly**: Captures all emails in a web UI (http://localhost:8025)
- **No spam risk**: Emails never leave localhost
- **Test automation**: E2E tests can verify emails were sent

**Production Path**:
```python
# Current (MailHog)
SMTP_HOST=mailhog
SMTP_PORT=1025

# Production (Real SMTP)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-api-key
```

No code changes required—just environment variables.

---

### 5. Alembic Data Migrations for Seed Data

**Decision**: Use Alembic migration to seed the attorney user, not a separate Python script

**Rationale**:
- **Version controlled**: Seed data is part of migration history
- **Idempotent**: Safe to run multiple times
- **Auditable**: Can see exactly when/how data was seeded
- **Reversible**: `alembic downgrade` removes seed data
- **Standard practice**: This is how reference data should be handled

**Previous Approach** (removed):
```bash
# Old way (separate script)
alembic upgrade head
python -m app.db.init_db  # ❌ Separate step

# New way (integrated)
alembic upgrade head  # ✅ Seeds data automatically
```

---

### 6. In-Memory SQLite for Tests

**Decision**: Tests use in-memory SQLite (`sqlite:///:memory:`)

**Rationale**:
- **Fast**: No disk I/O
- **Clean**: No leftover files
- **Isolated**: Each test gets a fresh database
- **No setup**: Works immediately without PostgreSQL running

**Previous Approach** (removed):
```python
# Old: Created test.db file
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# New: In-memory only
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
```

---

## Technology Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **API** | FastAPI | Async support, auto-docs, type safety |
| **Database** | PostgreSQL | ACID compliance, JSON support, mature |
| **ORM** | SQLAlchemy 2.0 | Industry standard, type-safe |
| **Migrations** | Alembic | Handles schema + data migrations |
| **Storage** | MinIO | S3-compatible, self-contained |
| **Email** | MailHog | SMTP capture for testing |
| **Auth** | JWT | Stateless, scalable |
| **Password** | bcrypt | Industry standard (OWASP recommended) |
| **Testing** | pytest | Async support, fixtures, coverage |
| **Package Manager** | uv | 10-100x faster than pip |

---

## Data Models

### User Model
```python
id: UUID (PK)
email: str (unique)
hashed_password: str
first_name: str
last_name: str
created_at: datetime
updated_at: datetime
```

### Lead Model
```python
id: UUID (PK)
first_name: str
last_name: str
email: str (indexed)
resume_url: str
state: LeadState (PENDING | REACHED_OUT, indexed)
created_at: datetime
updated_at: datetime
```

**Design Notes**:
- UUIDs prevent enumeration attacks
- `updated_at` tracks state changes
- State is an Enum for type safety
- Indexes on `email` and `state` for common queries

---

## API Design

### Public Endpoints

**POST /api/v1/leads** - Create lead (multipart/form-data)
- No authentication required
- Validates email format, file type, file size
- Returns 201 with lead details

### Protected Endpoints (JWT required)

**POST /api/v1/auth/login** - Get JWT token
**GET /api/v1/leads** - List leads (pagination, filtering)
**GET /api/v1/leads/{id}** - Get lead details
**PATCH /api/v1/leads/{id}/state** - Update lead state

**Design Notes**:
- RESTful conventions
- Proper HTTP status codes
- Pagination for list endpoints
- Filtering by state
- Auto-generated OpenAPI docs

---

## Security

### Authentication
- **JWT tokens**: 24-hour expiration
- **HTTP-only cookies**: Prevents XSS (if using cookies)
- **Bearer token**: Standard Authorization header

### File Upload Security
- **Type validation**: Only `.pdf`, `.doc`, `.docx`
- **Size limit**: 10MB max
- **Virus scanning**: Not implemented (future improvement)

### Password Security
- **bcrypt**: OWASP recommended, adaptive cost
- **72-byte limit**: Enforced at application level
- **No plain text**: Passwords never stored or logged

### Database Security
- **Parameterized queries**: SQLAlchemy prevents SQL injection
- **No raw SQL**: Except in migrations (controlled)
- **Error handling**: Rollback on transaction failures

---

## Storage Architecture

### Current: MinIO
```python
class MinIOStorage:
    def upload_file(self, file, name) -> str:
        self.client.put_object(bucket, name, file)
        return f"http://minio:9000/{bucket}/{name}"
```

### Production: AWS S3 (same interface)
```python
# Just change environment variables:
MINIO_ENDPOINT=s3.amazonaws.com
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Optionally use boto3:
import boto3
s3 = boto3.client('s3')
s3.upload_fileobj(file, bucket, name)
```

**Storage Protocol** (`StorageInterface`):
```python
class StorageInterface(Protocol):
    def upload_file(self, file: BinaryIO, name: str) -> str: ...
    def get_file_url(self, name: str) -> str: ...
    def delete_file(self, name: str) -> bool: ...
```

Any storage backend that implements this protocol can be swapped in without changing business logic.

---

## Email System

### Development: MailHog
- Captures all emails in memory
- Web UI at http://localhost:8025
- SMTP on port 1025
- Perfect for testing

### Production: Real SMTP
Common options:
- **SendGrid**: Easy API, good free tier
- **AWS SES**: Low cost, high deliverability
- **Mailgun**: Developer-friendly
- **Postmark**: Transactional emails

**Email Templates**:
- **Prospect confirmation**: "Thank you for submitting..."
- **Attorney notification**: "New lead: {name} ({email})"

No code changes needed—just update SMTP env vars.

---

## Testing Strategy

### Unit Tests (11 tests)
- Service layer logic
- Mocked repositories
- Fast (<1s)

### Integration Tests (22 tests)
- Full API endpoints
- In-memory database
- Real HTTP calls via TestClient

### E2E Tests (Python CLI)
- Real Docker services
- End-to-end workflows
- Manual + automated modes

**Total**: 33 tests, 100% passing ✅

---

## Deployment

### Development (Docker Compose)
```bash
docker-compose up
# All services start automatically
# Attorney account seeded
# Ready in ~60 seconds
```

### Production Options

**1. Docker Compose (Simple)**
- Deploy to VM
- Use docker-compose.yml
- Replace MailHog with real SMTP
- Replace MinIO with S3
- Use managed PostgreSQL (RDS)

**2. Kubernetes (Scalable)**
- Deploy backend as Deployment
- Use external services (RDS, S3, SES)
- Horizontal pod autoscaling
- Load balancer + Ingress

**3. Platform-as-a-Service**
- Heroku, Railway, Render
- Connect to managed database
- Use S3 for storage
- Configure SMTP add-on

---

## Scalability

### Bottlenecks (Current)
1. **Single backend instance**: No horizontal scaling
2. **File uploads**: Blocking I/O during upload
3. **Email sending**: Synchronous SMTP calls

### Solutions

**Horizontal Scaling**:
- Stateless backend → Add more instances behind load balancer
- JWT auth → No session storage needed
- PostgreSQL connection pooling

**Async Processing** (Future):
- **Celery + Redis**: Background tasks for email/upload
- **AWS Lambda**: Serverless resume processing
- **SQS**: Queue for async operations

**Caching** (Future):
- Redis for frequently accessed leads
- CDN for static assets
- CloudFront for resume downloads

---

## Trade-offs

### What We Prioritized
✅ **Developer Experience**: Works out-of-box
✅ **Simplicity**: Minimal external dependencies
✅ **Testability**: Comprehensive test coverage
✅ **Production-Ready Code**: Easy to migrate to real services

### What We Deferred
⏸️ **Background Jobs**: Emails sent synchronously
⏸️ **Caching**: No Redis layer
⏸️ **Advanced Features**: No search, tags, notes, etc.
⏸️ **Multi-tenancy**: Single law firm only

### Future Improvements
1. **Background jobs** with Celery for emails
2. **Search functionality** with ElasticSearch
3. **File scanning** for virus detection
4. **PDF parsing** to extract resume data
5. **Webhooks** for lead status updates
6. **Analytics dashboard** for lead metrics

---

## Running the Application

### Quick Start
```bash
git clone <repo>
cd AlmaLead
docker-compose up
```

That's it! No configuration needed.

### Access
- **API Docs**: http://localhost:8000/docs
- **MailHog**: http://localhost:8025
- **MinIO Console**: http://localhost:9001

### Default Credentials
- **Attorney**: attorney@almalead.com / attorney123
- **MinIO**: minioadmin / minioadmin

---

## Conclusion

AlmaLead demonstrates a **pragmatic approach** to API design:

1. **Self-contained for development** (Docker, MinIO, MailHog)
2. **Production-ready architecture** (layered, tested, documented)
3. **Easy migration path** (S3, real SMTP, managed DB)
4. **Developer-friendly** (works out-of-box, comprehensive docs)

The design prioritizes **getting started quickly** while maintaining **code quality** and **production readiness**. Every decision balances immediate usability with long-term maintainability.

**Key Takeaway**: You can be pragmatic (MailHog, MinIO, checked-in .env) for development while writing production-ready code (storage protocols, proper error handling, comprehensive tests). The two are not mutually exclusive.
