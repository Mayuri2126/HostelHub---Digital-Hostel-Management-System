import tkinter as tk
from tkinter import ttk, messagebox
from database import conn, cursor, get_room_info, get_available_room_labels
from theme import add_page_header, make_table, clear_table, insert_row


class RoomTab:
    def __init__(self, notebook, on_change):
        self.on_change = on_change
        self.frame = ttk.Frame(notebook, padding=22)
        notebook.add(self.frame, text="  Rooms  ")
        self.build()

    def build(self):
        add_page_header(self.frame, "Room Management", "Allocate rooms and monitor occupancy and available beds.")

        form = ttk.LabelFrame(self.frame, text="  Allocate Room  ", style="Section.TLabelframe", padding=18)
        form.pack(fill="x", pady=(0, 14))
        ttk.Label(form, text="Student Roll Number", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=7)
        self.roll_entry = ttk.Entry(form, width=24)
        self.roll_entry.grid(row=0, column=1, padx=(0, 25), pady=7)
        ttk.Label(form, text="Available Room", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=7)
        self.room_combo = ttk.Combobox(form, width=34, state="readonly")
        self.room_combo.grid(row=0, column=3, padx=(0, 15), pady=7)
        self.room_combo.bind("<<ComboboxSelected>>", self.show_room_details)
        ttk.Button(form, text="Allocate Room", style="Primary.TButton", command=self.allocate_room).grid(row=0, column=4, padx=8)
        self.info = ttk.Label(form, text="Select a room to view capacity.", style="Info.TLabel")
        self.info.grid(row=1, column=0, columnspan=5, sticky="w", padx=4, pady=(8, 0))

        table_box = ttk.LabelFrame(self.frame, text="  Room Occupancy  ", style="Section.TLabelframe", padding=10)
        table_box.pack(fill="both", expand=True)
        self.table = make_table(table_box, [
            ("Room No", 85, "center", False), ("Capacity", 90, "center", False),
            ("Occupied", 90, "center", False), ("Available Beds", 115, "center", False),
            ("Status", 100, "center", False), ("Students", 360, "w", True)])

        bottom = ttk.Frame(self.frame)
        bottom.pack(fill="x", pady=(12, 0))
        ttk.Button(bottom, text="Refresh Room Status", style="Light.TButton", command=self.refresh).pack(side="right")

    def refresh(self):
        self.show_rooms()
        labels = get_available_room_labels()
        self.room_combo["values"] = labels
        if labels:
            self.room_combo.current(0)
            self.show_room_details()
        else:
            self.room_combo.set("No rooms available")
            self.info.config(text="All rooms are currently full.")

    def show_room_details(self, event=None):
        selected = self.room_combo.get()
        if not selected or selected == "No rooms available":
            return
        try:
            room_no = int(selected.split()[1])
        except (ValueError, IndexError):
            return
        info = get_room_info(room_no)
        if info:
            capacity, occupied, available = info
            self.info.config(text=f"Room {room_no}  •  Capacity: {capacity}  •  Occupied: {occupied}  •  Available Beds: {available}")

    def show_rooms(self):
        clear_table(self.table)
        cursor.execute("SELECT room_no, capacity FROM rooms ORDER BY room_no")
        for i, (room_no, capacity) in enumerate(cursor.fetchall()):
            cursor.execute("SELECT name, roll_no FROM students WHERE room_no=? ORDER BY id", (room_no,))
            students = cursor.fetchall()
            occupied = len(students)
            available = max(capacity - occupied, 0)
            status = "FULL" if available == 0 else ("PARTIAL" if occupied else "AVAILABLE")
            names = ", ".join(f"{r[0]} ({r[1]})" for r in students) or "No student allocated"
            insert_row(self.table, (room_no, capacity, occupied, available, status, names), i,
                       iid=str(room_no),
                       status_tag={"FULL": "pending", "PARTIAL": "partial"}.get(status, "paid"))

    def allocate_room(self):
        roll = self.roll_entry.get().strip()
        selected = self.room_combo.get().strip()
        if not roll or not selected or selected == "No rooms available":
            messagebox.showerror("Missing Details", "Enter a student Roll Number and select a room.")
            return
        try:
            room_no = int(selected.split()[1])
        except (ValueError, IndexError):
            messagebox.showerror("Room", "Invalid room selected.")
            return
        cursor.execute("SELECT name, room_no FROM students WHERE roll_no=?", (roll,))
        student = cursor.fetchone()
        if not student:
            messagebox.showerror("Student Not Found", "No student exists with this Roll Number.")
            return
        if student[1] is not None:
            messagebox.showwarning("Already Allocated", f"{student[0]} is already in Room {student[1]}.")
            return
        info = get_room_info(room_no)
        if not info or info[2] <= 0:
            messagebox.showerror("Room Full", f"Room {room_no} is full.")
            return
        cursor.execute("UPDATE students SET room_no=? WHERE roll_no=?", (room_no, roll))
        conn.commit()
        self.roll_entry.delete(0, "end")
        self.on_change()
        messagebox.showinfo("Room Allocated", f"Room {room_no} allocated to {student[0]}.")
