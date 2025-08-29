# Shared pytest fixtures for a temp DB + test client.
import os
import sys
import tempfile
import pytest

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.app import create_app
from server.extensions import db  # use the same db instance

@pytest.fixture(scope="session")
def test_app():
    """Create a Flask test app with a temp SQLite DB file."""
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    app = create_app()
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        TESTING=True,
    )
    with app.app_context():
        db.create_all()

    try:
        yield app
    finally:
        with app.app_context():
            db.drop_all()
        if os.path.exists(db_path):
            os.unlink(db_path)

@pytest.fixture()
def client(test_app):
    return test_app.test_client()

@pytest.fixture()
def signup(client):
    """Return a function that signs up a user and returns the response."""
    def _signup(username="demo", password="demo123"):
        return client.post(
            "/signup",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
    return _signup

@pytest.fixture()
def login_resp(client):
    """Return a function that logs in and returns the raw response."""
    def _login_resp(username="demo", password="demo123"):
        return client.post(
            "/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
    return _login_resp

@pytest.fixture()
def login_token(signup, login_resp):
    """Ensure user exists, then log in and return the JWT string."""
    def _login_token(username="demo", password="demo123"):
        resp = signup(username, password)
        assert resp.status_code in (201, 409)
        resp = login_resp(username, password)
        assert resp.status_code == 200
        return resp.get_json()["access_token"]
    return _login_token

@pytest.fixture()
def auth_headers():
    """Build Authorization headers from a token."""
    def _auth_headers(token: str):
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return _auth_headers