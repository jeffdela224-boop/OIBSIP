import os
from cryptography.fernet import Fernet, InvalidToken
from config import KEY_FILE


# ── Key management ─────────────────────────────────────────────────────────────

def _load_or_generate_key() -> bytes:
    """Load the encryption key from disk, or create one if it doesn't exist yet.
    The key file is created at KEY_FILE (default: secret.key in the project root).
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        print(f"[ENCRYPTION] New key generated and saved to '{KEY_FILE}'.")
        return key


# Load the key once when this module is first imported.
# All encrypt/decrypt calls in this session use the same key object.
_KEY = _load_or_generate_key()
_CIPHER = Fernet(_KEY)


# ── Public API ────────────────────────────────────────────────────────────────

def encrypt_message(plaintext: str) -> str:
    """Encrypt a plain-text string and return the encrypted result as a string.
    The client calls this before sending; the server calls this before broadcasting.
    """
    encrypted_bytes = _CIPHER.encrypt(plaintext.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_message(ciphertext: str) -> str:
    """Decrypt an encrypted string and return the original plain text.
    Raises InvalidToken if the ciphertext has been tampered with or the key is wrong.
    """
    decrypted_bytes = _CIPHER.decrypt(ciphertext.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")


def safe_decrypt(ciphertext: str, fallback: str = "[unreadable message]") -> str:
    """Attempt decryption; return a fallback string if decryption fails.
    Useful in places where we want to display something rather than crash.
    """
    try:
        return decrypt_message(ciphertext)
    except (InvalidToken, Exception):
        return fallback