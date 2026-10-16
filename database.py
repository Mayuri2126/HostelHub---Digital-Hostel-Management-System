import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostel.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Fixed hostel fee for every student (single tier)
HOSTEL_FEE = 30000


def column_exists(table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            course TEXT,
            phone TEXT,
            room_no INTEGER,
            total_fee REAL DEFAULT 30000
        )
    """)

    # Add the new field when opening an older project database.
    if not column_exists("students", "total_fee"):
        cursor.execute("ALTER TABLE students ADD COLUMN total_fee REAL DEFAULT 0")

    # Fee tier is fixed: make every existing student use the same hostel fee.
    cursor.execute("UPDATE students SET total_fee = ? WHERE total_fee IS NOT ?", (HOSTEL_FEE, HOSTEL_FEE))

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            payment_date TEXT DEFAULT CURRENT_DATE
        )
    """)
    if not column_exists("fees", "payment_date"):
        cursor.execute("ALTER TABLE fees ADD COLUMN payment_date TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            complaint TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    if not column_exists("complaints", "created_at"):
        cursor.execute("ALTER TABLE complaints ADD COLUMN created_at TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_no INTEGER PRIMARY KEY,
            capacity INTEGER NOT NULL
        )
    """)

    for room in range(1, 21):
        cursor.execute(
            "INSERT OR IGNORE INTO rooms (room_no, capacity) VALUES (?, ?)",
            (room, 2)
        )
    conn.commit()


def get_room_info(room_no):
    cursor.execute("SELECT capacity FROM rooms WHERE room_no = ?", (room_no,))
    row = cursor.fetchone()
    if row is None:
        return None
    capacity = row[0]
    cursor.execute("SELECT COUNT(*) FROM students WHERE room_no = ?", (room_no,))
    occupied = cursor.fetchone()[0]
    return capacity, occupied, max(capacity - occupied, 0)


def get_available_room_labels():
    labels = []
    cursor.execute("SELECT room_no, capacity FROM rooms ORDER BY room_no")
    for room_no, capacity in cursor.fetchall():
        cursor.execute("SELECT COUNT(*) FROM students WHERE room_no = ?", (room_no,))
        occupied = cursor.fetchone()[0]
        if occupied < capacity:
            labels.append(f"Room {room_no} - {capacity - occupied} bed(s) available")
    return labels


def get_student_financials(roll_no):
    cursor.execute("SELECT total_fee FROM students WHERE roll_no = ?", (roll_no,))
    student = cursor.fetchone()
    if not student:
        return None
    total_fee = float(student[0] or 0)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM fees WHERE roll_no = ? AND status = 'Paid'", (roll_no,))
    paid = float(cursor.fetchone()[0] or 0)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM fees WHERE roll_no = ? AND status = 'Pending'", (roll_no,))
    pending_records = float(cursor.fetchone()[0] or 0)
    balance = max(total_fee - paid, 0)
    return total_fee, paid, pending_records, balance


def fee_status(total_fee, paid):
    """Return 'Paid', 'Partially Paid' or 'Pending' from total fee and amount paid."""
    if total_fee > 0 and paid >= total_fee:
        return "Paid"
    if paid > 0:
        return "Partially Paid"
    return "Pending"


def resequence_student_ids():
    """Keep student IDs continuous (1, 2, 3 ...) in order, e.g. after a delete."""
    cursor.execute("SELECT id FROM students ORDER BY id")
    ids = [r[0] for r in cursor.fetchall()]
    for new_id, old_id in enumerate(ids, start=1):
        if new_id != old_id:
            cursor.execute("UPDATE students SET id = ? WHERE id = ?", (new_id, old_id))
    cursor.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'students'", (len(ids),))
    conn.commit()


init_db()
resequence_student_ids()
