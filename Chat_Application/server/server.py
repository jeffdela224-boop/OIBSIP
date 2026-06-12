# =============================================================================
# server/server.py — The heart of the application.
#
# Responsibilities:
#   • Open a TCP socket and listen for incoming client connections.
#   • Spawn a dedicated thread for every client that connects.
#   • Run an authentication handshake before allowing a client into the chat.
#   • Receive messages, decrypt them, save them to the DB, re-encrypt, broadcast.
#   • Handle disconnections cleanly without crashing the server.
#
# Think of this file as the post office: it doesn't write letters,
# it receives and delivers them to the right people.
# =============================================================================

import socket
import threading
import json

from database.db    import initialize_db, save_message, get_recent_messages
from server.auth    import register_user, login_user
from utils.helpers  import get_timestamp
from utils.encryption import encrypt_message, decrypt_message, safe_decrypt
from config         import HOST, PORT, BUFFER_SIZE, MAX_HISTORY_MESSAGES


# ── Shared state ──────────────────────────────────────────────────────────────
# clients dict maps each socket connection → the authenticated username.
# clients_lock prevents two threads from modifying the dict at the same time
# (race conditions would cause random crashes or duplicate entries).

clients: dict[socket.socket, str] = {}
clients_lock = threading.Lock()


# ── Helper: send a JSON packet to one client ──────────────────────────────────

def send_packet(conn: socket.socket, data: dict):
    """Serialise `data` as a JSON string and send it over `conn`.
    A newline character is appended so the receiver can split packets reliably.
    """
    try:
        packet = json.dumps(data) + "\n"
        conn.sendall(packet.encode("utf-8"))
    except OSError:
        pass   # connection already closed — ignore silently


# ── Helper: broadcast a packet to all (or all but one) clients ───────────────

def broadcast(data: dict, exclude_conn: socket.socket = None):
    """Send `data` to every currently connected and authenticated client.
    Pass `exclude_conn` to skip the client who sent the original message
    (they don't need to receive their own message back from the server).
    """
    # Snapshot the list of connections while holding the lock, then release it
    # before sending.  Sending while holding the lock would block all other
    # threads until every send finishes — bad for performance.
    with clients_lock:
        recipients = list(clients.keys())

    failed = []
    for conn in recipients:
        if conn is exclude_conn:
            continue
        try:
            send_packet(conn, data)
        except OSError:
            failed.append(conn)

    # Remove any connections that failed during broadcast
    for conn in failed:
        _remove_client(conn)


# ── Helper: remove a client from the shared dict ─────────────────────────────

def _remove_client(conn: socket.socket) -> str | None:
    """Remove the connection from the clients dict.
    Returns the username that was associated with it, or None if it wasn't found.
    Safe to call multiple times — uses dict.pop() with a default.
    """
    with clients_lock:
        return clients.pop(conn, None)


# ── Authentication phase ──────────────────────────────────────────────────────

def _handle_auth(conn: socket.socket) -> str | None:
    """Block until the client sends valid login or register credentials.
    Returns the authenticated username on success, or None on failure/disconnect.

    The client sends packets like:
        {"action": "login",    "username": "alice", "password": "secret"}
        {"action": "register", "username": "bob",   "password": "pass123"}

    The server responds with:
        {"type": "auth", "success": true,  "message": "Login successful!"}
        {"type": "auth", "success": false, "message": "Incorrect password."}
    """
    buffer = ""
    while True:
        try:
            chunk = conn.recv(BUFFER_SIZE).decode("utf-8")
            if not chunk:
                return None    # client disconnected before authenticating

            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                data     = json.loads(line)
                action   = data.get("action", "")
                username = data.get("username", "").strip()
                password = data.get("password", "")

                if action == "register":
                    ok, msg = register_user(username, password)
                elif action == "login":
                    ok, msg = login_user(username, password)
                else:
                    ok, msg = False, "Unknown action. Use 'login' or 'register'."

                send_packet(conn, {"type": "auth", "success": ok, "message": msg})

                if ok:
                    return username   # authentication complete

        except (json.JSONDecodeError, KeyError):
            send_packet(conn, {"type": "auth", "success": False,
                               "message": "Malformed request."})
        except OSError:
            return None


