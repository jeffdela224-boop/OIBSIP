# =============================================================================
# server/auth.py — User registration and login.
#
# Key rule: passwords are NEVER stored as plain text.
# bcrypt hashes the password with a random salt before it is saved to the DB.
# During login, bcrypt compares the entered password against the stored hash
# without ever reversing (decrypting) the hash.
# =============================================================================

import bcrypt
from database.db import save_user, get_user
from utils.helpers import validate_username, validate_password


def register_user(username: str, password: str) -> tuple[bool, str]:
    """Register a new user account.

    Steps:
      1. Validate the username and password format.
      2. Check that the username is not already taken.
      3. Hash the password with bcrypt.
      4. Save the username + hash to the database.

    Returns (True, success_message) or (False, error_message).
    """
    #  Step 1: Validate inputs
    valid, error = validate_username(username)
    if not valid:
        return False, error

    valid, error = validate_password(password)
    if not valid:
        return False, error

    #  Step 2: Check for duplicate username 
    if get_user(username) is not None:
        return False, "Username is already taken. Please choose another."

    #  Step 3: Hash the password 
    # bcrypt.gensalt() creates a new random salt every time, so two users with
    # the same password will have completely different hashes in the database.
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    #  Step 4: Persist to database 
    # Store the hash as a string; bcrypt.checkpw() will re-encode it as needed.
    success = save_user(username, password_hash.decode("utf-8"))

    if success:
        print(f"[AUTH] New user registered: '{username}'")
        return True, "Registration successful! You are now logged in."
    else:
        return False, "Registration failed due to a server error. Please try again."


def login_user(username: str, password: str) -> tuple[bool, str]:
    """Authenticate an existing user.

    Steps:
      1. Look up the user in the database.
      2. Use bcrypt.checkpw() to compare the entered password against the stored hash.

    Returns (True, success_message) or (False, error_message).
    """
    #  Step 1: Find the user
    user = get_user(username)
    if user is None:
        return False, "Username not found. Please register first."

    #  Step 2: Verify the password
    stored_hash = user["password_hash"].encode("utf-8")

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        print(f"[AUTH] User logged in: '{username}'")
        return True, "Login successful!"
    else:
        return False, "Incorrect password. Please try again."