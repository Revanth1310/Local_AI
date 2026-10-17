import sqlite3
from pathlib import Path
from datetime import datetime
from memory.embeddings import create_embedding
from memory.embedding_store import save_embedding
from memory.embedding_store import (
    save_embedding,
    initialize_embedding_table
)
from memory.faiss_store import rebuild_index
# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "memory.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """Create and return a SQLite database connection."""

    connection = sqlite3.connect(DB_PATH)

    # Return rows as dictionary-like objects
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """Create all required tables if they don't already exist."""

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Current memories
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            content TEXT NOT NULL,

            memory_type TEXT NOT NULL
                DEFAULT 'general',

            importance REAL NOT NULL
                DEFAULT 0.5,

            confidence REAL NOT NULL
                DEFAULT 1.0,

            source TEXT,

            version INTEGER NOT NULL
                DEFAULT 1,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            is_active INTEGER NOT NULL
                DEFAULT 1
        )
    """)

    # --------------------------------------------------------
    # Memory history
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,

            memory_id INTEGER NOT NULL,

            version INTEGER NOT NULL,

            content TEXT NOT NULL,

            memory_type TEXT NOT NULL,

            importance REAL NOT NULL,

            confidence REAL NOT NULL,

            source TEXT,

            created_at TEXT NOT NULL,

            changed_at TEXT NOT NULL,

            change_type TEXT NOT NULL,

            FOREIGN KEY (memory_id)
                REFERENCES memories(id)
        )
    """)

    connection.commit()
    connection.close()
    initialize_embedding_table()

# ============================================================
# SAVE NEW MEMORY
# ============================================================

def save_memory(
    content,
    memory_type="general",
    importance=0.5,
    confidence=1.0,
    source=None
):
    """
    Save a new memory.

    A copy of the original memory is also stored
    in memory_history as version 1.
    """

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().isoformat()

    # --------------------------------------------------------
    # Insert into current memories
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO memories (
            content,
            memory_type,
            importance,
            confidence,
            source,
            version,
            created_at,
            updated_at,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        content,
        memory_type,
        importance,
        confidence,
        source,
        1,
        now,
        now,
        1
    ))

    memory_id = cursor.lastrowid

    # --------------------------------------------------------
    # Save version 1 into history
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO memory_history (
            memory_id,
            version,
            content,
            memory_type,
            importance,
            confidence,
            source,
            created_at,
            changed_at,
            change_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        memory_id,
        1,
        content,
        memory_type,
        importance,
        confidence,
        source,
        now,
        now,
        "created"
    ))

    connection.commit()
    connection.close()

    # --------------------------------------------------------
    # Create and save embedding
    # --------------------------------------------------------
    
    embedding = create_embedding(content)
    
    save_embedding(
        memory_id,
        embedding
    )
    
    return memory_id


# ============================================================
# GET ONE MEMORY
# ============================================================

def get_memory(memory_id):
    """Retrieve one active memory by ID."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM memories
        WHERE id = ?
        AND is_active = 1
    """, (memory_id,))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


# ============================================================
# GET ALL ACTIVE MEMORIES
# ============================================================

def get_all_memories():
    """Retrieve all active memories."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM memories
        WHERE is_active = 1
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


# ============================================================
# GET MEMORY HISTORY
# ============================================================

def get_memory_history(memory_id):
    """Retrieve all versions of a memory."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM memory_history
        WHERE memory_id = ?
        ORDER BY version ASC
    """, (memory_id,))

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


# ============================================================
# UPDATE MEMORY
# ============================================================

def update_memory(
    memory_id,
    content=None,
    memory_type=None,
    importance=None,
    confidence=None,
    source=None
):
    """
    Update a memory.

    The old version is preserved in memory_history.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Get current memory
    # --------------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM memories
        WHERE id = ?
        AND is_active = 1
    """, (memory_id,))

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return False

    existing = dict(row)

    # --------------------------------------------------------
    # Determine new values
    # --------------------------------------------------------

    new_content = (
        content
        if content is not None
        else existing["content"]
    )

    new_memory_type = (
        memory_type
        if memory_type is not None
        else existing["memory_type"]
    )

    new_importance = (
        importance
        if importance is not None
        else existing["importance"]
    )

    new_confidence = (
        confidence
        if confidence is not None
        else existing["confidence"]
    )

    new_source = (
        source
        if source is not None
        else existing["source"]
    )

    new_version = existing["version"] + 1

    now = datetime.now().isoformat()

    # --------------------------------------------------------
    # Update current memory
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE memories
        SET
            content = ?,
            memory_type = ?,
            importance = ?,
            confidence = ?,
            source = ?,
            version = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        new_content,
        new_memory_type,
        new_importance,
        new_confidence,
        new_source,
        new_version,
        now,
        memory_id
    ))

    # --------------------------------------------------------
    # Save new version into history
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO memory_history (
            memory_id,
            version,
            content,
            memory_type,
            importance,
            confidence,
            source,
            created_at,
            changed_at,
            change_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        memory_id,
        new_version,
        new_content,
        new_memory_type,
        new_importance,
        new_confidence,
        new_source,
        existing["created_at"],
        now,
        "updated"
    ))

    connection.commit()
    connection.close()

    # --------------------------------------------------------
    # Update embedding
    # --------------------------------------------------------

    embedding = create_embedding(new_content)

    save_embedding(
        memory_id,
        embedding
    )

    # --------------------------------------------------------
    # Rebuild FAISS
    # --------------------------------------------------------

    from memory.faiss_store import rebuild_index

    rebuild_index()

    return True


# ============================================================
# SOFT DELETE MEMORY
# ============================================================

def delete_memory(memory_id):
    """
    Soft-delete a memory.

    The actual database record remains.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Check memory exists
    # --------------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM memories
        WHERE id = ?
        AND is_active = 1
    """, (memory_id,))

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return False

    existing = dict(row)

    now = datetime.now().isoformat()

    # --------------------------------------------------------
    # Mark inactive
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE memories
        SET
            is_active = 0,
            updated_at = ?
        WHERE id = ?
    """, (
        now,
        memory_id
    ))

    # --------------------------------------------------------
    # Record deletion in history
    # --------------------------------------------------------

    cursor.execute("""
        INSERT INTO memory_history (
            memory_id,
            version,
            content,
            memory_type,
            importance,
            confidence,
            source,
            created_at,
            changed_at,
            change_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        memory_id,
        existing["version"] + 1,
        existing["content"],
        existing["memory_type"],
        existing["importance"],
        existing["confidence"],
        existing["source"],
        existing["created_at"],
        now,
        "deleted"
    ))

    connection.commit()
    connection.close()

    # --------------------------------------------------------
    # Rebuild FAISS
    # --------------------------------------------------------

    from memory.faiss_store import rebuild_index

    rebuild_index()

    return True

    