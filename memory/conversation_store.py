import sqlite3
from datetime import datetime
from pathlib import Path


# Same database used by the rest of the memory system
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "memory.db"


def initialize_conversation_table():
    """
    Create the conversations table if it does not already exist.
    """

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_conversation(user_message, assistant_response):
    """
    Save one user + assistant interaction.
    """

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO conversations (
            user_message,
            assistant_response,
            created_at
        )
        VALUES (?, ?, ?)
    """, (
        user_message,
        assistant_response,
        created_at
    ))

    conversation_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def get_conversation(conversation_id):
    """
    Get one conversation by ID.
    """

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_message,
            assistant_response,
            created_at
        FROM conversations
        WHERE id = ?
    """, (conversation_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "user_message": row[1],
        "assistant_response": row[2],
        "created_at": row[3]
    }


def get_recent_conversations(limit=10):
    """
    Get the most recent conversations.
    """

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_message,
            assistant_response,
            created_at
        FROM conversations
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    conversations = []

    for row in rows:
        conversations.append({
            "id": row[0],
            "user_message": row[1],
            "assistant_response": row[2],
            "created_at": row[3]
        })

    return conversations