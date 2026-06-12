# =============================================================================
# run_client.py — Entry point for the client side of the application.
#
# Run this on each machine (or in each terminal window) that wants to chat:
#
#     python run_client.py
#
# The server (run_server.py) must already be running before clients connect.
# Multiple clients can run simultaneously — each gets its own GUI window.
# =============================================================================

from client.gui import launch_gui

if __name__ == "__main__":
    launch_gui()