# ── Per-client thread ─────────────────────────────────────────────────────────

def handle_client(conn: socket.socket, addr: tuple):
    """Entry point for the thread that manages a single connected client.

    Flow:
      1. Tell the client auth is required.
      2. Wait for valid credentials.
      3. Register the client in the shared dict.
      4. Send the last N messages as history.
      5. Notify everyone that this user joined.
      6. Loop: receive → decrypt → save → re-encrypt → broadcast.
      7. On disconnect: clean up and notify everyone.
    """
    print(f"[NEW CONNECTION] {addr} connected.")
    username = None

    try:
        # ── Step 1: Signal that authentication is needed ──────────────────────
        send_packet(conn, {"type": "system", "message": "AUTH_REQUIRED"})

        # ── Step 2: Run the auth handshake ────────────────────────────────────
        username = _handle_auth(conn)
        if not username:
            print(f"[AUTH FAILED] {addr} could not authenticate. Closing.")
            return

        # ── Step 3: Check for duplicate sessions ─────────────────────────────
        with clients_lock:
            active_usernames = list(clients.values())

        if username in active_usernames:
            send_packet(conn, {"type": "system", "message": "ALREADY_CONNECTED"})
            print(f"[DUPLICATE] '{username}' is already connected. Rejecting {addr}.")
            return

        # Register this client in the shared dict
        with clients_lock:
            clients[conn] = username

        print(f"[JOINED] '{username}' authenticated from {addr}. "
              f"Active users: {len(clients)}")

        # ── Step 4: Send message history ─────────────────────────────────────
        history = get_recent_messages(MAX_HISTORY_MESSAGES)
        history_payload = [
            {
                "sender":    sender,
                "content":   encrypt_message(content),   # encrypt before sending
                "timestamp": timestamp
            }
            for sender, content, timestamp in history
        ]
        send_packet(conn, {"type": "history", "messages": history_payload})

        # ── Step 5: Announce the new arrival to everyone else ─────────────────
        broadcast(
            {"type": "system", "message": f"{username} has joined the chat."},
            exclude_conn=conn
        )

        # ── Step 6: Main receive loop ─────────────────────────────────────────
        buffer = ""
        while True:
            chunk = conn.recv(BUFFER_SIZE).decode("utf-8")
            if not chunk:
                break   # client disconnected

            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                data = json.loads(line)

                if data.get("type") == "message":
                    encrypted_content = data.get("content", "")

                    # Decrypt the message so it can be stored in plain text
                    plaintext = safe_decrypt(encrypted_content,
                                             fallback="[decryption error]")

                    timestamp = get_timestamp()

                    # Persist to database (plain text)
                    save_message(username, plaintext, timestamp)

                    # Re-encrypt and broadcast to all connected clients
                    # (including the sender, so they see the echoed message)
                    broadcast({
                        "type":      "message",
                        "username":  username,
                        "content":   encrypt_message(plaintext),
                        "timestamp": timestamp
                    })

    except (OSError, json.JSONDecodeError) as e:
        print(f"[ERROR] '{username or addr}': {e}")

    finally:
        # ── Step 7: Cleanup ───────────────────────────────────────────────────
        _remove_client(conn)
        try:
            conn.close()
        except OSError:
            pass

        if username:
            print(f"[LEFT] '{username}' disconnected. Active users: {len(clients)}")
            broadcast({"type": "system", "message": f"{username} has left the chat."})


# ── Server entry point ────────────────────────────────────────────────────────

def start_server():
    """Initialise the database, bind the socket, and accept connections forever."""
    initialize_db()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SO_REUSEADDR lets the server restart immediately without waiting for the OS
    # to release the port (avoids "Address already in use" errors during dev).
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[SERVER STARTED] Listening on {HOST}:{PORT} — waiting for connections...")
    print("Press Ctrl+C to stop the server.\n")

    try:
        while True:
            conn, addr = server_socket.accept()

            # Each client gets its own daemon thread so the server can handle
            # many clients simultaneously without blocking.
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True    # daemon threads are killed automatically when the
            )                  # main program exits
            thread.start()

    except KeyboardInterrupt:
        print("\n[SERVER SHUTTING DOWN] Goodbye.")
    finally:
        server_socket.close()