from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import os
import pickle
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from fastapi.responses import HTMLResponse

from app.api.deps import get_db
from app.db.models.user import User
from app.services.gmail import GmailService, GmailMessage
from app.core.config import settings

router = APIRouter()


@router.get("/authorize", response_model=Dict[str, str])
async def authorize_gmail():
    """
    Start the Gmail authorization process.
    Returns a URL that the user should visit to authorize the application.
    """
    try:
        gmail_service = GmailService()
        gmail_service.authenticate()
        return {"message": "Gmail authorization successful"}
    except Exception as e:
        # If we get an authentication required exception, it should contain the auth URL
        error_message = str(e)
        if "Authentication required. Please visit:" in error_message:
            auth_url = error_message.split("Please visit: ")[1]
            return {"auth_url": auth_url}
        
        logger.error(f"Gmail authorization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error authorizing Gmail: " + str(e)
        )


@router.get("/callback", response_model=None)
async def gmail_callback(
    request: Request,
    state: str = Query(...),
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle the OAuth2 callback from Google.
    Exchanges the authorization code for an access token.
    """
    try:
        # Ensure server host URL is properly formatted
        server_host = str(settings.SERVER_HOST).rstrip('/')
        callback_url = f"{server_host}/api/v1/gmail/callback"
        
        logger.info(f"Processing Gmail callback with state: {state}")
        
        # Create client config from settings
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [callback_url]
            }
        }
        
        # Create flow with the same settings as in the authorize endpoint
        flow = Flow.from_client_config(
            client_config,
            scopes=settings.GMAIL_API_SCOPES.split(','),
            redirect_uri=callback_url,
            state=state
        )
        
        # Exchange auth code for token
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save the credentials to the token file
        token_file = settings.GMAIL_API_TOKEN_FILE
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
            logger.info("Gmail credentials saved successfully")
            
        # Get the first CORS origin as frontend URL, prioritizing localhost:5173
        frontend_url = next((origin for origin in settings.CORS_ORIGINS if "localhost:5173" in origin), 
                       next((origin for origin in settings.CORS_ORIGINS if "localhost:3000" in origin), 
                       settings.CORS_ORIGINS[0]))
        
        # Ensure frontend URL is properly formatted
        frontend_url = frontend_url.rstrip('/')
        redirect_url = f"{frontend_url}/integrations?gmail_auth=success"
        
        logger.info(f"Gmail authentication successful, redirecting to: {redirect_url}")
        
        # Use an HTML response that shows a success message and redirects back to the frontend
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Gmail Authentication Successful</title>
                <meta http-equiv="refresh" content="3;url={redirect_url}" />
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f9f9f9;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        max-width: 500px;
                    }}
                    h1 {{
                        color: #4CAF50;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Gmail Connected Successfully!</h1>
                    <p>You'll be redirected back to EverRaise in a few seconds...</p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Gmail callback error: {e}")
        # Return a user-friendly error page instead of an HTTP exception
        error_html = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Gmail Authentication Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f9f9f9;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        max-width: 500px;
                    }}
                    h1 {{
                        color: #f44336;
                    }}
                    .error {{
                        margin-top: 1rem;
                        padding: 1rem;
                        background-color: #ffebee;
                        border-radius: 4px;
                        color: #b71c1c;
                        text-align: left;
                        font-family: monospace;
                        white-space: pre-wrap;
                        word-break: break-word;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Gmail Authentication Failed</h1>
                    <p>There was an error connecting to your Gmail account.</p>
                    <div class="error">{str(e)}</div>
                    <p>Please try again or contact support if the issue persists.</p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/messages", response_model=List[Dict[str, Any]])
async def get_gmail_messages(
    days: int = Query(30, description="Number of days to look back"),
    query: str = Query("", description="Gmail search query"),
    limit: int = Query(200, description="Maximum number of messages to return"),
):
    """
    Get recent Gmail messages.
    """
    try:
        gmail_service = GmailService()
        messages = gmail_service.get_recent_messages(
            days=days, query=query, max_results=limit
        )
        
        # Convert to dict for API response
        return [message.dict() for message in messages]
    except Exception as e:
        logger.error(f"Gmail fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching Gmail messages: " + str(e)
        )


@router.get("/messages/{message_id}", response_model=Dict[str, Any])
async def get_gmail_message_details(
    message_id: str,
):
    """
    Get details of a specific Gmail message.
    """
    try:
        gmail_service = GmailService()
        message = gmail_service.get_message_details(message_id)
        return message.dict()
    except Exception as e:
        logger.error(f"Gmail message fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching Gmail message: " + str(e)
        )


@router.get("/status", response_model=Dict[str, bool])
async def gmail_status():
    """
    Check if Gmail is connected.
    """
    try:
        token_file = settings.GMAIL_API_TOKEN_FILE
        logger.info(f"Checking Gmail connection status")
        
        if not os.path.exists(token_file):
            logger.info(f"No Gmail token file found")
            return {"connected": False}
            
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
                
        # Check if credentials are valid
        if creds and (creds.valid or (creds.expired and creds.refresh_token)):
            if creds.expired:
                try:
                    logger.info(f"Refreshing expired Gmail token")
                    creds.refresh(GoogleRequest())
                    # Save refreshed credentials
                    with open(token_file, 'wb') as token:
                        pickle.dump(creds, token)
                        logger.info("Saved refreshed Gmail credentials")
                except Exception as e:
                    logger.error(f"Error refreshing Gmail token: {e}")
                    return {"connected": False}
            
            logger.info(f"Gmail connection is valid")
            return {"connected": True}
        
        logger.info(f"Gmail token is invalid")
        return {"connected": False}
    except Exception as e:
        logger.error(f"Gmail status check error: {e}")
        return {"connected": False, "error": str(e)}


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_gmail_data(
    background_tasks: BackgroundTasks,
    days: int = Query(30, description="Number of days to look back"),
    query: str = Query("", description="Gmail search query"),
):
    """
    Refresh Gmail data by fetching new messages and updating the database.
    This is an asynchronous operation that runs in the background.
    """
    try:
        # Check if Gmail is connected
        token_file = settings.GMAIL_API_TOKEN_FILE
        if not os.path.exists(token_file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail is not connected. Please connect your Gmail account first."
            )
            
        # Start a background task to refresh the data
        def refresh_task():
            try:
                gmail_service = GmailService()
                messages = gmail_service.get_recent_messages(
                    days=days, query=query, max_results=500  # Fetch more messages for refresh
                )
                logger.info(f"Refreshed {len(messages)} Gmail messages")
                
                # In a real implementation, you would process and store these messages
                # For now, we'll just log the count
            except Exception as e:
                logger.error(f"Error in Gmail refresh background task: {e}")
                
        # Add the task to the background
        background_tasks.add_task(refresh_task)
        
        return {
            "status": "success",
            "message": "Gmail refresh started. The process will run in the background."
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Gmail refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing Gmail data: " + str(e)
        ) 