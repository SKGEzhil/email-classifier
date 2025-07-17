# tests/test_app.py
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api import app

client = TestClient(app)

def test_predict_endpoint():
    payload = {"text": "Hello! I'm interested in internship opportunities."}
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    # should at least return a 'label' field
    assert "prediction" in data
    assert isinstance(data["prediction"], str)

    # if you return probabilities, you can also test that:
    if "id" in data:
        assert isinstance(data["id"], int)
        assert data["id"] == 2  # Assuming the text is classified as "Internships"
