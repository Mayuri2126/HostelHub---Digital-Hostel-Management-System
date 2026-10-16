import tkinter as tk
from tkinter import ttk
from database import cursor, fee_status
from theme import add_page_header, card, make_table, clear_table, insert_row, fee_tag


class DashboardTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook, padding=22)
        notebook.add(self.frame, text="  Dashboard  ")
        self.build()

    def build(self):
        add_page_header(self.frame, "Hostel Dashboard", "A quick view of students, rooms, fees and complaints.")

        cards = tk.Frame(self.frame, bg="#f4f7fb")
        cards.pack(fill="x", pady=(0, 16))
        self.card_values = {}
        specs = [("Total Students", "#2563eb"), ("Occupied Beds", "#7c3aed"),
                 ("Available Beds", "#16a34a"), ("Fee Collected", "#ea580c"),
                 ("Open Complaints", "#dc2626")]
        for title, accent in specs:
            frame, label = card(cards, title, "0", accent)
            frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
            self.card_values[title] = label

        overview = ttk.LabelFrame(self.frame, text="Complete Student Overview", style="Section.TLabelframe", padding=12)
        overview.pack(fill="both", expand=True)

        toolbar = ttk.Frame(overview)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Label(toolbar, text="All important student details in one place.").pack(side="left")
        ttk.Button(toolbar, text="Refresh Dashboard", style="Light.TButton", command=self.refresh).pack(side="right")

        self.table = make_table(overview, [
            ("ID", 55, "center", False), ("Roll No", 90, "center", False),
            ("Student Name", 200, "w", True), ("Course", 100, "center", False),
            ("Phone", 120, "center", False), ("Room", 110, "center", False),
            ("Total Fee", 100, "center", False), ("Paid", 100, "center", False),
            ("Balance", 100, "center", False), ("Fee Status", 120, "center", False)])

    def refresh(self):
        cursor.execute("SELECT COUNT(*) FROM students")
        students = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(capacity),0) FROM rooms")
        total_beds = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students WHERE room_no IS NOT NULL")
        occupied = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM fees WHERE status='Paid'")
        collected = float(cursor.fetchone()[0] or 0)
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status != 'Resolved'")
        complaints = cursor.fetchone()[0]

        values = {
            "Total Students": students,
            "Occupied Beds": occupied,
            "Available Beds": max(total_beds - occupied, 0),
            "Fee Collected": f"₹{collected:,.0f}",
            "Open Complaints": complaints,
        }
        for key, value in values.items():
            self.card_values[key].config(text=str(value))

        clear_table(self.table)
        cursor.execute("""
            SELECT s.id, s.roll_no, s.name, COALESCE(s.course,'-'), COALESCE(s.phone,'-'),
                   COALESCE(CAST(s.room_no AS TEXT),'Not Allocated'),
                   COALESCE(s.total_fee,0),
                   COALESCE((SELECT SUM(f.amount) FROM fees f WHERE f.roll_no=s.roll_no AND f.status='Paid'),0)
            FROM students s ORDER BY s.id ASC
        """)
        for i, row in enumerate(cursor.fetchall()):
            total, paid = float(row[6] or 0), float(row[7] or 0)
            status = fee_status(total, paid)
            insert_row(self.table, (row[0], row[1], row[2], row[3], row[4], row[5],
                                    f"₹{total:,.0f}", f"₹{paid:,.0f}",
                                    f"₹{max(total - paid, 0):,.0f}", status),
                       i, iid=str(row[0]), status_tag=fee_tag(status))
