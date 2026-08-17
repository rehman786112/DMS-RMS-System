from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from databasemanager import DatabaseManager
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # database 
        self.db = DatabaseManager()
        self.data = None
        # Window setting
        self.setWindowTitle("DMS-RMS System")
        self.setFixedSize(600,500)
        self.setWindowIcon(QIcon("assets/icons/icon.png"))
        # Layout
        self.layout = QVBoxLayout()
        # Main Label
        self.label = QLabel("DMS/RMS Admin Authority")
        self.get_button = QPushButton("Check Admins")
        self.get_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.get_button.clicked.connect(self.get_admin_data)
        # Data Widget
        self.data_widget = QWidget()
        self.data_widget_layout = QVBoxLayout(self.data_widget)

        self.data_scroll = QScrollArea()
        self.data_scroll.setWidgetResizable(True)
        self.data_scroll.setWidget(self.data_widget)
        
        self.no_data_label = QLabel("No Data Available")
        if self.data == None or len(self.data) == 0:
            self.data_widget_layout.addWidget(self.no_data_label)
        self.layout.addWidget(self.label, alignment = Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.get_button,alignment = Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.data_scroll)
        # central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
    def admin_data(self,_name,_password):
        widget = QWidget()
        widget.setFixedHeight(50)
        widget.setStyleSheet("""
        QLabel{
            font-size: 20px;
            border:none;
            color:white;
        }
        QWidget{
            border:2px solid grey;
            border-radius:10px;
            background-color:black;
        }
        """)
        layout = QHBoxLayout(widget)

        admin_name = QLabel(f"Name: {_name}")
        admin_pass = QLabel(f"Password: {_password}")
        layout.addWidget(admin_name)
        layout.addWidget(admin_pass)

        return widget
    def get_admin_data(self):
        self.data = self.db.admin_data()
        if len(self.data) == 0:
            return
        for i in self.data:
            print(f"Name: {i['ad_name']}, Password: {i['password']}")
            _name = i['ad_name']
            _password = i['password']
            widget = self.admin_data(_name,_password)
            self.data_widget_layout.removeWidget(self.no_data_label)
            self.no_data_label.deleteLater()
            self.data_widget_layout.addWidget(widget)

app = QApplication([])

window = MainWindow()
window.show()

app.exec()