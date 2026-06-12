# =============================================================================
# utils/helpers.py — Small reusable functions shared across the project.
# Rule: if more than one file needs the same piece of logic, it belongs here.
# =============================================================================

from datetime import datetime
from config import MAX_USERNAME_LENGTH, MAX_MESSAGE_LENGTH


# ── Timestamps ────────────────────────────────────────────────────────────────

def get_timestamp() -> str:
    """Return the current time formatted as  12:45 PM."""
    return datetime.now().strftime("%I:%M %p")


# ── Message formatting ────────────────────────────────────────────────────────

def format_message(username: str, content: str, timestamp: str = None) -> str:
    """Build a consistently styled chat message string.
    Example output:  [12:45 PM] Alice: Hello everyone!
    """
    if timestamp is None:
        timestamp = get_timestamp()
    return f"[{timestamp}] {username}: {content}"


def format_system_message(content: str) -> str:
    """Build a system/event message string.
    Example output:  [12:45 PM] ── Alice has joined the chat. ──
    """
    return f"[{get_timestamp()}] ── {content} ──"


# ── Input validation ──────────────────────────────────────────────────────────

def validate_username(username: str) -> tuple[bool, str]:
    """Check that a username meets the application's rules.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    if not username or not username.strip():
        return False, "Username cannot be empty."
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username cannot exceed {MAX_USERNAME_LENGTH} characters."
    if not all(c.isalnum() or c == "_" for c in username):
        return False, "Username may only contain letters, numbers, and underscores."
    return True, ""


def validate_message(message: str) -> tuple[bool, str]:
    """Check that a chat message is non-empty and within the length limit.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    if not message or not message.strip():
        return False, "Message cannot be empty."
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message cannot exceed {MAX_MESSAGE_LENGTH} characters."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Check that a password meets minimum security requirements."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""