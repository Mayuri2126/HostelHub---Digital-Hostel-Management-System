import tkinter as tk
from tkinter import ttk, messagebox
from database import conn
from theme import setup_style, BG, NAVY, CARD, MUTED
from dashboard_tab import DashboardTab
from students_tab import StudentTab
from rooms_tab import RoomTab
from fees_tab import FeesTab
from complaints_tab import ComplaintsTab 


class HostelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HostelHub : Digital Hostel Management System")
        self.root.geometry("1400x850")
        self.root.minsize(1150, 700)
        self.root.configure(bg=BG)
        setup_style()
        self.build_header()
        self.build_notebook()
        self.refresh_all()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_header(self):
        header = tk.Frame(self.root, bg=NAVY, height=105)
        header.pack(fill="x")
        header.pack_propagate(False)
        left = tk.Frame(header, bg=NAVY)
        left.pack(side="left", padx=28, pady=16)
        tk.Label(left, text="HostelHub : Digital Hostel Management System", bg=NAVY, fg="white",
                 font=("Segoe UI", 23, "bold")).pack(anchor="w")
        tk.Label(left, text="Simple • Organized • Complete Hostel Administration",
                 bg=NAVY, fg="#cbd5e1", font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        tk.Label(header, text="ADMIN PANEL", bg="#244866", fg="white",
                 font=("Segoe UI", 9, "bold"), padx=14, pady=7).pack(side="right", padx=28, pady=31)

    def build_notebook(self):
        holder = ttk.Frame(self.root, padding=(18, 15, 18, 18))
        holder.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(holder)
        self.notebook.pack(fill="both", expand=True)
        self.dashboard = DashboardTab(self.notebook)
        self.students = StudentTab(self.notebook, self.refresh_all)
        self.rooms = RoomTab(self.notebook, self.refresh_all)
        self.fees = FeesTab(self.notebook, self.refresh_all)
        self.complaints = ComplaintsTab(self.notebook, self.refresh_all)
        self.tabs = [self.dashboard, self.students, self.rooms, self.fees, self.complaints]

    def refresh_all(self):
        # Dashboard refresh first, then all operational sections.
        self.dashboard.refresh()
        self.students.refresh()
        self.rooms.refresh()
        self.fees.refresh()
        self.complaints.refresh()

    def close(self):
        try:
            conn.close()
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()
    HostelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
