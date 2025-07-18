import sys
import os
import pytest
# ensure src directory is on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from gmail_client import GmailMonitor

class DummyCreds:
    valid = False
    expired = False
    refresh_token = None

@pytest.fixture(autouse=True)
def no_token_file(tmp_path, monkeypatch):
    # Change working directory to temp and ensure no token.json exists
    monkeypatch.chdir(tmp_path)

def test_authenticate_no_token(monkeypatch):
    gm = GmailMonitor()
    # Ensure no token file is present
    with pytest.raises(Exception) as excinfo:
        gm.authenticate()
    assert "Please authenticate via /auth_url" in str(excinfo.value)
