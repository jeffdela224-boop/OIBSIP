import os

# Get the absolute path to the directory containing config.py (the project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Network settings
HOST = "127.0.0.1"   # localhost — change to "0.0.0.0" to accept outside connections
PORT = 5555          # the port both server and client must agree on
BUFFER_SIZE = 4096   # maximum bytes read per socket recv() call

# Database
DB_PATH = os.path.join(BASE_DIR, "database", "chat.db")

# Encryption (Now guaranteed to use the exact same file everywhere)
KEY_FILE = os.path.join(BASE_DIR, "secret.key")

# Validation limits
MAX_USERNAME_LENGTH = 20
MAX_MESSAGE_LENGTH  = 500
MAX_HISTORY_MESSAGES = 50      # how many past messages are sent to a newly joined user