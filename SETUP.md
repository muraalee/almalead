# AlmaLead - Setup Guide

> Get up and running in 3 steps (takes ~2 minutes)

## Prerequisites

You need **Docker Desktop** installed. That's it!
- [Mac](https://docs.docker.com/desktop/install/mac-install/)
- [Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Linux](https://docs.docker.com/desktop/install/linux-install/)

---

## Setup (3 Steps)

### Step 1: Copy Configuration File

```bash
cp .env-local .env
```

This creates your configuration file with working defaults.

### Step 2: Start All Services

```bash
docker-compose up
```

This will:
- Start PostgreSQL (database)
- Start MinIO (file storage)
- Start MailHog (email server)
- Start Backend API
- Run database migrations
- Create attorney account

**Wait about 60 seconds** for all services to start.

### Step 3: Verify It's Working

Open your browser to **http://localhost:8000/docs**

You should see the API documentation (Swagger UI).

---

## Test the API

**Install uv (Python package manager):**

Mac/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Run the E2E test:**

```bash
cd backend
uv sync --all-extras
cd e2e
python test.py e2e
```

You should see:
```
✓ API is healthy
✓ Lead created successfully
✓ Login successful
✓ Found 1 lead(s)
✓ Lead Details: John Doe
✓ Lead updated successfully
🎉 E2E Test Completed Successfully!
```

---

## Access URLs

| Service | URL | Login |
|---------|-----|-------|
| **API Docs** | http://localhost:8000/docs | - |
| **MailHog** (emails) | http://localhost:8025 | - |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |

**Attorney Login:**
- Email: `attorney@company.com`
- Password: `SecurePassword123!`

---

## Troubleshooting

### "Port already in use"

Someone else is using port 8000, 5432, 9000, or 8025.

**Solution:**
```bash
docker-compose down
docker-compose up
```

### "Services won't start"

**Solution:**
```bash
docker-compose down -v
docker-compose up --build
```

This removes old data and rebuilds everything.

### "Can't connect to API"

Make sure Docker is running and wait 60 seconds after `docker-compose up`.

**Check status:**
```bash
docker-compose ps
```

All services should show "Up" or "healthy".

---

## Stop the Application

```bash
# Stop but keep data
docker-compose stop

# Stop and remove everything
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

---

## That's It!

You now have AlmaLead running locally.

For design decisions and architecture details, see [DESIGN.md](DESIGN.md).
