import sqlite3
import os
from config import DB_PATH


# ── Connection helper ─────────────────────────────────────────────────────────

def get_connection():
    """Open and return a connection to the SQLite database.
    Creates the database directory automatically if it does not exist yet.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name (row["username"])
    return conn


# ── Schema creation ───────────────────────────────────────────────────────────

def initialize_db():
    """Create all tables on first run.  Safe to call every time the server starts
    because CREATE TABLE IF NOT EXISTS does nothing if the table already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # users table — stores one row per registered account
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # messages table — stores every chat message sent through the server
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sender     TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            timestamp  TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[DATABASE] Tables ready.")


# ── User operations ───────────────────────────────────────────────────────────

def save_user(username: str, password_hash: str) -> bool:
    """Insert a new user row.
    Returns True on success, False if the username is already taken.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # UNIQUE constraint violation — username already exists
        return False
    finally:
        conn.close()


def get_user(username: str):
    """Fetch a user row by username.
    Returns a Row object with .username and .password_hash, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password_hash FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


# ── Message operations ────────────────────────────────────────────────────────

def save_message(sender: str, content: str, timestamp: str):
    """Save a chat message to the database (stored as plain text after decryption)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (sender, content, timestamp) VALUES (?, ?, ?)",
        (sender, content, timestamp)
    )
    conn.commit()
    conn.close()


def get_recent_messages(limit: int = 50) -> list:
    """Return the most recent `limit` messages in chronological order (oldest first).
    Each element is a tuple of (sender, content, timestamp).
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Fetch newest rows first, then reverse so they display oldest→newest in chat
    cursor.execute(
        "SELECT sender, content, timestamp FROM messages ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return list(reversed([(row["sender"], row["content"], row["timestamp"]) for row in rows]))
