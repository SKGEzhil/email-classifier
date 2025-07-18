import logging
import json
import asyncio
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from auth import SCOPES, TOKEN_PATH

# Prediction endpoint URL from env
PREDICTION_URL = os.environ.get("EMAIL_CLASSIFIER_URL", 'https://email-classifier.thankfulwater-706eddc2.centralindia.azurecontainerapps.io/predict')

logger = logging.getLogger(__name__)

class GmailMonitor:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.last_history_id = None
        self.monitoring = False

    def authenticate(self):
        """Authenticate with Gmail API using stored token.json"""
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        # Refresh or prompt if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            else:
                raise Exception("Credentials invalid or expired. Please authenticate via /auth_url.")
        self.credentials = creds
        self.service = build('gmail', 'v1', credentials=creds)

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

                self.last_history_id = history['historyId']

            return new_emails

        except HttpError as error:
            if error.resp.status == 404:
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
                        asyncio.create_task(get_prediction(self.service, email['message_id'], email['snippet'] + email['subject']))

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)

    def stop_monitoring(self):
        """Stop email monitoring"""
        self.monitoring = False
        logger.info("Email monitoring stopped")

async def get_prediction(service, message_id, message):
    """Send text to prediction endpoint and trigger label addition"""
    url = PREDICTION_URL
    payload = {'text': message}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)

    if response.ok:
        result = response.json()
        print(result)
        asyncio.create_task(add_label_to_email(service, message_id, result['prediction']))
        return result
    else:
        print(f'Error: {response.status_code} - {response.text}')

async def add_label_to_email(service, message_id, label_name):
    """Add a label to a specific email in Gmail"""
    try:
        labels = service.users().labels().list(userId='me').execute()
        label_id = None

        for label in labels['labels']:
            if label['name'] == label_name:
                label_id = label['id']
                break

        if not label_id:
            label_id = create_label(service, label_name)
            if not label_id:
                return

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
    """Create a new label in Gmail if it doesn't exist"""
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
