import sys
import os
import pytest
from fastapi.testclient import TestClient

# ensure src is on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Gmail Email Logger is running"
    assert isinstance(data.get("monitoring"), bool)


def test_status_default():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data.get("authenticated") is False
    assert data.get("monitoring") is False
    assert "last_history_id" in data


def test_auth_url(monkeypatch):
    import auth
    # stub the authorization_url method
    monkeypatch.setattr(auth.flow, "authorization_url", lambda access_type, prompt: ("http://fake.url", None))
    response = client.get("/auth_url")
    assert response.status_code == 200
    data = response.json()
    assert data.get("auth_url") == "http://fake.url"


def test_oauth2callback_missing_code():
    response = client.get("/oauth2callback")
    assert response.status_code == 400
