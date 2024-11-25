from PyQt6.QtWidgets import QApplication, QGridLayout, QVBoxLayout, QWidget, QLabel, QLineEdit, \
    QPushButton, QMainWindow, QTableWidget, QTableWidgetItem, QDialog, QComboBox, QToolBar, \
    QStatusBar, QMessageBox
from PyQt6.QtGui import QAction, QIcon
# for the matchflagstring method
from PyQt6.QtCore import Qt
import sys
import sqlite3
# Connects to mysql server, and this app is the client
import mysql.connector
# Better to use QMainWindow as you get things like the top menu bar


class Database:
    def __init__(self, host="localhost", user="root", password="###", database="school"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database


    def connection(self):
        connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        return connection


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Management")
        # Set the min. size of window so no need to expand.
        self.setMinimumSize(800,600)

        # Add menu bar
        file_menu_item = self.menuBar().addMenu("&File")
        help_menu_item = self.menuBar().addMenu("&Help")
        edit_menu_item = self.menuBar().addMenu("&Edit")

        # Create Actions
        add_student_action = QAction(QIcon("icons/add.png"), "Add Student", self)
        add_student_action.triggered.connect(self.insert)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.about)
        search_action = QAction(QIcon("icons/search.png"), "Search", self)
        search_action.triggered.connect(self.search)

        # Add actions to menu items
        file_menu_item.addAction(add_student_action)
        help_menu_item.addAction(about_action)
        edit_menu_item.addAction(search_action)

        # Add table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(("ID", "Name", "Course", "Mobile"))
        self.table.verticalHeader().setVisible(False)
        self.setCentralWidget(self.table)


        #Add a toolbar
        toolbar = QToolBar()
        toolbar.setMovable(True)
        toolbar.addAction(add_student_action)
        toolbar.addAction(search_action)
        self.addToolBar(toolbar)


        # Add a status bar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        # Detect when a cell is clicked:
        self.table.cellClicked.connect(self.cell_clicked)


    def about(self):
        dialog = AboutDialog()
        dialog.exec()


    def load_data(self):
        connection = Database().connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM students")
        result = cursor.fetchall()
        # sets the row count back to 0 every time instead of re-adding...
        # the rows everytime you open the app.
        self.table.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        cursor.close()
        connection.close()


    def insert(self):
        dialog = InsertDialog()
        dialog.exec()


    def search(self):
        dialog = SearchDialog()
        dialog.exec()


    # When cell is clicked, status bar with edit & delete buttons appear
    def cell_clicked(self):
        children = self.findChildren(QPushButton)
        if children:
            for child in children:
                self.statusbar.removeWidget(child)

        edit_button = QPushButton("Edit Record")
        self.statusbar.addWidget(edit_button)
        edit_button.clicked.connect(self.edit)

        delete_button = QPushButton("Delete Record")
        self.statusbar.addWidget(delete_button)
        delete_button.clicked.connect(self.delete)



    def edit(self):
        dialog = EditDialog()
        dialog.exec()


    def delete(self):
        dialog = DeleteDialog()
        dialog.exec()


class AboutDialog(QMessageBox):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About")
        content = """
        This app records student information in an SQL database.
        It was created through the 'Python in 60 days' course.
        Feel free to modify it.
        """
        self.setText(content)


class InsertDialog (QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Student")

        layout = QVBoxLayout()

        # Type in student name
        self.stud_name = QLineEdit()
        self.stud_name.setPlaceholderText("Name")
        layout.addWidget(self.stud_name)

        # Choose the course
        self.course_name = QComboBox()
        courses = ["Biology", "Astrology", "Maths", "Physics"]
        self.course_name.addItems(courses)
        self.course_name.setPlaceholderText("Course")
        layout.addWidget(self.course_name)

        # Type in mobile
        self.mobile = QLineEdit()
        self.mobile.setPlaceholderText("Mobile")
        layout.addWidget(self.mobile)

        # Submit button
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.add_student)
        layout.addWidget(submit_button)

        self.setLayout(layout)


    def add_student(self):
        name = self.stud_name.text()
        course = self.course_name.itemText(self.course_name.currentIndex())
        mobile = self.mobile.text()
        connection = Database().connection()
        # Have to create a cursor object when adding to a database
        cursor = connection.cursor()
        cursor.execute("INSERT into students (name, course, mobile) VALUES (%s, %s, %s)",
                       (name, course, mobile))
        connection.commit()
        cursor.close()
        connection.close()
        Window.load_data()


class SearchDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Search")

        layout = QVBoxLayout()

        # User types in student name
        self.stud_name = QLineEdit()
        self.stud_name.setPlaceholderText("Name")
        layout.addWidget(self.stud_name)

        # Search button
        search_button = QPushButton("Submit")
        search_button.clicked.connect(self.search_student)
        layout.addWidget(search_button)

        self.setLayout(layout)


    def search_student(self):
        name = self.stud_name.text()
        connection = Database().connection()
        cursor = connection.cursor()
        result = cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
        rows = list(result)
        # Qt.MatchFlag...searches for name and gives matched results
        items = Window.table.findItems(name, Qt.MatchFlag.MatchFixedString)
        for item in items:
            Window.table.item(item.row(),1).setSelected(True)

        cursor.close()
        connection.close()


class EditDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Update Student")

        layout = QVBoxLayout()

        index = Window.table.currentRow()
        self.stud_id = Window.table.item(index, 0).text()
        # Update student name
        student_name = Window.table.item(index, 1).text()
        self.stud_name = QLineEdit(student_name)
        layout.addWidget(self.stud_name)

        # Update the course
        # Note course_name is different to self.course_name
        course_name = Window.table.item(index, 2).text()
        self.course_name = QComboBox()
        courses = ["Biology", "Astrology", "Maths", "Physics"]
        self.course_name.addItems(courses)
        self.course_name.setCurrentText(course_name)
        layout.addWidget(self.course_name)

        # Update mobile
        mobile = Window.table.item(index, 3).text()
        self.mobile = QLineEdit(mobile)
        layout.addWidget(self.mobile)

        # Submit button
        submit_button = QPushButton("Update")
        submit_button.clicked.connect(self.update_student)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def update_student(self):
        connection = Database().connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE students SET name = %s, course = %s, mobile = %s WHERE id = %s",
                       (self.stud_name.text(),
                        self.course_name.itemText(self.course_name.currentIndex()),
                        self.mobile.text(),
                        self.stud_id))
        connection.commit()
        cursor.close()
        connection.close()
        Window.load_data()


class DeleteDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Delete Record")

        layout = QGridLayout()
        confirmation = QLabel("Are you sure want to delete the student record?")
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")

        layout.addWidget(confirmation, 0, 0, 1, 2)
        layout.addWidget(yes_button, 1, 0)
        layout.addWidget(no_button, 1, 1)
        self.setLayout(layout)

        yes_button.clicked.connect(self.delete_student)

    def delete_student(self):
        # Get student id
        index = Window.table.currentRow()
        stud_id = Window.table.item(index, 0).text()

        # Delete in sql database, put comma after stud_id below to make it a tuple
        connection = Database().connection()
        cursor = connection.cursor()
        cursor.execute("DELETE from students WHERE id = %s", (stud_id,))
        connection.commit()
        cursor.close()
        connection.close()
        Window.load_data()

        self.close()

        confirmation_widget = QMessageBox()
        confirmation_widget.setWindowTitle("Success")
        confirmation_widget.setText("Record was deleted successfully.")
        confirmation_widget.exec()


app = QApplication(sys.argv)
Window = MainWindow()
Window.show()
Window.load_data()
sys.exit(app.exec())