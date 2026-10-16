import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database import conn
from theme import add_page_header, make_table, clear_table, insert_row

MUTED = "#64748b"
STATUSES = ["Pending", "In Progress", "Resolved"]

# Column-name guesses (checked in this order against YOUR existing tables)
C_ID = ["id", "complaint_id"]
C_ROLL = ["roll_no", "roll_number", "student_roll", "student_roll_no", "roll", "student_id"]
C_TEXT = ["details", "description", "complaint", "complaint_text", "complaint_details",
          "issue", "message", "text"]
C_STATUS = ["status", "complaint_status"]
C_DATE = ["date", "complaint_date", "created_at", "created_on", "registered_on", "reg_date"]
S_ROLL = ["roll_no", "roll_number", "roll", "student_roll", "student_id"]
S_NAME = ["name", "student_name", "full_name"]
S_ROOM = ["room_no", "room_number", "room", "room_id"]


def table_columns(table):
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def pick(available, candidates, label, required=True):
    lower = {c.lower(): c for c in available}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    if required:
        messagebox.showerror(
            "Database column not found",
            f"Could not find the {label} column.\n\nColumns available: {', '.join(available)}")
        raise RuntimeError(f"Missing {label} column. Available: {available}")
    return None


class ComplaintsTab(ttk.Frame):
    def __init__(self, notebook, refresh_callback=None):
        super().__init__(notebook, padding=15)
        self.refresh_callback = refresh_callback
        self.setup_database()
        self.build_ui()
        notebook.add(self, text="Complaints")
        self.refresh()

    # ---------- database ----------
    def setup_database(self):
        # Creates the table only if you don't have one yet; an existing table is left untouched
        conn.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            date TEXT)""")
        conn.commit()

        c, s = table_columns("complaints"), table_columns("students")
        self.c_id = pick(c, C_ID, "complaint ID")
        self.c_roll = pick(c, C_ROLL, "complaint roll number")
        self.c_text = pick(c, C_TEXT, "complaint text")
        self.c_status = pick(c, C_STATUS, "complaint status")
        self.c_date = pick(c, C_DATE, "complaint date", required=False)
        self.s_roll = pick(s, S_ROLL, "student roll number")
        self.s_name = pick(s, S_NAME, "student name")
        self.s_room = pick(s, S_ROOM, "student room", required=False)

        room_sql = f's."{self.s_room}"' if self.s_room else "''"
        date_sql = f'c."{self.c_date}"' if self.c_date else "''"
        self.sql_list = (
            f'SELECT c."{self.c_id}", c."{self.c_roll}", s."{self.s_name}", {room_sql}, '
            f'c."{self.c_text}", c."{self.c_status}", {date_sql} '
            f'FROM complaints c LEFT JOIN students s ON s."{self.s_roll}" = c."{self.c_roll}" '
            f'ORDER BY c."{self.c_id}" DESC')

    # ---------- UI ----------
    def build_ui(self):
        add_page_header(self, "Complaint Management",
                        "Register student complaints and track their resolution status.")

        reg = ttk.LabelFrame(self, text="  Register New Complaint  ", style="Section.TLabelframe", padding=14)
        reg.pack(fill="x", pady=(0, 14))

        ttk.Label(reg, text="Student Roll Number", style="Card.TLabel").grid(row=0, column=0, padx=8, pady=8, sticky="n")
        self.roll_var = tk.StringVar()
        ttk.Entry(reg, textvariable=self.roll_var, width=20).grid(row=0, column=1, padx=5, pady=8, sticky="n")

        ttk.Label(reg, text="Complaint Details", style="Card.TLabel").grid(row=0, column=2, padx=8, pady=8, sticky="n")
        self.details_txt = tk.Text(reg, width=50, height=4, wrap="word", relief="solid", bd=1)
        self.details_txt.grid(row=0, column=3, padx=5, pady=8)

        ttk.Button(reg, text="Register Complaint", style="Warning.TButton",
                   command=self.register_complaint).grid(row=0, column=4, padx=15, pady=8, sticky="n")

        act = ttk.LabelFrame(self, text="  Complaint Actions  ", style="Section.TLabelframe", padding=12)
        act.pack(fill="x", pady=(0, 14))

        ttk.Label(act, text="New Status:", style="Card.TLabel").grid(row=0, column=0, padx=8)
        self.status_var = tk.StringVar(value=STATUSES[0])
        ttk.Combobox(act, textvariable=self.status_var, values=STATUSES,
                     state="readonly", width=15).grid(row=0, column=1, padx=5)
        ttk.Button(act, text="Update Status", style="Primary.TButton",
                   command=self.update_status).grid(row=0, column=2, padx=10)

        rec = ttk.LabelFrame(self, text="  Complaint Records  ", style="Section.TLabelframe", padding=10)
        rec.pack(fill="both", expand=True)

        self.tree = make_table(rec, [
            ("ID", 55, "center", False), ("Roll No", 100, "center", False),
            ("Student Name", 170, "w", False), ("Room", 80, "center", False),
            ("Complaint", 360, "w", True), ("Status", 110, "center", False),
            ("Date", 110, "center", False)])

    # ---------- actions ----------
    def register_complaint(self):
        roll = self.roll_var.get().strip()
        details = self.details_txt.get("1.0", "end").strip()

        if not roll or not details:
            messagebox.showwarning("Missing Data", "Enter both roll number and complaint details.")
            return

        found = conn.execute(f'SELECT 1 FROM students WHERE "{self.s_roll}" = ?', (roll,)).fetchone()
        if not found:
            messagebox.showerror("Not Found", f"No student found with roll number '{roll}'.")
            return

        cols = [self.c_roll, self.c_text, self.c_status]
        vals = [roll, details, "Pending"]
        if self.c_date:
            cols.append(self.c_date)
            vals.append(date.today().isoformat())
        names = ", ".join(f'"{c}"' for c in cols)
        marks = ", ".join("?" for _ in cols)
        conn.execute(f"INSERT INTO complaints ({names}) VALUES ({marks})", vals)
        conn.commit()

        self.roll_var.set("")
        self.details_txt.delete("1.0", "end")
        messagebox.showinfo("Success", "Complaint registered successfully.")
        self.notify()

    def update_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a complaint from the table first.")
            return
        complaint_id = self.tree.item(selected[0], "values")[0]
        conn.execute(f'UPDATE complaints SET "{self.c_status}" = ? WHERE "{self.c_id}" = ?',
                     (self.status_var.get(), complaint_id))
        conn.commit()
        self.notify()

    def notify(self):
        if self.refresh_callback:
            self.refresh_callback()
        else:
            self.refresh()

    def refresh(self):
        clear_table(self.tree)
        for i, row in enumerate(conn.execute(self.sql_list).fetchall()):
            # tuple(row) turns sqlite3.Row into real values -> no "<sqlite3.Row object ...>"
            values = tuple("" if v is None else v for v in tuple(row))
            tag = {"Resolved": "paid", "In Progress": "partial"}.get(values[5], "pending")
            insert_row(self.tree, values, i, iid=str(values[0]), status_tag=tag)
