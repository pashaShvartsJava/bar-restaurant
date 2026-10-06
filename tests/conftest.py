import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5452/authentication_test"
)

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
AUTH_SERVICE = ROOT / "authentication_service"
sys.path.insert(0, str(AUTH_SERVICE))

os.chdir(AUTH_SERVICE)

sys.path.insert(0, str(AUTH_SERVICE))

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)