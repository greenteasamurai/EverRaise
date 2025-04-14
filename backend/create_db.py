"""
Create a minimal database for EverRaise with only essential tables.
This script can be run directly to create the SQLite database.
"""
import os
import sqlite3

# Set up the database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "everraise.db") 

# Create the database and tables
def create_database():
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create essential tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        first_name TEXT,
        last_name TEXT,
        hashed_password TEXT,
        is_active INTEGER DEFAULT 1,
        is_superuser INTEGER DEFAULT 0,
        google_id TEXT UNIQUE,
        microsoft_id TEXT UNIQUE,
        slack_id TEXT UNIQUE,
        avatar_url TEXT,
        notification_email INTEGER DEFAULT 1,
        notification_slack INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS organization (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        logo_url TEXT,
        is_active INTEGER DEFAULT 1,
        plan_tier TEXT DEFAULT 'free',
        subscription_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_organization (
        user_id INTEGER,
        organization_id INTEGER,
        role TEXT DEFAULT 'member',
        PRIMARY KEY (user_id, organization_id),
        FOREIGN KEY (user_id) REFERENCES user (id),
        FOREIGN KEY (organization_id) REFERENCES organization (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS integration (
        id INTEGER PRIMARY KEY,
        organization_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        last_sync_at TEXT,
        credentials TEXT,
        refresh_token TEXT,
        access_token TEXT,
        config TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (organization_id) REFERENCES organization (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS data_source (
        id INTEGER PRIMARY KEY,
        integration_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        config TEXT,
        is_active INTEGER DEFAULT 1,
        last_sync_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (integration_id) REFERENCES integration (id)
    )
    ''')
    
    # Add a default organization and admin user
    cursor.execute('''
    INSERT OR IGNORE INTO organization (name, slug, description)
    VALUES ('Default Organization', 'default-organization', 'Default organization for development')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO user (email, first_name, last_name, is_superuser)
    VALUES ('admin@example.com', 'Admin', 'User', 1)
    ''')
    
    # Link admin user to the default organization
    cursor.execute('''
    INSERT OR IGNORE INTO user_organization (user_id, organization_id, role)
    VALUES (1, 1, 'owner')
    ''')
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"Database created at {DB_PATH}")

if __name__ == "__main__":
    create_database()
