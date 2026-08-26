from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
from Customers import Customers
from Vendors import Vendors
from Salemans import Salemans
from Managearea import ManageAreas


def load_stylesheet():
    try:
        with open("style.qss", 'r', encoding="utf-8") as f:
            return f.read()
    except Exception:
        print("Failed to Load Style Sheet.")
        return ""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/icons/icon.png"))
        self.setWindowTitle("Business Partners")
        self.setMinimumSize(1200, 750)
        
        # Main Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(60)
        self.header_widget.setObjectName("MainLabel")
        self.header_layout = QHBoxLayout(self.header_widget)
        
        self.header_label = QLabel("BUSINESS PARTNERS")
        self.header_label.setObjectName("mainlabel")
        self.header_layout.addWidget(self.header_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Content
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(300)
        
        self.tab_items = ['Customers', 'Vendors', 'Salemans', 'Manage Areas']
        for tab in self.tab_items:
            self.sidebar.addItem(QListWidgetItem(tab))

        # Content Stack
        self.content_stack = QStackedWidget()
        self.customer_widget = Customers()
        self.vendor_widget = Vendors()
        self.saleman_widget = Salemans()
        self.area_widget = ManageAreas()

        self.content_stack.addWidget(self.customer_widget)
        self.content_stack.addWidget(self.vendor_widget)
        self.content_stack.addWidget(self.saleman_widget)
        self.content_stack.addWidget(self.area_widget)

        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)

        self.content_layout.addWidget(self.sidebar)
        self.content_layout.addWidget(self.content_stack)

        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.content_widget)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)
        
        self.sidebar.setCurrentRow(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())
    window = MainWindow()
    window.show()
    app.exec()