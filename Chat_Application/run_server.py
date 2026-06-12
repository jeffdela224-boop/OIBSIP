# =============================================================================
# run_server.py — Entry point for the server side of the application.
#
# Run this first, before any client connects:
#
#     python run_server.py
#
# Why this file exists instead of running server/server.py directly:
#   Running a script from inside its own folder (cd server && python server.py)
#   causes Python import errors because the project root is not in sys.path.
#   Running from the root with this file ensures all package imports work.
# =============================================================================

from server.server import start_server

if __name__ == "__main__":
    start_server()