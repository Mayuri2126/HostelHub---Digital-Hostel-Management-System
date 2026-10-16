import tkinter as tk
from tkinter import ttk

BG = "#f4f7fb"
CARD = "#ffffff"
NAVY = "#17324d"
BLUE = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
ORANGE = "#ea580c"
PURPLE = "#7c3aed"
TEXT = "#1e293b"
MUTED = "#64748b"
BORDER = "#dbe3ec"
STRIPE = "#f1f5f9"
OK_BG, WARN_BG, BAD_BG = "#dcfce7", "#fef3c7", "#fee2e2"


def setup_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Title.TLabel", background=BG, foreground=NAVY, font=("Segoe UI", 18, "bold"))
    style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
    style.configure("Section.TLabelframe", background=CARD, bordercolor=BORDER, relief="solid")
    style.configure("Section.TLabelframe.Label", background=CARD, foreground=NAVY,
                    font=("Segoe UI", 11, "bold"))
    style.configure("TEntry", padding=7)
    style.configure("TCombobox", padding=7)
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background="#e8eef6", foreground=NAVY,
                    font=("Segoe UI", 10, "bold"), padding=(18, 11))
    style.map("TNotebook.Tab", background=[("selected", CARD)],
              foreground=[("selected", BLUE)])
    style.configure("Treeview", background=CARD, fieldbackground=CARD,
                    foreground=TEXT, rowheight=34, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", background=NAVY, foreground="white",
                    font=("Segoe UI", 9, "bold"), padding=9)
    style.map("Treeview", background=[("selected", "#dbeafe")],
              foreground=[("selected", NAVY)])
    for name, color in [("Primary", BLUE), ("Success", GREEN), ("Danger", RED),
                        ("Warning", ORANGE), ("Purple", PURPLE)]:
        style.configure(f"{name}.TButton", background=color, foreground="white",
                        font=("Segoe UI", 9, "bold"), padding=(13, 8), borderwidth=0)
        style.map(f"{name}.TButton", background=[("disabled", "#cbd5e1"), ("active", color)],
                  foreground=[("disabled", "#94a3b8")])
    style.configure("Light.TButton", background="#e8eef6", foreground=NAVY,
                    font=("Segoe UI", 9, "bold"), padding=(12, 8), borderwidth=0)
    style.map("Light.TButton", background=[("active", "#d5dfec")])
    style.configure("Info.TLabel", background=CARD, foreground=BLUE, font=("Segoe UI", 10, "bold"))
    style.configure("Fixed.TLabel", background=CARD, foreground=GREEN, font=("Segoe UI", 10, "bold"))
    style.configure("CardValue.TLabel", background=CARD, foreground=NAVY,
                    font=("Segoe UI", 20, "bold"))
    style.configure("CardSmall.TLabel", background=CARD, foreground=MUTED,
                    font=("Segoe UI", 9))


def add_page_header(parent, title, subtitle):
    box = tk.Frame(parent, bg=BG)
    box.pack(fill="x", pady=(0, 14))
    ttk.Label(box, text=title, style="Title.TLabel").pack(anchor="w")
    ttk.Label(box, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))
    return box


def card(parent, title, value, accent):
    frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    tk.Frame(frame, bg=accent, width=5).pack(side="left", fill="y")
    inner = tk.Frame(frame, bg=CARD, padx=15, pady=12)
    inner.pack(side="left", fill="both", expand=True)
    ttk.Label(inner, text=title, style="CardSmall.TLabel").pack(anchor="w")
    value_label = ttk.Label(inner, text=str(value), style="CardValue.TLabel")
    value_label.pack(anchor="w", pady=(3, 0))
    return frame, value_label


# ---------------------------------------------------------------------------
# Shared table helper: every table in the app is built with this function so
# headings and data always sit in the same column with the same alignment.
# columns = [(heading, width, anchor, stretch), ...]   anchor: "w" or "center"
# ---------------------------------------------------------------------------
def make_table(parent, columns, height=10):
    holder = ttk.Frame(parent)
    holder.pack(fill="both", expand=True)
    holder.rowconfigure(0, weight=1)
    holder.columnconfigure(0, weight=1)

    names = [c[0] for c in columns]
    tree = ttk.Treeview(holder, columns=names, show="headings",
                        selectmode="browse", height=height)
    for name, width, anchor, stretch in columns:
        tree.heading(name, text=name, anchor=anchor)          # heading aligned like its data
        tree.column(name, width=width, minwidth=max(50, width // 2),
                    anchor=anchor, stretch=stretch)

    y = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
    x = ttk.Scrollbar(holder, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
    tree.grid(row=0, column=0, sticky="nsew")
    y.grid(row=0, column=1, sticky="ns")
    x.grid(row=1, column=0, sticky="ew")

    tree.tag_configure("even", background=CARD)
    tree.tag_configure("odd", background=STRIPE)
    tree.tag_configure("paid", foreground=GREEN)
    tree.tag_configure("partial", foreground=ORANGE)
    tree.tag_configure("pending", foreground=RED)
    return tree


def clear_table(tree):
    tree.delete(*tree.get_children())


def insert_row(tree, values, index, iid=None, status_tag=None):
    """Insert one row with zebra striping (and optional status colour)."""
    tags = ["odd" if index % 2 else "even"]
    if status_tag:
        tags.append(status_tag)
    tree.insert("", "end", iid=iid, values=values, tags=tuple(tags))


def fee_tag(status):
    return {"Paid": "paid", "Partially Paid": "partial"}.get(status, "pending")
