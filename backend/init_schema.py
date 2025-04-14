import asyncio
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "everraise.db"

async def init_schema():
    print(f"Initializing database at {db_path}")
    
    # Simple schema for SQLite
    schema = [
        '''
        CREATE TABLE IF NOT EXISTS organization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            plan_tier TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            is_active INTEGER DEFAULT 1,
            is_superuser INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS user_organization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            is_owner INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (organization_id) REFERENCES organization (id)
        )
        '''
    ]
    
    # Create admin user
    admin_user = '''
    INSERT OR IGNORE INTO organization (name, slug, description, is_active, plan_tier)
    VALUES ('Admin Organization', 'admin-org', 'Default organization for admin users', 1, 'premium');
    
    INSERT OR IGNORE INTO user (email, hashed_password, first_name, last_name, is_active, is_superuser)
    VALUES ('admin@example.com', '\\\.jqyj2', 'Admin', 'User', 1, 1);
    
    INSERT OR IGNORE INTO user_organization (user_id, organization_id, is_owner)
    SELECT u.id, o.id, 1
    FROM user u, organization o
    WHERE u.email = 'admin@example.com' AND o.slug = 'admin-org';
    '''
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        for table_sql in schema:
            cursor.execute(table_sql)
            
        # Create admin user
        cursor.executescript(admin_user)
        
        conn.commit()
        print("Database schema created successfully!")
        return True
    except Exception as e:
        print(f"Error creating database schema: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(init_schema())
