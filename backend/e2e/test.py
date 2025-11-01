#!/usr/bin/env python3
"""
AlmaLead E2E Testing Script

A comprehensive CLI tool for testing the AlmaLead API end-to-end.

Usage:
    # Interactive mode (recommended)
    python test.py

    # Create single lead with specific data
    python test.py create --first-name John --last-name Doe --email john@example.com

    # Create multiple random leads
    python test.py create --count 5

    # Full E2E workflow
    python test.py e2e

    # Login and list leads
    python test.py login
    python test.py list

    # Get and update specific lead
    python test.py get <lead-id>
    python test.py update <lead-id> --state REACHED_OUT
"""

import requests
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    print("Warning: faker not installed. Install with: pip install faker")
    fake = None

# Configuration
API_URL = os.getenv("ALMALEAD_API_URL", "http://localhost:8000")
ATTORNEY_EMAIL = os.getenv("ATTORNEY_EMAIL", "attorney@almalead.com")
ATTORNEY_PASSWORD = os.getenv("ATTORNEY_PASSWORD", "attorney123")
TOKEN_FILE = Path.home() / ".almalead_token"


class AlmaLeadClient:
    """Client for interacting with AlmaLead API"""

    def __init__(self):
        self.base_url = API_URL
        self.token = self.load_token()

    def load_token(self):
        """Load saved authentication token"""
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
        return None

    def save_token(self, token):
        """Save authentication token to file"""
        TOKEN_FILE.write_text(token)
        print(f"✓ Token saved to {TOKEN_FILE}")

    def clear_token(self):
        """Clear saved authentication token"""
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
            print("✓ Token cleared")

    def login(self):
        """Login and save authentication token"""
        print(f"🔐 Logging in as {ATTORNEY_EMAIL}...")

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.save_token(self.token)
                print("✓ Login successful")
                return True
            else:
                print(f"✗ Login failed ({response.status_code}): {response.json()}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            print(f"  Make sure the backend is running at {self.base_url}")
            return False

    def create_lead(self, first_name=None, last_name=None, email=None):
        """Create a single lead"""
        # Generate random data if not provided
        if not first_name or not last_name or not email:
            if fake:
                first_name = first_name or fake.first_name()
                last_name = last_name or fake.last_name()
                email = email or fake.email()
            else:
                print("✗ Cannot generate random data without faker library")
                print("  Install with: pip install faker")
                return None

        print(f"📝 Creating lead: {first_name} {last_name} ({email})")

        # Find the sample resume
        resume_path = Path(__file__).parent / "sample_resume.pdf"

        if not resume_path.exists():
            print(f"✗ Resume file not found: {resume_path}")
            print("  Make sure sample_resume.pdf exists in the e2e directory")
            return None

        try:
            # Prepare multipart form data
            with open(resume_path, 'rb') as resume_file:
                files = {
                    'resume': ('resume.pdf', resume_file, 'application/pdf')
                }
                data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email
                }

                response = requests.post(
                    f"{self.base_url}/api/v1/leads",
                    data=data,
                    files=files
                )

            if response.status_code == 201:
                lead = response.json()
                print(f"✓ Lead created successfully")
                print(f"  ID: {lead['id']}")
                print(f"  State: {lead['state']}")
                return lead
            else:
                print(f"✗ Failed to create lead ({response.status_code}): {response.json()}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return None

    def create_multiple_leads(self, count):
        """Create multiple leads with random data"""
        if not fake:
            print("✗ Cannot generate random leads without faker library")
            print("  Install with: pip install faker")
            return []

        print(f"\n📋 Creating {count} leads with random data...\n")

        created_leads = []
        for i in range(count):
            print(f"[{i+1}/{count}] ", end="", flush=True)
            lead = self.create_lead()
            if lead:
                created_leads.append(lead)
            print()  # New line

        print(f"\n✓ Created {len(created_leads)}/{count} leads successfully")
        return created_leads

    def list_leads(self, state=None, limit=100):
        """List all leads"""
        if not self.token:
            print("✗ Not authenticated. Please login first.")
            print("  Run: python test.py login")
            return None

        print("📋 Fetching leads...")

        params = {'limit': limit}
        if state:
            params['state'] = state

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/v1/leads",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                leads = data['leads']
                total = data['total']

                print(f"\n✓ Found {total} lead(s)")

                if leads:
                    print()
                    print(f"{'ID':<38} {'Name':<25} {'Email':<30} {'State':<12}")
                    print("-" * 105)

                    for lead in leads:
                        name = f"{lead['first_name']} {lead['last_name']}"
                        print(f"{lead['id']:<38} {name:<25} {lead['email']:<30} {lead['state']:<12}")

                return leads
            elif response.status_code == 401:
                print("✗ Authentication failed. Token may have expired.")
                print("  Run: python test.py login")
                self.clear_token()
                return None
            else:
                print(f"✗ Failed to fetch leads ({response.status_code}): {response.json()}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return None

    def get_lead(self, lead_id):
        """Get lead details"""
        if not self.token:
            print("✗ Not authenticated. Please login first.")
            print("  Run: python test.py login")
            return None

        print(f"🔍 Fetching lead {lead_id}...")

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/v1/leads/{lead_id}",
                headers=headers
            )

            if response.status_code == 200:
                lead = response.json()
                print(f"\n✓ Lead Details:")
                print(f"  ID:         {lead['id']}")
                print(f"  Name:       {lead['first_name']} {lead['last_name']}")
                print(f"  Email:      {lead['email']}")
                print(f"  State:      {lead['state']}")
                print(f"  Resume:     {lead['resume_url']}")
                print(f"  Created:    {lead['created_at']}")
                print(f"  Updated:    {lead['updated_at']}")
                return lead
            elif response.status_code == 404:
                print(f"✗ Lead not found: {lead_id}")
                return None
            elif response.status_code == 401:
                print("✗ Authentication failed. Token may have expired.")
                print("  Run: python test.py login")
                self.clear_token()
                return None
            else:
                print(f"✗ Failed to fetch lead ({response.status_code}): {response.json()}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return None

    def update_lead_state(self, lead_id, state):
        """Update lead state"""
        if not self.token:
            print("✗ Not authenticated. Please login first.")
            print("  Run: python test.py login")
            return None

        print(f"📝 Updating lead {lead_id} to {state}...")

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.patch(
                f"{self.base_url}/api/v1/leads/{lead_id}/state",
                headers=headers,
                json={"state": state}
            )

            if response.status_code == 200:
                lead = response.json()
                print(f"✓ Lead updated successfully")
                print(f"  New state: {lead['state']}")
                return lead
            elif response.status_code == 404:
                print(f"✗ Lead not found: {lead_id}")
                return None
            elif response.status_code == 401:
                print("✗ Authentication failed. Token may have expired.")
                print("  Run: python test.py login")
                self.clear_token()
                return None
            else:
                print(f"✗ Failed to update lead ({response.status_code}): {response.json()}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return None

    def check_health(self):
        """Check API health"""
        print(f"🏥 Checking API health at {self.base_url}...")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                print("✓ API is healthy")
                print(f"  Status: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"✗ API returned status code {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Cannot connect to API: {e}")
            print(f"  Make sure the backend is running at {self.base_url}")
            print(f"  Run: docker-compose up (or) cd backend && uv run uvicorn app.main:app --reload")
            return False

    def run_e2e_workflow(self):
        """Run complete end-to-end workflow"""
        print("\n" + "="*70)
        print("🚀 Starting AlmaLead E2E Test Workflow")
        print("="*70 + "\n")

        # Step 0: Health check
        print("[Step 0/5] Checking API health...")
        if not self.check_health():
            print("\n✗ E2E test aborted - API is not reachable")
            return False
        print()

        # Step 1: Create a lead
        print("[Step 1/5] Creating test lead...")
        lead = self.create_lead("John", "Doe", f"john.doe.{datetime.now().timestamp()}@test.com")
        if not lead:
            print("\n✗ E2E test failed at step 1 (create lead)")
            return False
        lead_id = lead['id']
        print()

        # Step 2: Login
        print("[Step 2/5] Logging in as attorney...")
        if not self.login():
            print("\n✗ E2E test failed at step 2 (login)")
            return False
        print()

        # Step 3: List leads
        print("[Step 3/5] Listing all leads...")
        leads = self.list_leads()
        if leads is None:
            print("\n✗ E2E test failed at step 3 (list leads)")
            return False
        print()

        # Step 4: Get lead details
        print("[Step 4/5] Getting lead details...")
        lead_detail = self.get_lead(lead_id)
        if not lead_detail:
            print("\n✗ E2E test failed at step 4 (get lead)")
            return False
        print()

        # Step 5: Update lead state
        print("[Step 5/5] Updating lead state to REACHED_OUT...")
        updated_lead = self.update_lead_state(lead_id, "REACHED_OUT")
        if not updated_lead:
            print("\n✗ E2E test failed at step 5 (update state)")
            return False
        print()

        print("="*70)
        print("🎉 E2E Test Completed Successfully!")
        print("="*70)
        print("\nAll API endpoints are working correctly:")
        print("  ✓ Public lead creation")
        print("  ✓ Attorney authentication")
        print("  ✓ Lead listing")
        print("  ✓ Lead retrieval")
        print("  ✓ Lead state updates")
        return True


def interactive_mode():
    """Interactive menu mode"""
    client = AlmaLeadClient()

    while True:
        print("\n" + "="*60)
        print("    AlmaLead E2E Testing - Interactive Mode")
        print("="*60)
        print("1. Create a lead")
        print("2. Create multiple leads (random data)")
        print("3. Login as attorney")
        print("4. List all leads")
        print("5. Get lead details")
        print("6. Update lead state")
        print("7. Run full E2E workflow")
        print("8. Check API health")
        print("9. Logout (clear token)")
        print("0. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            print()
            first_name = input("First name (Enter for random): ").strip()
            last_name = input("Last name (Enter for random): ").strip()
            email = input("Email (Enter for random): ").strip()
            print()
            client.create_lead(
                first_name or None,
                last_name or None,
                email or None
            )
        elif choice == "2":
            try:
                count = int(input("\nHow many leads to create? ").strip())
                if count > 0:
                    client.create_multiple_leads(count)
                else:
                    print("✗ Count must be positive")
            except ValueError:
                print("✗ Invalid number")
        elif choice == "3":
            print()
            client.login()
        elif choice == "4":
            print()
            state_filter = input("Filter by state (PENDING/REACHED_OUT or Enter for all): ").strip().upper()
            print()
            client.list_leads(state_filter or None)
        elif choice == "5":
            lead_id = input("\nLead ID: ").strip()
            print()
            if lead_id:
                client.get_lead(lead_id)
            else:
                print("✗ Lead ID is required")
        elif choice == "6":
            lead_id = input("\nLead ID: ").strip()
            state = input("New state (PENDING/REACHED_OUT): ").strip().upper()
            print()
            if lead_id and state in ["PENDING", "REACHED_OUT"]:
                client.update_lead_state(lead_id, state)
            else:
                print("✗ Valid Lead ID and state are required")
        elif choice == "7":
            client.run_e2e_workflow()
        elif choice == "8":
            print()
            client.check_health()
        elif choice == "9":
            print()
            client.clear_token()
        else:
            print("\n✗ Invalid option")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="AlmaLead E2E Testing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py                                    # Interactive mode
  python test.py e2e                                # Run full E2E workflow
  python test.py create --count 5                   # Create 5 random leads
  python test.py create --first-name John --last-name Doe --email john@test.com
  python test.py login                              # Login and save token
  python test.py list                               # List all leads
  python test.py list --state PENDING               # Filter by state
  python test.py get <lead-id>                      # Get lead details
  python test.py update <lead-id> --state REACHED_OUT

Environment Variables:
  ALMALEAD_API_URL       API base URL (default: http://localhost:8000)
  ATTORNEY_EMAIL         Attorney email (default: attorney@almalead.com)
  ATTORNEY_PASSWORD      Attorney password (default: attorney123)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create lead(s)')
    create_parser.add_argument('--first-name', help='First name')
    create_parser.add_argument('--last-name', help='Last name')
    create_parser.add_argument('--email', help='Email address')
    create_parser.add_argument('--count', type=int, help='Number of random leads to create')

    # Login command
    subparsers.add_parser('login', help='Login as attorney and save token')

    # Logout command
    subparsers.add_parser('logout', help='Logout and clear saved token')

    # List command
    list_parser = subparsers.add_parser('list', help='List all leads')
    list_parser.add_argument('--state', choices=['PENDING', 'REACHED_OUT'], help='Filter by state')
    list_parser.add_argument('--limit', type=int, default=100, help='Maximum number of leads to fetch')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get lead details')
    get_parser.add_argument('lead_id', help='Lead ID (UUID)')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update lead state')
    update_parser.add_argument('lead_id', help='Lead ID (UUID)')
    update_parser.add_argument('--state', required=True, choices=['PENDING', 'REACHED_OUT'],
                               help='New state')

    # E2E command
    subparsers.add_parser('e2e', help='Run full end-to-end test workflow')

    # Health command
    subparsers.add_parser('health', help='Check API health')

    args = parser.parse_args()

    # If no command, run interactive mode
    if not args.command:
        interactive_mode()
        return

    # Execute command
    client = AlmaLeadClient()

    if args.command == 'create':
        if args.count:
            client.create_multiple_leads(args.count)
        else:
            client.create_lead(args.first_name, args.last_name, args.email)

    elif args.command == 'login':
        client.login()

    elif args.command == 'logout':
        client.clear_token()

    elif args.command == 'list':
        client.list_leads(args.state, args.limit)

    elif args.command == 'get':
        client.get_lead(args.lead_id)

    elif args.command == 'update':
        client.update_lead_state(args.lead_id, args.state)

    elif args.command == 'e2e':
        success = client.run_e2e_workflow()
        sys.exit(0 if success else 1)

    elif args.command == 'health':
        success = client.check_health()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
