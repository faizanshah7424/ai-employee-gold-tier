"""
Gmail Watcher - Silver Level Implementation
Monitors Gmail and creates action files in /Inbox

Follows the BaseWatcher pattern from hackathon document:
https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
"""
from __future__ import print_function
import os
import base64
import time
import logging
from email import message_from_bytes
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from qwen_agent import ask_qwen

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
VAULT = Path("AI_Employee_Vault")
PROCESSED_FILE = "processed_emails.txt"
CHECK_INTERVAL = 120  # Document spec: 120 seconds for Gmail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================
# BASE WATCHER (from document)
# ==============================
class BaseWatcher(ABC):
    """Abstract base class for all watchers per document spec"""
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / 'Inbox'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_ids = set()

    @abstractmethod
    def check_for_updates(self):
        """Return list of new items to process"""
        pass

    @abstractmethod
    def create_action_file(self, item):
        """Create .md file in Inbox folder"""
        pass

    def run(self):
        """Main watcher loop"""
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f'Error: {e}')
            time.sleep(self.check_interval)


# ==============================
# GMAIL WATCHER
# ==============================
class GmailWatcher(BaseWatcher):
    """
    Gmail watcher following document spec.
    Watches for unread, important emails and creates action files in /Inbox.
    """
    
    def __init__(self, vault_path: str = "AI_Employee_Vault", 
                 credentials_path: str = "credentials.json",
                 check_interval: int = CHECK_INTERVAL):
        super().__init__(vault_path, check_interval)
        self.credentials_path = credentials_path
        self.service = None
        self._load_processed_ids()
    
    def _load_processed_ids(self):
        """Load previously processed email IDs"""
        processed_file = Path(PROCESSED_FILE)
        if processed_file.exists():
            with open(processed_file, "r", encoding="utf-8") as f:
                self.processed_ids = set(f.read().splitlines())
        else:
            self.processed_ids = set()
    
    def _save_processed_id(self, email_id):
        """Save processed email ID"""
        with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
            f.write(email_id + "\n")
        self.processed_ids.add(email_id)
    
    def _authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        token_file = Path("token.json")
        
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def check_for_updates(self):
        """Check for new unread emails"""
        if not self.service:
            self._authenticate()
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important',
                maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = []
            
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    new_messages.append(msg)
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Error checking Gmail: {e}")
            # Try to re-authenticate
            self.service = None
            return []
    
    def create_action_file(self, message):
        """Create action file in /Inbox for new email"""
        try:
            msg_data = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
            subject = headers.get('Subject', 'No Subject')
            sender = headers.get('From', 'Unknown')
            
            # Extract body
            body = ""
            if 'parts' in msg_data['payload']:
                for part in msg_data['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
            elif 'body' in msg_data['payload']:
                data = msg_data['payload']['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            # AI filter: Check if email is important
            if not self._is_important_email(subject, sender, body):
                logger.info(f"Ignored: {subject}")
                self._save_processed_id(message['id'])
                return
            
            # Create action file in /Inbox (per document spec)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            action_file = self.inbox / f"EMAIL_{message['id']}_{timestamp}.md"
            
            content = f"""---
type: email
id: {message['id']}
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: high
status: new
---

# Email Content

**From:** {sender}
**Subject:** {subject}
**Received:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{body}

---

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing

*Generated by Gmail Watcher v0.1*
"""
            
            action_file.write_text(content, encoding="utf-8")
            self._save_processed_id(message['id'])
            logger.info(f"Action file created: {action_file.name}")
            
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
    
    def _is_important_email(self, subject, sender, body):
        """Use AI to filter important emails"""
        prompt = f"""
Decide if this email needs action.

Email:
Subject: {subject}
From: {sender}
Body: {body[:500] if body else "No content"}

Rules:
- Reply ONLY YES or NO
- YES → if action, work, client request, payment, task
- NO → if spam, OTP, promotion, newsletter
"""
        try:
            result = ask_qwen(prompt).strip().upper()
            return result == "YES"
        except:
            return True  # Default to processing on error


# ==============================
# RUN AS STANDALONE
# ==============================
if __name__ == "__main__":
    # Ensure Inbox exists
    (VAULT / "Inbox").mkdir(exist_ok=True)
    
    watcher = GmailWatcher()
    logger.info("Gmail Watcher started")
    logger.info(f"Watching Gmail every {CHECK_INTERVAL} seconds")
    logger.info(f"Action files created in: {VAULT / 'Inbox'}")
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Gmail Watcher stopped")
