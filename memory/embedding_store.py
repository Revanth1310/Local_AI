import sqlite3
import pickle
from datetime import datetime

DB_PATH = "memory.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_embedding_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            memory_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            dimensions INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_embedding(memory_id, embedding, model_name="BAAI/bge-small-en-v1.5"):
    conn = get_connection()
    cursor = conn.cursor()

    embedding_bytes = pickle.dumps(embedding.tolist())

    cursor.execute("""
        INSERT OR REPLACE INTO memory_embeddings
        (
            memory_id,
            embedding,
            dimensions,
            model_name,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        memory_id,
        embedding_bytes,
        len(embedding),
        model_name,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_embedding(memory_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT embedding
        FROM memory_embeddings
        WHERE memory_id = ?
    """, (memory_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return pickle.loads(row[0])