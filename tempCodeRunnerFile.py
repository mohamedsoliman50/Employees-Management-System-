import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from db import Database
import csv
import re

# ================= DATABASE =================
db = Database("employee.db")
selected_id = None

# ================= COLORS =================
BG = "#f1f5f9"
DARK = "#172554"
PRIMARY = "#2563eb"
GREEN = "#059669"
RED = "#dc2626"
WHITE = "#ffffff"
TEXT = "#1e293b"
MUTED = "#64748b"
PURPLE = "#7c3aed"
TEAL = "#0f766e"

# ================= MAIN WINDOW =================
root = tk.Tk()
root.title("Employee Management System")
root.geometry("1280x760")
root.minsize(1000, 650)
root.configure(bg=BG)

try:
    root.state("zoomed")
except tk.TclError:
    pass

# ================= VARIABLES =================
name = tk.StringVar()
age = tk.StringVar()
job = tk.StringVar()
email = tk.StringVar()
gender = tk.StringVar()
phone = tk.StringVar()
search_var = tk.StringVar()
status_var = tk.StringVar(value="Ready")
attendance_period = tk.StringVar(value="month")
attendance_employee = tk.StringVar(value="All Employees")

# ================= STYLE =================
style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background=WHITE,
    foreground=TEXT,
    rowheight=30,
    fieldbackground=WHITE,
    font=("Segoe UI", 10)
)

style.configure(
    "Treeview.Heading",
    background=DARK,
    foreground=WHITE,
    font=("Segoe UI", 10, "bold"),
    padding=8
)

style.map(
    "Treeview",
    background=[("selected", PRIMARY)],
    foreground=[("selected", WHITE)]
)

style.configure("TCombobox", padding=5)

# ================= MAIN LAYOUT =================
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# ================= HEADER =================
header = tk.Frame(root, bg=DARK, height=85)
header.grid(row=0, column=0, sticky="ew")
header.grid_columnconfigure(0, weight=1)

tk.Label(
    header,
    text="EMPLOYEE MANAGEMENT SYSTEM",
    bg=DARK,
    fg=WHITE,
    font=("Segoe UI", 21, "bold")
).grid(row=0, column=0, sticky="w", padx=25, pady=(12, 0))

tk.Label(
    header,
    text="Employee records, attendance and reports",
    bg=DARK,
    fg="#bfdbfe",
    font=("Segoe UI", 10)
).grid(row=1, column=0, sticky="w", padx=27, pady=(0, 12))

tk.Button(
    header,
    text="Full Screen",
    command=lambda: root.state("zoomed"),
    bg=PRIMARY,
    fg=WHITE,
    activebackground="#1d4ed8",
    activeforeground=WHITE,
    bd=0,
    padx=15,
    pady=8,
    cursor="hand2"
).grid(row=0, column=1, rowspan=2, padx=25)

# ================= CONTENT =================
content = tk.Frame(root, bg=BG)
content.grid(row=1, column=0, sticky="nsew", padx=18, pady=12)

content.grid_rowconfigure(2, weight=1)
content.grid_columnconfigure(0, weight=0, minsize=330)
content.grid_columnconfigure(1, weight=1)

# ================= STATISTICS =================
stats_frame = tk.Frame(content, bg=BG)
stats_frame.grid(
    row=0, column=0, columnspan=2,
    sticky="ew", pady=(0, 12)
)

for i in range(3):
    stats_frame.grid_columnconfigure(i, weight=1)


def create_stat_card(parent, column, title, color):
    card = tk.Frame(
        parent,
        bg=WHITE,
        highlightbackground="#e2e8f0",
        highlightthickness=1
    )
    card.grid(row=0, column=column, sticky="ew", padx=5)

    tk.Label(
        card,
        text=title,
        bg=WHITE,
        fg=MUTED,
        font=("Segoe UI", 10)
    ).pack(anchor="w", padx=15, pady=(10, 2))

    value = tk.Label(
        card,
        text="0",
        bg=WHITE,
        fg=color,
        font=("Segoe UI", 22, "bold")
    )
    value.pack(anchor="w", padx=15, pady=(0, 10))

    return value


