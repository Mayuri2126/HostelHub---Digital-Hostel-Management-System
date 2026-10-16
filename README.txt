HOSTELHUB - DIGITAL HOSTEL MANAGEMENT SYSTEM

Run:  python main.py      (needs Python 3 with tkinter; no extra packages)

Sections
1. Dashboard  - statistics + complete student overview (ID order, fee status colours)
2. Students   - add / search / UPDATE / DELETE students, change room
                (double-click a row or press "Update Student" to edit)
3. Rooms      - allocate rooms, occupancy, student names per room
4. Fees       - fixed hostel fee Rs 30,000 per student. Enter the amount paid;
                pending amount and status (Pending / Partially Paid / Paid)
                are calculated automatically. Payment history per student.
5. Complaints - register complaints + status tracking

Notes
- Students are always listed in Student ID order (1, 2, 3 ...). After a delete,
  IDs are renumbered so there are no gaps.
- Roll number cannot be changed while updating a student (fees/complaints are linked to it).
- Hostel fee is set in database.py (HOSTEL_FEE = 30000). Existing students in
  hostel.db are automatically moved to this fee.
- A payment larger than the pending amount is rejected.
