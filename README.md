
# 🎓 Course Enrollment System

A **Tkinter + MySQL based desktop application** that allows students to enroll in courses, view enrolled courses, and manage their academic records with a user-friendly interface.

## ✨ Features

* 🖥️ GUI Interface using Tkinter
* 🔐 Authentication with MySQL database
* 📚 Course Management – Add, enroll, view courses
* 👤 Student Records – Manage student data efficiently
* 📊 Clean Dashboard with organized sections
* ⚡ Error handling for invalid inputs and database connectivity issues

## 📂 Project Structure

```
task-management-system/
│-- CourseEnrollmentSystem.py      # Main application
│-- README.md                      # Project documentation
```

## 🛠️ Requirements

Make sure you have the following installed:

* Python 3.x
* Tkinter (comes with Python)
* MySQL Connector for Python

Install MySQL connector:

```bash
pip install mysql-connector-python
```

## 🚀 How to Run

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/task-management-system.git
   cd task-management-system
   ```
2. Run the application:

   ```bash
   python CourseEnrollmentSystem.py
   ```

## ⚙️ Database Setup

1. Create a MySQL database (e.g., `course_system`).
2. Create required tables for **students** and **courses**.
3. Update your database credentials in the code:

   ```python
   self.conn = mysql.connector.connect(
       host="localhost",
       user="your-username",
       password="your-password",
       database="course_system"
   )
   ```

## 📸 Screenshots

*Add screenshots of your interface here.*

## 🙌 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss.

## 📜 License

This project is licensed under the MIT License.

---

Ahmed, ab tum sirf is text ko `README.md` file me paste karke repo me daal do. ✅