total_value = create_stat_card(
    stats_frame, 0, "Total Employees", PRIMARY
)
male_value = create_stat_card(
    stats_frame, 1, "Male Employees", GREEN
)
female_value = create_stat_card(
    stats_frame, 2, "Female Employees", PURPLE
)


form_container = tk.Frame(
    content,
    bg=BG
)
form_container.grid(
    row=1, column=0, rowspan=2,
    sticky="nsew", padx=(5, 12)
)

form_container.grid_rowconfigure(0, weight=1)
form_container.grid_columnconfigure(0, weight=1)

# Canvas لعمل Scroll للفورم
form_canvas = tk.Canvas(
    form_container,
    bg=WHITE,
    highlightthickness=1,
    highlightbackground="#e2e8f0"
)

form_scrollbar = ttk.Scrollbar(
    form_container,
    orient="vertical",
    command=form_canvas.yview
)

form_canvas.configure(
    yscrollcommand=form_scrollbar.set
)

form_scrollbar.grid(row=0, column=1, sticky="ns")
form_canvas.grid(row=0, column=0, sticky="nsew")

# الفورم الداخلي
form = tk.Frame(
    form_canvas,
    bg=WHITE
)

form_window = form_canvas.create_window(
    (0, 0),
    window=form,
    anchor="nw"
)

form.grid_columnconfigure(0, weight=1)


def update_form_scroll(event=None):
    form_canvas.configure(
        scrollregion=form_canvas.bbox("all")
    )


def resize_form(event):
    form_canvas.itemconfigure(
        form_window,
        width=event.width
    )


form.bind("<Configure>", update_form_scroll)
form_canvas.bind("<Configure>", resize_form)


def form_mousewheel(event):
    form_canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


form_canvas.bind(
    "<Enter>",
    lambda event: form_canvas.bind_all(
        "<MouseWheel>", form_mousewheel
    )
)

form_canvas.bind(
    "<Leave>",
    lambda event: form_canvas.unbind_all("<MouseWheel>")
)

tk.Label(
    form,
    text="Employee Details",
    bg=WHITE,
    fg=TEXT,
    font=("Segoe UI", 15, "bold")
).grid(
    row=0, column=0,
    sticky="w", padx=16, pady=(12, 8)
)


def add_field(label, variable, row, values=None):
    tk.Label(
        form,
        text=label,
        bg=WHITE,
        fg=TEXT,
        font=("Segoe UI", 10, "bold")
    ).grid(
        row=row, column=0,
        sticky="w", padx=16, pady=(3, 1)
    )

    if values is None:
        widget = tk.Entry(
            form,
            textvariable=variable,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1
        )
    else:
        widget = ttk.Combobox(
            form,
            textvariable=variable,
            values=values,
            state="readonly",
            font=("Segoe UI", 11)
        )

    widget.grid(
        row=row + 1, column=0,
        sticky="ew", padx=16, pady=(0, 3),
        ipady=3
    )

    return widget


txt_name = add_field("Full Name", name, 1)
txt_age = add_field("Age", age, 3)
txt_job = add_field("Job Title", job, 5)
txt_email = add_field("Email Address", email, 7)
txt_gender = add_field("Gender", gender, 9, ("Male", "Female"))
txt_phone = add_field("Phone Number", phone, 11)

tk.Label(
    form,
    text="Address",
    bg=WHITE,
    fg=TEXT,
    font=("Segoe UI", 10, "bold")
).grid(
    row=13, column=0,
    sticky="w", padx=16, pady=(3, 1)
)

txt_address = tk.Text(
    form,
    height=2,
    font=("Segoe UI", 11),
    relief="solid",
    bd=1,
    wrap="word"
)
txt_address.grid(
    row=14, column=0,
    sticky="ew", padx=16, pady=(0, 5)
)

# ================= TABLE AREA / TABS =================
table_area = tk.Frame(
    content,
    bg=WHITE,
    highlightbackground="#e2e8f0",
    highlightthickness=1
)
table_area.grid(row=2, column=1, sticky="nsew", padx=5)
table_area.grid_rowconfigure(0, weight=1)
table_area.grid_columnconfigure(0, weight=1)

notebook = ttk.Notebook(table_area)
notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

employees_tab = tk.Frame(notebook, bg=WHITE)
attendance_tab = tk.Frame(notebook, bg=WHITE)

