"""
Mock objects and functions for testing.

This module provides mock implementations of various dependencies
used in the application, making it easier to write isolated unit tests.
"""

import asyncio
from typing import Any, Dict, List, Optional, TypeVar, Generic
from unittest.mock import MagicMock

# Generic type for repository mocks
T = TypeVar('T')

class MockRepository(Generic[T]):
    """
    A generic mock repository for database operations.
    
    This mock can be used to replace any repository class in the application,
    allowing tests to run without accessing the actual database.
    """
    
    def __init__(self, items: Optional[List[T]] = None):
        self.items = items or []
        self._id_counter = 1
    
    async def get(self, id: Any) -> Optional[T]:
        """Get an item by ID."""
        for item in self.items:
            if getattr(item, "id", None) == id:
                return item
        return None
    
    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get an item by a specific field value."""
        for item in self.items:
            if getattr(item, field, None) == value:
                return item
        return None
    
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple items with pagination."""
        return self.items[skip:skip + limit]
    
    async def create(self, obj_in: Any) -> T:
        """Create a new item."""
        # Simulate ID assignment
        if hasattr(obj_in, "id") and obj_in.id is None:
            setattr(obj_in, "id", self._id_counter)
            self._id_counter += 1
        
        self.items.append(obj_in)
        return obj_in
    
    async def update(self, db_obj: T, obj_in: Any) -> T:
        """Update an item."""
        # Apply updates from obj_in to db_obj
        for key, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, key, value)
        return db_obj
    
    async def delete(self, id: Any) -> Optional[T]:
        """Delete an item by ID."""
        for i, item in enumerate(self.items):
            if getattr(item, "id", None) == id:
                return self.items.pop(i)
        return None

class MockAuthService:
    """
    Mock authentication service.
    """
    
    def __init__(self, users: Dict[str, Dict[str, Any]] = None):
        self.users = users or {
            "test@example.com": {
                "id": "user123",
                "email": "test@example.com",
                "hashed_password": "hashed_secret",
                "is_active": True,
                "is_superuser": False,
            }
        }
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user."""
        user = self.users.get(email)
        if not user:
            return None
        # In a real implementation, you would verify the password
        # For testing, we'll just return the user
        return user
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create an access token."""
        return f"mock_token_for_{data.get('sub', 'unknown')}"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a token."""
        if not token.startswith("mock_token_for_"):
            return None
        
        user_id = token.replace("mock_token_for_", "")
        for user in self.users.values():
            if user["id"] == user_id:
                return user
        return None

class MockOpenAIClient:
    """
    Mock OpenAI client for testing LLM interactions.
    """
    
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.calls = []
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Mock chat completion endpoint."""
        self.calls.append({"messages": messages, "kwargs": kwargs})
        
        # Generate a default response if none is specified
        if not self.responses:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response from the LLM."
                    }
                }]
            }
        
        # Find a response based on the input messages
        for key, response in self.responses.items():
            if key in str(messages):
                return response
        
        # Return the first response as default
        return next(iter(self.responses.values()))

class MockEmailService:
    """
    Mock email service for testing email functionality.
    """
    
    def __init__(self):
        self.sent_emails = []
    
    async def send_email(
        self,
        email_to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Mock sending an email."""
        self.sent_emails.append({
            "to": email_to,
            "subject": subject,
            "html_content": html_content,
            "text_content": text_content,
        })
        return True
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all sent emails."""
        return self.sent_emails
    
    def clear_sent_emails(self) -> None:
        """Clear the list of sent emails."""
        self.sent_emails = []

# Mock HTTP client for external API calls
class MockHTTPClient:
    """
    Mock HTTP client for testing external API interactions.
    """
    
    def __init__(self, responses: Dict[str, Dict[str, Any]] = None):
        self.responses = responses or {}
        self.requests = []
    
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Mock GET request."""
        self.requests.append({"method": "GET", "url": url, "kwargs": kwargs})
        
        for pattern, response in self.responses.items():
            if pattern in url:
                if isinstance(response.get("content"), Exception):
                    raise response["content"]
                return response.get("content", {})
        
        return {"status": "ok", "data": "mock_data"}
    
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Mock POST request."""
        self.requests.append({"method": "POST", "url": url, "kwargs": kwargs})
        
        for pattern, response in self.responses.items():
            if pattern in url:
                if isinstance(response.get("content"), Exception):
                    raise response["content"]
                return response.get("content", {})
        
        return {"status": "created", "id": "mock_id"}
    
    def get_requests(self) -> List[Dict[str, Any]]:
        """Get all recorded requests."""
        return self.requests 