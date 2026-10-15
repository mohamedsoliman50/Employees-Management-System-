
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

class Database:
    def __init__(self, db="employee.db"):
        self.db_path = Path(db)
        self.con = sqlite3.connect(str(self.db_path))
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.execute("PRAGMA busy_timeout = 5000")
        self.create_tables()

    def create_tables(self):
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                job TEXT,
                email TEXT,
                gender TEXT,
                phone TEXT,
                address TEXT,
                salary REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                clock_in TEXT NOT NULL,
                clock_out TEXT,
                FOREIGN KEY(employee_id)
                    REFERENCES employees(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS leaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY(employee_id)
                    REFERENCES employees(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS payroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                pay_month TEXT NOT NULL,
                basic_salary REAL NOT NULL DEFAULT 0,
                bonus REAL NOT NULL DEFAULT 0,
                deductions REAL NOT NULL DEFAULT 0,
                UNIQUE(employee_id, pay_month),
                FOREIGN KEY(employee_id)
                    REFERENCES employees(id) ON DELETE CASCADE
            );
        """)

        columns = {
            row["name"]
            for row in self.con.execute(
                "PRAGMA table_info(employees)"
            ).fetchall()
        }

        if "salary" not in columns:
            self.con.execute(
                "ALTER TABLE employees "
                "ADD COLUMN salary REAL DEFAULT 0"
            )

        self.con.commit()

    # ================= EMPLOYEES =================

    def fetch(self, search=""):
        pattern = f"%{search.strip()}%"

        rows = self.con.execute("""
            SELECT id, name, age, job, email,
                   gender, phone, address
            FROM employees
            WHERE name LIKE ?
               OR phone LIKE ?
               OR email LIKE ?
               OR job LIKE ?
            ORDER BY id DESC
        """, (pattern, pattern, pattern, pattern)).fetchall()

        return [tuple(row) for row in rows]

    def insert(self, name, age, job, email, gender, phone, address):
        self.con.execute("""
            INSERT INTO employees
            (name, age, job, email, gender, phone, address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, age, job, email, gender, phone, address))

        self.con.commit()

    def update(self, employee_id, name, age, job, email,
               gender, phone, address):
        self.con.execute("""
            UPDATE employees
            SET name=?, age=?, job=?, email=?,
                gender=?, phone=?, address=?
            WHERE id=?
        """, (
            name, age, job, email, gender,
            phone, address, employee_id
        ))

        self.con.commit()

    def remove(self, employee_id):
        self.con.execute(
            "DELETE FROM attendance WHERE employee_id=?",
            (employee_id,)
        )
        self.con.execute(
            "DELETE FROM leaves WHERE employee_id=?",
            (employee_id,)
        )
        self.con.execute(
            "DELETE FROM payroll WHERE employee_id=?",
            (employee_id,)
        )
        self.con.execute(
            "DELETE FROM employees WHERE id=?",
            (employee_id,)
        )

        self.con.commit()

    def statistics(self):
        total = self.con.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        male = self.con.execute("""
            SELECT COUNT(*) FROM employees
            WHERE LOWER(gender) IN ('male', 'm')
        """).fetchone()[0]

        female = self.con.execute("""
            SELECT COUNT(*) FROM employees
            WHERE LOWER(gender) IN ('female', 'f')
        """).fetchone()[0]

        return total, male, female

    def get_salary(self, employee_id):
        row = self.con.execute(
            "SELECT salary FROM employees WHERE id=?",
            (employee_id,)
        ).fetchone()

        return float(row["salary"] or 0) if row else 0

    def set_salary(self, employee_id, salary):
        salary = float(salary)

        if salary < 0:
            raise ValueError("Salary cannot be negative.")

        self.con.execute(
            "UPDATE employees SET salary=? WHERE id=?",
            (salary, employee_id)
        )
        self.con.commit()

    # ================= ATTENDANCE =================

    def clock_in(self, employee_id):
        employee = self.con.execute(
            "SELECT id FROM employees WHERE id=?",
            (employee_id,)
        ).fetchone()

        if not employee:
            raise ValueError("Employee does not exist.")

        opened = self.con.execute("""
            SELECT id FROM attendance
            WHERE employee_id=? AND clock_out IS NULL
        """, (employee_id,)).fetchone()

        if opened:
            raise ValueError("Employee has already clocked in.")

        now = datetime.now().isoformat(timespec="seconds")

        self.con.execute("""
            INSERT INTO attendance (employee_id, clock_in)
            VALUES (?, ?)
        """, (employee_id, now))

        self.con.commit()

    def clock_out(self, employee_id):
        row = self.con.execute("""
            SELECT id, clock_in FROM attendance
            WHERE employee_id=? AND clock_out IS NULL
            ORDER BY id DESC LIMIT 1
        """, (employee_id,)).fetchone()

        if not row:
            raise ValueError("No open attendance record found.")

        now = datetime.now()
        start = datetime.fromisoformat(row["clock_in"])

        if now < start:
            raise ValueError("Invalid clock-out time.")

        self.con.execute("""
            UPDATE attendance
            SET clock_out=?
            WHERE id=?
        """, (
            now.isoformat(timespec="seconds"),
            row["id"]
        ))

        self.con.commit()

    def attendance_report(self, employee_id=None, period="month"):
        today = date.today()

        if period == "week":
            start_date = today - timedelta(days=today.weekday())
        elif period == "all":
            start_date = date(1900, 1, 1)
        else:
            start_date = today.replace(day=1)

        start = datetime.combine(
            start_date, datetime.min.time()
        )
        end = datetime.now()

        query = """
            SELECT a.id, a.employee_id, e.name,
                   a.clock_in, a.clock_out
            FROM attendance a
            JOIN employees e ON e.id=a.employee_id
            WHERE a.clock_in >= ? AND a.clock_in <= ?
        """

        params = [
            start.isoformat(timespec="seconds"),
            end.isoformat(timespec="seconds")
        ]

        if employee_id is not None:
            query += " AND a.employee_id=?"
            params.append(employee_id)

        query += " ORDER BY a.clock_in DESC"

        rows = self.con.execute(query, params).fetchall()
        result = []

        for row in rows:
            clock_in = datetime.fromisoformat(row["clock_in"])

            clock_out = (
                datetime.fromisoformat(row["clock_out"])
                if row["clock_out"] else None
            )

            # Calculate complete elapsed minutes.
            if clock_out:
                seconds = (
                    clock_out - clock_in
                ).total_seconds()

                total_minutes = max(0, int(seconds // 60))
            else:
                total_minutes = 0

            hours, minutes = divmod(total_minutes, 60)
            duration = f"{hours:02d}:{minutes:02d}"

            result.append((
                row["id"],
                row["employee_id"],
                row["name"],
                clock_in.strftime("%Y-%m-%d"),
                clock_in.strftime("%H:%M"),
                clock_out.strftime("%H:%M")
                if clock_out else "Not Clocked Out",
                duration,
                "Completed" if clock_out else "Open"
            ))

        return result

    # ================= LEAVES =================

    def request_leave(self, employee_id, leave_type,
                      start_date, end_date, reason=""):
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        if end < start:
            raise ValueError(
                "End date cannot be before start date."
            )

        if start.year != end.year:
            raise ValueError(
                "Leave must be within one calendar year."
            )

        if start < date.today():
            raise ValueError("Leave cannot start in the past.")

        overlap = self.con.execute("""
            SELECT id FROM leaves
            WHERE employee_id=?
              AND status IN ('Pending', 'Approved')
              AND start_date <= ? AND end_date >= ?
        """, (
            employee_id,
            end.isoformat(),
            start.isoformat()
        )).fetchone()

        if overlap:
            raise ValueError(
                "Leave overlaps another request."
            )

        self.con.execute("""
            INSERT INTO leaves
            (employee_id, leave_type, start_date,
             end_date, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (
            employee_id, leave_type,
            start.isoformat(), end.isoformat(), reason
        ))

        self.con.commit()

    def leave_report(self, employee_id=None):
        query = """
            SELECT l.id, l.employee_id, e.name, l.leave_type,
                   l.start_date, l.end_date, l.reason, l.status
            FROM leaves l
            JOIN employees e ON e.id=l.employee_id
        """

        params = []

        if employee_id is not None:
            query += " WHERE l.employee_id=?"
            params.append(employee_id)

        query += " ORDER BY l.id DESC"

        return [
            tuple(row)
            for row in self.con.execute(
                query, params
            ).fetchall()
        ]

    def review_leave(self, leave_id, decision):
        if decision not in ("Approved", "Rejected"):
            raise ValueError("Invalid leave decision.")

        row = self.con.execute(
            "SELECT status FROM leaves WHERE id=?",
            (leave_id,)
        ).fetchone()

        if not row:
            raise ValueError(
                "Leave request does not exist."
            )

        if row["status"] != "Pending":
            raise ValueError(
                "Leave request has already been reviewed."
            )

        self.con.execute(
            "UPDATE leaves SET status=? WHERE id=?",
            (decision, leave_id)
        )

        self.con.commit()

    # ================= PAYROLL =================

    def save_payroll(self, employee_id, pay_month,
                     basic_salary, bonus=0, deductions=0):
        datetime.strptime(pay_month, "%Y-%m")

        basic_salary = float(basic_salary)
        bonus = float(bonus)
        deductions = float(deductions)

        if min(basic_salary, bonus, deductions) < 0:
            raise ValueError(
                "Amounts cannot be negative."
            )

        if deductions > basic_salary + bonus:
            raise ValueError(
                "Deductions exceed gross salary."
            )

        self.con.execute("""
            INSERT INTO payroll
            (employee_id, pay_month, basic_salary,
             bonus, deductions)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(employee_id, pay_month)
            DO UPDATE SET
                basic_salary=excluded.basic_salary,
                bonus=excluded.bonus,
                deductions=excluded.deductions
        """, (
            employee_id, pay_month,
            basic_salary, bonus, deductions
        ))

        self.con.commit()

    def payroll_report(self, pay_month=None, employee_id=None):
        query = """
            SELECT p.id, p.employee_id, e.name, p.pay_month,
                   p.basic_salary, p.bonus, p.deductions,
                   p.basic_salary+p.bonus-p.deductions AS net_salary
            FROM payroll p
            JOIN employees e ON e.id=p.employee_id
            WHERE 1=1
        """

        params = []

        if pay_month:
            query += " AND p.pay_month=?"
            params.append(pay_month)

        if employee_id is not None:
            query += " AND p.employee_id=?"
            params.append(employee_id)

        query += " ORDER BY p.pay_month DESC, e.name"

        return [
            tuple(row)
            for row in self.con.execute(
                query, params
            ).fetchall()
        ]

    # ================= BACKUP =================

    def backup(self, destination):
        destination = Path(destination).resolve()

        if destination == self.db_path.resolve():
            raise ValueError(
                "Choose a different backup filename."
            )

        with sqlite3.connect(str(destination)) as backup_con:
            self.con.backup(backup_con)

    # ================= CLOSE =================

    def close(self):
        if self.con is not None:
            self.con.close()
            self.con = None