notebook.add(employees_tab, text="Employees")
notebook.add(attendance_tab, text="Attendance")

# ================= EMPLOYEE TABLE =================
employees_tab.grid_rowconfigure(2, weight=1)
employees_tab.grid_columnconfigure(0, weight=1)

tk.Label(
    employees_tab,
    text="Employees Directory",
    bg=WHITE,
    fg=TEXT,
    font=("Segoe UI", 15, "bold")
).grid(row=0, column=0, sticky="w", padx=12, pady=10)

search_frame = tk.Frame(employees_tab, bg=WHITE)
search_frame.grid(
    row=1, column=0, sticky="ew",
    padx=12, pady=(0, 10)
)
search_frame.grid_columnconfigure(0, weight=1)

search_entry = tk.Entry(
    search_frame,
    textvariable=search_var,
    font=("Segoe UI", 11),
    relief="solid",
    bd=1
)
search_entry.grid(
    row=0, column=0, sticky="ew",
    ipady=6, padx=(0, 8)
)

tk.Button(
    search_frame,
    text="Clear Search",
    command=lambda: search_var.set(""),
    bg="#e2e8f0",
    fg=TEXT,
    bd=0,
    padx=10,
    pady=7,
    cursor="hand2"
).grid(row=0, column=1)

employee_table_frame = tk.Frame(employees_tab, bg=WHITE)
employee_table_frame.grid(
    row=2, column=0, sticky="nsew",
    padx=12, pady=(0, 12)
)
employee_table_frame.grid_rowconfigure(0, weight=1)
employee_table_frame.grid_columnconfigure(0, weight=1)

columns = (
    "id", "name", "age", "job",
    "email", "gender", "phone", "address"
)

tv = ttk.Treeview(
    employee_table_frame,
    columns=columns,
    show="headings",
    selectmode="browse"
)

headings = {
    "id": ("ID", 45),
    "name": ("Name", 130),
    "age": ("Age", 50),
    "job": ("Job", 110),
    "email": ("Email", 180),
    "gender": ("Gender", 75),
    "phone": ("Phone", 110),
    "address": ("Address", 160)
}

for col, (heading, width) in headings.items():
    tv.heading(col, text=heading)
    tv.column(col, width=width, minwidth=40, anchor="w")

yscroll = ttk.Scrollbar(
    employee_table_frame, orient="vertical", command=tv.yview
)
xscroll = ttk.Scrollbar(
    employee_table_frame, orient="horizontal", command=tv.xview
)

tv.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
tv.grid(row=0, column=0, sticky="nsew")
yscroll.grid(row=0, column=1, sticky="ns")
xscroll.grid(row=1, column=0, sticky="ew")

tv.tag_configure("even", background="#f8fafc")
tv.tag_configure("odd", background=WHITE)

# ================= ATTENDANCE TAB =================
attendance_tab.grid_rowconfigure(2, weight=1)
attendance_tab.grid_columnconfigure(0, weight=1)

tk.Label(
    attendance_tab,
    text="Attendance Management",
    bg=WHITE,
    fg=TEXT,
    font=("Segoe UI", 15, "bold")
).grid(row=0, column=0, sticky="w", padx=12, pady=10)

attendance_controls = tk.Frame(attendance_tab, bg=WHITE)
attendance_controls.grid(
    row=1, column=0, sticky="ew",
    padx=12, pady=(0, 10)
)

tk.Label(
    attendance_controls,
    text="Period:",
    bg=WHITE,
    fg=TEXT
).pack(side="left", padx=(0, 5))

period_combo = ttk.Combobox(
    attendance_controls,
    textvariable=attendance_period,
    values=("week", "month"),
    state="readonly",
    width=9
)
period_combo.pack(side="left", padx=(0, 12))

tk.Label(
    attendance_controls,
    text="Employee:",
    bg=WHITE,
    fg=TEXT
).pack(side="left", padx=(0, 5))

attendance_employee_combo = ttk.Combobox(
    attendance_controls,
    textvariable=attendance_employee,
    state="readonly",
    width=22
)
attendance_employee_combo.pack(side="left", padx=(0, 10))

