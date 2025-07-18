from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
import time
from datetime import datetime
from typing import Optional
import asyncio
from contextlib import asynccontextmanager
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]


class GmailMonitor:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.last_history_id = None
        self.monitoring = False

    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None

        # Load existing credentials
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "credentials.json not found. Please download it from Google Cloud Console"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API authentication successful")

    def get_initial_history_id(self):
        """Get the current history ID to start monitoring from"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            self.last_history_id = profile['historyId']
            logger.info(f"Initial history ID: {self.last_history_id}")
        except HttpError as error:
            logger.error(f"Error getting profile: {error}")

    def get_message_details(self, message_id):
        """Get detailed information about a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = message['payload'].get('headers', [])
            details = {
                'message_id': message_id,
                'thread_id': message['threadId'],
                'snippet': message.get('snippet', ''),
                'from': '',
                'subject': '',
                'date': '',
                'timestamp': datetime.now().isoformat()
            }

            for header in headers:
                name = header['name'].lower()
                if name == 'from':
                    details['from'] = header['value']
                elif name == 'subject':
                    details['subject'] = header['value']
                elif name == 'date':
                    details['date'] = header['value']

            return details

        except HttpError as error:
            logger.error(f"Error getting message details: {error}")
            return None

    def check_new_emails(self):
        """Check for new emails since last check"""
        try:
            if not self.last_history_id:
                self.get_initial_history_id()
                return []

            # Get history since last check
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=self.last_history_id
            ).execute()

            new_emails = []

            if 'history' in history:
                for record in history['history']:
                    if 'messagesAdded' in record:
                        for message_added in record['messagesAdded']:
                            message_id = message_added['message']['id']
                            details = self.get_message_details(message_id)
                            if details:
                                new_emails.append(details)
                                logger.info(
                                    f"New email detected: From: {details['from']}, Subject: {details['subject']}")

                # Update history ID
                self.last_history_id = history['historyId']

            return new_emails

        except HttpError as error:
            if error.resp.status == 404:
                # History ID expired, get new one
                logger.warning("History ID expired, getting new one")
                self.get_initial_history_id()
                return []
            else:
                logger.error(f"Error checking emails: {error}")
                return []

    async def monitor_emails(self):
        """Continuously monitor for new emails"""
        logger.info("Starting email monitoring...")
        self.monitoring = True

        while self.monitoring:
            try:
                new_emails = self.check_new_emails()
                if new_emails:
                    for email in new_emails:
                        logger.info(f"📧 NEW EMAIL LOGGED: {json.dumps(email, indent=2)}")
                        asyncio.create_task(get_prediction(self.service, email['message_id'], email['snippet']+email['subject']))

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error

    def stop_monitoring(self):
        """Stop email monitoring"""
        self.monitoring = False
        logger.info("Email monitoring stopped")


# Global monitor instance
gmail_monitor = GmailMonitor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        gmail_monitor.authenticate()
        gmail_monitor.get_initial_history_id()
        # Start monitoring in background
        asyncio.create_task(gmail_monitor.monitor_emails())
        logger.info("Gmail monitoring started")
    except Exception as e:
        logger.error(f"Failed to start Gmail monitoring: {e}")

    yield

    # Shutdown
    gmail_monitor.stop_monitoring()
    logger.info("Gmail monitoring stopped")

async def get_prediction(service, message_id, message):
    # POST request with JSON payload
    url = 'http://localhost:8000/predict'
    payload = {'text': message}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)

    if response.ok:
        result = response.json()
        print(result)
        # Add label to the email
        asyncio.create_task(add_label_to_email(service, message_id, result['prediction']))
        return result
    else:
        print(f'Error: {response.status_code} - {response.text}')

async def add_label_to_email(service, message_id, label_name):
    """
    Add a label to a specific email in Gmail

    Args:
        service: Gmail API service object
        message_id: Gmail message ID
        label_name: Name of the label to add

    Returns:
    """
    try:
        # Get all labels to find the label ID
        labels = service.users().labels().list(userId='me').execute()
        label_id = None

        # Find the label ID by name
        for label in labels['labels']:
            if label['name'] == label_name:
                label_id = label['id']
                break

        # If label doesn't exist, create it
        if not label_id:
            label_id = create_label(service, label_name)
            if not label_id:
                return

        # Add the label to the message
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()

        logging.info(f"Successfully added label '{label_name}' to message {message_id}")
        return

    except HttpError as error:
        logging.error(f"Error adding label to message: {error}")
        return

def create_label(service, label_name):
    """
    Create a new label in Gmail if it doesn't exist

    Args:
        service: Gmail API service object
        label_name: Name of the label to create

    Returns:
        str: Label ID if successful, None otherwise
    """
    try:
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }

        result = service.users().labels().create(
            userId='me',
            body=label_body
        ).execute()

        logging.info(f"Created new label: {label_name}")
        return result['id']

    except HttpError as error:
        logging.error(f"Error creating label: {error}")
        return None


# FastAPI app
app = FastAPI(
    title="Gmail Email Logger",
    description="Monitor and log incoming Gmail emails",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {"message": "Gmail Email Logger is running", "monitoring": gmail_monitor.monitoring}


@app.get("/status")
async def get_status():
    return {
        "monitoring": gmail_monitor.monitoring,
        "authenticated": gmail_monitor.service is not None,
        "last_history_id": gmail_monitor.last_history_id
    }


@app.get("/start-monitoring")
async def start_monitoring():
    if gmail_monitor.monitoring:
        return {"message": "Monitoring is already active"}

    try:
        if not gmail_monitor.service:
            gmail_monitor.authenticate()

        asyncio.create_task(gmail_monitor.monitor_emails())
        return {"message": "Monitoring started successfully"}
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-monitoring")
async def stop_monitoring():
    gmail_monitor.stop_monitoring()
    return {"message": "Monitoring stopped"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)