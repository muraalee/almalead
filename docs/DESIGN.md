# AlmaLead - Design Document

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Technology Choices](#technology-choices)
4. [Design Patterns](#design-patterns)
5. [Security Considerations](#security-considerations)
6. [Scalability & Performance](#scalability--performance)
7. [Trade-offs & Future Improvements](#trade-offs--future-improvements)

## System Overview

AlmaLead is a lead management system designed for law firms to collect and manage prospect applications. The system consists of:

- **Public-facing form**: Prospects submit their information with resume upload
- **Attorney portal**: Secure dashboard for managing leads
- **Email notifications**: Automated emails to prospects and attorneys
- **File storage**: Secure storage for resume files

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Environment                    │
│                                                          │
│  ┌────────────┐     ┌──────────────┐                   │
│  │  Next.js   │────▶│   FastAPI    │                   │
│  │  Frontend  │     │   Backend    │                   │
│  │  (Port 3000│     │  (Port 8000) │                   │
│  └────────────┘     └──────┬───────┘                   │
│                            │                             │
│                     ┌──────┴──────┐                     │
│                     │             │                      │
│              ┌──────▼────┐  ┌────▼─────┐               │
│              │ PostgreSQL│  │  MinIO   │               │
│              │  Database │  │ Storage  │               │
│              └───────────┘  └──────────┘               │
│                                                          │
│              ┌──────────────┐                           │
│              │   MailHog    │                           │
│              │  SMTP Server │                           │
│              └──────────────┘                           │
└─────────────────────────────────────────────────────────┘
```

## Architecture Decisions

### 1. Layered Backend Architecture

**Decision**: Implement a 3-layer architecture (Controller → Service → Repository)

**Rationale**:
- **Separation of Concerns**: Each layer has a distinct responsibility
- **Testability**: Layers can be tested in isolation with mocked dependencies
- **Maintainability**: Changes to one layer don't affect others
- **Industry Standard**: Widely recognized pattern in enterprise applications

**Implementation**:
```
API Layer (app/api/)
  ├─ Handles HTTP requests/responses
  ├─ Input validation (Pydantic)
  └─ Authentication/Authorization

Service Layer (app/services/)
  ├─ Business logic
  ├─ Orchestrates multiple operations
  └─ Calls repositories, storage, email

Repository Layer (app/repositories/)
  ├─ Database queries (SQLAlchemy)
  ├─ CRUD operations
  └─ Data access abstraction
```

### 2. Storage Abstraction

**Decision**: Create a Protocol-based storage interface with MinIO implementation

**Rationale**:
- **Flexibility**: Easy to swap MinIO with AWS S3 in production
- **Testability**: Can mock storage in tests
- **S3 Compatibility**: MinIO uses same API as AWS S3

**Code Structure**:
```python
# app/utils/storage.py
class StorageInterface(Protocol):
    def upload_file(self, file, object_name) -> str: ...
    def get_file_url(self, object_name) -> str: ...
    def delete_file(self, object_name) -> bool: ...

# app/utils/minio_storage.py
class MinIOStorage:
    # Implements StorageInterface
    # Can be replaced with S3Storage without code changes
```

**Benefits**:
- Same code works locally (MinIO) and production (S3)
- No vendor lock-in
- Cost-effective local development

### 3. Docker-First Development

**Decision**: All services run in Docker containers

**Rationale**:
- **Environment Consistency**: "Works on my machine" → "Works everywhere"
- **Easy Setup**: Single `docker-compose up` command
- **Matches Production**: Development environment mirrors production
- **No Manual Setup**: No need to install PostgreSQL, SMTP server locally

**Services**:
- **FastAPI**: Backend application
- **Next.js**: Frontend application
- **PostgreSQL**: Relational database
- **MinIO**: Object storage
- **MailHog**: Email testing

### 4. uv for Python Package Management

**Decision**: Use `uv` instead of pip/poetry

**Rationale**:
- **Speed**: 10-100x faster than pip
- **Modern**: Built with Rust, actively maintained
- **PEP 621 Compliant**: Uses standard `pyproject.toml`
- **Lockfile**: Reproducible builds with `uv.lock`

### 5. Next.js with TypeScript

**Decision**: Use Next.js 15 with TypeScript for frontend

**Rationale**:
- **Type Safety**: TypeScript prevents runtime errors
- **Server-Side Rendering**: Better SEO and performance
- **App Router**: Modern routing with layouts
- **Developer Experience**: Hot reload, great tooling

### 6. JWT Authentication

**Decision**: Use JWT tokens for attorney authentication

**Rationale**:
- **Stateless**: No session storage needed
- **Scalable**: Works across multiple backend instances
- **Standard**: Industry-standard authentication method
- **Secure**: Signed tokens prevent tampering

**Flow**:
```
1. Attorney logs in → POST /api/v1/auth/login
2. Backend validates credentials
3. Backend generates JWT token (exp: 24 hours)
4. Frontend stores token in localStorage
5. Frontend sends token in Authorization header
6. Backend validates token on protected endpoints
```

## Technology Choices

### Backend: FastAPI

**Why FastAPI over Django/Flask?**
- **Performance**: Async support, one of the fastest Python frameworks
- **Type Safety**: Pydantic validation, automatic OpenAPI docs
- **Modern**: Built for Python 3.7+, uses type hints
- **Developer Experience**: Auto-generated API docs (Swagger UI)

### Database: PostgreSQL

**Why PostgreSQL over MySQL/MongoDB?**
- **Reliability**: ACID compliant, battle-tested
- **Features**: JSON support, full-text search, array types
- **Ecosystem**: Excellent Python support (psycopg2, SQLAlchemy)
- **Performance**: Handles concurrent writes well

### ORM: SQLAlchemy with Alembic

**Why SQLAlchemy?**
- **Mature**: Industry standard for Python
- **Flexible**: Can use ORM or raw SQL
- **Migrations**: Alembic provides version-controlled schema changes
- **Type-Safe**: Works well with Pydantic models

### Object Storage: MinIO

**Why MinIO over filesystem storage?**
- **S3 Compatible**: Same API as AWS S3
- **Scalable**: Distributed storage in production
- **Flexible**: Easy to swap with real S3
- **Access Control**: Bucket policies, presigned URLs

**Alternative Considered**: Local filesystem
- ❌ Not scalable
- ❌ Hard to replicate across instances
- ❌ No built-in access control

### Email: MailHog (Development)

**Why MailHog?**
- **Email Capture**: View all sent emails in web UI
- **No Setup**: Works out of the box
- **Safe**: Never accidentally emails real users
- **Easy Swap**: Replace with real SMTP for production

### Frontend: Next.js

**Why Next.js over Create React App?**
- **Server-Side Rendering**: Better initial load time
- **File-based Routing**: No need for react-router
- **API Routes**: Can serve backend logic if needed
- **Built-in Optimization**: Image optimization, code splitting

### Styling: Tailwind CSS

**Why Tailwind over Bootstrap/Material-UI?**
- **Utility-First**: Faster development
- **Customizable**: Easy to match brand
- **Small Bundle**: Only includes used styles
- **Modern**: Great developer experience

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract database operations from business logic

**Example**:
```python
class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, lead: Lead) -> Lead:
        self.db.add(lead)
        self.db.commit()
        return lead

    def get_by_id(self, lead_id: UUID) -> Optional[Lead]:
        return self.db.query(Lead).filter(Lead.id == lead_id).first()
```

**Benefits**:
- Single source of truth for data access
- Easy to mock in tests
- Can optimize queries in one place

### 2. Service Layer Pattern

**Purpose**: Encapsulate business logic and orchestrate operations

**Example**:
```python
class LeadService:
    def __init__(self, db: Session):
        self.lead_repo = LeadRepository(db)
        self.storage = storage
        self.email_service = email_service

    async def create_lead(self, data, file):
        # 1. Upload resume
        url = self.storage.upload_file(file, filename)

        # 2. Create lead in database
        lead = self.lead_repo.create(Lead(...))

        # 3. Send emails
        await self.email_service.send_prospect_confirmation(...)
        await self.email_service.send_attorney_notification(...)

        return lead
```

**Benefits**:
- Transaction management
- Orchestrates multiple repositories
- Keeps API layer thin

### 3. Dependency Injection

**Purpose**: Provide dependencies to components

**Example**:
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/leads")
def create_lead(db: Session = Depends(get_db)):
    service = LeadService(db)
    ...
```

**Benefits**:
- Testable (can inject mocks)
- Flexible (can swap implementations)
- FastAPI manages lifecycle

### 4. Protocol (Interface) Pattern

**Purpose**: Define contracts without implementation

**Example**:
```python
class StorageInterface(Protocol):
    def upload_file(...) -> str: ...

class MinIOStorage:
    # Implements interface

class S3Storage:
    # Also implements interface
```

**Benefits**:
- Type-safe duck typing
- Easy to swap implementations
- Clear contracts

## Security Considerations

### 1. Authentication & Authorization

**Implementation**:
- JWT tokens with expiration (24 hours)
- Bearer token authentication
- Password hashing with bcrypt
- Protected endpoints require valid token

**Security Measures**:
- Passwords never stored in plain text
- Tokens signed with secret key
- Token validation on every request

### 2. File Upload Security

**Validations**:
- File type restriction (.pdf, .doc, .docx)
- File size limit (10MB)
- Unique filename generation (prevents overwrites)
- Stored in isolated bucket

**Potential Improvements**:
- Virus scanning
- Content-type verification
- Filename sanitization

### 3. SQL Injection Prevention

**Protection**:
- SQLAlchemy ORM (parameterized queries)
- Pydantic validation (input sanitization)
- No raw SQL with user input

### 4. CORS Configuration

**Current**: Allow all origins (development)
**Production**: Specify exact frontend domain

### 5. Environment Variables

**Sensitive Data**:
- All secrets in `.env` file
- `.env` excluded from git
- Different configs for dev/prod

## Scalability & Performance

### Horizontal Scaling

**Backend**:
- Stateless design (JWT tokens)
- Can run multiple instances behind load balancer
- Database connection pooling

**Frontend**:
- Static assets can be CDN-cached
- API calls are stateless
- Can run multiple instances

### Database Optimization

**Current**:
- Indexes on email, state fields
- Connection pooling
- Efficient queries (eager loading when needed)

**Future**:
- Read replicas for heavy read workloads
- Caching layer (Redis) for frequent queries
- Database partitioning for large datasets

### File Storage

**Current**:
- MinIO with single bucket
- Direct upload/download

**Future**:
- CDN in front of MinIO/S3
- Presigned URLs for direct browser upload
- Thumbnail generation for preview

### Email Performance

**Current**:
- Synchronous email sending (blocks response)

**Future**:
- Background task queue (Celery, RQ)
- Batch email sending
- Email service with better deliverability

## Trade-offs & Future Improvements

### Current Limitations

1. **Synchronous Email Sending**
   - **Issue**: API waits for email to send
   - **Solution**: Background task queue

2. **Single Attorney Account**
   - **Issue**: Hardcoded credentials
   - **Solution**: User management system with registration

3. **No Pagination on Frontend**
   - **Issue**: All leads loaded at once
   - **Solution**: Implement infinite scroll or pagination

4. **No Search/Filter**
   - **Issue**: Hard to find specific lead
   - **Solution**: Add search by name/email, filter by state/date

5. **No Audit Logs**
   - **Issue**: Can't track who changed what
   - **Solution**: Add audit log table

6. **Basic Error Handling**
   - **Issue**: Generic error messages
   - **Solution**: Structured error responses, better logging

### Future Enhancements

#### Phase 2: User Management
- Attorney registration/invitation
- Role-based access control (admin, attorney, viewer)
- User profile management

#### Phase 3: Advanced Features
- Lead assignment to specific attorneys
- Lead scoring/prioritization
- Notes/comments on leads
- Lead activity timeline
- Email templates customization
- Bulk operations

#### Phase 4: Analytics
- Lead conversion metrics
- Time-to-response tracking
- Attorney performance dashboard
- Reports and exports

#### Phase 5: Integrations
- Calendar integration (schedule interviews)
- CRM integration (Salesforce, HubSpot)
- Video interview integration (Zoom, Meet)
- Background check services

### Production Readiness Checklist

- [ ] Replace MailHog with real SMTP
- [ ] Use AWS S3 instead of MinIO
- [ ] Add rate limiting
- [ ] Implement CAPTCHA on public form
- [ ] Add comprehensive logging
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure CDN for frontend
- [ ] Set up CI/CD pipeline
- [ ] Add load balancer
- [ ] Configure auto-scaling
- [ ] Set up backup strategy
- [ ] Implement disaster recovery
- [ ] Security audit
- [ ] Performance testing
- [ ] Penetration testing

## Conclusion

AlmaLead is designed with production-readiness in mind while maintaining simplicity for the MVP. The layered architecture, clear separation of concerns, and use of industry-standard patterns make it easy to maintain, test, and extend.

Key strengths:
- **Clean Architecture**: Easy to understand and modify
- **Type Safety**: TypeScript + Pydantic reduce bugs
- **Docker-First**: Consistent environments
- **Abstraction**: Easy to swap components
- **Scalable**: Can handle growth

The design prioritizes:
1. **Developer Experience**: Easy to set up and develop
2. **Maintainability**: Clear patterns and structure
3. **Scalability**: Can grow with the business
4. **Security**: Following best practices

---

**Document Version**: 1.0
**Last Updated**: 2025-11-01
**Author**: AlmaLead Development Team