attendance_table_frame = tk.Frame(attendance_tab, bg=WHITE)
attendance_table_frame.grid(
    row=2, column=0, sticky="nsew",
    padx=12, pady=(0, 12)
)
attendance_table_frame.grid_rowconfigure(0, weight=1)
attendance_table_frame.grid_columnconfigure(0, weight=1)

attendance_columns = (
    "id", "employee_id", "name", "date",
    "clock_in", "clock_out", "hours", "status"
)

attendance_tv = ttk.Treeview(
    attendance_table_frame,
    columns=attendance_columns,
    show="headings",
    selectmode="browse"
)

attendance_headings = {
    "id": ("Record ID", 75),
    "employee_id": ("Employee ID", 85),
    "name": ("Employee", 150),
    "date": ("Date", 100),
    "clock_in": ("Clock In", 100),
    "clock_out": ("Clock Out", 140),
    "hours": ("Hours", 70),
    "status": ("Status", 100)
}

for col, (heading, width) in attendance_headings.items():
    attendance_tv.heading(col, text=heading)
    attendance_tv.column(
        col, width=width, minwidth=60, anchor="w"
    )

attendance_y = ttk.Scrollbar(
    attendance_table_frame,
    orient="vertical",
    command=attendance_tv.yview
)
attendance_x = ttk.Scrollbar(
    attendance_table_frame,
    orient="horizontal",
    command=attendance_tv.xview
)

attendance_tv.configure(
    yscrollcommand=attendance_y.set,
    xscrollcommand=attendance_x.set
)

attendance_tv.grid(row=0, column=0, sticky="nsew")
attendance_y.grid(row=0, column=1, sticky="ns")
attendance_x.grid(row=1, column=0, sticky="ew")

attendance_tv.tag_configure("open", background="#fef3c7")
attendance_tv.tag_configure("completed", background="#dcfce7")

# ================= STATUS BAR =================
status_bar = tk.Label(
    root,
    textvariable=status_var,
    bg="#e2e8f0",
    fg=TEXT,
    anchor="w",
    padx=15,
    pady=7,
    font=("Segoe UI", 9)
)
status_bar.grid(row=2, column=0, sticky="ew")

# ================= EMPLOYEE FUNCTIONS =================
def clear_form():
    global selected_id
    selected_id = None

    name.set("")
    age.set("")
    job.set("")
    email.set("")
    gender.set("")
    phone.set("")
    txt_address.delete("1.0", tk.END)

    for item in tv.selection():
        tv.selection_remove(item)

    status_var.set("Ready")
    txt_name.focus_set()


def refresh_statistics():
    total, male, female = db.statistics()
    total_value.config(text=str(total))
    male_value.config(text=str(male))
    female_value.config(text=str(female))


def display_all(*args):
    try:
        tv.delete(*tv.get_children())
        records = db.fetch(search_var.get().strip())

        for index, record in enumerate(records):
            tag = "even" if index % 2 == 0 else "odd"
            tv.insert("", tk.END, values=record, tags=(tag,))

        refresh_statistics()
        refresh_employee_options()
        status_var.set(f"{len(records)} employee(s) displayed")

    except Exception as error:
        messagebox.showerror("Database Error", str(error))


def select_employee(event=None):
    global selected_id

    selection = tv.selection()
    if not selection:
        return

    values = tv.item(selection[0], "values")
    if not values:
        return

    selected_id = int(values[0])

    name.set(values[1])
    age.set(values[2])
    job.set(values[3])
    email.set(values[4])
    gender.set(values[5])
    phone.set(values[6])

    txt_address.delete("1.0", tk.END)
    txt_address.insert("1.0", values[7])

    status_var.set(f"Selected employee ID: {selected_id}")


def validate_form():
    fields = [
        name.get().strip(),
        age.get().strip(),
        job.get().strip(),
        email.get().strip(),
        gender.get().strip(),
        phone.get().strip(),
        txt_address.get("1.0", tk.END).strip()
    ]

    if not all(fields):
        messagebox.showwarning(
            "Missing Data", "Please fill in all fields."
        )
        return False

    try:
        employee_age = int(age.get().strip())
        if not 18 <= employee_age <= 100:
            messagebox.showwarning(
                "Invalid Age", "Age must be between 18 and 100."
            )
            return False
    except ValueError:
        messagebox.showwarning(
            "Invalid Age", "Age must be a whole number."
        )
        return False

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email.get().strip()
    ):
        messagebox.showwarning(
            "Invalid Email", "Please enter a valid email address."
        )
        return False

    if len(phone.get().strip()) < 6:
        messagebox.showwarning(
            "Invalid Phone", "Please enter a valid phone number."
        )
        return False

    return True


