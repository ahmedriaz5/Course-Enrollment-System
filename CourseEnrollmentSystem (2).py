#!/usr/bin/env python
# coding: utf-8

# In[1]:


import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime
import hashlib
from tkinter import filedialog
from tkinter import simpledialog
from tkcalendar import Calendar
from PIL import Image, ImageTk

class CourseEnrollmentSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Course Enrollment System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f5f5f5")  # Light gray background

        # Color theme
        self.bg_color = "#f5f5f5"  # Light gray (almost white)
        self.main_color = "#deb887"  # Burlywood
        self.secondary_color = "#f0e0c0"  # Lighter burlywood
        self.highlight_color = "#cdab7d"  # Darker burlywood
        self.text_color = "#333333"  # Dark gray for text
        self.accent_color = "#8b7355"  # Darker brown for accents

        # Database connection
        self.conn = pymysql.connect(
            host="localhost",
            user="root",
            password="AHMED",  
            database="course_enrollment_system"
        )

        # Initialize database
        self.initialize_database()

        # Style configuration
        self.style = ttk.Style()

        # Configure the main frame style
        self.style.configure('TFrame', background=self.bg_color)

        # Configure button styles
        self.style.configure('TButton', 
                           font=('Arial', 10), 
                           padding=5,
                           background=self.main_color,
                           foreground=self.text_color,
                           bordercolor=self.accent_color)
        self.style.map('TButton',
                      background=[('active', self.highlight_color),
                                 ('disabled', '#d3d3d3')],
                      foreground=[('disabled', '#a0a0a0')])

        # Configure label styles
        self.style.configure('TLabel', 
                           font=('Arial', 10),
                           background=self.bg_color,
                           foreground=self.text_color)

        # Configure entry styles
        self.style.configure('TEntry', 
                           font=('Arial', 10),
                           fieldbackground='white',
                           foreground=self.text_color)

        # Configure treeview styles
        self.style.configure('Treeview', 
                           font=('Arial', 10), 
                           rowheight=25,
                           background='white',
                           foreground=self.text_color,
                           fieldbackground='white')
        self.style.configure('Treeview.Heading', 
                           font=('Arial', 10, 'bold'),
                           background=self.main_color,
                           foreground=self.text_color,
                           relief='raised')
        self.style.map('Treeview',
                      background=[('selected', self.highlight_color)])

        # Configure scrollbar style
        self.style.configure('Vertical.TScrollbar', 
                           background=self.main_color,
                           troughcolor=self.bg_color)

        # Configure combobox style
        self.style.configure('TCombobox',
                           fieldbackground='white',
                           background=self.bg_color)

        # Configure notebook style (if you add tabs later)
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab', 
                           background=self.secondary_color,
                           foreground=self.text_color,
                           padding=[10, 5])
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.main_color),
                                 ('active', self.highlight_color)])

        # Login frame
        self.create_login_frame()

        # Current user info
        self.current_user = None

    def initialize_database(self):
        try:
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

            # Create tables if they don't exist
            self.cursor.execute("""
                  CREATE TABLE IF NOT EXISTS users (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  username VARCHAR(50) UNIQUE NOT NULL,
                  password VARCHAR(255) NOT NULL,
                  role ENUM('admin', 'registrar', 'faculty', 'student') NOT NULL,
                  full_name VARCHAR(100),
                  email VARCHAR(100),
                  degree_program VARCHAR(100),
                  current_semester INT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  # Add this line
               )
               """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS degrees (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    duration_years INT NOT NULL,
                    total_credits INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS semesters (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    degree_id INT NOT NULL,
                    semester_number INT NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    FOREIGN KEY (degree_id) REFERENCES degrees(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_semester (degree_id, semester_number)
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    credits INT NOT NULL,
                    capacity INT NOT NULL,
                    semester_id INT,
                    faculty_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (faculty_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE SET NULL
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id INT NOT NULL,
                    day ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    room VARCHAR(20),
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    course_id INT NOT NULL,
                    enrollment_date DATE NOT NULL,
                    status ENUM('registered', 'waitlisted', 'dropped') DEFAULT 'registered',
                    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_enrollment (student_id, course_id)
                )
            """)

            self.conn.commit()

            # Create admin if not exists
            self.cursor.execute("SELECT * FROM users WHERE username='admin'")
            if not self.cursor.fetchone():
                hashed_password = self.hash_password("admin123")
                self.cursor.execute(
                    "INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                    ("admin", hashed_password, "admin", "Administrator")
                )
                self.conn.commit()

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error initializing database: {err}")
            self.root.quit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_login_frame(self):
        self.login_frame = tk.Frame(self.root, bg=self.bg_color)
        self.login_frame.pack(pady=100)

        # Logo or title
        tk.Label(self.login_frame, 
                text="Course Enrollment System", 
                font=('Arial', 18, 'bold'), 
                bg=self.bg_color,
                fg=self.accent_color).grid(row=0, column=0, columnspan=2, pady=20)

        # Login widgets
        tk.Label(self.login_frame, 
                text="Username:", 
                font=('Arial', 12), 
                bg=self.bg_color,
                fg=self.text_color).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_entry = ttk.Entry(self.login_frame, font=('Arial', 12))
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.login_frame, 
                text="Password:", 
                font=('Arial', 12), 
                bg=self.bg_color,
                fg=self.text_color).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.password_entry = ttk.Entry(self.login_frame, show="*", font=('Arial', 12))
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)

        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.grid(row=3, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required!")
            return

        hashed_password = self.hash_password(password)

        try:
            self.cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = self.cursor.fetchone()

            if user:
                self.current_user = {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "full_name": user["full_name"],
                    "degree_program": user.get("degree_program"),
                    "current_semester": user.get("current_semester")
                }
                self.show_main_application()
            else:
                messagebox.showerror("Error", "Invalid username or password!")
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def show_main_application(self):
        self.login_frame.pack_forget()

        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create menu bar
        self.create_menu_bar()

        # Show dashboard by default
        self.show_dashboard()

    def create_menu_bar(self):
        self.menu_bar = tk.Menu(self.root, bg=self.secondary_color, fg=self.text_color)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
        file_menu.add_command(label="Dashboard", command=self.show_dashboard)
        file_menu.add_separator()
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Admin menu
        if self.current_user["role"] in ["admin", "registrar"]:
            admin_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
            admin_menu.add_command(label="Manage Users", command=self.manage_users)
            admin_menu.add_command(label="Manage Degrees", command=self.manage_degrees)
            admin_menu.add_command(label="Manage Courses", command=self.manage_courses)
            admin_menu.add_command(label="Manage Schedules", command=self.manage_schedules)
            self.menu_bar.add_cascade(label="Admin", menu=admin_menu)

        # Student menu
        if self.current_user["role"] in ["admin", "registrar", "student"]:
            student_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
            student_menu.add_command(label="Course Catalog", command=self.view_course_catalog)
            student_menu.add_command(label="My Courses", command=self.view_my_courses)
            self.menu_bar.add_cascade(label="Courses", menu=student_menu)

        # Faculty menu
        if self.current_user["role"] in ["admin", "registrar", "faculty"]:
            faculty_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
            faculty_menu.add_command(label="My Teaching", command=self.view_my_teaching)
            self.menu_bar.add_cascade(label="Faculty", menu=faculty_menu)

        # Reports menu
        if self.current_user["role"] in ["admin", "registrar"]:
            reports_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.secondary_color, fg=self.text_color)
            reports_menu.add_command(label="Enrollment Reports", command=self.generate_enrollment_reports)
            reports_menu.add_command(label="Course Capacity", command=self.generate_capacity_reports)
            self.menu_bar.add_cascade(label="Reports", menu=reports_menu)

    def show_dashboard(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Dashboard title
        title_text = f"Dashboard - Welcome {self.current_user['full_name']} ({self.current_user['role'].title()})"
        if self.current_user["role"] == "student" and self.current_user["degree_program"]:
            title_text += f" | {self.current_user['degree_program']} (Semester {self.current_user['current_semester']})"

        tk.Label(self.main_frame, 
                text=title_text, 
                font=('Arial', 14, 'bold'), 
                bg=self.bg_color,
                fg=self.accent_color).pack(pady=10)

        # Dashboard statistics based on role
        if self.current_user["role"] in ["admin", "registrar"]:
            self.show_admin_dashboard()
        elif self.current_user["role"] == "faculty":
            self.show_faculty_dashboard()
        else:  # student
            self.show_student_dashboard()

    def show_admin_dashboard(self):
        stats_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        stats_frame.pack(pady=20)

        try:
            # Get statistics for admin
            self.cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='student'")
            total_students = self.cursor.fetchone()["count"]

            self.cursor.execute("SELECT COUNT(*) as count FROM users WHERE role='faculty'")
            total_faculty = self.cursor.fetchone()["count"]

            self.cursor.execute("SELECT COUNT(*) as count FROM courses")
            total_courses = self.cursor.fetchone()["count"]

            current_month = datetime.now().strftime("%m")
            self.cursor.execute(
                "SELECT COUNT(*) as count FROM enrollments WHERE MONTH(enrollment_date) = %s AND status='registered'",
                (current_month,)
            )
            monthly_enrollments = self.cursor.fetchone()["count"]

            # Display statistics
            stats = [
                ("Total Students", total_students),
                ("Total Faculty", total_faculty),
                ("Total Courses", total_courses),
                ("Monthly Enrollments", monthly_enrollments)
            ]

            for i, (label, value) in enumerate(stats):
                stat_frame = tk.Frame(stats_frame, bg=self.secondary_color, bd=2, relief=tk.RAISED, padx=10, pady=10)
                stat_frame.grid(row=0, column=i, padx=10)

                tk.Label(stat_frame, 
                        text=label, 
                        font=('Arial', 12), 
                        bg=self.secondary_color,
                        fg=self.text_color).pack()
                tk.Label(stat_frame, 
                        text=value, 
                        font=('Arial', 16, 'bold'), 
                        bg=self.secondary_color,
                        fg=self.accent_color).pack()

            # Recent enrollments table
            tk.Label(self.main_frame, 
                    text="Recent Enrollments", 
                    font=('Arial', 12, 'bold'), 
                    bg=self.bg_color,
                    fg=self.accent_color).pack(pady=(20, 5))

            columns = ("Student", "Course", "Date", "Status")
            self.recent_enrollments_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=8)

            for col in columns:
                self.recent_enrollments_tree.heading(col, text=col)
                self.recent_enrollments_tree.column(col, width=150, anchor=tk.CENTER)

            self.recent_enrollments_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(self.recent_enrollments_tree, orient="vertical", command=self.recent_enrollments_tree.yview)
            scrollbar.pack(side="right", fill="y")
            self.recent_enrollments_tree.configure(yscrollcommand=scrollbar.set)

            # Fetch and display recent enrollments
            self.cursor.execute('''
                SELECT u.full_name, c.title, e.enrollment_date, e.status
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                JOIN courses c ON e.course_id = c.id
                ORDER BY e.enrollment_date DESC
                LIMIT 15
            ''')

            for enrollment in self.cursor.fetchall():
                self.recent_enrollments_tree.insert("", "end", values=(
                    enrollment["full_name"], enrollment["title"], 
                    enrollment["enrollment_date"], enrollment["status"].title()
                ))

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def show_faculty_dashboard(self):
        stats_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        stats_frame.pack(pady=20)

        try:
            # Get statistics for faculty
            self.cursor.execute('''
                SELECT COUNT(*) as count, SUM(c.credits) as total_credits
                FROM courses c
                WHERE c.faculty_id = %s
            ''', (self.current_user["id"],))
            teaching_stats = self.cursor.fetchone()

            self.cursor.execute('''
                SELECT COUNT(DISTINCT e.student_id) as students
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                WHERE c.faculty_id = %s AND e.status = 'registered'
            ''', (self.current_user["id"],))
            student_count = self.cursor.fetchone()["students"]

            # Display statistics
            stats = [
                ("Courses Teaching", teaching_stats["count"]),
                ("Total Credit Hours", teaching_stats["total_credits"] or 0),
                ("Students", student_count)
            ]

            for i, (label, value) in enumerate(stats):
                stat_frame = tk.Frame(stats_frame, bg=self.secondary_color, bd=2, relief=tk.RAISED, padx=10, pady=10)
                stat_frame.grid(row=0, column=i, padx=10)

                tk.Label(stat_frame, 
                        text=label, 
                        font=('Arial', 12), 
                        bg=self.secondary_color,
                        fg=self.text_color).pack()
                tk.Label(stat_frame, 
                        text=value, 
                        font=('Arial', 16, 'bold'), 
                        bg=self.secondary_color,
                        fg=self.accent_color).pack()

            # My courses table
            tk.Label(self.main_frame, 
                    text="My Teaching Courses", 
                    font=('Arial', 12, 'bold'), 
                    bg=self.bg_color,
                    fg=self.accent_color).pack(pady=(20, 5))

            columns = ("Code", "Title", "Credits", "Students", "Schedule")
            self.faculty_courses_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=8)

            for col in columns:
                self.faculty_courses_tree.heading(col, text=col)
                self.faculty_courses_tree.column(col, width=120, anchor=tk.CENTER)

            self.faculty_courses_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(self.faculty_courses_tree, orient="vertical", command=self.faculty_courses_tree.yview)
            scrollbar.pack(side="right", fill="y")
            self.faculty_courses_tree.configure(yscrollcommand=scrollbar.set)

            # Fetch and display faculty courses
            self.cursor.execute('''
                SELECT c.code, c.title, c.credits, 
                       COUNT(e.id) as students,
                       GROUP_CONCAT(
                           CONCAT(s.day, ' ', s.start_time, '-', s.end_time, 
                                  CASE WHEN s.room IS NOT NULL THEN CONCAT(' (', s.room, ')') ELSE '' END)
                           SEPARATOR '\n'
                       ) as schedule
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
                LEFT JOIN schedules s ON s.course_id = c.id
                WHERE c.faculty_id = %s
                GROUP BY c.id
                ORDER BY c.code
            ''', (self.current_user["id"],))

            for course in self.cursor.fetchall():
                self.faculty_courses_tree.insert("", "end", values=(
                    course["code"], course["title"], course["credits"],
                    course["students"], course["schedule"] or "Not scheduled"
                ))

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def show_student_dashboard(self):
        stats_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        stats_frame.pack(pady=20)

        try:
            # Get statistics for student
            self.cursor.execute('''
                SELECT COUNT(*) as count, SUM(c.credits) as total_credits
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                WHERE e.student_id = %s AND e.status = 'registered'
            ''', (self.current_user["id"],))
            enrollment_stats = self.cursor.fetchone()

            # Display statistics
            stats = [
                ("Courses Enrolled", enrollment_stats["count"]),
                ("Total Credit Hours", enrollment_stats["total_credits"] or 0)
            ]

            if self.current_user["degree_program"]:
                stats.append(("Degree Program", self.current_user["degree_program"]))
                stats.append(("Current Semester", self.current_user["current_semester"]))

            for i, (label, value) in enumerate(stats):
                stat_frame = tk.Frame(stats_frame, bg=self.secondary_color, bd=2, relief=tk.RAISED, padx=10, pady=10)
                stat_frame.grid(row=0, column=i, padx=10)

                tk.Label(stat_frame, 
                        text=label, 
                        font=('Arial', 12), 
                        bg=self.secondary_color,
                        fg=self.text_color).pack()
                tk.Label(stat_frame, 
                        text=value, 
                        font=('Arial', 16, 'bold'), 
                        bg=self.secondary_color,
                        fg=self.accent_color).pack()

            # My courses table
            tk.Label(self.main_frame, 
                    text="My Enrolled Courses", 
                    font=('Arial', 12, 'bold'), 
                    bg=self.bg_color,
                    fg=self.accent_color).pack(pady=(20, 5))

            columns = ("Code", "Title", "Credits", "Faculty", "Schedule")
            self.student_courses_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=8)

            for col in columns:
                self.student_courses_tree.heading(col, text=col)
                self.student_courses_tree.column(col, width=120, anchor=tk.CENTER)

            self.student_courses_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(self.student_courses_tree, orient="vertical", command=self.student_courses_tree.yview)
            scrollbar.pack(side="right", fill="y")
            self.student_courses_tree.configure(yscrollcommand=scrollbar.set)

            # Fetch and display student courses
            self.cursor.execute('''
                SELECT c.code, c.title, c.credits, u.full_name as faculty,
                       GROUP_CONCAT(
                           CONCAT(s.day, ' ', s.start_time, '-', s.end_time, 
                                  CASE WHEN s.room IS NOT NULL THEN CONCAT(' (', s.room, ')') ELSE '' END)
                           SEPARATOR '\n'
                       ) as schedule
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                LEFT JOIN users u ON c.faculty_id = u.id
                LEFT JOIN schedules s ON s.course_id = c.id
                WHERE e.student_id = %s AND e.status = 'registered'
                GROUP BY c.id
                ORDER BY c.code
            ''', (self.current_user["id"],))

            for course in self.cursor.fetchall():
                self.student_courses_tree.insert("", "end", values=(
                    course["code"], course["title"], course["credits"],
                    course["faculty"] or "Not assigned",
                    course["schedule"] or "Not scheduled"
                ))

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def manage_users(self):
     if self.current_user["role"] not in ["admin", "registrar"]:
        messagebox.showerror("Error", "You don't have permission to manage users!")
        return

     # Clear main frame properly
     for widget in self.main_frame.winfo_children():
        widget.destroy()

     # Add a back button
     back_button = ttk.Button(self.main_frame, text="Back to Dashboard", command=self.show_dashboard)
     back_button.pack(pady=5, anchor="ne")

     # Users management title
     tk.Label(self.main_frame, text="Manage Users", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

     # Add user button
     ttk.Button(self.main_frame, text="Add New User", command=self.add_new_user).pack(pady=5)

     # Users table with improved column widths
     columns = ("ID", "Username", "Full Name", "Role", "Degree Program", "Semester", "Email", "Created At")
     self.users_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

     # Configure columns with appropriate widths
     col_widths = [50, 100, 150, 80, 120, 80, 150, 120]
     for col, width in zip(columns, col_widths):
        self.users_tree.heading(col, text=col)
        self.users_tree.column(col, width=width, anchor=tk.CENTER)

     self.users_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

     # Add scrollbar properly
     scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.users_tree.yview)
     scrollbar.pack(side="right", fill="y")
     self.users_tree.configure(yscrollcommand=scrollbar.set)

     # Context menu for user actions
     self.user_context_menu = tk.Menu(self.root, tearoff=0)
     self.user_context_menu.add_command(label="Edit User", command=self.edit_user)
     self.user_context_menu.add_command(label="Delete User", command=self.delete_user)

     self.users_tree.bind("<Button-3>", self.show_user_context_menu)

     # Double-click to edit
     self.users_tree.bind("<Double-1>", lambda event: self.edit_user())

     # Fetch and display users
     self.refresh_users_list()

    def refresh_users_list(self):
     # Clear existing data
     for item in self.users_tree.get_children():
        self.users_tree.delete(item)

     try:
        # Fetch and display users - REMOVE created_at from the query
        self.cursor.execute("SELECT id, username, full_name, role, degree_program, current_semester, email FROM users")
        for user in self.cursor.fetchall():
            self.users_tree.insert("", "end", values=(
                user["id"], user["username"], user["full_name"], 
                user["role"].title(), 
                user.get("degree_program", ""),
                user.get("current_semester", ""),
                user.get("email", "")
                # Removed created_at from here
            ))
     except pymysql.MySQLError as err:
        messagebox.showerror("Database Error", f"Error loading users: {err}")

    def show_user_context_menu(self, event):
        item = self.users_tree.identify_row(event.y)
        if item:
            self.users_tree.selection_set(item)
            self.user_context_menu.post(event.x_root, event.y_root)

    def add_new_user(self):
     self.add_user_window = tk.Toplevel(self.root)
     self.add_user_window.title("Add New User")
     self.add_user_window.geometry("500x500")

     tk.Label(self.add_user_window, text="Add New User", font=('Arial', 14)).pack(pady=10)

     # Form frame
     form_frame = tk.Frame(self.add_user_window)
     form_frame.pack(pady=10)

      # Form fields
     tk.Label(form_frame, text="Full Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
     self.new_user_fullname = ttk.Entry(form_frame)
     self.new_user_fullname.grid(row=0, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
     self.new_user_username = ttk.Entry(form_frame)
     self.new_user_username.grid(row=1, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
     self.new_user_password = ttk.Entry(form_frame, show="*")
     self.new_user_password.grid(row=2, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Email:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
     self.new_user_email = ttk.Entry(form_frame)
     self.new_user_email.grid(row=3, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Role:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
     self.new_user_role = ttk.Combobox(form_frame, values=["admin", "registrar", "faculty", "student"])
     self.new_user_role.grid(row=4, column=1, padx=5, pady=5)

     # Degree program and semester (initially hidden)
     self.degree_label = tk.Label(form_frame, text="")
     self.degree_label.grid(row=5, column=0, padx=5, pady=5, sticky="e")
     self.new_user_degree = ttk.Combobox(form_frame)
     self.new_user_degree.grid(row=5, column=1, padx=5, pady=5)
     self.new_user_degree.grid_remove()

     self.semester_label = tk.Label(form_frame, text="")
     self.semester_label.grid(row=6, column=0, padx=5, pady=5, sticky="e")
     self.new_user_semester = ttk.Spinbox(form_frame, from_=1, to=8)
     self.new_user_semester.grid(row=6, column=1, padx=5, pady=5)
     self.new_user_semester.grid_remove()

     # Bind role change event
     self.new_user_role.bind("<<ComboboxSelected>>", self.update_new_user_form_fields)

     ttk.Button(self.add_user_window, text="Save", command=self.save_new_user).pack(pady=15)

    def update_new_user_form_fields(self, event=None):
     role = self.new_user_role.get().lower()

     if role == "student":
        # Show degree and semester fields
        self.degree_label.config(text="Degree Program:")
        self.new_user_degree.grid()

        # Populate degree programs
        try:
            self.cursor.execute("SELECT name FROM degrees")
            degrees = [d["name"] for d in self.cursor.fetchall()]
            self.new_user_degree['values'] = degrees
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading degrees: {err}")

        self.semester_label.config(text="Semester:")
        self.new_user_semester.grid()
     else:
        # Hide degree and semester fields
        self.degree_label.config(text="")
        self.new_user_degree.grid_remove()
        self.new_user_degree.set('')

        self.semester_label.config(text="")
        self.new_user_semester.grid_remove()
        self.new_user_semester.set('')

    def save_new_user(self):
        fullname = self.new_user_fullname.get().strip()
        username = self.new_user_username.get().strip()
        password = self.new_user_password.get()
        email = self.new_user_email.get().strip()
        role = self.new_user_role.get()
        degree = self.new_user_degree.get().strip() if self.new_user_degree.get() else None
        semester = self.new_user_semester.get() if self.new_user_semester.get() else None

        if not all([fullname, username, password, role]):
            messagebox.showerror("Error", "Full Name, Username, Password and Role are required!")
            return

        if role == "student" and not degree:
            messagebox.showerror("Error", "Degree program is required for students!")
            return

        hashed_password = self.hash_password(password)

        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, role, full_name, email, degree_program, current_semester) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (username, hashed_password, role, fullname, email, degree, semester)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "User added successfully!")
            self.add_user_window.destroy()
            self.refresh_users_list()
        except pymysql.MySQLError as err:
            if err.errno == 1062:  # Duplicate entry
                messagebox.showerror("Error", "Username already exists!")
            else:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_user(self):
     selected_item = self.users_tree.selection()
     if not selected_item:
        messagebox.showerror("Error", "Please select a user to edit!")
        return

     user_data = self.users_tree.item(selected_item)['values']

     self.edit_user_window = tk.Toplevel(self.root)
     self.edit_user_window.title("Edit User")
     self.edit_user_window.geometry("500x500")

     tk.Label(self.edit_user_window, text="Edit User", font=('Arial', 14)).pack(pady=10)

     # Form frame
     form_frame = tk.Frame(self.edit_user_window)
     form_frame.pack(pady=10)

     # Form fields
     tk.Label(form_frame, text="Full Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
     self.edit_user_fullname = ttk.Entry(form_frame)
     self.edit_user_fullname.insert(0, user_data[2])
     self.edit_user_fullname.grid(row=0, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
     self.edit_user_username = ttk.Entry(form_frame)
     self.edit_user_username.insert(0, user_data[1])
     self.edit_user_username.grid(row=1, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="New Password (leave blank to keep current):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
     self.edit_user_password = ttk.Entry(form_frame, show="*")
     self.edit_user_password.grid(row=2, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Email:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
     self.edit_user_email = ttk.Entry(form_frame)
     self.edit_user_email.insert(0, user_data[6])
     self.edit_user_email.grid(row=3, column=1, padx=5, pady=5)

     tk.Label(form_frame, text="Role:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
     self.edit_user_role = ttk.Combobox(form_frame, values=["admin", "registrar", "faculty", "student"])
     self.edit_user_role.set(user_data[3])
     self.edit_user_role.grid(row=4, column=1, padx=5, pady=5)

     # Store the original role to detect changes
     self.original_role = user_data[3].lower()

     # Degree program (only for students)
     if self.original_role == "student":
        tk.Label(form_frame, text="Degree Program:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.edit_user_degree = ttk.Combobox(form_frame)
        self.edit_user_degree.grid(row=5, column=1, padx=5, pady=5)

        # Populate degree programs
        try:
            self.cursor.execute("SELECT name FROM degrees")
            degrees = [d["name"] for d in self.cursor.fetchall()]
            self.edit_user_degree['values'] = degrees
            if user_data[4]:
                self.edit_user_degree.set(user_data[4])
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading degrees: {err}")

        tk.Label(form_frame, text="Semester:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.edit_user_semester = ttk.Spinbox(form_frame, from_=1, to=8)
        self.edit_user_semester.grid(row=6, column=1, padx=5, pady=5)
        if user_data[5]:
            self.edit_user_semester.set(user_data[5])

     self.editing_user_id = user_data[0]

     # Bind role change event to update form fields
     self.edit_user_role.bind("<<ComboboxSelected>>", self.update_user_form_fields)

     ttk.Button(self.edit_user_window, text="Update", command=self.update_user).pack(pady=15)

    def update_user_form_fields(self, event=None):
     # Show/hide degree and semester fields based on selected role
     selected_role = self.edit_user_role.get().lower()

     # If changing from student to non-student, clear degree and semester
     if self.original_role == "student" and selected_role != "student":
        if hasattr(self, 'edit_user_degree'):
            self.edit_user_degree.set('')
        if hasattr(self, 'edit_user_semester'):
            self.edit_user_semester.set('')

     # If changing to student, show degree and semester fields
     if selected_role == "student":
        if not hasattr(self, 'edit_user_degree'):
            # Add degree field
            tk.Label(self.edit_user_window, text="Degree Program:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
            self.edit_user_degree = ttk.Combobox(self.edit_user_window)
            self.edit_user_degree.grid(row=5, column=1, padx=5, pady=5)

            # Populate degree programs
            try:
                self.cursor.execute("SELECT name FROM degrees")
                degrees = [d["name"] for d in self.cursor.fetchall()]
                self.edit_user_degree['values'] = degrees
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error loading degrees: {err}")

        if not hasattr(self, 'edit_user_semester'):
            # Add semester field
            tk.Label(self.edit_user_window, text="Semester:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
            self.edit_user_semester = ttk.Spinbox(self.edit_user_window, from_=1, to=8)
            self.edit_user_semester.grid(row=6, column=1, padx=5, pady=5)
     else:
        # Remove degree and semester fields if they exist
        if hasattr(self, 'edit_user_degree'):
            self.edit_user_degree.grid_forget()
            tk.Label(self.edit_user_window, text="").grid(row=5, column=0)  # Clear label
        if hasattr(self, 'edit_user_semester'):
            self.edit_user_semester.grid_forget()
            tk.Label(self.edit_user_window, text="").grid(row=6, column=0)  # Clear label

    def update_user(self):
     fullname = self.edit_user_fullname.get().strip()
     username = self.edit_user_username.get().strip()
     password = self.edit_user_password.get()
     email = self.edit_user_email.get().strip()
     role = self.edit_user_role.get().lower()

     # Handle degree and semester only for students
     if role == "student":
        degree = self.edit_user_degree.get().strip() if hasattr(self, 'edit_user_degree') and self.edit_user_degree.get() else None
        try:
            semester = int(self.edit_user_semester.get()) if hasattr(self, 'edit_user_semester') and self.edit_user_semester.get() else None
        except ValueError:
            messagebox.showerror("Error", "Semester must be a number!")
            return
     else:
        degree = None
        semester = None

     if not all([fullname, username, role]):
        messagebox.showerror("Error", "Full Name, Username and Role are required!")
        return

     if role == "student" and not degree:
        messagebox.showerror("Error", "Degree program is required for students!")
        return

     try:
        if password:
            hashed_password = self.hash_password(password)
            self.cursor.execute(
                "UPDATE users SET username=%s, password=%s, role=%s, full_name=%s, email=%s, degree_program=%s, current_semester=%s WHERE id=%s",
                (username, hashed_password, role, fullname, email, degree, semester, self.editing_user_id)
            )
        else:
            self.cursor.execute(
                "UPDATE users SET username=%s, role=%s, full_name=%s, email=%s, degree_program=%s, current_semester=%s WHERE id=%s",
                (username, role, fullname, email, degree, semester, self.editing_user_id)
            )

        self.conn.commit()
        messagebox.showinfo("Success", "User updated successfully!")
        self.edit_user_window.destroy()
        self.refresh_users_list()

        # Update current user info if editing self
        if self.current_user["id"] == self.editing_user_id:
            self.current_user["full_name"] = fullname
            self.current_user["role"] = role
            if role == "student":
                self.current_user["degree_program"] = degree
                self.current_user["current_semester"] = semester
            else:
                self.current_user["degree_program"] = None
                self.current_user["current_semester"] = None

     except pymysql.MySQLError as err:
        if isinstance(err, pymysql.err.IntegrityError) and err.args[0] == 1062:  # Duplicate entry
            messagebox.showerror("Error", "Username already exists!")
        else:
            messagebox.showerror("Database Error", f"Error: {err}")

    def delete_user(self):
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a user to delete!")
            return

        user_data = self.users_tree.item(selected_item)['values']

        if user_data[0] == self.current_user["id"]:
            messagebox.showerror("Error", "You cannot delete your own account!")
            return

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete user {user_data[1]}?"):
            try:
                self.cursor.execute("DELETE FROM users WHERE id=%s", (user_data[0],))
                self.conn.commit()
                messagebox.showinfo("Success", "User deleted successfully!")
                self.refresh_users_list()
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def manage_degrees(self):
        if self.current_user["role"] not in ["admin", "registrar"]:
            messagebox.showerror("Error", "You don't have permission to manage degrees!")
            return

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Degrees management title
        tk.Label(self.main_frame, text="Manage Degrees", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Add degree button
        ttk.Button(self.main_frame, text="Add New Degree", command=self.add_new_degree).pack(pady=5)

        # Degrees table
        columns = ("ID", "Name", "Duration (Years)", "Total Credits")
        self.degrees_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.degrees_tree.heading(col, text=col)
            self.degrees_tree.column(col, width=120, anchor=tk.CENTER)

        self.degrees_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.degrees_tree, orient="vertical", command=self.degrees_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.degrees_tree.configure(yscrollcommand=scrollbar.set)

        # Context menu for degree actions
        self.degree_context_menu = tk.Menu(self.root, tearoff=0)
        self.degree_context_menu.add_command(label="Edit Degree", command=self.edit_degree)
        self.degree_context_menu.add_command(label="Delete Degree", command=self.delete_degree)
        self.degree_context_menu.add_command(label="Manage Semesters", command=self.manage_semesters)

        self.degrees_tree.bind("<Button-3>", self.show_degree_context_menu)

        # Fetch and display degrees
        self.refresh_degrees_list()

    def refresh_degrees_list(self):
        # Clear existing data
        for item in self.degrees_tree.get_children():
            self.degrees_tree.delete(item)

        try:
            # Fetch and display degrees
            self.cursor.execute("SELECT id, name, duration_years, total_credits FROM degrees")
            for degree in self.cursor.fetchall():
                self.degrees_tree.insert("", "end", values=(
                    degree["id"], degree["name"], degree["duration_years"], degree["total_credits"]
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading degrees: {err}")

    def show_degree_context_menu(self, event):
        item = self.degrees_tree.identify_row(event.y)
        if item:
            self.degrees_tree.selection_set(item)
            self.degree_context_menu.post(event.x_root, event.y_root)

    def add_new_degree(self):
        self.add_degree_window = tk.Toplevel(self.root)
        self.add_degree_window.title("Add New Degree")
        self.add_degree_window.geometry("400x300")

        tk.Label(self.add_degree_window, text="Add New Degree", font=('Arial', 14)).pack(pady=10)

        # Form frame
        form_frame = tk.Frame(self.add_degree_window)
        form_frame.pack(pady=10)

        # Form fields
        tk.Label(form_frame, text="Degree Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.new_degree_name = ttk.Entry(form_frame)
        self.new_degree_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Duration (Years):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.new_degree_duration = ttk.Spinbox(form_frame, from_=1, to=6)
        self.new_degree_duration.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Total Credits:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.new_degree_credits = ttk.Spinbox(form_frame, from_=1, to=200)
        self.new_degree_credits.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(self.add_degree_window, text="Save", command=self.save_new_degree).pack(pady=15)

    def save_new_degree(self):
        name = self.new_degree_name.get().strip()
        duration = self.new_degree_duration.get()
        credits = self.new_degree_credits.get()

        if not all([name, duration, credits]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            duration = int(duration)
            credits = int(credits)
        except ValueError:
            messagebox.showerror("Error", "Duration and credits must be numbers!")
            return

        try:
            self.cursor.execute(
                "INSERT INTO degrees (name, duration_years, total_credits) VALUES (%s, %s, %s)",
                (name, duration, credits)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Degree added successfully!")
            self.add_degree_window.destroy()
            self.refresh_degrees_list()
        except pymysql.MySQLError as err:
            if err.errno == 1062:  # Duplicate entry
                messagebox.showerror("Error", "Degree name already exists!")
            else:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_degree(self):
        selected_item = self.degrees_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a degree to edit!")
            return

        degree_data = self.degrees_tree.item(selected_item)['values']

        self.edit_degree_window = tk.Toplevel(self.root)
        self.edit_degree_window.title("Edit Degree")
        self.edit_degree_window.geometry("400x300")

        tk.Label(self.edit_degree_window, text="Edit Degree", font=('Arial', 14)).pack(pady=10)

        # Form frame
        form_frame = tk.Frame(self.edit_degree_window)
        form_frame.pack(pady=10)

        # Form fields
        tk.Label(form_frame, text="Degree Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.edit_degree_name = ttk.Entry(form_frame)
        self.edit_degree_name.insert(0, degree_data[1])
        self.edit_degree_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Duration (Years):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.edit_degree_duration = ttk.Spinbox(form_frame, from_=1, to=6)
        self.edit_degree_duration.set(degree_data[2])
        self.edit_degree_duration.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Total Credits:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.edit_degree_credits = ttk.Spinbox(form_frame, from_=1, to=200)
        self.edit_degree_credits.set(degree_data[3])
        self.edit_degree_credits.grid(row=2, column=1, padx=5, pady=5)

        self.editing_degree_id = degree_data[0]

        ttk.Button(self.edit_degree_window, text="Update", command=self.update_degree).pack(pady=15)

    def update_degree(self):
        name = self.edit_degree_name.get().strip()
        duration = self.edit_degree_duration.get()
        credits = self.edit_degree_credits.get()

        if not all([name, duration, credits]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            duration = int(duration)
            credits = int(credits)
        except ValueError:
            messagebox.showerror("Error", "Duration and credits must be numbers!")
            return

        try:
            self.cursor.execute(
                "UPDATE degrees SET name=%s, duration_years=%s, total_credits=%s WHERE id=%s",
                (name, duration, credits, self.editing_degree_id)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Degree updated successfully!")
            self.edit_degree_window.destroy()
            self.refresh_degrees_list()
        except pymysql.MySQLError as err:
            if err.errno == 1062:  # Duplicate entry
                messagebox.showerror("Error", "Degree name already exists!")
            else:
                messagebox.showerror("Database Error", f"Error: {err}")

    def delete_degree(self):
        selected_item = self.degrees_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a degree to delete!")
            return

        degree_data = self.degrees_tree.item(selected_item)['values']

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete degree {degree_data[1]}?"):
            try:
                self.cursor.execute("DELETE FROM degrees WHERE id=%s", (degree_data[0],))
                self.conn.commit()
                messagebox.showinfo("Success", "Degree deleted successfully!")
                self.refresh_degrees_list()
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def manage_semesters(self):
        selected_item = self.degrees_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a degree to manage semesters!")
            return

        degree_data = self.degrees_tree.item(selected_item)['values']
        self.current_degree = {"id": degree_data[0], "name": degree_data[1]}

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Semesters management title
        tk.Label(self.main_frame, text=f"Manage Semesters for {degree_data[1]}", 
                font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Add semester button
        ttk.Button(self.main_frame, text="Add New Semester", command=self.add_new_semester).pack(pady=5)

        # Semesters table
        columns = ("Semester Number", "Name", "Courses Count")
        self.semesters_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.semesters_tree.heading(col, text=col)
            self.semesters_tree.column(col, width=120, anchor=tk.CENTER)

        self.semesters_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.semesters_tree, orient="vertical", command=self.semesters_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.semesters_tree.configure(yscrollcommand=scrollbar.set)

        # Context menu for semester actions
        self.semester_context_menu = tk.Menu(self.root, tearoff=0)
        self.semester_context_menu.add_command(label="Edit Semester", command=self.edit_semester)
        self.semester_context_menu.add_command(label="Delete Semester", command=self.delete_semester)
        self.semester_context_menu.add_command(label="View Courses", command=self.view_semester_courses)

        self.semesters_tree.bind("<Button-3>", self.show_semester_context_menu)

        # Fetch and display semesters
        self.refresh_semesters_list()

    def refresh_semesters_list(self):
        # Clear existing data
        for item in self.semesters_tree.get_children():
            self.semesters_tree.delete(item)

        try:
            # Fetch and display semesters with course counts
            self.cursor.execute('''
                SELECT s.id, s.semester_number, s.name, COUNT(c.id) as courses_count
                FROM semesters s
                LEFT JOIN courses c ON c.semester_id = s.id
                WHERE s.degree_id = %s
                GROUP BY s.id
                ORDER BY s.semester_number
            ''', (self.current_degree["id"],))

            for semester in self.cursor.fetchall():
                self.semesters_tree.insert("", "end", values=(
                    semester["semester_number"], semester["name"], semester["courses_count"]
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading semesters: {err}")

    def show_semester_context_menu(self, event):
        item = self.semesters_tree.identify_row(event.y)
        if item:
            self.semesters_tree.selection_set(item)
            self.semester_context_menu.post(event.x_root, event.y_root)

    def add_new_semester(self):
        self.add_semester_window = tk.Toplevel(self.root)
        self.add_semester_window.title("Add New Semester")
        self.add_semester_window.geometry("400x250")

        tk.Label(self.add_semester_window, text="Add New Semester", font=('Arial', 14)).pack(pady=10)

        # Form frame
        form_frame = tk.Frame(self.add_semester_window)
        form_frame.pack(pady=10)

        # Form fields
        tk.Label(form_frame, text="Semester Number:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.new_semester_number = ttk.Spinbox(form_frame, from_=1, to=8)
        self.new_semester_number.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Semester Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.new_semester_name = ttk.Entry(form_frame)
        self.new_semester_name.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.add_semester_window, text="Save", command=self.save_new_semester).pack(pady=15)

    def save_new_semester(self):
        number = self.new_semester_number.get()
        name = self.new_semester_name.get().strip()

        if not all([number, name]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            number = int(number)
        except ValueError:
            messagebox.showerror("Error", "Semester number must be a number!")
            return

        try:
            self.cursor.execute(
                "INSERT INTO semesters (degree_id, semester_number, name) VALUES (%s, %s, %s)",
                (self.current_degree["id"], number, name)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Semester added successfully!")
            self.add_semester_window.destroy()
            self.refresh_semesters_list()
        except pymysql.MySQLError as err:
            if err.errno == 1062:  # Duplicate entry
                messagebox.showerror("Error", "Semester number already exists for this degree!")
            else:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_semester(self):
        selected_item = self.semesters_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a semester to edit!")
            return

        semester_data = self.semesters_tree.item(selected_item)['values']

        self.edit_semester_window = tk.Toplevel(self.root)
        self.edit_semester_window.title("Edit Semester")
        self.edit_semester_window.geometry("400x250")

        tk.Label(self.edit_semester_window, text="Edit Semester", font=('Arial', 14)).pack(pady=10)

        # Form frame
        form_frame = tk.Frame(self.edit_semester_window)
        form_frame.pack(pady=10)

        # Form fields
        tk.Label(form_frame, text="Semester Number:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.edit_semester_number = ttk.Spinbox(form_frame, from_=1, to=8)
        self.edit_semester_number.set(semester_data[0])
        self.edit_semester_number.grid(row=0, column=1, padx=5, pady=5)
        self.edit_semester_number.config(state='readonly')

        tk.Label(form_frame, text="Semester Name:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.edit_semester_name = ttk.Entry(form_frame)
        self.edit_semester_name.insert(0, semester_data[1])
        self.edit_semester_name.grid(row=1, column=1, padx=5, pady=5)

        # Get semester ID
        self.cursor.execute(
            "SELECT id FROM semesters WHERE degree_id=%s AND semester_number=%s",
            (self.current_degree["id"], semester_data[0])
        )
        semester = self.cursor.fetchone()

        if not semester:
            messagebox.showerror("Error", "Semester not found!")
            return

        self.editing_semester_id = semester["id"]

        ttk.Button(self.edit_semester_window, text="Update", command=self.update_semester).pack(pady=15)

    def update_semester(self):
        name = self.edit_semester_name.get().strip()

        if not name:
            messagebox.showerror("Error", "Semester name is required!")
            return

        try:
            self.cursor.execute(
                "UPDATE semesters SET name=%s WHERE id=%s",
                (name, self.editing_semester_id)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Semester updated successfully!")
            self.edit_semester_window.destroy()
            self.refresh_semesters_list()
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def delete_semester(self):
        selected_item = self.semesters_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a semester to delete!")
            return

        semester_data = self.semesters_tree.item(selected_item)['values']

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete semester {semester_data[1]}?"):
            try:
                self.cursor.execute(
                    "DELETE FROM semesters WHERE degree_id=%s AND semester_number=%s",
                    (self.current_degree["id"], semester_data[0])
                )
                self.conn.commit()
                messagebox.showinfo("Success", "Semester deleted successfully!")
                self.refresh_semesters_list()
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def view_semester_courses(self):
        selected_item = self.semesters_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a semester to view courses!")
            return

        semester_data = self.semesters_tree.item(selected_item)['values']

        # Get semester ID
        self.cursor.execute(
            "SELECT id FROM semesters WHERE degree_id=%s AND semester_number=%s",
            (self.current_degree["id"], semester_data[0])
        )
        semester = self.cursor.fetchone()

        if not semester:
            messagebox.showerror("Error", "Semester not found!")
            return

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Courses management title
        tk.Label(self.main_frame, 
                text=f"Courses for {self.current_degree['name']} - Semester {semester_data[0]}", 
                font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Add course button
        ttk.Button(self.main_frame, text="Add New Course", command=lambda: self.add_new_course(semester["id"])).pack(pady=5)

        # Courses table
        columns = ("Code", "Title", "Credits", "Capacity", "Faculty")
        self.semester_courses_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.semester_courses_tree.heading(col, text=col)
            self.semester_courses_tree.column(col, width=120, anchor=tk.CENTER)

        self.semester_courses_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.semester_courses_tree, orient="vertical", command=self.semester_courses_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.semester_courses_tree.configure(yscrollcommand=scrollbar.set)

        # Context menu for course actions
        self.semester_course_context_menu = tk.Menu(self.root, tearoff=0)
        self.semester_course_context_menu.add_command(label="Edit Course", command=self.edit_semester_course)
        self.semester_course_context_menu.add_command(label="Delete Course", command=self.delete_semester_course)
        self.semester_course_context_menu.add_command(label="View Details", command=self.view_semester_course_details)

        self.semester_courses_tree.bind("<Button-3>", self.show_semester_course_context_menu)

        # Fetch and display courses
        self.refresh_semester_courses_list(semester["id"])

    def refresh_semester_courses_list(self, semester_id):
        # Clear existing data
        for item in self.semester_courses_tree.get_children():
            self.semester_courses_tree.delete(item)

        try:
            # Fetch and display courses
            self.cursor.execute('''
                SELECT c.code, c.title, c.credits, c.capacity, u.full_name as faculty
                FROM courses c
                LEFT JOIN users u ON c.faculty_id = u.id
                WHERE c.semester_id = %s
                ORDER BY c.code
            ''', (semester_id,))
            for course in self.cursor.fetchall():
                self.semester_courses_tree.insert("", "end", values=(
                    course["code"], course["title"], course["credits"],
                    course["capacity"], course["faculty"] or "Not assigned"
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading courses: {err}")

    def show_semester_course_context_menu(self, event):
        item = self.semester_courses_tree.identify_row(event.y)
        if item:
            self.semester_courses_tree.selection_set(item)
            self.semester_course_context_menu.post(event.x_root, event.y_root)

    def add_new_course(self, semester_id=None):
        self.add_course_window = tk.Toplevel(self.root)
        self.add_course_window.title("Add New Course")
        self.add_course_window.geometry("500x500")

        tk.Label(self.add_course_window, text="Add New Course", font=('Arial', 14)).pack(pady=10)

        # Form frame
        form_frame = tk.Frame(self.add_course_window)
        form_frame.pack(pady=10)

        # Form fields
        tk.Label(form_frame, text="Course Code:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.new_course_code = ttk.Entry(form_frame)
        self.new_course_code.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Course Title:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.new_course_title = ttk.Entry(form_frame)
        self.new_course_title.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.new_course_description = tk.Text(form_frame, width=30, height=4)
        self.new_course_description.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Credits:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.new_course_credits = ttk.Entry(form_frame)
        self.new_course_credits.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Capacity:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.new_course_capacity = ttk.Entry(form_frame)
        self.new_course_capacity.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Faculty:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.new_course_faculty = ttk.Combobox(form_frame)
        self.new_course_faculty.grid(row=5, column=1, padx=5, pady=5)

        # Populate faculty combobox
        try:
            self.cursor.execute("SELECT id, full_name FROM users WHERE role='faculty'")
            faculty = self.cursor.fetchall()
            faculty_dict = {f["full_name"]: f["id"] for f in faculty}
            self.new_course_faculty['values'] = list(faculty_dict.keys())
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading faculty: {err}")

        # Semester selection (only if not adding to a specific semester)
        if not semester_id:
            tk.Label(form_frame, text="Semester:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
            self.new_course_semester = ttk.Combobox(form_frame)
            self.new_course_semester.grid(row=6, column=1, padx=5, pady=5)

            # Populate semesters
            try:
                self.cursor.execute('''
                    SELECT s.id, d.name as degree_name, s.semester_number
                    FROM semesters s
                    JOIN degrees d ON s.degree_id = d.id
                    ORDER BY d.name, s.semester_number
                ''')
                semesters = self.cursor.fetchall()
                semester_dict = {f"{s['degree_name']} - Semester {s['semester_number']}": s["id"] for s in semesters}
                self.new_course_semester['values'] = list(semester_dict.keys())
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error loading semesters: {err}")
        else:
            self.new_course_semester_id = semester_id

        ttk.Button(self.add_course_window, text="Save", command=lambda: self.save_new_course(semester_id)).pack(pady=15)

    def save_new_course(self, semester_id=None):
        code = self.new_course_code.get().strip()
        title = self.new_course_title.get().strip()
        description = self.new_course_description.get("1.0", tk.END).strip()
        credits = self.new_course_credits.get().strip()
        capacity = self.new_course_capacity.get().strip()
        faculty_name = self.new_course_faculty.get().strip()

        if not all([code, title, credits, capacity]):
            messagebox.showerror("Error", "Code, Title, Credits and Capacity are required!")
            return

        try:
            credits = int(credits)
            capacity = int(capacity)
        except ValueError:
            messagebox.showerror("Error", "Credits and Capacity must be numbers!")
            return

        # Get semester ID if not provided
        if not semester_id:
            semester_name = self.new_course_semester.get().strip()
            if not semester_name:
                messagebox.showerror("Error", "Semester is required!")
                return

            # Find semester ID from the selected name
            try:
                degree_name, sem_num = semester_name.split(" - Semester ")
                self.cursor.execute('''
                    SELECT s.id
                    FROM semesters s
                    JOIN degrees d ON s.degree_id = d.id
                    WHERE d.name = %s AND s.semester_number = %s
                ''', (degree_name, sem_num))
                semester = self.cursor.fetchone()
                if not semester:
                    messagebox.showerror("Error", "Selected semester not found!")
                    return
                semester_id = semester["id"]
            except Exception as e:
                messagebox.showerror("Error", "Invalid semester selection!")
                return

        # Get faculty ID
        faculty_id = None
        if faculty_name:
            self.cursor.execute("SELECT id FROM users WHERE full_name=%s AND role='faculty'", (faculty_name,))
            faculty = self.cursor.fetchone()
            if faculty:
                faculty_id = faculty["id"]
            else:
                messagebox.showerror("Error", "Selected faculty not found!")
                return

        try:
            self.cursor.execute(
                "INSERT INTO courses (code, title, description, credits, capacity, semester_id, faculty_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (code, title, description, credits, capacity, semester_id, faculty_id)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Course added successfully!")
            self.add_course_window.destroy()

            # Refresh the appropriate list
            if hasattr(self, 'semester_courses_tree'):
                self.refresh_semester_courses_list(semester_id)
            else:
                self.refresh_courses_list()
        except pymysql.MySQLError as err:
            if err.errno == 1062:  # Duplicate entry
                messagebox.showerror("Error", "Course code already exists!")
            else:
                messagebox.showerror("Database Error", f"Error: {err}")

    def edit_semester_course(self):
        selected_item = self.semester_courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to edit!")
            return

        course_data = self.semester_courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        # Get full course details
        try:
            self.cursor.execute('''
                SELECT c.*, u.full_name as faculty_name
                FROM courses c
                LEFT JOIN users u ON c.faculty_id = u.id
                WHERE c.code = %s
            ''', (course_code,))
            course = self.cursor.fetchone()

            self.edit_course_window = tk.Toplevel(self.root)
            self.edit_course_window.title("Edit Course")
            self.edit_course_window.geometry("500x500")

            tk.Label(self.edit_course_window, text="Edit Course", font=('Arial', 14)).pack(pady=10)

            # Form frame
            form_frame = tk.Frame(self.edit_course_window)
            form_frame.pack(pady=10)

            # Form fields
            tk.Label(form_frame, text="Course Code:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_code = ttk.Entry(form_frame)
            self.edit_course_code.insert(0, course["code"])
            self.edit_course_code.grid(row=0, column=1, padx=5, pady=5)
            self.edit_course_code.config(state='readonly')

            tk.Label(form_frame, text="Course Title:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_title = ttk.Entry(form_frame)
            self.edit_course_title.insert(0, course["title"])
            self.edit_course_title.grid(row=1, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_description = tk.Text(form_frame, width=30, height=4)
            self.edit_course_description.insert("1.0", course["description"] or "")
            self.edit_course_description.grid(row=2, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Credits:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_credits = ttk.Entry(form_frame)
            self.edit_course_credits.insert(0, course["credits"])
            self.edit_course_credits.grid(row=3, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Capacity:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_capacity = ttk.Entry(form_frame)
            self.edit_course_capacity.insert(0, course["capacity"])
            self.edit_course_capacity.grid(row=4, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Faculty:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_faculty = ttk.Combobox(form_frame)
            self.edit_course_faculty.grid(row=5, column=1, padx=5, pady=5)

            # Populate faculty combobox
            self.cursor.execute("SELECT id, full_name FROM users WHERE role='faculty'")
            faculty = self.cursor.fetchall()
            faculty_dict = {f["full_name"]: f["id"] for f in faculty}
            self.edit_course_faculty['values'] = list(faculty_dict.keys())
            if course["faculty_name"]:
                self.edit_course_faculty.set(course["faculty_name"])

            self.editing_course_id = course["id"]
            self.faculty_dict = faculty_dict

            ttk.Button(self.edit_course_window, text="Update", command=self.update_semester_course).pack(pady=15)

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def update_semester_course(self):
        title = self.edit_course_title.get().strip()
        description = self.edit_course_description.get("1.0", tk.END).strip()
        credits = self.edit_course_credits.get().strip()
        capacity = self.edit_course_capacity.get().strip()
        faculty_name = self.edit_course_faculty.get().strip()

        if not all([title, credits, capacity]):
            messagebox.showerror("Error", "Title, Credits and Capacity are required!")
            return

        try:
            credits = int(credits)
            capacity = int(capacity)
        except ValueError:
            messagebox.showerror("Error", "Credits and Capacity must be numbers!")
            return

        # Get faculty ID
        faculty_id = None
        if faculty_name:
            faculty_id = self.faculty_dict.get(faculty_name)
            if not faculty_id:
                messagebox.showerror("Error", "Selected faculty not found!")
                return

        try:
            self.cursor.execute(
                "UPDATE courses SET title=%s, description=%s, credits=%s, capacity=%s, faculty_id=%s WHERE id=%s",
                (title, description, credits, capacity, faculty_id, self.editing_course_id)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Course updated successfully!")
            self.edit_course_window.destroy()

            # Refresh the appropriate list
            if hasattr(self, 'semester_courses_tree'):
                # Get semester ID to refresh the semester courses list
                self.cursor.execute("SELECT semester_id FROM courses WHERE id=%s", (self.editing_course_id,))
                semester_id = self.cursor.fetchone()["semester_id"]
                self.refresh_semester_courses_list(semester_id)
            else:
                self.refresh_courses_list()
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def delete_semester_course(self):
        selected_item = self.semester_courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to delete!")
            return

        course_data = self.semester_courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete course {course_code}?"):
            try:
                self.cursor.execute("DELETE FROM courses WHERE code=%s", (course_code,))
                self.conn.commit()
                messagebox.showinfo("Success", "Course deleted successfully!")

                # Refresh the semester courses list
                if hasattr(self, 'semester_courses_tree'):
                    # Get semester ID from the course being deleted
                    self.cursor.execute("SELECT semester_id FROM courses WHERE code=%s", (course_code,))
                    semester_id = self.cursor.fetchone()["semester_id"]
                    self.refresh_semester_courses_list(semester_id)
                else:
                    self.refresh_courses_list()
            except pymysql.MySQLError as err:
                if err.errno == 1451:  # Foreign key constraint
                    messagebox.showerror("Error", "Cannot delete course with existing enrollments or schedules!")
                else:
                    messagebox.showerror("Database Error", f"Error: {err}")

    def view_semester_course_details(self):
        selected_item = self.semester_courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to view details!")
            return

        course_data = self.semester_courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course details
            self.cursor.execute('''
                SELECT c.*, u.full_name as faculty_name
                FROM courses c
                LEFT JOIN users u ON c.faculty_id = u.id
                WHERE c.code = %s
            ''', (course_code,))
            course = self.cursor.fetchone()

            # Get course schedules
            self.cursor.execute('''
                SELECT day, start_time, end_time, room
                FROM schedules
                WHERE course_id = %s
                ORDER BY 
                    CASE day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    start_time
            ''', (course["id"],))
            schedules = self.cursor.fetchall()

            # Get enrolled students
            self.cursor.execute('''
                SELECT u.full_name, e.enrollment_date, e.status
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.course_id = %s
                ORDER BY e.enrollment_date
            ''', (course["id"],))
            enrollments = self.cursor.fetchall()

            # Create details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Course Details - {course_code}")
            details_window.geometry("800x600")

            # Course info frame
            info_frame = tk.Frame(details_window)
            info_frame.pack(pady=10, fill=tk.X)

            tk.Label(info_frame, text=f"Course: {course['code']} - {course['title']}", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky="w")
            tk.Label(info_frame, text=f"Credits: {course['credits']}", font=('Arial', 12)).grid(row=1, column=0, sticky="w")
            tk.Label(info_frame, text=f"Capacity: {course['capacity']}", font=('Arial', 12)).grid(row=2, column=0, sticky="w")
            tk.Label(info_frame, text=f"Faculty: {course['faculty_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=3, column=0, sticky="w")

            # Description
            desc_frame = tk.Frame(details_window)
            desc_frame.pack(pady=10, fill=tk.X)

            tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor="w")
            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD)
            desc_text.insert("1.0", course["description"] or "No description available")
            desc_text.config(state="disabled")
            desc_text.pack(fill=tk.X)

            # Schedules
            tk.Label(details_window, text="Schedule:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if schedules:
                schedule_frame = tk.Frame(details_window)
                schedule_frame.pack(fill=tk.X)

                columns = ("Day", "Start Time", "End Time", "Room")
                schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show="headings", height=len(schedules))

                for col in columns:
                    schedule_tree.heading(col, text=col)
                    schedule_tree.column(col, width=100, anchor=tk.CENTER)

                for schedule in schedules:
                    schedule_tree.insert("", "end", values=(
                        schedule["day"], schedule["start_time"], schedule["end_time"], schedule["room"] or "N/A"
                    ))

                schedule_tree.pack(fill=tk.X)
            else:
                tk.Label(details_window, text="No schedule available", font=('Arial', 10)).pack(anchor="w")

            # Enrollments
            tk.Label(details_window, text="Enrollments:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if enrollments:
                enroll_frame = tk.Frame(details_window)
                enroll_frame.pack(fill=tk.BOTH, expand=True)

                columns = ("Student", "Enrollment Date", "Status")
                enroll_tree = ttk.Treeview(enroll_frame, columns=columns, show="headings", height=min(5, len(enrollments)))

                for col in columns:
                    enroll_tree.heading(col, text=col)
                    enroll_tree.column(col, width=100, anchor=tk.CENTER)

                for enrollment in enrollments:
                    enroll_tree.insert("", "end", values=(
                        enrollment["full_name"], enrollment["enrollment_date"], enrollment["status"].title()
                    ))

                enroll_tree.pack(fill=tk.BOTH, expand=True)

                # Add scrollbar
                scrollbar = ttk.Scrollbar(enroll_tree, orient="vertical", command=enroll_tree.yview)
                scrollbar.pack(side="right", fill="y")
                enroll_tree.configure(yscrollcommand=scrollbar.set)
            else:
                tk.Label(details_window, text="No enrollments yet", font=('Arial', 10)).pack(anchor="w")

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def manage_courses(self):
     if self.current_user["role"] not in ["admin", "registrar"]:
        messagebox.showerror("Error", "You don't have permission to manage courses!")
        return

     # Clear main frame properly
     for widget in self.main_frame.winfo_children():
        widget.destroy()

     # Add a back button
     back_button = ttk.Button(self.main_frame, text="Back to Dashboard", command=self.show_dashboard)
     back_button.pack(pady=5, anchor="ne")

     # Courses management title
     tk.Label(self.main_frame, text="Manage Courses", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

     # Search and filter frame
     filter_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
     filter_frame.pack(pady=10)

     tk.Label(filter_frame, text="Search:", bg="#f0f8ff").grid(row=0, column=0, padx=5)
     self.course_search_entry = ttk.Entry(filter_frame, width=30)
     self.course_search_entry.grid(row=0, column=1, padx=5)

     ttk.Button(filter_frame, text="Search", command=self.search_courses_manage).grid(row=0, column=2, padx=5)

     # Add course button
     ttk.Button(self.main_frame, text="Add New Course", command=self.add_new_course).pack(pady=5)

     # Courses table with improved columns
     columns = ("Code", "Title", "Credits", "Semester", "Faculty", "Enrolled", "Capacity")
     self.courses_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

     # Configure columns with appropriate widths
     col_widths = [80, 200, 60, 150, 150, 70, 70]
     for col, width in zip(columns, col_widths):
        self.courses_tree.heading(col, text=col)
        self.courses_tree.column(col, width=width, anchor=tk.CENTER)

     self.courses_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

     # Add scrollbar properly
     scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.courses_tree.yview)
     scrollbar.pack(side="right", fill="y")
     self.courses_tree.configure(yscrollcommand=scrollbar.set)

     # Context menu for course actions
     self.course_context_menu = tk.Menu(self.root, tearoff=0)
     self.course_context_menu.add_command(label="Edit Course", command=self.edit_course)
     self.course_context_menu.add_command(label="Delete Course", command=self.delete_course)
     self.course_context_menu.add_command(label="View Details", command=self.view_course_details)

     self.courses_tree.bind("<Button-3>", self.show_course_context_menu)
     self.courses_tree.bind("<Double-1>", lambda event: self.view_course_details())

     # Fetch and display courses
     self.refresh_courses_list()

    def search_courses_manage(self):
     search_term = self.course_search_entry.get().strip()

     # Clear existing data
     for item in self.courses_tree.get_children():
        self.courses_tree.delete(item)

     try:
        query = '''
            SELECT c.code, c.title, c.credits, 
                   CONCAT(d.name, ' - Semester ', s.semester_number) as semester,
                   u.full_name as faculty,
                   COUNT(e.id) as enrolled,
                   c.capacity
            FROM courses c
            LEFT JOIN semesters s ON c.semester_id = s.id
            LEFT JOIN degrees d ON s.degree_id = d.id
            LEFT JOIN users u ON c.faculty_id = u.id
            LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
        '''

        if search_term:
            query += f" WHERE c.code LIKE '%{search_term}%' OR c.title LIKE '%{search_term}%' OR u.full_name LIKE '%{search_term}%'"

        query += '''
            GROUP BY c.id
            ORDER BY c.code
        '''

        self.cursor.execute(query)
        for course in self.cursor.fetchall():
            self.courses_tree.insert("", "end", values=(
                course["code"], course["title"], course["credits"],
                course["semester"] or "Not assigned",
                course["faculty"] or "Not assigned",
                course["enrolled"],
                course["capacity"]
            ))
     except pymysql.MySQLError as err:
        messagebox.showerror("Database Error", f"Error searching courses: {err}")

    def refresh_courses_list(self):
        # Clear existing data
        for item in self.courses_tree.get_children():
            self.courses_tree.delete(item)

        try:
            # Fetch and display courses with semester information
            self.cursor.execute('''
                SELECT c.code, c.title, c.credits, 
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester,
                       c.capacity, u.full_name as faculty
                FROM courses c
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                LEFT JOIN users u ON c.faculty_id = u.id
                ORDER BY d.name, s.semester_number, c.code
            ''')
            for course in self.cursor.fetchall():
                self.courses_tree.insert("", "end", values=(
                    course["code"], course["title"], course["credits"],
                    course["semester"] or "Not assigned",
                    course["capacity"], course["faculty"] or "Not assigned"
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading courses: {err}")

    def show_course_context_menu(self, event):
        item = self.courses_tree.identify_row(event.y)
        if item:
            self.courses_tree.selection_set(item)
            self.course_context_menu.post(event.x_root, event.y_root)

    def edit_course(self):
        selected_item = self.courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to edit!")
            return

        course_data = self.courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        # Get full course details
        try:
            self.cursor.execute('''
                SELECT c.*, u.full_name as faculty_name,
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester_name
                FROM courses c
                LEFT JOIN users u ON c.faculty_id = u.id
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                WHERE c.code = %s
            ''', (course_code,))
            course = self.cursor.fetchone()

            self.edit_course_window = tk.Toplevel(self.root)
            self.edit_course_window.title("Edit Course")
            self.edit_course_window.geometry("500x500")

            tk.Label(self.edit_course_window, text="Edit Course", font=('Arial', 14)).pack(pady=10)

            # Form frame
            form_frame = tk.Frame(self.edit_course_window)
            form_frame.pack(pady=10)

            # Form fields
            tk.Label(form_frame, text="Course Code:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_code = ttk.Entry(form_frame)
            self.edit_course_code.insert(0, course["code"])
            self.edit_course_code.grid(row=0, column=1, padx=5, pady=5)
            self.edit_course_code.config(state='readonly')

            tk.Label(form_frame, text="Course Title:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_title = ttk.Entry(form_frame)
            self.edit_course_title.insert(0, course["title"])
            self.edit_course_title.grid(row=1, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_description = tk.Text(form_frame, width=30, height=4)
            self.edit_course_description.insert("1.0", course["description"] or "")
            self.edit_course_description.grid(row=2, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Credits:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_credits = ttk.Entry(form_frame)
            self.edit_course_credits.insert(0, course["credits"])
            self.edit_course_credits.grid(row=3, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Capacity:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_capacity = ttk.Entry(form_frame)
            self.edit_course_capacity.insert(0, course["capacity"])
            self.edit_course_capacity.grid(row=4, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Semester:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_semester = ttk.Combobox(form_frame)
            self.edit_course_semester.grid(row=5, column=1, padx=5, pady=5)

            # Populate semesters
            try:
                self.cursor.execute('''
                    SELECT s.id, d.name as degree_name, s.semester_number
                    FROM semesters s
                    JOIN degrees d ON s.degree_id = d.id
                    ORDER BY d.name, s.semester_number
                ''')
                semesters = self.cursor.fetchall()
                self.semester_dict = {f"{s['degree_name']} - Semester {s['semester_number']}": s["id"] for s in semesters}
                self.edit_course_semester['values'] = list(self.semester_dict.keys())
                if course["semester_name"]:
                    self.edit_course_semester.set(course["semester_name"])
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error loading semesters: {err}")

            tk.Label(form_frame, text="Faculty:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
            self.edit_course_faculty = ttk.Combobox(form_frame)
            self.edit_course_faculty.grid(row=6, column=1, padx=5, pady=5)

            # Populate faculty combobox
            self.cursor.execute("SELECT id, full_name FROM users WHERE role='faculty'")
            faculty = self.cursor.fetchall()
            self.faculty_dict = {f["full_name"]: f["id"] for f in faculty}
            self.edit_course_faculty['values'] = list(self.faculty_dict.keys())
            if course["faculty_name"]:
                self.edit_course_faculty.set(course["faculty_name"])

            self.editing_course_id = course["id"]

            ttk.Button(self.edit_course_window, text="Update", command=self.update_course).pack(pady=15)

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def update_course(self):
        title = self.edit_course_title.get().strip()
        description = self.edit_course_description.get("1.0", tk.END).strip()
        credits = self.edit_course_credits.get().strip()
        capacity = self.edit_course_capacity.get().strip()
        semester_name = self.edit_course_semester.get().strip()
        faculty_name = self.edit_course_faculty.get().strip()

        if not all([title, credits, capacity]):
            messagebox.showerror("Error", "Title, Credits and Capacity are required!")
            return

        try:
            credits = int(credits)
            capacity = int(capacity)
        except ValueError:
            messagebox.showerror("Error", "Credits and Capacity must be numbers!")
            return

        # Get semester ID
        semester_id = None
        if semester_name:
            semester_id = self.semester_dict.get(semester_name)
            if not semester_id:
                messagebox.showerror("Error", "Selected semester not found!")
                return

        # Get faculty ID
        faculty_id = None
        if faculty_name:
            faculty_id = self.faculty_dict.get(faculty_name)
            if not faculty_id:
                messagebox.showerror("Error", "Selected faculty not found!")
                return

        try:
            self.cursor.execute(
                "UPDATE courses SET title=%s, description=%s, credits=%s, capacity=%s, semester_id=%s, faculty_id=%s WHERE id=%s",
                (title, description, credits, capacity, semester_id, faculty_id, self.editing_course_id)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Course updated successfully!")
            self.edit_course_window.destroy()
            self.refresh_courses_list()
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def delete_course(self):
        selected_item = self.courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to delete!")
            return

        course_data = self.courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete course {course_code}?"):
            try:
                self.cursor.execute("DELETE FROM courses WHERE code=%s", (course_code,))
                self.conn.commit()
                messagebox.showinfo("Success", "Course deleted successfully!")
                self.refresh_courses_list()
            except pymysql.MySQLError as err:
                if err.errno == 1451:  # Foreign key constraint
                    messagebox.showerror("Error", "Cannot delete course with existing enrollments or schedules!")
                else:
                    messagebox.showerror("Database Error", f"Error: {err}")

    def view_course_details(self):
        selected_item = self.courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to view details!")
            return

        course_data = self.courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course details
            self.cursor.execute('''
                SELECT c.*, u.full_name as faculty_name,
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester_name
                FROM courses c
                LEFT JOIN users u ON c.faculty_id = u.id
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                WHERE c.code = %s
            ''', (course_code,))
            course = self.cursor.fetchone()

            # Get course schedules
            self.cursor.execute('''
                SELECT day, start_time, end_time, room
                FROM schedules
                WHERE course_id = %s
                ORDER BY 
                    CASE day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    start_time
            ''', (course["id"],))
            schedules = self.cursor.fetchall()

            # Get enrolled students
            self.cursor.execute('''
                SELECT u.full_name, e.enrollment_date, e.status
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.course_id = %s
                ORDER BY e.enrollment_date
            ''', (course["id"],))
            enrollments = self.cursor.fetchall()

            # Create details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Course Details - {course_code}")
            details_window.geometry("800x600")

            # Course info frame
            info_frame = tk.Frame(details_window)
            info_frame.pack(pady=10, fill=tk.X)

            tk.Label(info_frame, text=f"Course: {course['code']} - {course['title']}", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky="w")
            tk.Label(info_frame, text=f"Credits: {course['credits']}", font=('Arial', 12)).grid(row=1, column=0, sticky="w")
            tk.Label(info_frame, text=f"Semester: {course['semester_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=2, column=0, sticky="w")
            tk.Label(info_frame, text=f"Capacity: {course['capacity']}", font=('Arial', 12)).grid(row=3, column=0, sticky="w")
            tk.Label(info_frame, text=f"Faculty: {course['faculty_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=4, column=0, sticky="w")

            # Description
            desc_frame = tk.Frame(details_window)
            desc_frame.pack(pady=10, fill=tk.X)

            tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor="w")
            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD)
            desc_text.insert("1.0", course["description"] or "No description available")
            desc_text.config(state="disabled")
            desc_text.pack(fill=tk.X)

            # Schedules
            tk.Label(details_window, text="Schedule:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if schedules:
                schedule_frame = tk.Frame(details_window)
                schedule_frame.pack(fill=tk.X)

                columns = ("Day", "Start Time", "End Time", "Room")
                schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show="headings", height=len(schedules))

                for col in columns:
                    schedule_tree.heading(col, text=col)
                    schedule_tree.column(col, width=100, anchor=tk.CENTER)

                for schedule in schedules:
                    schedule_tree.insert("", "end", values=(
                        schedule["day"], schedule["start_time"], schedule["end_time"], schedule["room"] or "N/A"
                    ))

                schedule_tree.pack(fill=tk.X)
            else:
                tk.Label(details_window, text="No schedule available", font=('Arial', 10)).pack(anchor="w")

            # Enrollments
            tk.Label(details_window, text="Enrollments:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if enrollments:
                enroll_frame = tk.Frame(details_window)
                enroll_frame.pack(fill=tk.BOTH, expand=True)

                columns = ("Student", "Enrollment Date", "Status")
                enroll_tree = ttk.Treeview(enroll_frame, columns=columns, show="headings", height=min(5, len(enrollments)))

                for col in columns:
                    enroll_tree.heading(col, text=col)
                    enroll_tree.column(col, width=100, anchor=tk.CENTER)

                for enrollment in enrollments:
                    enroll_tree.insert("", "end", values=(
                        enrollment["full_name"], enrollment["enrollment_date"], enrollment["status"].title()
                    ))

                enroll_tree.pack(fill=tk.BOTH, expand=True)

                # Add scrollbar
                scrollbar = ttk.Scrollbar(enroll_tree, orient="vertical", command=enroll_tree.yview)
                scrollbar.pack(side="right", fill="y")
                enroll_tree.configure(yscrollcommand=scrollbar.set)
            else:
                tk.Label(details_window, text="No enrollments yet", font=('Arial', 10)).pack(anchor="w")

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def manage_schedules(self):
     if self.current_user["role"] not in ["admin", "registrar"]:
        messagebox.showerror("Error", "You don't have permission to manage schedules!")
        return

     # Clear main frame properly
     for widget in self.main_frame.winfo_children():
        widget.destroy()

     # Add a back button with larger size
     back_button = ttk.Button(self.main_frame, text="Back to Dashboard", 
                           command=self.show_dashboard, style='Large.TButton')
     back_button.pack(pady=10, anchor="ne")

     # Schedules management title with larger font and padding
     tk.Label(self.main_frame, text="Manage Schedules", 
            font=('Arial', 18, 'bold'), bg="#f0f8ff").pack(pady=15)

     # Filter frame with increased spacing
     filter_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
     filter_frame.pack(pady=15)

     tk.Label(filter_frame, text="Filter by Room:", 
            font=('Arial', 12), bg="#f0f8ff").grid(row=0, column=0, padx=10, pady=5)

     self.schedule_room_filter = ttk.Entry(filter_frame, width=30, font=('Arial', 12))
     self.schedule_room_filter.grid(row=0, column=1, padx=10, pady=5)

     ttk.Button(filter_frame, text="Filter", command=self.refresh_schedules_list, 
              style='Large.TButton').grid(row=0, column=2, padx=10, pady=5)
     ttk.Button(filter_frame, text="Clear", command=self.clear_schedule_filters, 
              style='Large.TButton').grid(row=0, column=3, padx=10, pady=5)

     # Add schedule button with larger size and padding
     ttk.Button(self.main_frame, text="Add New Schedule", 
              command=self.add_new_schedule, style='Large.TButton').pack(pady=15)

     # Create a style for larger elements
     self.style.configure('Large.TButton', font=('Arial', 12), padding=8)

     # Schedules table with increased dimensions
     columns = ("ID", "Course", "Day", "Start Time", "End Time", "Room")
     self.schedules_tree = ttk.Treeview(self.main_frame, columns=columns, 
                                      show="headings", height=20)  # Increased height

     # Configure columns with larger widths
     col_widths = [60, 300, 150, 150, 150, 200]  # Further increased widths
     for col, width in zip(columns, col_widths):
        self.schedules_tree.heading(col, text=col, anchor=tk.CENTER)
        self.schedules_tree.column(col, width=width, anchor=tk.CENTER)

     # Set larger fonts and spacing for treeview
     self.style.configure('Treeview', font=('Arial', 12), rowheight=35)  # Increased row height
     self.style.configure('Treeview.Heading', font=('Arial', 13, 'bold'))

     # Pack the treeview with more padding and expansion
     self.schedules_tree.pack(pady=15, padx=30, fill=tk.BOTH, expand=True)

     # Add scrollbar with larger grip
     scrollbar = ttk.Scrollbar(self.schedules_tree, orient="vertical", 
                             command=self.schedules_tree.yview)
     scrollbar.pack(side="right", fill="y")
     self.schedules_tree.configure(yscrollcommand=scrollbar.set)

     # Context menu with larger font
     self.schedule_context_menu = tk.Menu(self.root, tearoff=0, font=('Arial', 12))
     self.schedule_context_menu.add_command(label="Edit Schedule", command=self.edit_schedule)
     self.schedule_context_menu.add_command(label="Delete Schedule", command=self.delete_schedule)

     self.schedules_tree.bind("<Button-3>", self.show_schedule_context_menu)
     self.schedules_tree.bind("<Double-1>", lambda event: self.edit_schedule())

     # Fetch and display schedules
     self.refresh_schedules_list()

    def clear_schedule_filters(self):
     self.schedule_room_filter.delete(0, tk.END)
     self.refresh_schedules_list()

    def refresh_schedules_list(self):
     room_filter = self.schedule_room_filter.get().strip()

     # Clear existing data
     for item in self.schedules_tree.get_children():
        self.schedules_tree.delete(item)

     try:
        query = '''
            SELECT sch.id, c.title, sch.day, sch.start_time, sch.end_time, sch.room
            FROM schedules sch
            JOIN courses c ON sch.course_id = c.id
        '''

        if room_filter:
            query += f" WHERE sch.room LIKE '%{room_filter}%'"

        query += '''
            ORDER BY 
                CASE sch.day
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END,
                sch.start_time
        '''

        self.cursor.execute(query)
        for schedule in self.cursor.fetchall():
            self.schedules_tree.insert("", "end", values=(
                schedule["id"], schedule["title"], schedule["day"],
                schedule["start_time"], schedule["end_time"],
                schedule["room"] or "N/A"
            ))
     except pymysql.MySQLError as err:
        messagebox.showerror("Database Error", f"Error loading schedules: {err}")

    def show_schedule_context_menu(self, event):
        item = self.schedules_tree.identify_row(event.y)
        if item:
            self.schedules_tree.selection_set(item)
            self.schedule_context_menu.post(event.x_root, event.y_root)

    def add_new_schedule(self):
        self.add_schedule_window = tk.Toplevel(self.root)
        self.add_schedule_window.title("Add New Schedule")
        self.add_schedule_window.geometry("500x400")

        tk.Label(self.add_schedule_window, text="Add New Schedule", font=('Arial', 14)).pack(pady=10)

        # Form frame
        form_frame = tk.Frame(self.add_schedule_window)
        form_frame.pack(pady=10)

        # Form fields
        tk.Label(form_frame, text="Course:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.new_schedule_course = ttk.Combobox(form_frame)
        self.new_schedule_course.grid(row=0, column=1, padx=5, pady=5)

        # Populate course combobox
        try:
            self.cursor.execute('''
                SELECT c.id, c.code, c.title, 
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester
                FROM courses c
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                ORDER BY c.code
            ''')
            courses = self.cursor.fetchall()
            self.course_dict = {f"{c['code']} - {c['title']} ({c['semester'] or 'No semester'})": c["id"] for c in courses}
            self.new_schedule_course['values'] = list(self.course_dict.keys())
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading courses: {err}")

        tk.Label(form_frame, text="Day:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.new_schedule_day = ttk.Combobox(form_frame, 
                                           values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.new_schedule_day.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Start Time:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.new_schedule_start = ttk.Entry(form_frame)
        self.new_schedule_start.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="End Time:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.new_schedule_end = ttk.Entry(form_frame)
        self.new_schedule_end.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Room:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.new_schedule_room = ttk.Entry(form_frame)
        self.new_schedule_room.grid(row=4, column=1, padx=5, pady=5)

        ttk.Button(self.add_schedule_window, text="Save", command=self.save_new_schedule).pack(pady=15)

    def save_new_schedule(self):
        course_name = self.new_schedule_course.get().strip()
        day = self.new_schedule_day.get().strip()
        start_time = self.new_schedule_start.get().strip()
        end_time = self.new_schedule_end.get().strip()
        room = self.new_schedule_room.get().strip()

        if not all([course_name, day, start_time, end_time]):
            messagebox.showerror("Error", "Course, Day, Start Time and End Time are required!")
            return

        # Get course ID
        course_id = self.course_dict.get(course_name)
        if not course_id:
            messagebox.showerror("Error", "Selected course not found!")
            return

        try:
            self.cursor.execute(
                "INSERT INTO schedules (course_id, day, start_time, end_time, room) VALUES (%s, %s, %s, %s, %s)",
                (course_id, day, start_time, end_time, room or None)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Schedule added successfully!")
            self.add_schedule_window.destroy()
            self.refresh_schedules_list()
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def edit_schedule(self):
        selected_item = self.schedules_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a schedule to edit!")
            return

        schedule_data = self.schedules_tree.item(selected_item)['values']
        course_title = schedule_data[0]
        day = schedule_data[2]
        start_time = schedule_data[3]
        end_time = schedule_data[4]
        room = schedule_data[5]

        # Get schedule ID
        try:
            self.cursor.execute('''
                SELECT sch.id
                FROM schedules sch
                JOIN courses c ON sch.course_id = c.id
                WHERE c.title = %s AND sch.day = %s AND sch.start_time = %s AND sch.end_time = %s
            ''', (course_title, day, start_time, end_time))
            schedule = self.cursor.fetchone()

            if not schedule:
                messagebox.showerror("Error", "Schedule not found!")
                return

            self.edit_schedule_window = tk.Toplevel(self.root)
            self.edit_schedule_window.title("Edit Schedule")
            self.edit_schedule_window.geometry("500x400")

            tk.Label(self.edit_schedule_window, text="Edit Schedule", font=('Arial', 14)).pack(pady=10)

            # Form frame
            form_frame = tk.Frame(self.edit_schedule_window)
            form_frame.pack(pady=10)

            # Form fields
            tk.Label(form_frame, text="Course:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.edit_schedule_course = ttk.Entry(form_frame)
            self.edit_schedule_course.insert(0, course_title)
            self.edit_schedule_course.grid(row=0, column=1, padx=5, pady=5)
            self.edit_schedule_course.config(state='readonly')

            tk.Label(form_frame, text="Day:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.edit_schedule_day = ttk.Combobox(form_frame, 
                                                values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            self.edit_schedule_day.set(day)
            self.edit_schedule_day.grid(row=1, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Start Time:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            self.edit_schedule_start = ttk.Entry(form_frame)
            self.edit_schedule_start.insert(0, start_time)
            self.edit_schedule_start.grid(row=2, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="End Time:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            self.edit_schedule_end = ttk.Entry(form_frame)
            self.edit_schedule_end.insert(0, end_time)
            self.edit_schedule_end.grid(row=3, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Room:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            self.edit_schedule_room = ttk.Entry(form_frame)
            self.edit_schedule_room.insert(0, room)
            self.edit_schedule_room.grid(row=4, column=1, padx=5, pady=5)

            self.editing_schedule_id = schedule["id"]

            ttk.Button(self.edit_schedule_window, text="Update", command=self.update_schedule).pack(pady=15)

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading schedule details: {err}")

    def update_schedule(self):
        day = self.edit_schedule_day.get().strip()
        start_time = self.edit_schedule_start.get().strip()
        end_time = self.edit_schedule_end.get().strip()
        room = self.edit_schedule_room.get().strip()

        if not all([day, start_time, end_time]):
            messagebox.showerror("Error", "Day, Start Time and End Time are required!")
            return

        try:
            self.cursor.execute(
                "UPDATE schedules SET day=%s, start_time=%s, end_time=%s, room=%s WHERE id=%s",
                (day, start_time, end_time, room or None, self.editing_schedule_id)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Schedule updated successfully!")
            self.edit_schedule_window.destroy()
            self.refresh_schedules_list()
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def delete_schedule(self):
        selected_item = self.schedules_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a schedule to delete!")
            return

        schedule_data = self.schedules_tree.item(selected_item)['values']
        course_title = schedule_data[0]
        day = schedule_data[2]
        start_time = schedule_data[3]
        end_time = schedule_data[4]

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete this schedule for {course_title}?"):
            try:
                self.cursor.execute('''
                    DELETE sch FROM schedules sch
                    JOIN courses c ON sch.course_id = c.id
                    WHERE c.title = %s AND sch.day = %s AND sch.start_time = %s AND sch.end_time = %s
                ''', (course_title, day, start_time, end_time))
                self.conn.commit()
                messagebox.showinfo("Success", "Schedule deleted successfully!")
                self.refresh_schedules_list()
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error: {err}")

    def view_course_catalog(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Course catalog title
        tk.Label(self.main_frame, text="Course Catalog", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Search frame
        search_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Search:", bg="#f0f8ff").pack(side=tk.LEFT, padx=5)
        self.course_search_entry = ttk.Entry(search_frame, width=30)
        self.course_search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="Search", command=self.search_courses).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Show All", command=self.refresh_course_catalog).pack(side=tk.LEFT, padx=5)

        # Filter by semester (for students)
        if self.current_user["role"] == "student":
            filter_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
            filter_frame.pack(pady=10)

            tk.Label(filter_frame, text="Filter by Semester:", bg="#f0f8ff").pack(side=tk.LEFT, padx=5)
            self.course_filter_semester = ttk.Combobox(filter_frame)
            self.course_filter_semester.pack(side=tk.LEFT, padx=5)

            # Populate semester filter
            try:
                self.cursor.execute('''
                    SELECT DISTINCT s.semester_number
                    FROM semesters s
                    JOIN courses c ON s.id = c.semester_id
                    ORDER BY s.semester_number
                ''')
                semesters = [str(s["semester_number"]) for s in self.cursor.fetchall()]
                self.course_filter_semester['values'] = ["All"] + semesters
                self.course_filter_semester.set("All")
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error loading semesters: {err}")

            ttk.Button(filter_frame, text="Filter", command=self.refresh_course_catalog).pack(side=tk.LEFT, padx=5)

        # Courses table

        columns = ("Code", "Title", "Credits", "Semester", "Faculty", "Schedule", "Enrolled", "Capacity")       
        self.catalog_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        # Configure columns with appropriate widths
        col_widths = [80, 200, 60, 150, 150, 250, 70, 70]  # Increased width for Schedule column
        for col, width in zip(columns, col_widths):
         self.catalog_tree.heading(col, text=col)
         self.catalog_tree.column(col, width=width, anchor=tk.CENTER)

        self.catalog_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.catalog_tree, orient="vertical", command=self.catalog_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.catalog_tree.configure(yscrollcommand=scrollbar.set)

        # Context menu for course actions
        if self.current_user["role"] == "student":
            self.catalog_context_menu = tk.Menu(self.root, tearoff=0)
            self.catalog_context_menu.add_command(label="View Details", command=self.view_catalog_course_details)
            self.catalog_context_menu.add_command(label="Enroll", command=self.enroll_in_course)
            self.catalog_tree.bind("<Button-3>", self.show_catalog_context_menu)

        # Fetch and display courses
        self.refresh_course_catalog()
    def show_schedule_tooltip(event):
     item = self.catalog_tree.identify_row(event.y)
     col = self.catalog_tree.identify_column(event.x)
     if item and col == "#6":  # Assuming schedule is column 6
        schedule = self.catalog_tree.item(item, "values")[5]
        if schedule and schedule != "Not scheduled":
            tooltip = tk.Toplevel(self.root)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=schedule, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            tooltip.after(3000, tooltip.destroy)

     self.catalog_tree.bind("<Motion>", show_schedule_tooltip)
    def refresh_course_catalog(self):
     # Clear existing data
     for item in self.catalog_tree.get_children():
        self.catalog_tree.delete(item)

     try:
        # Modify the query to get schedule information in a better format
        query = '''
            SELECT c.id, c.code, c.title, c.credits, c.capacity, 
                   CONCAT(d.name, ' - Semester ', s.semester_number) as semester,
                   u.full_name as faculty,
                   COUNT(e.id) as enrolled,
                   GROUP_CONCAT(
                       CONCAT(sch.day, ' ', TIME_FORMAT(sch.start_time, '%h:%i %p'), '-', 
                       TIME_FORMAT(sch.end_time, '%h:%i %p'),
                       CASE WHEN sch.room IS NOT NULL THEN CONCAT(' (', sch.room, ')') ELSE '' END)
                       ORDER BY 
                           CASE sch.day
                               WHEN 'Monday' THEN 1
                               WHEN 'Tuesday' THEN 2
                               WHEN 'Wednesday' THEN 3
                               WHEN 'Thursday' THEN 4
                               WHEN 'Friday' THEN 5
                               WHEN 'Saturday' THEN 6
                               WHEN 'Sunday' THEN 7
                           END,
                           sch.start_time
                       SEPARATOR '; '
                   ) as schedule
            FROM courses c
            LEFT JOIN semesters s ON c.semester_id = s.id
            LEFT JOIN degrees d ON s.degree_id = d.id
            LEFT JOIN users u ON c.faculty_id = u.id
            LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
            LEFT JOIN schedules sch ON sch.course_id = c.id
            WHERE 1=1
        '''

        # Add search condition if search term exists
        search_term = self.course_search_entry.get().strip()
        if search_term:
            search_pattern = f"%{search_term}%"
            query += f" AND (c.code LIKE '{search_pattern}' OR c.title LIKE '{search_pattern}' OR u.full_name LIKE '{search_pattern}')"

        # Add semester filter for students
        if self.current_user["role"] == "student" and hasattr(self, 'course_filter_semester'):
            semester_filter = self.course_filter_semester.get()
            if semester_filter and semester_filter != "All":
                query += f" AND s.semester_number = {semester_filter}"

        query += '''
            GROUP BY c.id
            ORDER BY c.code
        '''

        # Fetch and display courses
        self.cursor.execute(query)

        for course in self.cursor.fetchall():
            # Format the schedule text better
            schedule_text = course["schedule"] or "Not scheduled"
            if schedule_text != "Not scheduled":
                schedule_text = schedule_text.replace("; ", "\n")

            enrolled = course["enrolled"]
            capacity = course["capacity"]

            # Color coding based on capacity
            tags = ()
            if enrolled >= capacity:
                tags = ('full',)
            elif enrolled >= capacity * 0.8:
                tags = ('almost_full',)

            self.catalog_tree.insert("", "end", values=(
                course["code"], course["title"], course["credits"],
                course["semester"] or "Not assigned",
                course["faculty"] or "Not assigned",
                schedule_text,
                enrolled,
                capacity
            ), tags=tags)

        # Configure tag colors
        self.catalog_tree.tag_configure('full', background='#ffcccc')  # Light red for full courses
        self.catalog_tree.tag_configure('almost_full', background='#fff3cd')  # Light yellow for almost full

     except pymysql.MySQLError as err:
        messagebox.showerror("Database Error", f"Error loading course catalog: {err}")

    def search_courses(self):
        self.refresh_course_catalog()

    def show_catalog_context_menu(self, event):
        item = self.catalog_tree.identify_row(event.y)
        if item:
            self.catalog_tree.selection_set(item)
            self.catalog_context_menu.post(event.x_root, event.y_root)

    def view_catalog_course_details(self):
        selected_item = self.catalog_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to view details!")
            return

        course_data = self.catalog_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course details
            self.cursor.execute('''
                SELECT c.*, u.full_name as faculty_name,
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester_name
                FROM courses c
                LEFT JOIN users u ON c.faculty_id = u.id
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                WHERE c.code = %s
            ''', (course_code,))
            course = self.cursor.fetchone()

            # Get course schedules
            self.cursor.execute('''
                SELECT day, start_time, end_time, room
                FROM schedules
                WHERE course_id = %s
                ORDER BY 
                    CASE day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    start_time
            ''', (course["id"],))
            schedules = self.cursor.fetchall()

            # Create details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Course Details - {course_code}")
            details_window.geometry("800x600")

            # Course info frame
            info_frame = tk.Frame(details_window)
            info_frame.pack(pady=10, fill=tk.X)

            tk.Label(info_frame, text=f"Course: {course['code']} - {course['title']}", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky="w")
            tk.Label(info_frame, text=f"Credits: {course['credits']}", font=('Arial', 12)).grid(row=1, column=0, sticky="w")
            tk.Label(info_frame, text=f"Semester: {course['semester_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=2, column=0, sticky="w")
            tk.Label(info_frame, text=f"Capacity: {course['capacity']}", font=('Arial', 12)).grid(row=3, column=0, sticky="w")
            tk.Label(info_frame, text=f"Faculty: {course['faculty_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=4, column=0, sticky="w")

            # Description
            desc_frame = tk.Frame(details_window)
            desc_frame.pack(pady=10, fill=tk.X)

            tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor="w")
            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD)
            desc_text.insert("1.0", course["description"] or "No description available")
            desc_text.config(state="disabled")
            desc_text.pack(fill=tk.X)

            # Schedules
            tk.Label(details_window, text="Schedule:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if schedules:
                schedule_frame = tk.Frame(details_window)
                schedule_frame.pack(fill=tk.X)

                columns = ("Day", "Start Time", "End Time", "Room")
                schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show="headings", height=len(schedules))

                for col in columns:
                    schedule_tree.heading(col, text=col)
                    schedule_tree.column(col, width=100, anchor=tk.CENTER)

                for schedule in schedules:
                    schedule_tree.insert("", "end", values=(
                        schedule["day"], schedule["start_time"], schedule["end_time"], schedule["room"] or "N/A"
                    ))

                schedule_tree.pack(fill=tk.X)
            else:
                tk.Label(details_window, text="No schedule available", font=('Arial', 10)).pack(anchor="w")

            # Enroll button for students
            if self.current_user["role"] == "student":
                # Check if already enrolled
                self.cursor.execute('''
                    SELECT status FROM enrollments 
                    WHERE student_id = %s AND course_id = %s
                ''', (self.current_user["id"], course["id"]))
                enrollment = self.cursor.fetchone()

                button_frame = tk.Frame(details_window)
                button_frame.pack(pady=10)

                if enrollment:
                    status = enrollment["status"]
                    if status == "registered":
                        ttk.Button(button_frame, text="Drop Course", 
                                  command=lambda: self.drop_course(course["id"], details_window)).pack(side=tk.LEFT, padx=5)
                    elif status == "waitlisted":
                        tk.Label(button_frame, text="You are on the waitlist for this course", 
                                font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
                else:
                    ttk.Button(button_frame, text="Enroll in Course", 
                              command=lambda: self.enroll_in_specific_course(course["id"], details_window)).pack(side=tk.LEFT, padx=5)

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def enroll_in_course(self):
        selected_item = self.catalog_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to enroll in!")
            return

        course_data = self.catalog_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course ID
            self.cursor.execute("SELECT id, capacity FROM courses WHERE code = %s", (course_code,))
            course = self.cursor.fetchone()

            if not course:
                messagebox.showerror("Error", "Course not found!")
                return

            # Check if already enrolled
            self.cursor.execute('''
                SELECT status FROM enrollments 
                WHERE student_id = %s AND course_id = %s
            ''', (self.current_user["id"], course["id"]))
            enrollment = self.cursor.fetchone()

            if enrollment:
                status = enrollment["status"]
                if status == "registered":
                    messagebox.showinfo("Info", "You are already registered for this course!")
                elif status == "waitlisted":
                    messagebox.showinfo("Info", "You are already on the waitlist for this course!")
                return

            # Check capacity
            self.cursor.execute('''
                SELECT COUNT(*) as count FROM enrollments 
                WHERE course_id = %s AND status = 'registered'
            ''', (course["id"],))
            enrolled = self.cursor.fetchone()["count"]

            if enrolled >= course["capacity"]:
                if messagebox.askyesno("Course Full", "This course is full. Would you like to join the waitlist?"):
                    self.cursor.execute(
                        "INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES (%s, %s, CURDATE(), 'waitlisted')",
                        (self.current_user["id"], course["id"])
                    )
                    self.conn.commit()
                    messagebox.showinfo("Success", "You have been added to the waitlist!")
                    self.refresh_course_catalog()
            else:
                self.cursor.execute(
                    "INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES (%s, %s, CURDATE(), 'registered')",
                    (self.current_user["id"], course["id"])
                )
                self.conn.commit()
                messagebox.showinfo("Success", "You have been enrolled in the course!")
                self.refresh_course_catalog()

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error enrolling in course: {err}")

    def enroll_in_specific_course(self, course_id, window=None):
        try:
            # Get course capacity
            self.cursor.execute("SELECT capacity FROM courses WHERE id = %s", (course_id,))
            course = self.cursor.fetchone()

            if not course:
                messagebox.showerror("Error", "Course not found!")
                return

            # Check if already enrolled
            self.cursor.execute('''
                SELECT status FROM enrollments 
                WHERE student_id = %s AND course_id = %s
            ''', (self.current_user["id"], course_id))
            enrollment = self.cursor.fetchone()

            if enrollment:
                status = enrollment["status"]
                if status == "registered":
                    messagebox.showinfo("Info", "You are already registered for this course!")
                elif status == "waitlisted":
                    messagebox.showinfo("Info", "You are already on the waitlist for this course!")
                return

            # Check capacity
            self.cursor.execute('''
                SELECT COUNT(*) as count FROM enrollments 
                WHERE course_id = %s AND status = 'registered'
            ''', (course_id,))
            enrolled = self.cursor.fetchone()["count"]

            if enrolled >= course["capacity"]:
                if messagebox.askyesno("Course Full", "This course is full. Would you like to join the waitlist?"):
                    self.cursor.execute(
                        "INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES (%s, %s, CURDATE(), 'waitlisted')",
                        (self.current_user["id"], course_id)
                    )
                    self.conn.commit()
                    messagebox.showinfo("Success", "You have been added to the waitlist!")
                    if window:
                        window.destroy()
                    self.refresh_course_catalog()
            else:
                self.cursor.execute(
                    "INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES (%s, %s, CURDATE(), 'registered')",
                    (self.current_user["id"], course_id)
                )
                self.conn.commit()
                messagebox.showinfo("Success", "You have been enrolled in the course!")
                if window:
                    window.destroy()
                self.refresh_course_catalog()

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error enrolling in course: {err}")

    def drop_course(self, course_id, window=None):
        if messagebox.askyesno("Confirm", "Are you sure you want to drop this course?"):
            try:
                self.cursor.execute(
                    "DELETE FROM enrollments WHERE student_id = %s AND course_id = %s",
                    (self.current_user["id"], course_id)
                )
                self.conn.commit()
                messagebox.showinfo("Success", "You have been dropped from the course!")
                if window:
                    window.destroy()
                self.refresh_course_catalog()
            except pymysql.MySQLError as err:
                messagebox.showerror("Database Error", f"Error dropping course: {err}")

    def view_my_courses(self):
        if self.current_user["role"] != "student":
            messagebox.showerror("Error", "Only students can view their courses!")
            return

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # My courses title
        tk.Label(self.main_frame, text="My Courses", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Courses table
        columns = ("Course Code", "Title", "Credits", "Semester", "Faculty", "Schedule", "Status")
        self.my_courses_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.my_courses_tree.heading(col, text=col)
            self.my_courses_tree.column(col, width=120, anchor=tk.CENTER)

        self.my_courses_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.my_courses_tree, orient="vertical", command=self.my_courses_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.my_courses_tree.configure(yscrollcommand=scrollbar.set)

        # Context menu for course actions
        self.my_courses_context_menu = tk.Menu(self.root, tearoff=0)
        self.my_courses_context_menu.add_command(label="View Details", command=self.view_my_course_details)
        self.my_courses_context_menu.add_command(label="Drop Course", command=self.drop_selected_course)

        self.my_courses_tree.bind("<Button-3>", self.show_my_courses_context_menu)

        # Fetch and display my courses
        self.refresh_my_courses_list()

    def refresh_my_courses_list(self):
        # Clear existing data
        for item in self.my_courses_tree.get_children():
            self.my_courses_tree.delete(item)

        try:
            # Fetch and display my courses with semester information
            self.cursor.execute('''
                SELECT c.code, c.title, c.credits, 
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester,
                       u.full_name as faculty, e.status,
                       GROUP_CONCAT(
                           CONCAT(sch.day, ' ', sch.start_time, '-', sch.end_time, 
                                  CASE WHEN sch.room IS NOT NULL THEN CONCAT(' (', sch.room, ')') ELSE '' END)
                           SEPARATOR '\n'
                       ) as schedule
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                LEFT JOIN users u ON c.faculty_id = u.id
                LEFT JOIN schedules sch ON sch.course_id = c.id
                WHERE e.student_id = %s
                GROUP BY c.id, e.status
                ORDER BY c.code
            ''', (self.current_user["id"],))

            for course in self.cursor.fetchall():
                self.my_courses_tree.insert("", "end", values=(
                    course["code"], course["title"], course["credits"],
                    course["semester"] or "Not assigned",
                    course["faculty"] or "Not assigned",
                    course["schedule"] or "Not scheduled",
                    course["status"].title()
                ))

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading your courses: {err}")

    def show_my_courses_context_menu(self, event):
        item = self.my_courses_tree.identify_row(event.y)
        if item:
            self.my_courses_tree.selection_set(item)
            self.my_courses_context_menu.post(event.x_root, event.y_root)

    def view_my_course_details(self):
        selected_item = self.my_courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to view details!")
            return

        course_data = self.my_courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course details
            self.cursor.execute('''
                SELECT c.*, u.full_name as faculty_name,
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester_name
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                LEFT JOIN users u ON c.faculty_id = u.id
                WHERE c.code = %s AND e.student_id = %s
            ''', (course_code, self.current_user["id"]))
            course = self.cursor.fetchone()

            if not course:
                messagebox.showerror("Error", "Course not found in your enrollments!")
                return

            # Get course schedules
            self.cursor.execute('''
                SELECT day, start_time, end_time, room
                FROM schedules
                WHERE course_id = %s
                ORDER BY 
                    CASE day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    start_time
            ''', (course["id"],))
            schedules = self.cursor.fetchall()

            # Create details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Course Details - {course_code}")
            details_window.geometry("800x600")

            # Course info frame
            info_frame = tk.Frame(details_window)
            info_frame.pack(pady=10, fill=tk.X)

            tk.Label(info_frame, text=f"Course: {course['code']} - {course['title']}", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky="w")
            tk.Label(info_frame, text=f"Credits: {course['credits']}", font=('Arial', 12)).grid(row=1, column=0, sticky="w")
            tk.Label(info_frame, text=f"Semester: {course['semester_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=2, column=0, sticky="w")
            tk.Label(info_frame, text=f"Faculty: {course['faculty_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=3, column=0, sticky="w")

            # Description
            desc_frame = tk.Frame(details_window)
            desc_frame.pack(pady=10, fill=tk.X)

            tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor="w")
            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD)
            desc_text.insert("1.0", course["description"] or "No description available")
            desc_text.config(state="disabled")
            desc_text.pack(fill=tk.X)

            # Schedules
            tk.Label(details_window, text="Schedule:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if schedules:
                schedule_frame = tk.Frame(details_window)
                schedule_frame.pack(fill=tk.X)

                columns = ("Day", "Start Time", "End Time", "Room")
                schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show="headings", height=len(schedules))

                for col in columns:
                    schedule_tree.heading(col, text=col)
                    schedule_tree.column(col, width=100, anchor=tk.CENTER)

                for schedule in schedules:
                    schedule_tree.insert("", "end", values=(
                        schedule["day"], schedule["start_time"], schedule["end_time"], schedule["room"] or "N/A"
                    ))

                schedule_tree.pack(fill=tk.X)
            else:
                tk.Label(details_window, text="No schedule available", font=('Arial', 10)).pack(anchor="w")

            # Drop button
            button_frame = tk.Frame(details_window)
            button_frame.pack(pady=10)

            ttk.Button(button_frame, text="Drop Course", 
                      command=lambda: self.drop_course(course["id"], details_window)).pack()

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def drop_selected_course(self):
        selected_item = self.my_courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to drop!")
            return

        course_data = self.my_courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course ID
            self.cursor.execute("SELECT id FROM courses WHERE code = %s", (course_code,))
            course = self.cursor.fetchone()

            if not course:
                messagebox.showerror("Error", "Course not found!")
                return

            if messagebox.askyesno("Confirm", f"Are you sure you want to drop {course_code}?"):
                self.cursor.execute(
                    "DELETE FROM enrollments WHERE student_id = %s AND course_id = %s",
                    (self.current_user["id"], course["id"])
                )
                self.conn.commit()
                messagebox.showinfo("Success", "You have been dropped from the course!")
                self.refresh_my_courses_list()

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error dropping course: {err}")

    def view_my_teaching(self):
        if self.current_user["role"] != "faculty":
            messagebox.showerror("Error", "Only faculty can view their teaching assignments!")
            return

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # My teaching title
        tk.Label(self.main_frame, text="My Teaching Assignments", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Courses table
        columns = ("Code", "Title", "Credits", "Semester", "Students", "Schedule")
        self.faculty_courses_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.faculty_courses_tree.heading(col, text=col)
            self.faculty_courses_tree.column(col, width=120, anchor=tk.CENTER)

        self.faculty_courses_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.faculty_courses_tree, orient="vertical", command=self.faculty_courses_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.faculty_courses_tree.configure(yscrollcommand=scrollbar.set)

        # Context menu for course actions
        self.faculty_courses_context_menu = tk.Menu(self.root, tearoff=0)
        self.faculty_courses_context_menu.add_command(label="View Details", command=self.view_faculty_course_details)

        self.faculty_courses_tree.bind("<Button-3>", self.show_faculty_courses_context_menu)

        # Fetch and display faculty courses
        self.refresh_faculty_courses_list()

    def refresh_faculty_courses_list(self):
        # Clear existing data
        for item in self.faculty_courses_tree.get_children():
            self.faculty_courses_tree.delete(item)

        try:
            # Fetch and display faculty courses with enrollment counts
            self.cursor.execute('''
                SELECT c.code, c.title, c.credits, 
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester,
                       COUNT(e.id) as students,
                       GROUP_CONCAT(
                           CONCAT(sch.day, ' ', sch.start_time, '-', sch.end_time, 
                                  CASE WHEN sch.room IS NOT NULL THEN CONCAT(' (', sch.room, ')') ELSE '' END)
                           SEPARATOR '\n'
                       ) as schedule
                FROM courses c
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
                LEFT JOIN schedules sch ON sch.course_id = c.id
                WHERE c.faculty_id = %s
                GROUP BY c.id
                ORDER BY c.code
            ''', (self.current_user["id"],))

            for course in self.cursor.fetchall():
                self.faculty_courses_tree.insert("", "end", values=(
                    course["code"], course["title"], course["credits"],
                    course["semester"] or "Not assigned",
                    course["students"],
                    course["schedule"] or "Not scheduled"
                ))

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading your teaching assignments: {err}")

    def show_faculty_courses_context_menu(self, event):
        item = self.faculty_courses_tree.identify_row(event.y)
        if item:
            self.faculty_courses_tree.selection_set(item)
            self.faculty_courses_context_menu.post(event.x_root, event.y_root)

    def view_faculty_course_details(self):
        selected_item = self.faculty_courses_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a course to view details!")
            return

        course_data = self.faculty_courses_tree.item(selected_item)['values']
        course_code = course_data[0]

        try:
            # Get course details
            self.cursor.execute('''
                SELECT c.*, 
                       CONCAT(d.name, ' - Semester ', s.semester_number) as semester_name
                FROM courses c
                LEFT JOIN semesters s ON c.semester_id = s.id
                LEFT JOIN degrees d ON s.degree_id = d.id
                WHERE c.code = %s AND c.faculty_id = %s
            ''', (course_code, self.current_user["id"]))
            course = self.cursor.fetchone()

            if not course:
                messagebox.showerror("Error", "Course not found in your teaching assignments!")
                return

            # Get course schedules
            self.cursor.execute('''
                SELECT day, start_time, end_time, room
                FROM schedules
                WHERE course_id = %s
                ORDER BY 
                    CASE day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    start_time
            ''', (course["id"],))
            schedules = self.cursor.fetchall()

            # Get enrolled students
            self.cursor.execute('''
                SELECT u.full_name, e.enrollment_date, e.status
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.course_id = %s
                ORDER BY e.enrollment_date
            ''', (course["id"],))
            enrollments = self.cursor.fetchall()

            # Create details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Course Details - {course_code}")
            details_window.geometry("800x600")

            # Course info frame
            info_frame = tk.Frame(details_window)
            info_frame.pack(pady=10, fill=tk.X)

            tk.Label(info_frame, text=f"Course: {course['code']} - {course['title']}", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky="w")
            tk.Label(info_frame, text=f"Credits: {course['credits']}", font=('Arial', 12)).grid(row=1, column=0, sticky="w")
            tk.Label(info_frame, text=f"Semester: {course['semester_name'] or 'Not assigned'}", font=('Arial', 12)).grid(row=2, column=0, sticky="w")
            tk.Label(info_frame, text=f"Capacity: {course['capacity']}", font=('Arial', 12)).grid(row=3, column=0, sticky="w")

            # Description
            desc_frame = tk.Frame(details_window)
            desc_frame.pack(pady=10, fill=tk.X)

            tk.Label(desc_frame, text="Description:", font=('Arial', 12, 'bold')).pack(anchor="w")
            desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD)
            desc_text.insert("1.0", course["description"] or "No description available")
            desc_text.config(state="disabled")
            desc_text.pack(fill=tk.X)

            # Schedules
            tk.Label(details_window, text="Schedule:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if schedules:
                schedule_frame = tk.Frame(details_window)
                schedule_frame.pack(fill=tk.X)

                columns = ("Day", "Start Time", "End Time", "Room")
                schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show="headings", height=len(schedules))

                for col in columns:
                    schedule_tree.heading(col, text=col)
                    schedule_tree.column(col, width=100, anchor=tk.CENTER)

                for schedule in schedules:
                    schedule_tree.insert("", "end", values=(
                        schedule["day"], schedule["start_time"], schedule["end_time"], schedule["room"] or "N/A"
                    ))

                schedule_tree.pack(fill=tk.X)
            else:
                tk.Label(details_window, text="No schedule available", font=('Arial', 10)).pack(anchor="w")

            # Enrollments
            tk.Label(details_window, text="Enrollments:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=(10, 5))

            if enrollments:
                enroll_frame = tk.Frame(details_window)
                enroll_frame.pack(fill=tk.BOTH, expand=True)

                columns = ("Student", "Enrollment Date", "Status")
                enroll_tree = ttk.Treeview(enroll_frame, columns=columns, show="headings", height=min(5, len(enrollments)))

                for col in columns:
                    enroll_tree.heading(col, text=col)
                    enroll_tree.column(col, width=100, anchor=tk.CENTER)

                for enrollment in enrollments:
                    enroll_tree.insert("", "end", values=(
                        enrollment["full_name"], enrollment["enrollment_date"], enrollment["status"].title()
                    ))

                enroll_tree.pack(fill=tk.BOTH, expand=True)

                # Add scrollbar
                scrollbar = ttk.Scrollbar(enroll_tree, orient="vertical", command=enroll_tree.yview)
                scrollbar.pack(side="right", fill="y")
                enroll_tree.configure(yscrollcommand=scrollbar.set)
            else:
                tk.Label(details_window, text="No enrollments yet", font=('Arial', 10)).pack(anchor="w")

        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error loading course details: {err}")

    def generate_enrollment_reports(self):
        if self.current_user["role"] not in ["admin", "registrar"]:
            messagebox.showerror("Error", "You don't have permission to generate reports!")
            return

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Reports title
        tk.Label(self.main_frame, text="Enrollment Reports", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Report options frame
        options_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        options_frame.pack(pady=20)

        # Course-wise enrollment report
        ttk.Button(options_frame, text="Course-wise Enrollment", 
                 command=self.generate_course_enrollment_report, width=25).grid(row=0, column=0, padx=10, pady=10)

        # Student-wise enrollment report
        ttk.Button(options_frame, text="Student-wise Enrollment", 
                 command=self.generate_student_enrollment_report, width=25).grid(row=0, column=1, padx=10, pady=10)

        # Faculty-wise enrollment report
        ttk.Button(options_frame, text="Faculty-wise Enrollment", 
                 command=self.generate_faculty_enrollment_report, width=25).grid(row=1, column=0, padx=10, pady=10)

        # Waitlist report
        ttk.Button(options_frame, text="Waitlist Report", 
                 command=self.generate_waitlist_report, width=25).grid(row=1, column=1, padx=10, pady=10)

    def generate_course_enrollment_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Course-wise Enrollment Report", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Filter frame
        filter_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        filter_frame.pack(pady=10)

        tk.Label(filter_frame, text="Filter by Semester:", bg="#f0f8ff").grid(row=0, column=0, padx=5)
        self.course_report_semester = ttk.Combobox(filter_frame, values=["All", "Spring", "Summer", "Fall"])
        self.course_report_semester.grid(row=0, column=1, padx=5)
        self.course_report_semester.set("All")

        ttk.Button(filter_frame, text="Generate", command=self.refresh_course_enrollment_report).grid(row=0, column=2, padx=10)

        # Report table
        columns = ("Course Code", "Title", "Semester", "Faculty", "Enrolled", "Capacity", "Percentage")
        self.course_report_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.course_report_tree.heading(col, text=col)
            self.course_report_tree.column(col, width=120, anchor=tk.CENTER)

        self.course_report_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.course_report_tree, orient="vertical", command=self.course_report_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.course_report_tree.configure(yscrollcommand=scrollbar.set)

        # Generate initial report
        self.refresh_course_enrollment_report()

    def refresh_course_enrollment_report(self):
        semester = self.course_report_semester.get()

        query = '''
            SELECT c.code, c.title, 
                   CONCAT(d.name, ' - Semester ', s.semester_number) as semester,
                   u.full_name as faculty, 
                   COUNT(e.id) as enrolled, c.capacity,
                   ROUND(COUNT(e.id) * 100.0 / c.capacity, 2) as percentage
            FROM courses c
            LEFT JOIN semesters s ON c.semester_id = s.id
            LEFT JOIN degrees d ON s.degree_id = d.id
            LEFT JOIN users u ON c.faculty_id = u.id
            LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
            WHERE 1=1
        '''

        if semester != "All":
            # This is a simplified filter - in a real system you'd have semesters properly defined
            query += " AND c.code LIKE '%%%s%%'" % semester[0]

        query += '''
            GROUP BY c.id
            ORDER BY percentage DESC
        '''

        # Clear existing data
        for item in self.course_report_tree.get_children():
            self.course_report_tree.delete(item)

        try:
            # Fetch and display report data
            self.cursor.execute(query)
            for row in self.cursor.fetchall():
                self.course_report_tree.insert("", "end", values=(
                    row["code"], row["title"], row["semester"] or "Not assigned",
                    row["faculty"] or "Not assigned",
                    row["enrolled"], row["capacity"], f"{row['percentage']}%"
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def generate_student_enrollment_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Student-wise Enrollment Report", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Filter frame
        filter_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        filter_frame.pack(pady=10)

        tk.Label(filter_frame, text="Filter by Class Year:", bg="#f0f8ff").grid(row=0, column=0, padx=5)
        self.student_report_year = ttk.Combobox(filter_frame, values=["All", "Freshman", "Sophomore", "Junior", "Senior"])
        self.student_report_year.grid(row=0, column=1, padx=5)
        self.student_report_year.set("All")

        ttk.Button(filter_frame, text="Generate", command=self.refresh_student_enrollment_report).grid(row=0, column=2, padx=10)

        # Report table
        columns = ("Student ID", "Student Name", "Degree Program", "Semester", "Courses Enrolled", "Total Credits")
        self.student_report_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.student_report_tree.heading(col, text=col)
            self.student_report_tree.column(col, width=120, anchor=tk.CENTER)

        self.student_report_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.student_report_tree, orient="vertical", command=self.student_report_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.student_report_tree.configure(yscrollcommand=scrollbar.set)

        # Generate initial report
        self.refresh_student_enrollment_report()

    def refresh_student_enrollment_report(self):
        year = self.student_report_year.get()

        query = '''
            SELECT u.id, u.username, u.full_name, u.degree_program, u.current_semester,
                   COUNT(e.id) as courses_enrolled,
                   SUM(c.credits) as total_credits
            FROM users u
            LEFT JOIN enrollments e ON e.student_id = u.id AND e.status = 'registered'
            LEFT JOIN courses c ON e.course_id = c.id
            WHERE u.role = 'student'
        '''

        if year != "All":
            # This is a simplified filter - in a real system you'd have class years properly defined
            query += " AND u.username LIKE '%%%s%%'" % year[0]

        query += '''
            GROUP BY u.id
            ORDER BY total_credits DESC
        '''

        # Clear existing data
        for item in self.student_report_tree.get_children():
            self.student_report_tree.delete(item)

        try:
            # Fetch and display report data
            self.cursor.execute(query)
            for row in self.cursor.fetchall():
                self.student_report_tree.insert("", "end", values=(
                    row["username"], row["full_name"],
                    row["degree_program"] or "Not assigned",
                    row["current_semester"] or "Not assigned",
                    row["courses_enrolled"] or 0,
                    row["total_credits"] or 0
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def generate_faculty_enrollment_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Faculty-wise Enrollment Report", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Report table
        columns = ("Faculty Name", "Courses Teaching", "Total Students", "Average Enrollment")
        self.faculty_report_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.faculty_report_tree.heading(col, text=col)
            self.faculty_report_tree.column(col, width=120, anchor=tk.CENTER)

        self.faculty_report_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.faculty_report_tree, orient="vertical", command=self.faculty_report_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.faculty_report_tree.configure(yscrollcommand=scrollbar.set)

        # Generate report
        try:
            # Fetch and display report data
            self.cursor.execute('''
                SELECT u.full_name, 
                       COUNT(DISTINCT c.id) as courses_teaching,
                       COUNT(e.id) as total_students,
                       ROUND(COUNT(e.id) * 1.0 / COUNT(DISTINCT c.id), 2) as avg_enrollment
                FROM users u
                JOIN courses c ON c.faculty_id = u.id
                LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
                WHERE u.role = 'faculty'
                GROUP BY u.id
                ORDER BY total_students DESC
            ''')

            for row in self.cursor.fetchall():
                self.faculty_report_tree.insert("", "end", values=(
                    row["full_name"], row["courses_teaching"],
                    row["total_students"], row["avg_enrollment"]
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def generate_waitlist_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Waitlist Report", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Report table
        columns = ("Course Code", "Title", "Student Name", "Waitlist Date")
        self.waitlist_report_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.waitlist_report_tree.heading(col, text=col)
            self.waitlist_report_tree.column(col, width=120, anchor=tk.CENTER)

        self.waitlist_report_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.waitlist_report_tree, orient="vertical", command=self.waitlist_report_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.waitlist_report_tree.configure(yscrollcommand=scrollbar.set)

        # Generate report
        try:
            # Fetch and display report data
            self.cursor.execute('''
                SELECT c.code, c.title, u.full_name as student_name, e.enrollment_date
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                JOIN users u ON e.student_id = u.id
                WHERE e.status = 'waitlisted'
                ORDER BY c.code, e.enrollment_date
            ''')

            for row in self.cursor.fetchall():
                self.waitlist_report_tree.insert("", "end", values=(
                    row["code"], row["title"], row["student_name"], row["enrollment_date"]
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def generate_capacity_reports(self):
        if self.current_user["role"] not in ["admin", "registrar"]:
            messagebox.showerror("Error", "You don't have permission to generate reports!")
            return

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Reports title
        tk.Label(self.main_frame, text="Capacity Reports", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Report options frame
        options_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        options_frame.pack(pady=20)

        # Over-capacity courses report
        ttk.Button(options_frame, text="Over-capacity Courses", 
                 command=self.generate_over_capacity_report, width=25).grid(row=0, column=0, padx=10, pady=10)

        # Under-capacity courses report
        ttk.Button(options_frame, text="Under-capacity Courses", 
                 command=self.generate_under_capacity_report, width=25).grid(row=0, column=1, padx=10, pady=10)

        # Room utilization report
        ttk.Button(options_frame, text="Room Utilization", 
                 command=self.generate_room_utilization_report, width=25).grid(row=1, column=0, padx=10, pady=10)

    def generate_over_capacity_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Over-capacity Courses", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Report table
        columns = ("Course Code", "Title", "Enrolled", "Capacity", "Over by")
        self.over_capacity_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.over_capacity_tree.heading(col, text=col)
            self.over_capacity_tree.column(col, width=120, anchor=tk.CENTER)

        self.over_capacity_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.over_capacity_tree, orient="vertical", command=self.over_capacity_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.over_capacity_tree.configure(yscrollcommand=scrollbar.set)

        # Generate report
        try:
            # Fetch and display report data
            self.cursor.execute('''
                SELECT c.code, c.title, 
                       COUNT(e.id) as enrolled, 
                       c.capacity,
                       COUNT(e.id) - c.capacity as over_by
                FROM courses c
                JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
                GROUP BY c.id
                HAVING COUNT(e.id) > c.capacity
                ORDER BY over_by DESC
            ''')

            for row in self.cursor.fetchall():
                self.over_capacity_tree.insert("", "end", values=(
                    row["code"], row["title"], row["enrolled"], 
                    row["capacity"], row["over_by"]
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def generate_under_capacity_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Under-capacity Courses", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Threshold frame
        threshold_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        threshold_frame.pack(pady=10)

        tk.Label(threshold_frame, text="Minimum Enrollment Threshold:", bg="#f0f8ff").grid(row=0, column=0, padx=5)
        self.under_capacity_threshold = ttk.Entry(threshold_frame, width=5)
        self.under_capacity_threshold.insert(0, "5")
        self.under_capacity_threshold.grid(row=0, column=1, padx=5)

        ttk.Button(threshold_frame, text="Generate", command=self.refresh_under_capacity_report).grid(row=0, column=2, padx=10)

        # Report table
        columns = ("Course Code", "Title", "Enrolled", "Capacity", "Percentage")
        self.under_capacity_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.under_capacity_tree.heading(col, text=col)
            self.under_capacity_tree.column(col, width=120, anchor=tk.CENTER)

        self.under_capacity_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.under_capacity_tree, orient="vertical", command=self.under_capacity_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.under_capacity_tree.configure(yscrollcommand=scrollbar.set)

        # Generate initial report
        self.refresh_under_capacity_report()

    def refresh_under_capacity_report(self):
        try:
            threshold = int(self.under_capacity_threshold.get())
        except ValueError:
            messagebox.showerror("Error", "Threshold must be a number!")
            return

        # Clear existing data
        for item in self.under_capacity_tree.get_children():
            self.under_capacity_tree.delete(item)

        try:
            # Fetch and display report data
            self.cursor.execute('''
                SELECT c.code, c.title, 
                       COUNT(e.id) as enrolled, 
                       c.capacity,
                       ROUND(COUNT(e.id) * 100.0 / c.capacity, 2) as percentage
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id AND e.status = 'registered'
                GROUP BY c.id
                HAVING COUNT(e.id) < %s OR COUNT(e.id) = 0
                ORDER BY percentage
            ''', (threshold,))

            for row in self.cursor.fetchall():
                enrolled = row["enrolled"] or 0
                percentage = row["percentage"] or 0
                self.under_capacity_tree.insert("", "end", values=(
                    row["code"], row["title"], enrolled, 
                    row["capacity"], f"{percentage}%"
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def generate_room_utilization_report(self):
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Report title
        tk.Label(self.main_frame, text="Room Utilization Report", font=('Arial', 14, 'bold'), bg="#f0f8ff").pack(pady=10)

        # Report table
        columns = ("Room", "Day", "Time Slot", "Course", "Faculty")
        self.room_utilization_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.room_utilization_tree.heading(col, text=col)
            self.room_utilization_tree.column(col, width=120, anchor=tk.CENTER)

        self.room_utilization_tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.room_utilization_tree, orient="vertical", command=self.room_utilization_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.room_utilization_tree.configure(yscrollcommand=scrollbar.set)

        # Generate report
        try:
            # Fetch and display report data
            self.cursor.execute('''
                SELECT s.room, s.day, 
                       CONCAT(s.start_time, '-', s.end_time) as time_slot,
                       c.title as course,
                       u.full_name as faculty
                FROM schedules s
                JOIN courses c ON s.course_id = c.id
                LEFT JOIN users u ON c.faculty_id = u.id
                WHERE s.room IS NOT NULL
                ORDER BY s.room, 
                    CASE s.day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    s.start_time
            ''')

            for row in self.cursor.fetchall():
                self.room_utilization_tree.insert("", "end", values=(
                    row["room"], row["day"], row["time_slot"],
                    row["course"], row["faculty"] or "Not assigned"
                ))
        except pymysql.MySQLError as err:
            messagebox.showerror("Database Error", f"Error generating report: {err}")

    def logout(self):
        self.main_frame.pack_forget()
        self.current_user = None

        # Clear any open windows
        for attr in dir(self):
            if attr.endswith('_window') and hasattr(getattr(self, attr), 'winfo_exists'):
                if getattr(self, attr).winfo_exists():
                    getattr(self, attr).destroy()

        # Clear login fields
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

        self.login_frame.pack(pady=100)

if __name__ == "__main__":
    root = tk.Tk()
    app = CourseEnrollmentSystem(root)
    root.mainloop()


# In[ ]:





# In[ ]:




