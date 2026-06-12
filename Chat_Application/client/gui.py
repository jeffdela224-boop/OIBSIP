# =============================================================================
# client/gui.py — Graphical User Interface for the Chat Application.
#
# This file handles all visual elements using Tkinter. It acts as the bridge
# between the user and the ChatClient network layer. 
# =============================================================================

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from client.client import ChatClient
from utils.helpers import format_message, format_system_message, validate_message


class ChatGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Secure Chat Application")
        self.root.geometry("600x700")
        self.root.minsize(450, 500)
        
        # Intercept the window close button to disconnect safely
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure standard styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f4f5f7')
        self.style.configure('TButton', font=('Segoe UI', 10), padding=5)
        self.style.configure('TLabel', font=('Segoe UI', 11), background='#f4f5f7')
        self.root.configure(bg='#f4f5f7')

        # Initialise the network client
        self.client = ChatClient(
            on_message_received=self._safe_on_message,
            on_system_event=self._safe_on_system,
            on_history_received=self._safe_on_history,
            on_auth_response=self._safe_on_auth
        )

        # Setup screens
        self.setup_login_frame()
        self.setup_chat_frame()
        
        # Start at the login screen
        self.login_frame.pack(fill=tk.BOTH, expand=True)

    # ── UI Layout ─────────────────────────────────────────────────────────────

    def setup_login_frame(self):
        """Sets up the Authentication (Login/Register) view."""
        self.login_frame = ttk.Frame(self.root)
        
        container = ttk.Frame(self.login_frame)
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        title_label = ttk.Label(container, text="Welcome to Chat", font=('Segoe UI', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(container, text="Username:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=10)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(container, textvariable=self.username_var, width=25, font=('Segoe UI', 11))
        self.username_entry.grid(row=1, column=1, padx=5, pady=10)

        ttk.Label(container, text="Password:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=10)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(container, textvariable=self.password_var, show="*", width=25, font=('Segoe UI', 11))
        self.password_entry.grid(row=2, column=1, padx=5, pady=10)

        # Buttons
        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Login", command=lambda: self.attempt_auth("login")).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Register", command=lambda: self.attempt_auth("register")).pack(side=tk.LEFT, padx=10)

    def setup_chat_frame(self):
        """Sets up the Main Chat view, including the message board and inputs."""
        self.chat_frame = ttk.Frame(self.root)

        # 1. Input Box Area (Bottom)
        self.input_frame = ttk.Frame(self.chat_frame, padding=10)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.msg_var = tk.StringVar()
        self.msg_entry = ttk.Entry(self.input_frame, textvariable=self.msg_var, font=('Segoe UI', 11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        # Emoji Toggle Button
        self.emoji_btn = ttk.Button(self.input_frame, text="😀", width=3, command=self.toggle_emoji_picker)
        self.emoji_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.send_btn = ttk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT)

        # 2. Emoji Picker Panel (Hidden by default, packed above input frame)
        self.emoji_frame = ttk.Frame(self.chat_frame, padding=5)
        self._build_emoji_grid()

        # 3. Chat History Display Area (Top/Middle)
        self.chat_area = scrolledtext.ScrolledText(
            self.chat_frame, wrap=tk.WORD, font=('Segoe UI', 11),
            bg='#ffffff', fg='#333333', state=tk.DISABLED
        )
        self.chat_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        # Text highlighting tags
        self.chat_area.tag_config('system', foreground='#888888', font=('Segoe UI', 10, 'italic'))
        self.chat_area.tag_config('self_user', foreground='#005a9e', font=('Segoe UI', 11, 'bold'))
        self.chat_area.tag_config('other_user', foreground='#107c10', font=('Segoe UI', 11, 'bold'))
        self.chat_area.tag_config('timestamp', foreground='#aaaaaa', font=('Segoe UI', 9))

    def _build_emoji_grid(self):
        """Populates the toggleable emoji panel."""
        emojis = [
            "😀", "😂", "🥰", "😎", "🥺", "😭", "😡", "👍", 
            "🙏", "🎉", "❤️", "🔥", "✨", "💀", "👀", "✔️"
        ]
        for i, em in enumerate(emojis):
            btn = ttk.Button(self.emoji_frame, text=em, width=3, 
                             command=lambda e=em: self.insert_emoji(e))
            btn.grid(row=i // 8, column=i % 8, padx=2, pady=2)


    # ── User Actions ──────────────────────────────────────────────────────────

    def attempt_auth(self, action: str):
        """Connects to the server and attempts login/registration."""
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
            return

        # Connect if not already connected
        if not self.client.connected:
            if not self.client.connect():
                messagebox.showerror("Connection Error", "Cannot reach the chat server.")
                return
            self.client.start_receiving()

        # Disable buttons temporarily
        self.root.config(cursor="watch")
        self.client.authenticate(action, username, password)

    def send_message(self):
        """Validates and sends the user's input to the server."""
        content = self.msg_var.get()
        valid, error = validate_message(content)
        
        if valid:
            self.client.send_message(content)
            self.msg_var.set("")
            # Hide emoji picker on send to clear UI clutter
            if self.emoji_frame.winfo_ismapped():
                self.emoji_frame.pack_forget()
        else:
            if content.strip():  # Only warn if they actually typed something invalid
                messagebox.showwarning("Invalid Message", error)

    def toggle_emoji_picker(self):
        """Shows or hides the emoji panel above the input bar."""
        if self.emoji_frame.winfo_ismapped():
            self.emoji_frame.pack_forget()
        else:
            # Pack it before the input frame so it appears directly above it
            self.emoji_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10)

    def insert_emoji(self, emoji: str):
        """Inserts an emoji at the cursor position in the message entry."""
        current_pos = self.msg_entry.index(tk.INSERT)
        self.msg_entry.insert(current_pos, emoji)
        self.msg_entry.focus()

    def on_closing(self):
        """Ensures network sockets are closed when the window is 'X'd out."""
        self.client.disconnect()
        self.root.destroy()


    # ── Thread-Safe Callbacks ─────────────────────────────────────────────────
    # The client networking runs in a background thread. All UI updates MUST
    # be routed back to the main Tkinter thread using `root.after(0, ...)`.

    def _safe_on_auth(self, success: bool, message: str):
        self.root.after(0, self._handle_auth_response, success, message)

    def _safe_on_message(self, username: str, content: str, timestamp: str):
        self.root.after(0, self._display_message, username, content, timestamp)

    def _safe_on_system(self, message: str):
        self.root.after(0, self._display_system_message, message)

    def _safe_on_history(self, messages: list):
        self.root.after(0, self._display_history, messages)


    # ── UI Updaters ───────────────────────────────────────────────────────────

    def _handle_auth_response(self, success: bool, message: str):
        self.root.config(cursor="")
        
        if success:
            # Switch views
            self.login_frame.pack_forget()
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            self.root.title(f"Secure Chat — {self.client.username}")
            self.msg_entry.focus()
            
            # Load cached history if it arrived right before the UI was ready
            if self.client._history_buffer:
                self._display_history(self.client._history_buffer)
                self.client._history_buffer = None 
        else:
            # Disconnect on failed auth to keep server clean
            self.client.disconnect()
            messagebox.showerror("Authentication Failed", message)
            self.password_var.set("") # Clear password for safety

    def _display_message(self, username: str, content: str, timestamp: str):
        self.chat_area.config(state=tk.NORMAL)
        
        # Insert timestamp
        self.chat_area.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Insert username with appropriate colour
        user_tag = 'self_user' if username == self.client.username else 'other_user'
        self.chat_area.insert(tk.END, f"{username}: ", user_tag)
        
        # Insert content
        self.chat_area.insert(tk.END, f"{content}\n")
        
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def _display_system_message(self, message: str):
        self.chat_area.config(state=tk.NORMAL)
        formatted = format_system_message(message)
        self.chat_area.insert(tk.END, f"{formatted}\n", 'system')
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)

    def _display_history(self, messages: list):
        """Displays a bulk list of dictionary messages upon joining."""
        self.chat_area.config(state=tk.NORMAL)
        if messages:
            self.chat_area.insert(tk.END, "─── Previous Chat History ───\n", 'system')
            for msg in messages:
                self._display_message(msg["sender"], msg["content"], msg["timestamp"])
            self.chat_area.insert(tk.END, "─── End of History ───\n\n", 'system')
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.yview(tk.END)


# ── Launch Entry Point ────────────────────────────────────────────────────────

def launch_gui():
    """Initialises Tkinter and launches the application."""
    root = tk.Tk()
    
    # Optional: ensure high DPI awareness on Windows to prevent blurry text
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = ChatGUI(root)
    root.mainloop()