def add_employee():
    if not validate_form():
        return

    try:
        db.insert(
            name.get().strip(),
            int(age.get().strip()),
            job.get().strip(),
            email.get().strip(),
            gender.get(),
            phone.get().strip(),
            txt_address.get("1.0", tk.END).strip()
        )

        display_all()
        refresh_attendance()
        clear_form()

        messagebox.showinfo(
            "Success", "Employee added successfully."
        )

    except Exception as error:
        messagebox.showerror("Error", str(error))


def update_employee():
    if selected_id is None:
        messagebox.showwarning(
            "Select Employee",
            "Select an employee from the table first."
        )
        return

    if not validate_form():
        return

    try:
        db.update(
            selected_id,
            name.get().strip(),
            int(age.get().strip()),
            job.get().strip(),
            email.get().strip(),
            gender.get(),
            phone.get().strip(),
            txt_address.get("1.0", tk.END).strip()
        )

        display_all()
        refresh_attendance()
        clear_form()

        messagebox.showinfo(
            "Success", "Employee updated successfully."
        )

    except Exception as error:
        messagebox.showerror("Error", str(error))


def delete_employee():
    if selected_id is None:
        messagebox.showwarning(
            "Select Employee",
            "Select an employee from the table first."
        )
        return

    if not messagebox.askyesno(
        "Confirm Delete",
        "Delete this employee and their attendance records?"
    ):
        return

    try:
        db.remove(selected_id)
        display_all()
        refresh_attendance()
        clear_form()

        messagebox.showinfo(
            "Success", "Employee deleted successfully."
        )

    except Exception as error:
        messagebox.showerror("Error", str(error))


def export_csv():
    try:
        records = db.fetch(search_var.get().strip())

        if not records:
            messagebox.showinfo(
                "Export", "There are no records to export."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Export Employees",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="employees.csv"
        )

        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([
                "ID", "Name", "Age", "Job",
                "Email", "Gender", "Phone", "Address"
            ])
            writer.writerows(records)

        messagebox.showinfo(
            "Export", f"Export completed:\n{path}"
        )

    except Exception as error:
        messagebox.showerror("Export Error", str(error))


def backup_database():
    try:
        path = filedialog.asksaveasfilename(
            title="Save Database Backup",
            defaultextension=".db",
            filetypes=[("SQLite database", "*.db")],
            initialfile="employee_backup.db"
        )

        if not path:
            return

        db.backup(path)

        messagebox.showinfo(
            "Backup",
            f"Database backup created successfully:\n{path}"
        )

    except Exception as error:
        messagebox.showerror("Backup Error", str(error))


# ================= ATTENDANCE FUNCTIONS =================
def refresh_employee_options():
    try:
        records = db.fetch("")
        options = ["All Employees"] + [
            f"{record[0]} - {record[1]}"
            for record in records
        ]

        previous = attendance_employee.get()
        attendance_employee_combo["values"] = options

        if previous in options:
            attendance_employee.set(previous)
        else:
            attendance_employee.set("All Employees")

    except Exception as error:
        messagebox.showerror(
            "Attendance Error", str(error)
        )


def refresh_attendance(*args):
    try:
        attendance_tv.delete(*attendance_tv.get_children())

        selected = attendance_employee.get()
        employee_id = None

        if selected and selected != "All Employees":
            try:
                employee_id = int(selected.split(" - ", 1)[0])
            except (ValueError, IndexError):
                employee_id = None

        records = db.attendance_report(
            employee_id=employee_id,
            period=attendance_period.get()
        )

        for record in records:
            tag = "completed" if record[7] == "Completed" else "open"
            attendance_tv.insert(
                "", tk.END, values=record, tags=(tag,)
            )

        status_var.set(
            f"{len(records)} attendance record(s) displayed"
        )

    except Exception as error:
        messagebox.showerror(
            "Attendance Error", str(error)
        )


