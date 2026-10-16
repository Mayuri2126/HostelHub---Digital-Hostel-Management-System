import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from database import conn, cursor, fee_status, HOSTEL_FEE
from theme import (add_page_header, make_table, clear_table, insert_row, fee_tag)


class FeesTab:
    def __init__(self, notebook, on_change):
        self.on_change = on_change
        self.frame = ttk.Frame(notebook, padding=22)
        notebook.add(self.frame, text="  Fees  ")
        self.build()

    # ------------------------------------------------------------------ UI
    def build(self):
        add_page_header(self.frame, "Fee Management",
                        f"Fixed hostel fee: ₹{HOSTEL_FEE:,} per student. "
                        "Enter the amount paid - pending amount and status update automatically.")

        form = ttk.LabelFrame(self.frame, text="  Record Fee Payment  ",
                              style="Section.TLabelframe", padding=18)
        form.pack(fill="x", pady=(0, 14))
        ttk.Label(form, text="Student Roll Number", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", padx=4, pady=7)
        self.roll_entry = ttk.Entry(form, width=22)
        self.roll_entry.grid(row=0, column=1, padx=(0, 22), pady=7)
        ttk.Label(form, text="Amount Paid (₹)", style="Card.TLabel").grid(
            row=0, column=2, sticky="w", padx=4, pady=7)
        self.amount_entry = ttk.Entry(form, width=18)
        self.amount_entry.grid(row=0, column=3, padx=(0, 22), pady=7)
        ttk.Button(form, text="Save Payment", style="Success.TButton",
                   command=self.add_fee).grid(row=0, column=4, padx=5)
        self.info = ttk.Label(form, text="Enter a roll number to see the pending amount.",
                              style="Info.TLabel")
        self.info.grid(row=1, column=0, columnspan=5, sticky="w", padx=4, pady=(8, 0))
        self.roll_entry.bind("<KeyRelease>", lambda e: self.show_pending())

        search = ttk.LabelFrame(self.frame, text="  Search  ",
                                style="Section.TLabelframe", padding=12)
        search.pack(fill="x", pady=(0, 14))
        ttk.Label(search, text="Roll No / Name:", style="Card.TLabel").pack(side="left", padx=(2, 8))
        self.search_entry = ttk.Entry(search, width=24)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda e: self.refresh())
        ttk.Button(search, text="Search", style="Primary.TButton",
                   command=self.refresh).pack(side="left", padx=7)
        ttk.Button(search, text="Show All", style="Light.TButton",
                   command=self.show_all).pack(side="left")

        # ---- per-student summary
        box = ttk.LabelFrame(self.frame, text="  Student Fee Summary (click a student to see payments)  ",
                             style="Section.TLabelframe", padding=10)
        box.pack(fill="both", expand=True)
        self.summary = make_table(box, [
            ("ID", 60, "center", False), ("Roll No", 100, "center", False),
            ("Student Name", 220, "w", True), ("Total Fee", 110, "center", False),
            ("Paid", 110, "center", False), ("Pending", 110, "center", False),
            ("Status", 130, "center", False)], height=6)
        self.summary.bind("<<TreeviewSelect>>", self.on_select_student)

        # ---- payment history
        hist = ttk.LabelFrame(self.frame, text="  Payment History  ",
                              style="Section.TLabelframe", padding=10)
        hist.pack(fill="both", expand=True, pady=(14, 0))
        self.history = make_table(hist, [
            ("Payment ID", 90, "center", False), ("Roll No", 100, "center", False),
            ("Student Name", 220, "w", True), ("Payment Date", 130, "center", False),
            ("Amount", 120, "center", False), ("Status", 110, "center", False)], height=5)
        bar = ttk.Frame(hist)
        bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bar, text="Delete Selected Payment", style="Danger.TButton",
                   command=self.delete_payment).pack(side="right")

    # ---------------------------------------------------------------- data
    def show_all(self):
        self.search_entry.delete(0, "end")
        self.refresh()

    def refresh(self):
        keep = self.summary.selection()
        clear_table(self.summary)
        term = self.search_entry.get().strip()
        sql = ("SELECT id, roll_no, name, total_fee, "
               "COALESCE((SELECT SUM(amount) FROM fees f WHERE f.roll_no = s.roll_no "
               "AND f.status = 'Paid'), 0) FROM students s ")
        if term:
            cursor.execute(sql + "WHERE roll_no LIKE ? OR name LIKE ? ORDER BY id ASC",
                           (f"%{term}%", f"%{term}%"))
        else:
            cursor.execute(sql + "ORDER BY id ASC")
        for i, (sid, roll, name, total, paid) in enumerate(cursor.fetchall()):
            total, paid = float(total or 0), float(paid or 0)
            pending = max(total - paid, 0)
            status = fee_status(total, paid)
            insert_row(self.summary, (sid, roll, name, f"₹{total:,.0f}", f"₹{paid:,.0f}",
                                      f"₹{pending:,.0f}", status), i,
                       iid=str(roll), status_tag=fee_tag(status))   # iid = roll number
        if keep and self.summary.exists(keep[0]):
            self.summary.selection_set(keep[0])
        self.fill_history()
        self.show_pending()

    def fill_history(self):
        clear_table(self.history)
        selected = self.summary.selection()
        sql = ("SELECT f.id, f.roll_no, COALESCE(s.name,'Unknown Student'), "
               "COALESCE(f.payment_date,'-'), f.amount, f.status "
               "FROM fees f LEFT JOIN students s ON f.roll_no = s.roll_no ")
        if selected:
            cursor.execute(sql + "WHERE f.roll_no = ? ORDER BY f.id DESC", (selected[0],))
        else:
            cursor.execute(sql + "ORDER BY f.id DESC")
        for i, r in enumerate(cursor.fetchall()):
            insert_row(self.history, (r[0], r[1], r[2], r[3], f"₹{float(r[4]):,.0f}", r[5]),
                       i, iid=str(r[0]))                        # iid = payment id

    def on_select_student(self, event=None):
        selected = self.summary.selection()
        if selected:
            self.roll_entry.delete(0, "end")
            self.roll_entry.insert(0, selected[0])
        self.fill_history()
        self.show_pending()

    def show_pending(self):
        roll = self.roll_entry.get().strip()
        if not roll:
            self.info.config(text="Enter a roll number to see the pending amount.")
            return
        cursor.execute("SELECT name, total_fee FROM students WHERE roll_no=?", (roll,))
        student = cursor.fetchone()
        if not student:
            self.info.config(text="No student found with this roll number.")
            return
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM fees WHERE roll_no=? AND status='Paid'", (roll,))
        paid = float(cursor.fetchone()[0] or 0)
        total = float(student[1] or 0)
        self.info.config(text=f"{student[0]}  •  Total: ₹{total:,.0f}  •  Paid: ₹{paid:,.0f}  •  "
                              f"Pending: ₹{max(total - paid, 0):,.0f}  •  {fee_status(total, paid)}")

    # ------------------------------------------------------------- actions
    def add_fee(self):
        roll = self.roll_entry.get().strip()
        amount_text = self.amount_entry.get().strip().replace(",", "")
        if not roll or not amount_text:
            messagebox.showerror("Missing Details", "Enter Roll Number and Amount Paid.")
            return
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Enter a valid amount greater than 0.")
            return
        cursor.execute("SELECT name, total_fee FROM students WHERE roll_no=?", (roll,))
        student = cursor.fetchone()
        if not student:
            messagebox.showerror("Student Not Found", "No student exists with this Roll Number.")
            return
        total = float(student[1] or 0)
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM fees WHERE roll_no=? AND status='Paid'", (roll,))
        paid_before = float(cursor.fetchone()[0] or 0)
        pending_before = max(total - paid_before, 0)
        if pending_before <= 0:
            messagebox.showinfo("Already Paid", f"{student[0]} has already paid the full ₹{total:,.0f}.")
            return
        if amount > pending_before:
            messagebox.showerror("Amount Too High",
                                 f"Only ₹{pending_before:,.0f} is pending for {student[0]}.\n"
                                 f"Enter an amount up to ₹{pending_before:,.0f}.")
            return
        cursor.execute("INSERT INTO fees (roll_no, amount, status, payment_date) VALUES (?, ?, 'Paid', ?)",
                       (roll, amount, date.today().isoformat()))
        conn.commit()
        paid_now = paid_before + amount
        pending_now = max(total - paid_now, 0)
        self.amount_entry.delete(0, "end")
        self.on_change()
        messagebox.showinfo("Payment Saved",
                            f"₹{amount:,.0f} recorded for {student[0]}.\n\n"
                            f"Total Fee: ₹{total:,.0f}\nTotal Paid: ₹{paid_now:,.0f}\n"
                            f"Pending: ₹{pending_now:,.0f}\nStatus: {fee_status(total, paid_now)}")

    def delete_payment(self):
        selected = self.history.selection()
        if not selected:
            messagebox.showwarning("Select Payment", "Select a payment from Payment History first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this payment record?\n"
                                   "The student's pending amount and status will be recalculated."):
            return
        cursor.execute("DELETE FROM fees WHERE id=?", (int(selected[0]),))
        conn.commit()
        self.on_change()
