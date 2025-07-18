import os
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Env-configurable constants
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

# 2) Load client config from env or file
CLIENT_CONFIG_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
CLIENT_CONFIG_PATH = os.environ.get("GOOGLE_CLIENT_CONFIG_PATH", "credentials_.json")
if CLIENT_CONFIG_JSON:
    client_config = json.loads(CLIENT_CONFIG_JSON)
else:
    with open(CLIENT_CONFIG_PATH, "r") as f:
        client_config = json.load(f)

# 3) Build the flow with a redirect URI configured via env
REDIRECT_URI = os.environ.get("OAUTH2_REDIRECT_URI", "http://127.0.0.1:8001/oauth2callback")

flow = InstalledAppFlow.from_client_config(
    client_config,
    SCOPES,
    redirect_uri=REDIRECT_URI
)

router = APIRouter()
# token file path from env
TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", "token.json")

@router.get("/auth_url")
def auth_url():
    """
    Step 1: generate and return the Google consent URL.
    """
    auth_url, _ = flow.authorization_url(
        access_type="offline",      # get a refresh token
        prompt="consent"            # force the consent screen
    )
    return JSONResponse({"auth_url": auth_url})

@router.get("/oauth2callback")
def oauth2callback(request: Request):
    """
    Step 2: Google redirects here after user consents.
    Exchange the code for tokens and save them.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing `code` in callback")

    # Exchange code for credentials
    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials

    # Persist to disk for reuse (you can also write this to a DB or volume)
    with open(TOKEN_PATH, "w") as token_file:
        token_file.write(creds.to_json())

    html = """
    <html>
      <body>
        <h1>Gmail Authentication Complete</h1>
        <p>Token saved. You can now restart your server; it will use token.json going forward.</p>
      </body>
    </html>
    """
    return HTMLResponse(html)
