# AlmaLead E2E Testing

End-to-end testing tool for the AlmaLead API. This CLI tool allows you to test all API endpoints interactively or programmatically.

## Features

- ✅ **Interactive Mode**: Menu-driven interface for manual testing
- ✅ **Command-Line Mode**: Script individual operations
- ✅ **Full E2E Workflow**: Automated end-to-end testing
- ✅ **Token Management**: Automatic JWT token storage and reuse
- ✅ **Random Data Generation**: Create test leads with Faker library
- ✅ **Health Checks**: Verify API availability

## Installation

### Prerequisites

- Python 3.11+
- **uv** (Python package manager) - [Install uv](https://github.com/astral-sh/uv#installation)
- AlmaLead backend running (http://localhost:8000)

### Install uv

If you don't have `uv` installed yet:

```bash
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Install Dependencies

The E2E tools are now part of the backend's development dependencies. Install everything with one command:

```bash
cd backend
uv sync --all-extras
```

This installs:
- Backend dependencies (FastAPI, SQLAlchemy, etc.)
- Test dependencies (pytest, httpx)
- E2E dependencies (requests, faker, python-dotenv)

All dependencies share the same `.venv` for simplicity.

**Note:** This project uses `uv` as the standard package manager for consistency across backend and E2E testing.

## Usage

**Note:** All commands below assume you are in the `backend/e2e` directory:
```bash
cd backend/e2e
```

### Interactive Mode (Recommended)

```bash
python test.py
```

This will show a menu with all available operations:

```
===========================================================
    AlmaLead E2E Testing - Interactive Mode
===========================================================
1. Create a lead
2. Create multiple leads (random data)
3. Login as attorney
4. List all leads
5. Get lead details
6. Update lead state
7. Run full E2E workflow
8. Check API health
9. Logout (clear token)
0. Exit

Select option:
```

### Command-Line Mode

#### Create Leads

```bash
# Create a single lead with specific data
python test.py create --first-name John --last-name Doe --email john@example.com

# Create a single lead with random data
python test.py create

# Create 10 leads with random data
python test.py create --count 10
```

#### Authentication

```bash
# Login and save token
python test.py login

# Logout and clear token
python test.py logout
```

#### List Leads

```bash
# List all leads
python test.py list

# Filter by state
python test.py list --state PENDING
python test.py list --state REACHED_OUT

# Limit results
python test.py list --limit 50
```

#### Get Lead Details

```bash
# Get specific lead by ID
python test.py get <lead-id>

# Example
python test.py get a3b8c9d0-1234-5678-90ab-cdef12345678
```

#### Update Lead State

```bash
# Update lead to REACHED_OUT
python test.py update <lead-id> --state REACHED_OUT

# Update lead back to PENDING
python test.py update <lead-id> --state PENDING
```

#### Run Full E2E Workflow

```bash
# Test all endpoints automatically
python test.py e2e
```

This will:
1. Check API health
2. Create a test lead
3. Login as attorney
4. List all leads
5. Get the created lead details
6. Update the lead state to REACHED_OUT

#### Health Check

```bash
# Check if API is running
python test.py health
```

## Configuration

### Environment Variables

You can customize the configuration using environment variables:

```bash
export ALMALEAD_API_URL=http://localhost:8000
export ATTORNEY_EMAIL=attorney@almalead.com
export ATTORNEY_PASSWORD=attorney123
```

Or create a `.env` file:

```bash
ALMALEAD_API_URL=http://localhost:8000
ATTORNEY_EMAIL=attorney@almalead.com
ATTORNEY_PASSWORD=attorney123
```

### Default Configuration

- **API URL**: `http://localhost:8000`
- **Attorney Email**: `attorney@almalead.com`
- **Attorney Password**: `attorney123`
- **Token Storage**: `~/.almalead_token`

## Examples

### Complete Testing Workflow

```bash
# 1. Check if API is running
python test.py health

# 2. Create some test leads
python test.py create --count 5

# 3. Login
python test.py login

# 4. View all leads
python test.py list

# 5. Get details of a specific lead
python test.py get <lead-id>

# 6. Update lead state
python test.py update <lead-id> --state REACHED_OUT

# 7. Filter leads by state
python test.py list --state REACHED_OUT
```

### Automated E2E Test

```bash
# Run the complete workflow automatically
python test.py e2e
```

Expected output:
```
======================================================================
🚀 Starting AlmaLead E2E Test Workflow
======================================================================

[Step 0/5] Checking API health...
✓ API is healthy

[Step 1/5] Creating test lead...
✓ Lead created successfully

[Step 2/5] Logging in as attorney...
✓ Login successful

[Step 3/5] Listing all leads...
✓ Found 5 leads

[Step 4/5] Getting lead details...
✓ Lead Details: John Doe

[Step 5/5] Updating lead state to REACHED_OUT...
✓ Lead updated successfully

======================================================================
🎉 E2E Test Completed Successfully!
======================================================================
```

### Using with Different Environments

```bash
# Test against staging
ALMALEAD_API_URL=https://staging.almalead.com python test.py e2e

# Test with different credentials
ATTORNEY_EMAIL=admin@company.com ATTORNEY_PASSWORD=secret123 python test.py login
```

## Files

- **test.py**: Main CLI script (~400 lines)
- **sample_resume.pdf**: Sample PDF file for lead creation
- **requirements.txt**: Python dependencies
- **.almalead_token** (generated): Saved JWT token in your home directory

## Troubleshooting

### "Cannot connect to API"

Make sure the backend is running:

```bash
# From project root
docker-compose up

# Or run backend directly
cd backend
uv run uvicorn app.main:app --reload
```

### "Resume file not found"

Make sure you're running the script from the correct directory:

```bash
cd e2e
python test.py
```

### "faker not installed"

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### "Authentication failed"

Your token may have expired. Login again:

```bash
python test.py login
```

## Development

### Adding New Commands

The CLI is built with argparse. To add a new command:

1. Add a new subparser in `main()`:
```python
new_parser = subparsers.add_parser('mycommand', help='My command')
new_parser.add_argument('--option', help='My option')
```

2. Add the handler in the command execution section:
```python
elif args.command == 'mycommand':
    client.my_method(args.option)
```

3. Add the method to `AlmaLeadClient` class:
```python
def my_method(self, option):
    # Implementation
    pass
```

## Testing in CI/CD

The E2E script can be used in continuous integration:

```bash
# Run E2E test and fail pipeline if it fails
python test.py e2e || exit 1
```

Exit codes:
- `0`: Success
- `1`: Failure

## API Documentation

For detailed API documentation, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Support

For issues or questions, refer to the main project README or DESIGN.md documentation.
