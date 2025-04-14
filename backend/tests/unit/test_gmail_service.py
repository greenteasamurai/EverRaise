import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
import base64

from app.services.gmail import GmailService, GmailMessage

@pytest.fixture
def gmail_service():
    """
    Create a Gmail service with mocked authentication.
    """
    with patch.object(GmailService, 'authenticate') as mock_auth:
        service = GmailService()
        service.service = MagicMock()
        yield service

def create_mock_message(message_id="msg123", thread_id="thread123"):
    """Helper to create a mock message response."""
    date_str = "Mon, 15 Mar 2023 12:34:56 -0700"
    text_content = "This is the plain text content"
    html_content = "<div>This is the HTML content</div>"
    
    # Encode the content as it would be in a real Gmail API response
    text_data = base64.urlsafe_b64encode(text_content.encode()).decode()
    html_data = base64.urlsafe_b64encode(html_content.encode()).decode()
    
    return {
        "id": message_id,
        "threadId": thread_id,
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com, cc@example.com"},
                {"name": "Subject", "value": "Test Email Subject"},
                {"name": "Date", "value": date_str}
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": text_data}
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": html_data}
                }
            ]
        }
    }

def test_get_message_details(gmail_service):
    """Test parsing message details from the Gmail API response."""
    # Set up mock
    mock_message = create_mock_message()
    gmail_service.service.users().messages().get().execute.return_value = mock_message
    
    # Call the method
    message = gmail_service.get_message_details("msg123")
    
    # Verify method was called correctly
    gmail_service.service.users().messages().get.assert_called_with(
        userId='me', id="msg123", format='full'
    )
    
    # Verify message parsing
    assert message.id == "msg123"
    assert message.thread_id == "thread123"
    assert message.from_email == "sender@example.com"
    assert "recipient@example.com" in message.to_email
    assert "cc@example.com" in message.to_email
    assert message.subject == "Test Email Subject"
    assert isinstance(message.date, datetime)
    assert message.body_text == "This is the plain text content"
    assert message.body_html == "<div>This is the HTML content</div>"
    assert "INBOX" in message.labels
    assert "UNREAD" in message.labels

def test_list_messages(gmail_service):
    """Test listing messages with a specific query."""
    # Set up mock
    mock_response = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"}
        ]
    }
    gmail_service.service.users().messages().list().execute.return_value = mock_response
    
    # Call the method
    messages = gmail_service.list_messages(query="is:unread", max_results=10)
    
    # Verify method was called correctly
    gmail_service.service.users().messages().list.assert_called_with(
        userId='me', q="is:unread", maxResults=10
    )
    
    # Verify results
    assert len(messages) == 2
    assert messages[0]["id"] == "msg1"
    assert messages[1]["threadId"] == "thread2"

def test_get_recent_messages(gmail_service):
    """Test retrieving recent messages."""
    # Set up mocks
    mock_list_response = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"}
        ]
    }
    
    gmail_service.service.users().messages().list().execute.return_value = mock_list_response
    
    # Mock the get_message_details method to avoid complexity
    with patch.object(gmail_service, 'get_message_details') as mock_get_details:
        # Set up mock return values for message details
        mock_get_details.side_effect = [
            GmailMessage(
                id="msg1",
                thread_id="thread1",
                from_email="sender1@example.com",
                to_email=["recipient1@example.com"],
                subject="Subject 1",
                date=datetime.now(),
                body_text="Content 1",
                labels=["INBOX"]
            ),
            GmailMessage(
                id="msg2",
                thread_id="thread2",
                from_email="sender2@example.com",
                to_email=["recipient2@example.com"],
                subject="Subject 2",
                date=datetime.now(),
                body_text="Content 2",
                labels=["INBOX"]
            )
        ]
        
        # Call the method
        messages = gmail_service.get_recent_messages(days=3, query="important", max_results=5)
        
        # Verify the list method was called with the correct query
        assert "after:" in gmail_service.service.users().messages().list.call_args[1]['q']
        assert "important" in gmail_service.service.users().messages().list.call_args[1]['q']
        
        # Verify get_message_details was called for each message
        assert mock_get_details.call_count == 2
        mock_get_details.assert_any_call("msg1")
        mock_get_details.assert_any_call("msg2")
        
        # Verify results
        assert len(messages) == 2
        assert messages[0].id == "msg1"
        assert messages[1].id == "msg2" 