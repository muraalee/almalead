# AlmaLead API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Protected endpoints require a JWT Bearer token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Obtain a token by logging in via `/api/v1/auth/login`.

---

## API Endpoints

### Health Check

#### GET /health

Check if the API is running.

**Response**:
```json
{
  "status": "healthy"
}
```

---

## Authentication

### Login

#### POST /api/v1/auth/login

Authenticate an attorney and receive a JWT token.

**Request Body**:
```json
{
  "email": "attorney@company.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "attorney@company.com",
    "password": "SecurePassword123!"
  }'
```

---

## Leads

### Create Lead (Public)

#### POST /api/v1/leads

Submit a new lead application. This endpoint is **public** (no authentication required).

**Request**:
- Content-Type: `multipart/form-data`

**Form Data**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| first_name | string | Yes | Prospect's first name |
| last_name | string | Yes | Prospect's last name |
| email | string | Yes | Prospect's email (valid format) |
| resume | file | Yes | Resume file (.pdf, .doc, .docx, max 10MB) |

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_url": "http://minio:9000/resumes/550e8400-e29b-41d4-a716-446655440000.pdf",
  "state": "PENDING",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input (missing fields, invalid email)
- `413 Request Entity Too Large`: File exceeds 10MB
- `400 Bad Request`: Invalid file type

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/leads \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john.doe@example.com" \
  -F "resume=@/path/to/resume.pdf"
```

**Side Effects**:
1. Resume uploaded to MinIO storage
2. Lead created in database with state=PENDING
3. Confirmation email sent to prospect
4. Notification email sent to attorney

---

### Get All Leads (Protected)

#### GET /api/v1/leads

Retrieve all leads with optional filtering and pagination.

**Authentication**: Required

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of leads to skip |
| limit | integer | 100 | Maximum number of leads to return |
| state | enum | null | Filter by state (PENDING, REACHED_OUT) |

**Response** (200 OK):
```json
{
  "total": 42,
  "leads": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "resume_url": "http://minio:9000/resumes/550e8400-e29b-41d4-a716-446655440000.pdf",
      "state": "PENDING",
      "created_at": "2025-11-01T10:00:00Z",
      "updated_at": "2025-11-01T10:00:00Z"
    },
    ...
  ]
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/leads?skip=0&limit=10&state=PENDING" \
  -H "Authorization: Bearer <your_token>"
```

---

### Get Lead by ID (Protected)

#### GET /api/v1/leads/{lead_id}

Retrieve a specific lead by UUID.

**Authentication**: Required

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| lead_id | UUID | Lead identifier |

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_url": "http://minio:9000/resumes/550e8400-e29b-41d4-a716-446655440000.pdf",
  "state": "PENDING",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:00:00Z"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token
- `404 Not Found`: Lead not found

**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/v1/leads/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_token>"
```

---

### Update Lead State (Protected)

#### PATCH /api/v1/leads/{lead_id}/state

Update the state of a lead.

**Authentication**: Required

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| lead_id | UUID | Lead identifier |

**Request Body**:
```json
{
  "state": "REACHED_OUT"
}
```

**Valid States**:
- `PENDING`
- `REACHED_OUT`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "resume_url": "http://minio:9000/resumes/550e8400-e29b-41d4-a716-446655440000.pdf",
  "state": "REACHED_OUT",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:30:00Z"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token
- `404 Not Found`: Lead not found
- `400 Bad Request`: Invalid state value

**cURL Example**:
```bash
curl -X PATCH http://localhost:8000/api/v1/leads/550e8400-e29b-41d4-a716-446655440000/state \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"state": "REACHED_OUT"}'
```

---

## Data Models

### Lead

```typescript
{
  id: string (UUID);
  first_name: string;
  last_name: string;
  email: string (email format);
  resume_url: string (URL);
  state: "PENDING" | "REACHED_OUT";
  created_at: string (ISO 8601 datetime);
  updated_at: string (ISO 8601 datetime);
}
```

### Token Response

```typescript
{
  access_token: string (JWT token);
  token_type: string ("bearer");
}
```

### Login Request

```typescript
{
  email: string (email format);
  password: string;
}
```

### Lead State Update

```typescript
{
  state: "PENDING" | "REACHED_OUT";
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 404 | Not Found | Resource not found |
| 413 | Payload Too Large | File exceeds size limit |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider:
- Rate limiting on public endpoints (lead submission)
- Higher limits for authenticated users
- IP-based rate limiting

---

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints
- See request/response schemas
- Try out API calls directly in the browser
- Download OpenAPI specification

---

## Postman Collection

You can import this API into Postman using the OpenAPI spec:

1. Visit http://localhost:8000/openapi.json
2. Copy the JSON
3. In Postman: Import → Raw Text → Paste JSON

---

## Authentication Flow

```
1. POST /api/v1/auth/login
   ├─ Request: { email, password }
   └─ Response: { access_token, token_type }

2. Store token in client (localStorage, cookie, etc.)

3. Include token in subsequent requests:
   Authorization: Bearer <access_token>

4. Token expires after 24 hours
   └─ Re-authenticate to get new token
```

---

## File Upload Specifications

### Resume Upload

**Accepted Formats**:
- PDF (.pdf)
- Microsoft Word (.doc)
- Microsoft Word (.docx)

**Size Limit**: 10 MB (10,485,760 bytes)

**Storage**:
- Files stored in MinIO bucket named "resumes"
- Filename format: `{uuid}.{extension}`
- Access via presigned URL or direct MinIO access

**Validation**:
1. File extension check
2. File size check
3. MIME type verification (future enhancement)

---

## Pagination

All list endpoints support pagination:

```
GET /api/v1/leads?skip=0&limit=10
```

- `skip`: Offset from the beginning (default: 0)
- `limit`: Maximum items to return (default: 100, max: 1000)

Response includes:
- `total`: Total number of items
- `leads`: Array of items for current page

Example: To get page 2 with 20 items per page:
```
GET /api/v1/leads?skip=20&limit=20
```

---

## Filtering

### Filter by State

```
GET /api/v1/leads?state=PENDING
GET /api/v1/leads?state=REACHED_OUT
```

### Combining Filters

```
GET /api/v1/leads?state=PENDING&skip=0&limit=10
```

---

## Testing the API

### Using cURL

See individual endpoint examples above.

### Using Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "attorney@company.com", "password": "SecurePassword123!"}
)
token = response.json()["access_token"]

# Get leads
response = requests.get(
    "http://localhost:8000/api/v1/leads",
    headers={"Authorization": f"Bearer {token}"}
)
leads = response.json()["leads"]
```

### Using JavaScript/Fetch

```javascript
// Login
const response = await fetch("http://localhost:8000/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "attorney@company.com",
    password: "SecurePassword123!"
  })
});
const { access_token } = await response.json();

// Get leads
const leadsResponse = await fetch("http://localhost:8000/api/v1/leads", {
  headers: { Authorization: `Bearer ${access_token}` }
});
const { leads } = await leadsResponse.json();
```

---

## WebSocket Support

Not currently implemented. Future consideration for real-time updates.

---

## Versioning

Current version: `v1`

All endpoints are prefixed with `/api/v1/`.

Future versions will use `/api/v2/`, etc., maintaining backward compatibility.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-01
**API Version**: 1.0.0
