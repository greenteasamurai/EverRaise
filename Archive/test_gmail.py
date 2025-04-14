import sys
from loguru import logger
from app.services.gmail import GmailService

def main():
    try:
        print("Testing Gmail connection...")
        service = GmailService()
        service.authenticate()
        print("Authentication successful!")
        
        print("\nFetching email list...")
        messages = service.list_messages(max_results=5)
        print(f"Found {len(messages)} message metadata entries")
        
        if messages:
            message_id = messages[0]['id']
            print(f"\nFetching details for message {message_id}...")
            message_details = service.get_message_details(message_id)
            print(f"Subject: {message_details.subject}")
            print(f"From: {message_details.from_email}")
            print(f"Date: {message_details.date}")
            print(f"Body preview: {message_details.body_text[:100]}...")
        else:
            print("No messages found.")
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 