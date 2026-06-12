# =============================================================================
# client/client.py — Networking layer for the client.
#
# This file handles everything to do with the socket connection:
#   • Connecting to the server.
#   • Sending authentication credentials.
#   • Sending encrypted chat messages.
#   • Receiving all incoming server packets in a background thread.
#   • Calling the appropriate callback so the GUI can react.
#
# The GUI (gui.py) does NOT do any networking itself.
# It calls functions on this class and provides callbacks for incoming data.
# =============================================================================

import socket
import threading
import json

from utils.encryption import encrypt_message, safe_decrypt
from config import HOST, PORT, BUFFER_SIZE


class ChatClient:
    """Manages the TCP connection between this user and the chat server.

    Usage pattern:
        client = ChatClient(on_message_received=..., on_system_event=...,
                            on_history_received=..., on_auth_response=...)
        client.connect()
        client.start_receiving()
        client.authenticate("login", "alice", "secret")
        client.send_message("Hello everyone!")
        client.disconnect()

    All callbacks are called from the background receive thread, so GUI code
    inside them must use root.after(0, ...) to safely update Tkinter widgets.
    """

    def __init__(self,
                 on_message_received,   # (username, content, timestamp) → None
                 on_system_event,       # (message_str) → None
                 on_history_received,   # (list of message dicts) → None
                 on_auth_response):     # (success: bool, message: str) → None
        self._socket    = None
        self.username   = None
        self.connected  = False

        # Callbacks — the GUI replaces these after authentication succeeds
        self.on_message_received = on_message_received
        self.on_system_event     = on_system_event
        self.on_history_received = on_history_received
        self.on_auth_response    = on_auth_response

        # Buffer to store history that might arrive before the ChatWindow is ready
        self._history_buffer: list | None = None


    # ── Connection management ─────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open a TCP connection to the server.
        Returns True on success, False if the server is unreachable.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((HOST, PORT))
            self.connected = True
            return True
        except (ConnectionRefusedError, OSError):
            return False

    def disconnect(self):
        """Close the connection gracefully."""
        self.connected = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass


    # ── Sending ───────────────────────────────────────────────────────────────

    def _send_packet(self, data: dict):
        """Serialise and send a JSON packet to the server."""
        if not self.connected:
            return
        try:
            packet = json.dumps(data) + "\n"
            self._socket.sendall(packet.encode("utf-8"))
        except OSError:
            self.connected = False

    def authenticate(self, action: str, username: str, password: str):
        """Send login or registration credentials to the server.
        `action` must be either "login" or "register".
        """
        self.username = username
        self._send_packet({
            "action":   action,
            "username": username,
            "password": password
        })

    def send_message(self, content: str):
        """Encrypt `content` and send it to the server as a chat message."""
        if not content.strip():
            return
        encrypted = encrypt_message(content)
        self._send_packet({"type": "message", "content": encrypted})


    # ── Receiving ─────────────────────────────────────────────────────────────

    def start_receiving(self):
        """Start the background thread that listens for incoming server packets.
        Call this once after connect() and before authenticate().
        """
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()

    def _receive_loop(self):
        """Run in a background thread.
        Continuously reads from the socket, splits on newlines to get complete
        JSON packets, and dispatches each one to _dispatch().
        """
        buffer = ""
        while self.connected:
            try:
                chunk = self._socket.recv(BUFFER_SIZE).decode("utf-8")
                if not chunk:
                    break   # server closed the connection

                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            self._dispatch(json.loads(line))
                        except json.JSONDecodeError:
                            pass   # ignore malformed packets

            except OSError:
                break

        self.connected = False
        self.on_system_event("DISCONNECTED")

    def _dispatch(self, data: dict):
        """Route an incoming packet to the correct callback based on its 'type'."""
        msg_type = data.get("type")

        if msg_type == "message":
            # Decrypt the content before handing it to the GUI
            plaintext = safe_decrypt(data.get("content", ""))
            self.on_message_received(
                data.get("username", "?"),
                plaintext,
                data.get("timestamp", "")
            )

        elif msg_type == "system":
            self.on_system_event(data.get("message", ""))

        elif msg_type == "auth":
            self.on_auth_response(
                data.get("success", False),
                data.get("message", "")
            )

        elif msg_type == "history":
            messages = data.get("messages", [])
            
            # FIX: Decrypt each history message before passing it to the GUI
            for msg in messages:
                msg["content"] = safe_decrypt(msg.get("content", ""))
                
            self._history_buffer = messages          # cache in case GUI isn't ready yet
            self.on_history_received(messages)