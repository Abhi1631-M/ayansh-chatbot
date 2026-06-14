"""
Migration script to add the chat_logs table to the SQLite database
without affecting existing data.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ayansh.db"

def migrate():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Creating chat_logs table if it doesn't exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_query     TEXT NOT NULL,
            bot_response   TEXT NOT NULL,
            route_decision TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("Migration successful: chat_logs table is ready.")

if __name__ == "__main__":
    migrate()
