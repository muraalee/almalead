"""
Pytest configuration and fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.session import Base
from app.main import app
from app.db.session import get_db


# Use in-memory SQLite for tests (no file created)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Keep the same in-memory database for all connections
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    class MockStorage:
        def upload_file(self, file, object_name):
            return f"http://test-storage/{object_name}"

        def get_file_url(self, object_name):
            return f"http://test-storage/{object_name}"

        def delete_file(self, object_name):
            return True

        def ensure_bucket_exists(self):
            pass

    return MockStorage()


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test.attorney@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "Attorney",
    }


@pytest.fixture
def auth_headers(client, db_session, sample_user_data):
    """Create authenticated user and return auth headers."""
    from app.models.user import User
    from app.core.security import get_password_hash

    # Create test user
    user = User(
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"]),
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
    )
    db_session.add(user)
    db_session.commit()

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
