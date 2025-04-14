import os
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import base64
import json

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from pydantic import BaseModel
from loguru import logger
from google.auth.credentials import Credentials
from googleapiclient.errors import HttpError

from app.core.config import settings


class GmailMessage(BaseModel):
    """Model representing a Gmail message."""
    id: str
    thread_id: str
    from_email: str
    to_email: List[str]
    subject: str
    date: datetime
    body_text: str
    body_html: Optional[str] = None
    labels: List[str]


class GmailService:
    """
    Service for interacting with Gmail API.
    Manages authentication, fetching messages.
    """

    def __init__(self):
        try:
            self.client_id = settings.GMAIL_CLIENT_ID
            self.client_secret = settings.GMAIL_CLIENT_SECRET
            self.redirect_uri = settings.GMAIL_REDIRECT_URI
            self.scopes = settings.GMAIL_SCOPES
        except AttributeError as e:
            logger.error(f"Gmail API credentials missing in settings: {e}")
            self.client_id = None
            self.client_secret = None
            self.redirect_uri = None
            self.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
            
        self.token_file = "gmail_token.json"
        self.creds = None
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from file if they exist."""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as token:
                    creds_data = json.load(token)
                    self.creds = Credentials.from_authorized_user_info(creds_data)
                    
                    # Check if credentials are expired or will expire soon (within 5 minutes)
                    if self.creds and (self.creds.expired or not self.creds.valid 
                                     or (self.creds.expiry and (self.creds.expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds() < 300)):
                        logger.info("Credentials expired or expiring soon, attempting to refresh")
                        try:
                            if self.creds.refresh_token:
                                self.creds.refresh(Request())
                                self._save_credentials()
                                logger.info("Successfully refreshed token")
                            else:
                                logger.warning("No refresh token available, user will need to re-authenticate")
                                self.creds = None
                        except Exception as e:
                            logger.error(f"Error refreshing token: {e}")
                            # If refresh fails, credentials are probably invalid
                            self.creds = None
                            # Remove invalid token file
                            self._remove_invalid_token_file()
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            self.creds = None
            # Remove potentially corrupted token file
            self._remove_invalid_token_file()

    def _remove_invalid_token_file(self):
        """Remove the token file if it's invalid."""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                logger.info(f"Removed invalid token file: {self.token_file}")
        except Exception as e:
            logger.error(f"Failed to remove invalid token file: {e}")

    def _save_credentials(self):
        """Save credentials to file."""
        try:
            if self.creds:
                creds_data = json.loads(self.creds.to_json())
                with open(self.token_file, "w") as token:
                    json.dump(creds_data, token)
                logger.info(f"Saved credentials to {self.token_file}")
                
                # Log token expiry time for debugging
                if hasattr(self.creds, 'expiry') and self.creds.expiry:
                    expiry_time = self.creds.expiry.isoformat()
                    logger.info(f"Token will expire at: {expiry_time}")
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")

    def get_auth_url(self) -> str:
        """Generate Gmail authentication URL."""
        try:
            if not all([self.client_id, self.client_secret, self.redirect_uri]):
                error_msg = "Gmail API credentials not configured. Check your .env file."
                logger.error(error_msg)
                return {"error": error_msg}
                
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [self.redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                self.scopes,
                redirect_uri=self.redirect_uri,
            )
            auth_url, _ = flow.authorization_url(
                access_type="offline", include_granted_scopes="true", prompt="consent"
            )
            logger.info(f"Generated Gmail auth URL for scopes: {', '.join(self.scopes)}")
            return auth_url
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            raise ValueError(f"Failed to generate Gmail authentication URL: {str(e)}")

    def handle_auth_callback(self, code: str):
        """Handle OAuth callback and save credentials."""
        try:
            if not all([self.client_id, self.client_secret, self.redirect_uri]):
                error_msg = "Gmail API credentials not configured. Check your .env file."
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [self.redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                self.scopes,
                redirect_uri=self.redirect_uri,
            )
            
            try:
                self.creds = flow.fetch_token(code=code)
                logger.info("Successfully obtained Gmail credentials")
                
                # Log token details for debugging (without exposing sensitive data)
                if self.creds:
                    token_info = {
                        "has_refresh_token": bool(getattr(self.creds, "refresh_token", None)),
                        "expiry": getattr(self.creds, "expiry", None),
                        "scopes": getattr(self.creds, "scopes", [])
                    }
                    logger.info(f"Token info: {token_info}")
                
                self._save_credentials()
                
                # Test the credentials immediately
                result = self.test_connection()
                if not result.get("connected", False):
                    logger.warning(f"Credentials obtained but connection test failed: {result.get('error')}")
                    
                return True
            except Exception as e:
                logger.error(f"Error in auth callback flow: {e}")
                if hasattr(e, 'authorization_response'):
                    logger.error(f"Authorization response: {e.authorization_response}")
                return False
        except Exception as e:
            logger.error(f"Error handling auth callback: {e}")
            raise ValueError(f"Failed to handle Gmail authentication callback: {str(e)}")

    def get_messages(self, query: str = "", max_results: int = 10) -> List[GmailMessage]:
        """Fetch messages from Gmail."""
        try:
            if not self.creds:
                logger.error("No credentials available for Gmail API")
                return []

            # Try to refresh token if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_credentials()
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    return []
            
            service = build("gmail", "v1", credentials=self.creds)
            
            # Check if max_results is a reasonable number
            if max_results > 100:
                logger.warning(f"Requested {max_results} messages, limiting to 100")
                max_results = 100
                
            response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = response.get("messages", [])
            
            logger.info(f"Fetched {len(messages)} messages from Gmail matching query: '{query}'")
            
            results = []
            for msg in messages:
                try:
                    full_msg = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
                    
                    headers = {header["name"]: header["value"] for header in full_msg["payload"]["headers"]}
                    
                    subject = headers.get("Subject", "")
                    sender = headers.get("From", "")
                    date = headers.get("Date", "")
                    snippet = full_msg.get("snippet", "")
                    
                    body = ""
                    if "parts" in full_msg["payload"]:
                        for part in full_msg["payload"]["parts"]:
                            if part["mimeType"] == "text/plain" and "body" in part and "data" in part["body"]:
                                body_data = part["body"]["data"]
                                body += base64.urlsafe_b64decode(body_data).decode("utf-8")
                    elif "body" in full_msg["payload"] and "data" in full_msg["payload"]["body"]:
                        body_data = full_msg["payload"]["body"]["data"]
                        body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    
                    results.append(
                        GmailMessage(
                            id=msg["id"],
                            subject=subject,
                            sender=sender,
                            date=date,
                            body=body,
                            snippet=snippet,
                        )
                    )
                except Exception as e:
                    logger.error(f"Error processing message {msg.get('id')}: {e}")
            
            return results
        except HttpError as e:
            error_reason = json.loads(e.content.decode('utf-8')).get('error', {}).get('message', 'Unknown error')
            logger.error(f"Gmail API HTTP error: {error_reason}")
            
            # Handle specific common error cases
            if "invalid_grant" in str(e) or "Invalid Credentials" in str(e):
                logger.error("Invalid credentials - user needs to re-authenticate")
                # Clear invalid credentials
                self.creds = None
                self._remove_invalid_token_file()
            
            return []
        except Exception as e:
            logger.error(f"Error fetching Gmail messages: {e}")
            return []
            
    def test_connection(self):
        """Test if Gmail API connection is working."""
        try:
            if not self.creds:
                return {"connected": False, "error": "No credentials available"}
                
            # Try to refresh token if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_credentials()
                except Exception as e:
                    logger.error(f"Error refreshing token during connection test: {e}")
                    return {"connected": False, "error": f"Token refresh failed: {str(e)}"}
            
            service = build("gmail", "v1", credentials=self.creds)
            
            # Just get profile info as a lightweight test
            profile = service.users().getProfile(userId="me").execute()
            
            if profile and "emailAddress" in profile:
                return {
                    "connected": True, 
                    "email": profile["emailAddress"],
                    "message_total": profile.get("messagesTotal", 0),
                    "thread_total": profile.get("threadsTotal", 0)
                }
            else:
                return {"connected": False, "error": "Could not retrieve profile information"}
                
        except HttpError as e:
            error_reason = json.loads(e.content.decode('utf-8')).get('error', {}).get('message', 'Unknown error')
            logger.error(f"Gmail API connection test failed: {error_reason}")
            
            # Clear credentials if they're invalid
            if "invalid_grant" in str(e) or "Invalid Credentials" in str(e):
                self.creds = None
                self._remove_invalid_token_file()
                return {"connected": False, "error": "Invalid credentials - please re-authenticate"}
            
            return {"connected": False, "error": f"API error: {error_reason}"}
        except Exception as e:
            logger.error(f"Error testing Gmail connection: {e}")
            return {"connected": False, "error": str(e)}

    def get_message_details(self, message_id: str) -> GmailMessage:
        """Get details of a specific message."""
        if not self.creds:
            self.authenticate()
            
        msg = self.service.users().messages().get(
            userId='me', id=message_id, format='full').execute()
        
        headers = {header['name']: header['value'] 
                  for header in msg['payload']['headers']}
        
        # Extract message details from headers
        from_email = headers.get('From', '')
        to_email = [headers.get('To', '')]
        if ',' in to_email[0]:
            to_email = [email.strip() for email in to_email[0].split(',')]
        subject = headers.get('Subject', '')
        
        # Parse date
        date_str = headers.get('Date', '')
        date = datetime.now()  # Default to now if parsing fails
        try:
            from email.utils import parsedate_to_datetime
            date = parsedate_to_datetime(date_str)
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
        
        # Extract message body
        body_text = ""
        body_html = None
        
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    body_text = base64.urlsafe_b64decode(
                        part['body']['data'].encode('ASCII')
                    ).decode('utf-8')
                elif mime_type == 'text/html':
                    body_html = base64.urlsafe_b64decode(
                        part['body']['data'].encode('ASCII')
                    ).decode('utf-8')
        elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
            body_text = base64.urlsafe_b64decode(
                msg['payload']['body']['data'].encode('ASCII')
            ).decode('utf-8')
        
        return GmailMessage(
            id=msg['id'],
            thread_id=msg['threadId'],
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            date=date,
            body_text=body_text,
            body_html=body_html,
            labels=msg['labelIds']
        )
    
    def list_messages(self, query: str = '', max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List messages matching the specified query.
        
        Args:
            query: Gmail search query (same syntax as Gmail search box)
            max_results: Maximum number of results to return
            
        Returns:
            List of message metadata (id and threadId)
        """
        if not self.creds:
            self.authenticate()
            
        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=max_results).execute()
        
        messages = results.get('messages', [])
        return messages
    
    def get_recent_messages(self, days: int = 7, query: str = '', max_results: int = 100) -> List[GmailMessage]:
        """
        Get recent messages from the last specified days.
        
        Args:
            days: Number of days to look back
            query: Additional search criteria
            max_results: Maximum number of results to return
            
        Returns:
            List of GmailMessage objects
        """
        date_filter = datetime.now() - timedelta(days=days)
        date_str = date_filter.strftime('%Y/%m/%d')
        
        full_query = f"after:{date_str} {query}".strip()
        message_list = self.list_messages(query=full_query, max_results=max_results)
        
        messages = []
        for msg_meta in message_list:
            try:
                message = self.get_message_details(msg_meta['id'])
                messages.append(message)
            except Exception as e:
                logger.error(f"Error processing message {msg_meta['id']}: {e}")
        
        return messages

    # Add backward compatibility method to maintain API compatibility with existing code
    def authenticate(self):
        """Backward compatibility method for existing code."""
        if self.creds:
            service = build("gmail", "v1", credentials=self.creds)
            logger.info("Successfully built Gmail API service")
            return service
        else:
            logger.warning("No credentials available. Need to authenticate with get_auth_url() first.")
            raise ValueError("Authentication required. Use get_auth_url() to obtain an authentication URL.") 