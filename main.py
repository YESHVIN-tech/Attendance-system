
"""
Simple Student Attendance Management System (Tkinter + SQLite)

Features:
- Add student (ID, Name)
- Mark today's attendance (Present/Absent)
- View attendance records for a selected date
- Export attendance for a date to CSV

Run: python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import date
import csv
import os

DB = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE,
                    name TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    att_date TEXT,
                    status TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id)
                )""")
    conn.commit()
    conn.close()

def add_student(student_id, name):
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("INSERT INTO students (student_id, name) VALUES (?, ?)", (student_id, name))
        conn.commit()
        conn.close()
        return True, "Student added."
    except Exception as e:
        return False, str(e)

def get_students():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT student_id, name FROM students ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_attendance(att_date, records):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # remove existing for that date to allow re-marking
    cur.execute("DELETE FROM attendance WHERE att_date=?", (att_date,))
    for student_id, status in records.items():
        cur.execute("INSERT INTO attendance (student_id, att_date, status) VALUES (?, ?, ?)", (student_id, att_date, status))
    conn.commit()
    conn.close()

def get_attendance_for_date(att_date):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""SELECT s.student_id, s.name, IFNULL(a.status, 'Absent') 
                   FROM students s
                   LEFT JOIN attendance a ON s.student_id = a.student_id AND a.att_date=?
                   ORDER BY s.name""", (att_date,))
    rows = cur.fetchall()
    conn.close()
    return rows

def export_csv(att_date, dest_path):
    rows = get_attendance_for_date(att_date)
    with open(dest_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Student ID", "Name", "Status", "Date"])
        for sid, name, status in rows:
            writer.writerow([sid, name, status, att_date])

# --- Tkinter UI ---
class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Attendance Management")
        self.geometry("700x500")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        # Add student frame
        frm_add = ttk.LabelFrame(self, text="Add Student")
        frm_add.place(x=10, y=10, width=680, height=80)

        ttk.Label(frm_add, text="Student ID:").place(x=10,y=10)
        self.ent_id = ttk.Entry(frm_add, width=20)
        self.ent_id.place(x=90, y=10)
        ttk.Label(frm_add, text="Name:").place(x=300, y=10)
        self.ent_name = ttk.Entry(frm_add, width=30)
        self.ent_name.place(x=350, y=10)
        ttk.Button(frm_add, text="Add", command=self.add_student_ui).place(x=580, y=8)

        # Attendance frame
        frm_att = ttk.LabelFrame(self, text="Mark Attendance")
        frm_att.place(x=10, y=100, width=680, height=250)

        ttk.Label(frm_att, text="Date (YYYY-MM-DD):").place(x=10, y=10)
        self.ent_date = ttk.Entry(frm_att, width=15)
        self.ent_date.place(x=140, y=10)
        self.ent_date.insert(0, str(date.today()))

        ttk.Button(frm_att, text="Load Students", command=self.load_students_for_marking).place(x=300, y=8)
        ttk.Button(frm_att, text="Save Attendance", command=self.save_attendance).place(x=420, y=8)
        ttk.Button(frm_att, text="Export CSV", command=self.export_attendance).place(x=540, y=8)

        # Treeview for students
        cols = ("student_id", "name", "status")
        self.tree = ttk.Treeview(frm_att, columns=cols, show="headings", height=10)
        self.tree.heading("student_id", text="Student ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("status", text="Status")
        self.tree.column("student_id", width=120)
        self.tree.column("name", width=360)
        self.tree.column("status", width=120)
        self.tree.place(x=10, y=45)

        # Right-click menu to toggle status
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Mark Present", command=lambda: self.set_status_selected("Present"))
        self.menu.add_command(label="Mark Absent", command=lambda: self.set_status_selected("Absent"))
        self.tree.bind("<Button-3>", self.show_context)

        # View attendance frame
        frm_view = ttk.LabelFrame(self, text="View Attendance")
        frm_view.place(x=10, y=360, width=680, height=130)
        ttk.Label(frm_view, text="Date (YYYY-MM-DD):").place(x=10, y=10)
        self.view_date = ttk.Entry(frm_view, width=15)
        self.view_date.place(x=140, y=10)
        self.view_date.insert(0, str(date.today()))
        ttk.Button(frm_view, text="Show", command=self.show_attendance_view).place(x=300, y=8)

        self.txt_view = tk.Text(frm_view, width=78, height=4)
        self.txt_view.place(x=10, y=40)

    def add_student_ui(self):
        sid = self.ent_id.get().strip()
        name = self.ent_name.get().strip()
        if not sid or not name:
            messagebox.showwarning("Input", "Enter both Student ID and Name.")
            return
        ok, msg = add_student(sid, name)
        if ok:
            messagebox.showinfo("Success", msg)
            self.ent_id.delete(0, tk.END)
            self.ent_name.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)

    def load_students_for_marking(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        students = get_students()
        for sid, name in students:
            # default Absent unless there is record
            self.tree.insert("", tk.END, values=(sid, name, "Absent"))

    def set_status_selected(self, status):
        sel = self.tree.selection()
        for s in sel:
            vals = list(self.tree.item(s, "values"))
            vals[2] = status
            self.tree.item(s, values=vals)

    def show_context(self, event):
        try:
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def save_attendance(self):
        att_date = self.ent_date.get().strip()
        if not att_date:
            messagebox.showwarning("Input", "Enter date.")
            return
        records = {}
        for item in self.tree.get_children():
            sid, name, status = self.tree.item(item, "values")
            records[sid] = status
        mark_attendance(att_date, records)
        messagebox.showinfo("Saved", f"Attendance saved for {att_date}")

    def export_attendance(self):
        att_date = self.ent_date.get().strip()
        if not att_date:
            messagebox.showwarning("Input", "Enter date.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], initialfile=f"attendance_{att_date}.csv")
        if f:
            export_csv(att_date, f)
            messagebox.showinfo("Exported", f"Attendance exported to {f}")

    def show_attendance_view(self):
        att_date = self.view_date.get().strip()
        rows = get_attendance_for_date(att_date)
        self.txt_view.delete(1.0, tk.END)
        if not rows:
            self.txt_view.insert(tk.END, "No students found.\n")
            return
        lines = []
        for sid, name, status in rows:
            lines.append(f"{sid} | {name} -> {status}")
        self.txt_view.insert(tk.END, "\n".join(lines))

if __name__ == "__main__":
    init_db()
    app = AttendanceApp()
    app.mainloop()
