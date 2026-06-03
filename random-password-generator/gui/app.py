"""
Random Password Generator — GUI
Oasis Infobyte Internship Project
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import string
import sys
import os

# Allow direct imports of src/ when running from any cwd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from generator import generate_password


#Colour palette
BG         = "#0f1117"
SURFACE    = "#1a1d27"
CARD       = "#22263a"
ACCENT     = "#3b82f6"
ACCENT2    = "#60a5fa"
SUCCESS    = "#22c55e"
WARNING    = "#f59e0b"
DANGER     = "#ef4444"
TEXT       = "#f1f5f9"
SUBTEXT    = "#94a3b8"
BORDER     = "#2e3347"

STRENGTH_COLORS = [DANGER, "#f97316", WARNING, "#84cc16", SUCCESS]
STRENGTH_LABELS = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]


#Helper: password strength scorer
def score_password(pwd: str) -> int:
    score = 0
    if len(pwd) >= 12:
        score += 1
    if any(c.islower() for c in pwd):
        score += 1
    if any(c.isupper() for c in pwd):
        score += 1
    if any(c.isdigit() for c in pwd):
        score += 1
    if any(c in string.punctuation for c in pwd):
        score += 1
    return min(score, 4)


#Main application window
class PasswordGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PassForge — Random Password Generator")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.password_var       = tk.StringVar()
        self.length_var         = tk.IntVar(value=16)
        self.use_uppercase      = tk.BooleanVar(value=True)
        self.use_lowercase      = tk.BooleanVar(value=True)
        self.use_digits         = tk.BooleanVar(value=True)
        self.use_special        = tk.BooleanVar(value=True)
        self.exclude_ambiguous  = tk.BooleanVar(value=False)
        self.quantity_var       = tk.IntVar(value=1)

        self._build_ui()
        self._generate()

    def _build_ui(self):
        outer = tk.Frame(self, bg=BG, padx=28, pady=24)
        outer.pack(fill="both", expand=True)

        #Header
        hdr = tk.Frame(outer, bg=BG)
        hdr.pack(fill="x", pady=(0, 20))
        tk.Label(hdr, text="🔐  PassForge",
                 font=("Courier New", 22, "bold"),
                 bg=BG, fg=ACCENT2).pack(side="left")
        tk.Label(hdr, text="Random Password Generator",
                 font=("Courier New", 9), bg=BG, fg=SUBTEXT).pack(
                     side="left", padx=(10, 0), pady=(8, 0))

        #Password display card 
        disp_card = tk.Frame(outer, bg=CARD, padx=16, pady=14,
                             highlightbackground=BORDER, highlightthickness=1)
        disp_card.pack(fill="x", pady=(0, 14))

        tk.Label(disp_card, text="GENERATED PASSWORD",
                 font=("Courier New", 8, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w")

        pw_row = tk.Frame(disp_card, bg=CARD)
        pw_row.pack(fill="x", pady=(6, 0))

        self.pw_label = tk.Label(
            pw_row, textvariable=self.password_var,
            font=("Courier New", 15, "bold"),
            bg=CARD, fg=TEXT, wraplength=460, justify="left")
        self.pw_label.pack(side="left", fill="x", expand=True)

        tk.Button(
            pw_row, text="⧉  Copy",
            font=("Courier New", 9, "bold"),
            bg=ACCENT, fg=TEXT, activebackground=ACCENT2,
            activeforeground=TEXT, relief="flat", padx=12, pady=6,
            cursor="hand2", command=self._copy).pack(side="right", padx=(10, 0))

        # Strength bar
        sf = tk.Frame(disp_card, bg=CARD)
        sf.pack(fill="x", pady=(10, 0))
        tk.Label(sf, text="Strength:", font=("Courier New", 9),
                 bg=CARD, fg=SUBTEXT).pack(side="left")
        self.strength_label = tk.Label(sf, text="",
                                       font=("Courier New", 9, "bold"),
                                       bg=CARD, fg=SUCCESS)
        self.strength_label.pack(side="left", padx=(6, 0))
        self.strength_bar = tk.Canvas(sf, height=6, bg=SURFACE,
                                      highlightthickness=0, width=180)
        self.strength_bar.pack(side="left", padx=(10, 0))

        #Options card 
        opt_card = tk.Frame(outer, bg=CARD, padx=16, pady=14,
                            highlightbackground=BORDER, highlightthickness=1)
        opt_card.pack(fill="x", pady=(0, 14))

        tk.Label(opt_card, text="OPTIONS",
                 font=("Courier New", 8, "bold"),
                 bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(0, 10))

        # Length slider
        len_row = tk.Frame(opt_card, bg=CARD)
        len_row.pack(fill="x", pady=(0, 10))
        tk.Label(len_row, text="Length", font=("Courier New", 10),
                 bg=CARD, fg=TEXT, width=14, anchor="w").pack(side="left")
        self.length_disp = tk.Label(len_row, text=str(self.length_var.get()),
                                    font=("Courier New", 10, "bold"),
                                    bg=CARD, fg=ACCENT2, width=4)
        self.length_disp.pack(side="right")
        ttk.Scale(len_row, from_=4, to=64, variable=self.length_var,
                  orient="horizontal",
                  command=self._on_length_change).pack(
                      side="left", fill="x", expand=True, padx=(10, 6))

        # Toggles
        toggles = [
            ("Uppercase  (A–Z)",           self.use_uppercase),
            ("Lowercase  (a–z)",           self.use_lowercase),
            ("Digits  (0–9)",              self.use_digits),
            ("Symbols  (!@#…)",            self.use_special),
            ("Exclude ambiguous  (0 O l 1)", self.exclude_ambiguous),
        ]
        grid = tk.Frame(opt_card, bg=CARD)
        grid.pack(fill="x")
        for i, (label, var) in enumerate(toggles):
            tk.Checkbutton(
                grid, text=label, variable=var,
                onvalue=True, offvalue=False,
                font=("Courier New", 9),
                bg=CARD, fg=TEXT, selectcolor=SURFACE,
                activebackground=CARD, activeforeground=ACCENT2,
                cursor="hand2", command=self._generate
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 24), pady=3)

        # Quantity
        qty_row = tk.Frame(opt_card, bg=CARD)
        qty_row.pack(fill="x", pady=(10, 0))
        tk.Label(qty_row, text="Quantity", font=("Courier New", 10),
                 bg=CARD, fg=TEXT, width=14, anchor="w").pack(side="left")
        for val in (1, 5, 10):
            tk.Radiobutton(
                qty_row, text=str(val), variable=self.quantity_var, value=val,
                font=("Courier New", 9), bg=CARD, fg=TEXT, selectcolor=SURFACE,
                activebackground=CARD, activeforeground=ACCENT2,
                cursor="hand2").pack(side="left", padx=(0, 12))

        #Action buttons
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(4, 0))

        tk.Button(btn_row, text="⟳  Generate",
                  font=("Courier New", 11, "bold"),
                  bg=ACCENT, fg=TEXT, activebackground=ACCENT2,
                  activeforeground=TEXT, relief="flat",
                  padx=20, pady=10, cursor="hand2",
                  command=self._generate).pack(
                      side="left", expand=True, fill="x", padx=(0, 8))

        tk.Button(btn_row, text="⊞  Batch",
                  font=("Courier New", 11, "bold"),
                  bg=SURFACE, fg=ACCENT2, activebackground=CARD,
                  activeforeground=ACCENT2, relief="flat",
                  padx=20, pady=10, cursor="hand2",
                  highlightbackground=BORDER, highlightthickness=1,
                  command=self._batch).pack(
                      side="left", expand=True, fill="x")

        #Status bar
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(outer, textvariable=self.status_var,
                 font=("Courier New", 8),
                 bg=BG, fg=SUBTEXT, anchor="w").pack(fill="x", pady=(12, 0))

    #Helpers
    def _on_length_change(self, val):
        self.length_disp.config(text=str(int(float(val))))
        self._generate()

    def _build_charset(self):
        chars = ""
        if self.use_uppercase.get():
            chars += string.ascii_uppercase
        if self.use_lowercase.get():
            chars += string.ascii_lowercase
        if self.use_digits.get():
            chars += string.digits
        if self.use_special.get():
            chars += string.punctuation
        if self.exclude_ambiguous.get():
            for ch in "0Ol1I|`\"'":
                chars = chars.replace(ch, "")
        return chars

    def _any_selected(self):
        return any([self.use_uppercase.get(), self.use_lowercase.get(),
                    self.use_digits.get(), self.use_special.get()])

    def _generate_one(self) -> str:
        charset = self._build_charset()
        if not charset:
            return ""
        length = int(self.length_var.get())
        return ''.join(random.choice(charset) for _ in range(length))

    def _generate(self, *_):
        if not self._any_selected():
            self.password_var.set("⚠  Select at least one character type")
            self.status_var.set("No character type selected.")
            self._update_strength("")
            return
        pwd = self._generate_one()
        self.password_var.set(pwd)
        self._update_strength(pwd)
        self.status_var.set(
            f"Generated  ·  Length: {len(pwd)}  ·  Charset: {len(self._build_charset())} chars")

    def _update_strength(self, pwd: str):
        if not pwd:
            self.strength_label.config(text="—", fg=SUBTEXT)
            self.strength_bar.delete("all")
            return
        s = score_password(pwd)
        color = STRENGTH_COLORS[s]
        self.strength_label.config(text=STRENGTH_LABELS[s], fg=color)
        self.strength_bar.delete("all")
        fill_w = int((s / 4) * 180)
        self.strength_bar.create_rectangle(0, 0, 180, 6, fill=SURFACE, outline="")
        if fill_w:
            self.strength_bar.create_rectangle(0, 0, fill_w, 6, fill=color, outline="")

    def _copy(self):
        pwd = self.password_var.get()
        if not pwd or pwd.startswith("⚠"):
            return
        self.clipboard_clear()
        self.clipboard_append(pwd)
        self.status_var.set("✓  Copied to clipboard!")
        self.after(2000, lambda: self.status_var.set(
            f"Generated  ·  Length: {len(pwd)}  ·  Charset: {len(self._build_charset())} chars"))

    def _batch(self):
        qty = self.quantity_var.get()
        if not self._any_selected():
            messagebox.showwarning("No character type", "Select at least one character type.")
            return
        passwords = [self._generate_one() for _ in range(qty)]

        win = tk.Toplevel(self)
        win.title(f"Batch — {qty} Password{'s' if qty > 1 else ''}")
        win.configure(bg=BG)
        win.resizable(False, False)

        tk.Label(win, text=f"BATCH  ·  {qty} PASSWORDS",
                 font=("Courier New", 9, "bold"),
                 bg=BG, fg=SUBTEXT).pack(anchor="w", padx=20, pady=(16, 6))

        frame = tk.Frame(win, bg=BG)
        frame.pack(padx=20, pady=(0, 14))

        for i, p in enumerate(passwords, 1):
            row = tk.Frame(frame, bg=CARD, padx=12, pady=8,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{i:02d}.", font=("Courier New", 9),
                     bg=CARD, fg=SUBTEXT, width=3).pack(side="left")
            tk.Label(row, text=p, font=("Courier New", 11, "bold"),
                     bg=CARD, fg=TEXT).pack(side="left", padx=(8, 20))

            def _copy_one(pwd=p):
                win.clipboard_clear(); win.clipboard_append(pwd)
            tk.Button(row, text="Copy", font=("Courier New", 8),
                      bg=ACCENT, fg=TEXT, relief="flat", padx=8, pady=3,
                      cursor="hand2", command=_copy_one).pack(side="right")

        all_text = "\n".join(passwords)
        tk.Button(win, text="⧉  Copy All",
                  font=("Courier New", 10, "bold"),
                  bg=ACCENT, fg=TEXT, activebackground=ACCENT2,
                  relief="flat", padx=16, pady=8, cursor="hand2",
                  command=lambda: (win.clipboard_clear(), win.clipboard_append(all_text))
                  ).pack(pady=(0, 16))


def main():
    app = PasswordGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()