def get_selected_employee_id():
    if selected_id is not None:
        return selected_id

    selection = tv.selection()
    if selection:
        values = tv.item(selection[0], "values")
        if values:
            return int(values[0])

    messagebox.showwarning(
        "Select Employee",
        "Select an employee from the Employees tab first."
    )
    return None


def clock_in_employee():
    employee_id = get_selected_employee_id()
    if employee_id is None:
        return

    try:
        db.clock_in(employee_id)
        refresh_attendance()
        status_var.set(f"Employee {employee_id} clocked in")

        messagebox.showinfo(
            "Clock In", "Attendance recorded successfully."
        )

    except Exception as error:
        messagebox.showerror("Clock In Error", str(error))


def clock_out_employee():
    employee_id = get_selected_employee_id()
    if employee_id is None:
        return

    try:
        db.clock_out(employee_id)
        refresh_attendance()
        status_var.set(f"Employee {employee_id} clocked out")

        messagebox.showinfo(
            "Clock Out", "Clock-out recorded successfully."
        )

    except Exception as error:
        messagebox.showerror("Clock Out Error", str(error))


def export_attendance_csv():
    try:
        records = db.attendance_report(
            period=attendance_period.get()
        )

        selected = attendance_employee.get()
        if selected and selected != "All Employees":
            try:
                employee_id = int(selected.split(" - ", 1)[0])
                records = db.attendance_report(
                    employee_id=employee_id,
                    period=attendance_period.get()
                )
            except (ValueError, IndexError):
                pass

        if not records:
            messagebox.showinfo(
                "Export", "No attendance records to export."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Export Attendance",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="attendance_report.csv"
        )

        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Record ID", "Employee ID", "Employee Name",
                "Date", "Clock In", "Clock Out", "Hours", "Status"
            ])
            writer.writerows(records)

        messagebox.showinfo(
            "Export",
            f"Attendance report exported:\n{path}"
        )

    except Exception as error:
        messagebox.showerror("Export Error", str(error))


# ================= ACTION BUTTONS =================
actions = tk.Frame(form, bg=WHITE)
actions.grid(
    row=15, column=0, sticky="ew",
    padx=10, pady=(3, 8)
)

for col in range(2):
    actions.grid_columnconfigure(col, weight=1)


def action_button(text, command, color, row, col):
    tk.Button(
        actions,
        text=text,
        command=command,
        bg=color,
        fg=WHITE,
        activebackground=color,
        activeforeground=WHITE,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=3,
        pady=7
    ).grid(
        row=row, column=col,
        sticky="ew", padx=3, pady=3
    )


action_button("Add Employee", add_employee, GREEN, 0, 0)
action_button("Update", update_employee, PRIMARY, 0, 1)
action_button("Delete", delete_employee, RED, 1, 0)
action_button("Clear Form", clear_form, "#475569", 1, 1)
action_button("Export CSV", export_csv, PURPLE, 2, 0)
action_button("Backup DB", backup_database, TEAL, 2, 1)

action_button(
    "Clock In", clock_in_employee, GREEN, 3, 0
)
action_button(
    "Clock Out", clock_out_employee, RED, 3, 1
)
action_button(
    "Attendance CSV", export_attendance_csv, PURPLE, 4, 0
)
action_button(
    "Refresh Attendance", refresh_attendance, TEAL, 4, 1
)

# ================= EVENTS =================
tv.bind("<<TreeviewSelect>>", select_employee)
search_var.trace_add("write", display_all)
attendance_period.trace_add("write", refresh_attendance)
attendance_employee.trace_add("write", refresh_attendance)

notebook.bind(
    "<<NotebookTabChanged>>",
    lambda event: refresh_attendance()
)

# Keyboard shortcuts
root.bind("<Control-f>", lambda event: search_entry.focus_set())
root.bind("<Escape>", lambda event: clear_form())
root.bind("<Control-s>", lambda event: export_csv())

# ================= START =================
display_all()
refresh_employee_options()
refresh_attendance()
txt_name.focus_set()


def close_app():
    try:
        db.close()
    finally:
        root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()