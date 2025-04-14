"""
Standalone script to initialize the database.
"""

import asyncio
import sys
import os

# Make the script runnable from the backend directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app.db.init_db import init_db
    
    async def setup_database():
        print("Initializing database...")
        result = await init_db()
        if result:
            print("Database initialized successfully!")
        else:
            print("Database initialization failed!")
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(setup_database())
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you are running this script from the backend directory.")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing database: {e}")
    sys.exit(1) 