import tkinter as tk
from tkinter import ttk, messagebox
from database import (conn, cursor, get_available_room_labels, get_room_info,
                      resequence_student_ids, HOSTEL_FEE)
from theme import add_page_header, make_table, clear_table, insert_row


class StudentTab:
    def __init__(self, notebook, on_change):
        self.on_change = on_change
        self.editing_id = None            # student id being edited (None = adding new)
        self.frame = ttk.Frame(notebook, padding=22)
        notebook.add(self.frame, text="  Students  ")
        self.build()

    # ------------------------------------------------------------------ UI
    def build(self):
        add_page_header(self.frame, "Student Management",
                        "Add, search, update, delete and allocate students.")

        # ---- form (fixed grid: label column / entry column, always aligned)
        self.form = ttk.LabelFrame(self.frame, text="  Add New Student  ",
                                   style="Section.TLabelframe", padding=18)
        self.form.pack(fill="x", pady=(0, 14))
        form = self.form
        for col in (1, 3):
            form.columnconfigure(col, weight=1, uniform="entries")

        self.name_entry = ttk.Entry(form)
        self.roll_entry = ttk.Entry(form)
        self.course_entry = ttk.Entry(form)
        self.phone_entry = ttk.Entry(form)
        layout = [("Full Name *", self.name_entry, 0, 0), ("Roll Number *", self.roll_entry, 0, 2),
                  ("Course", self.course_entry, 1, 0), ("Phone Number", self.phone_entry, 1, 2)]
        for text, entry, r, c in layout:
            ttk.Label(form, text=text, style="Card.TLabel", width=14).grid(
                row=r, column=c, sticky="w", padx=(3, 8), pady=7)
            entry.grid(row=r, column=c + 1, sticky="ew", padx=(0, 25), pady=7)

        ttk.Label(form, text="Hostel Fee", style="Card.TLabel", width=14).grid(
            row=2, column=0, sticky="w", padx=(3, 8), pady=7)
        ttk.Label(form, text=f"₹{HOSTEL_FEE:,}  (fixed for every student)",
                  style="Fixed.TLabel").grid(row=2, column=1, sticky="w", pady=7)

        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=0, column=4, rowspan=3, padx=(10, 0), sticky="ns")
        self.save_btn = ttk.Button(buttons, text="+  Add Student", style="Success.TButton",
                                   command=self.save_student)
        self.save_btn.pack(fill="x", pady=(0, 8))
        self.cancel_btn = ttk.Button(buttons, text="Clear / Cancel", style="Light.TButton",
                                     command=self.reset_form)
        self.cancel_btn.pack(fill="x")

        # ---- search
        search = ttk.LabelFrame(self.frame, text="  Search Students  ",
                                style="Section.TLabelframe", padding=12)
        search.pack(fill="x", pady=(0, 14))
        ttk.Label(search, text="Name / Roll No:", style="Card.TLabel").pack(side="left", padx=(2, 8))
        self.search_entry = ttk.Entry(search, width=30)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda e: self.search_student())
        ttk.Button(search, text="Search", style="Primary.TButton",
                   command=self.search_student).pack(side="left", padx=7)
        ttk.Button(search, text="Show All", style="Light.TButton",
                   command=self.show_all).pack(side="left", padx=(0, 8))
        # Keep Update/Delete visible above the expanding records table.
        ttk.Button(search, text="Update Student", style="Warning.TButton",
                   command=self.load_for_edit).pack(side="right", padx=(8, 2))
        ttk.Button(search, text="Delete Student", style="Danger.TButton",
                   command=self.delete_student).pack(side="right", padx=2)

        # ---- table
        table_box = ttk.LabelFrame(self.frame, text="  Student Records (in Student ID order)  ",
                                   style="Section.TLabelframe", padding=10)
        table_box.pack(fill="both", expand=True)
        self.table = make_table(table_box, [
            ("ID", 60, "center", False), ("Name", 220, "w", True),
            ("Roll No", 110, "center", False), ("Course", 130, "center", False),
            ("Phone", 130, "center", False), ("Room", 110, "center", False),
            ("Hostel Fee", 110, "center", False)])

        # ---- actions on selected student
        actions = ttk.LabelFrame(self.frame, text="  Selected Student Actions  ",
                                 style="Section.TLabelframe", padding=12)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Label(actions, text="Change Room:", style="Card.TLabel").pack(side="left", padx=(2, 7))
        self.change_room_combo = ttk.Combobox(actions, width=30, state="readonly")
        self.change_room_combo.pack(side="left")
        ttk.Button(actions, text="Change Room", style="Primary.TButton",
                   command=self.change_student_room).pack(side="left", padx=8)
        self.table.bind("<Double-1>", lambda e: self.load_for_edit())
        self.reset_form()

    # ------------------------------------------------------------ data view
    def refresh(self):
        self._fill(self.search_entry.get().strip())
        self.update_change_room_dropdown()

    def show_all(self):
        self.search_entry.delete(0, "end")
        self._fill()

    def _fill(self, search=""):
        clear_table(self.table)
        sql = ("SELECT id, name, roll_no, COALESCE(course,'-'), COALESCE(phone,'-'), "
               "COALESCE(CAST(room_no AS TEXT),'Not Allocated'), total_fee FROM students ")
        if search:
            cursor.execute(sql + "WHERE name LIKE ? OR roll_no LIKE ? ORDER BY id ASC",
                           (f"%{search}%", f"%{search}%"))
        else:
            cursor.execute(sql + "ORDER BY id ASC")          # first student first
        for i, row in enumerate(cursor.fetchall()):
            values = list(tuple(row))
            values[-1] = f"₹{float(values[-1] or 0):,.0f}"
            insert_row(self.table, values, i, iid=str(row[0]))   # iid = student id

    def update_change_room_dropdown(self):
        labels = get_available_room_labels()
        self.change_room_combo["values"] = labels
        if labels:
            self.change_room_combo.current(0)
        else:
            self.change_room_combo.set("No rooms available")

    def selected_id(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Select Student", "Select a student from the table first.")
            return None
        return int(selected[0])

    # ----------------------------------------------------------- add / edit
    def reset_form(self):
        self.editing_id = None
        for e in (self.name_entry, self.roll_entry, self.course_entry, self.phone_entry):
            e.config(state="normal")
            e.delete(0, "end")
        self.form.config(text="  Add New Student  ")
        self.save_btn.config(text="+  Add Student", style="Success.TButton")

    def load_for_edit(self):
        sid = self.selected_id()
        if sid is None:
            return
        cursor.execute("SELECT name, roll_no, course, phone FROM students WHERE id=?", (sid,))
        row = cursor.fetchone()
        if not row:
            return
        self.reset_form()
        self.editing_id = sid
        self.name_entry.insert(0, row[0] or "")
        self.roll_entry.insert(0, row[1] or "")
        self.course_entry.insert(0, row[2] or "")
        self.phone_entry.insert(0, row[3] or "")
        self.roll_entry.config(state="disabled")      # roll no links fees/complaints, so it stays fixed
        self.form.config(text=f"  Update Student (ID {sid})  ")
        self.save_btn.config(text="Save Changes", style="Warning.TButton")
        self.name_entry.focus_set()

    def save_student(self):
        name, roll = self.name_entry.get().strip(), self.roll_entry.get().strip()
        course, phone = self.course_entry.get().strip(), self.phone_entry.get().strip()
        if not name or not roll:
            messagebox.showerror("Missing Details", "Full Name and Roll Number are required.")
            return
        if phone and not (phone.isdigit() and len(phone) == 10):
            messagebox.showerror("Invalid Phone", "Phone number must be exactly 10 digits.")
            return

        if self.editing_id is None:
            cursor.execute("SELECT 1 FROM students WHERE roll_no=?", (roll,))
            if cursor.fetchone():
                messagebox.showerror("Duplicate Roll Number", "This Roll Number already exists.")
                return
            cursor.execute("""INSERT INTO students (name, roll_no, course, phone, room_no, total_fee)
                              VALUES (?, ?, ?, ?, NULL, ?)""", (name, roll, course, phone, HOSTEL_FEE))
            conn.commit()
            message = f"{name} was added successfully."
            title = "Student Added"
        else:
            cursor.execute("UPDATE students SET name=?, course=?, phone=? WHERE id=?",
                           (name, course, phone, self.editing_id))
            conn.commit()
            message = f"{name}'s record was updated."
            title = "Student Updated"
        self.reset_form()
        self.on_change()
        messagebox.showinfo(title, message)

    def search_student(self):
        value = self.search_entry.get().strip()
        self._fill(value)
        if value and not self.table.get_children():
            messagebox.showinfo("Search", "No student found.")

    # ---------------------------------------------------------------- delete
    def delete_student(self):
        sid = self.selected_id()
        if sid is None:
            return
        cursor.execute("SELECT name, roll_no FROM students WHERE id=?", (sid,))
        row = cursor.fetchone()
        if not row:
            return
        name, roll = row[0], row[1]
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete {name} (Roll {roll})?\n\nTheir fee records and complaints "
                                   f"will also be removed and their room will become available."):
            return
        cursor.execute("DELETE FROM students WHERE id=?", (sid,))
        cursor.execute("DELETE FROM fees WHERE roll_no=?", (roll,))
        cursor.execute("DELETE FROM complaints WHERE roll_no=?", (roll,))
        conn.commit()
        resequence_student_ids()                      # keep IDs 1, 2, 3 ... without gaps
        self.reset_form()
        self.on_change()

    # ----------------------------------------------------------- room change
    def change_student_room(self):
        sid = self.selected_id()
        if sid is None:
            return
        cursor.execute("SELECT name FROM students WHERE id=?", (sid,))
        name = cursor.fetchone()[0]
        selected_room = self.change_room_combo.get()
        if not selected_room or selected_room == "No rooms available":
            messagebox.showerror("Room", "No available room selected.")
            return
        try:
            room_no = int(selected_room.split()[1])
        except (ValueError, IndexError):
            messagebox.showerror("Room", "Invalid room selected.")
            return
        info = get_room_info(room_no)
        if not info or info[2] <= 0:
            messagebox.showerror("Room Full", f"Room {room_no} has no available bed.")
            return
        if not messagebox.askyesno("Confirm Room Change", f"Move {name} to Room {room_no}?"):
            return
        cursor.execute("UPDATE students SET room_no=? WHERE id=?", (room_no, sid))
        conn.commit()
        self.on_change()
