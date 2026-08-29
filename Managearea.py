# manage_areas.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from database import DatabaseManager
import functools
import traceback

db = DatabaseManager()


# ============================================
# ERROR HANDLING DECORATOR
# ============================================
def handle_errors(func):
    """Decorator to handle errors in manage areas UI methods"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            
            action = func.__name__.replace("_", " ").strip().title()
            
            explanation = "An unexpected error occurred."
            
            if isinstance(e, ValueError):
                explanation = "One of the values entered isn't valid. Please check your input."
            elif isinstance(e, TypeError):
                explanation = "The program used a value the wrong way internally."
            elif isinstance(e, (IndexError, KeyError)):
                explanation = "Some data the program expected was missing or doesn't exist."
            elif isinstance(e, AttributeError):
                explanation = "A step was likely skipped before this action."
            elif isinstance(e, (FileNotFoundError, PermissionError, OSError)):
                explanation = "There was a problem reading or writing a file."
            elif type(e).__name__ in ("OperationalError", "InterfaceError", "DatabaseError",
                                      "ProgrammingError", "IntegrityError"):
                explanation = "There was a problem with the database connection or query."
            
            QMessageBox.critical(
                self,
                f"Error - {action}",
                f"Something went wrong while:\n"
                f"   {action}\n\n"
                f"What this usually means:\n"
                f"   {explanation}\n\n"
                f"Technical details:\n"
                f"   {type(e).__name__}: {e}"
            )
            return None
    return wrapper


class ManageAreas(QWidget):
    def __init__(self):
        super().__init__()

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Header
        self.main_label = QLabel("Manage Areas & Sub Areas")
        self.main_label.setObjectName("tablabels")
        self.main_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px; color: #0F172A;")
        self.main_layout.addWidget(self.main_label)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                background: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                color: #0F172A;
            }
            QTabBar::tab:selected {
                background: #093573;
                color: white;
                border-color: #093573;
            }
            QTabBar::tab:hover:!selected {
                background: #E2E8F0;
            }
        """)

        # Create tabs
        self.areas_tab = QWidget()
        self.subareas_tab = QWidget()

        self.tab_widget.addTab(self.areas_tab, "Areas")
        self.tab_widget.addTab(self.subareas_tab, "Sub Areas")

        # Setup each tab
        self.setup_areas_tab()
        self.setup_subareas_tab()

        self.main_layout.addWidget(self.tab_widget)

        # Setup Enter key navigation
        self.setup_enter_navigation()

    def setup_enter_navigation(self):
        """Install event filter on all input widgets for Enter key navigation"""
        for widget in self.findChildren(QLineEdit):
            widget.installEventFilter(self)
        for widget in self.findChildren(QComboBox):
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle Enter key press to move to next widget"""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.focusNextChild()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle Enter key press at widget level"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.focusNextChild()
        else:
            super().keyPressEvent(event)

    # =========================================================
    # AREAS TAB
    # =========================================================

    @handle_errors
    def setup_areas_tab(self):
        """Setup the Areas tab with input form and table"""
        layout = QHBoxLayout(self.areas_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Left side - Input form
        input_widget = QWidget()
        input_widget.setFixedWidth(350)
        input_widget.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        input_layout = QVBoxLayout(input_widget)
        input_layout.setSpacing(15)

        # Form title
        form_title = QLabel("Area Details")
        form_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        input_layout.addWidget(form_title)

        # ID field (hidden/readonly)
        self.area_id_widget, self.area_id_input = self.create_input_field("ID")
        self.area_id_input.setEnabled(False)
        input_layout.addWidget(self.area_id_widget)

        # Area name field
        self.area_name_widget, self.area_name_input = self.create_input_field("Area Name *")
        self.area_name_input.setPlaceholderText("Enter area name...")
        input_layout.addWidget(self.area_name_widget)

        # Active status
        self.area_active_check = QCheckBox("Active")
        self.area_active_check.setChecked(True)
        self.area_active_check.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F172A;")
        input_layout.addWidget(self.area_active_check)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.area_save_btn = QPushButton("Save")
        self.area_save_btn.setFixedHeight(40)
        self.area_save_btn.setStyleSheet("""
            QPushButton {
                background: #22C55E;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #16A34A;
            }
            QPushButton:pressed {
                background: #15803D;
            }
        """)
        self.area_save_btn.clicked.connect(self.save_area)

        self.area_clear_btn = QPushButton("Clear")
        self.area_clear_btn.setFixedHeight(40)
        self.area_clear_btn.setStyleSheet("""
            QPushButton {
                background: #F59E0B;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #D97706;
            }
            QPushButton:pressed {
                background: #B45309;
            }
        """)
        self.area_clear_btn.clicked.connect(self.clear_area_form)

        button_layout.addWidget(self.area_save_btn)
        button_layout.addWidget(self.area_clear_btn)
        input_layout.addLayout(button_layout)

        input_layout.addStretch()

        # Right side - Table with search
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(10)

        # Search bar (NO DELETE BUTTON)
        search_layout = QHBoxLayout()
        self.area_search_input = QLineEdit()
        self.area_search_input.setPlaceholderText("Search areas...")
        self.area_search_input.setFixedHeight(35)
        self.area_search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E2E8F0;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #093573;
            }
        """)

        self.area_refresh_btn = QPushButton("Refresh")
        self.area_refresh_btn.setFixedSize(120, 35)
        self.area_refresh_btn.setStyleSheet("""
            QPushButton {
                background: #093573;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #0B4A8A;
            }
        """)
        self.area_refresh_btn.clicked.connect(self.refresh_areas)

        search_layout.addWidget(self.area_search_input)
        search_layout.addWidget(self.area_refresh_btn)
        table_layout.addLayout(search_layout)

        # Table view
        self.area_table = QTableView()
        self.area_table.setAlternatingRowColors(True)
        self.area_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.area_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.area_table.verticalHeader().setVisible(False)
        self.area_table.setStyleSheet("""
            QTableView {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                gridline-color: #F1F5F9;
                background: white;
            }
            QTableView::item {
                padding: 8px;
                color: #0F172A;
            }
            QTableView::item:selected {
                background: #BFDBFE;
                color: #0F172A;
            }
            QHeaderView::section {
                background-color: #093573;
                color: white;
                padding: 10px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background-color: #0B4A8A;
            }
        """)

        # Setup model and proxy for areas
        self.area_model = AreaTableModel()
        self.area_proxy = QSortFilterProxyModel()
        self.area_proxy.setSourceModel(self.area_model)
        self.area_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.area_proxy.setFilterKeyColumn(1)  # Search by area name

        self.area_table.setModel(self.area_proxy)
        self.area_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.area_table.horizontalHeader().setVisible(True)

        # Connect signals
        self.area_search_input.textChanged.connect(self.area_proxy.setFilterFixedString)
        self.area_table.clicked.connect(self.on_area_select)

        table_layout.addWidget(self.area_table)

        # Add to main layout
        layout.addWidget(input_widget, 1)
        layout.addWidget(table_widget, 3)

    # =========================================================
    # SUB AREAS TAB
    # =========================================================

    @handle_errors
    def setup_subareas_tab(self):
        """Setup the Sub Areas tab with input form and table"""
        layout = QHBoxLayout(self.subareas_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Left side - Input form
        input_widget = QWidget()
        input_widget.setFixedWidth(400)
        input_widget.setStyleSheet("""
            QWidget {
                background: #F8FAFC;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        input_layout = QVBoxLayout(input_widget)
        input_layout.setSpacing(15)

        # Form title
        form_title = QLabel("Sub Area Details")
        form_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        input_layout.addWidget(form_title)

        # ID field (hidden/readonly)
        self.subarea_id_widget, self.subarea_id_input = self.create_input_field("ID")
        self.subarea_id_input.setEnabled(False)
        input_layout.addWidget(self.subarea_id_widget)

        # Area selection (parent area)
        self.subarea_area_widget, self.subarea_area_combo = self.create_combo_field("Area *")
        self.subarea_area_combo.addItem("Select Area")
        input_layout.addWidget(self.subarea_area_widget)

        # Sub area name field
        self.subarea_name_widget, self.subarea_name_input = self.create_input_field("Sub Area*")
        self.subarea_name_input.setPlaceholderText("Enter sub area name...")
        input_layout.addWidget(self.subarea_name_widget)

        # Active status
        self.subarea_active_check = QCheckBox("Active")
        self.subarea_active_check.setChecked(True)
        self.subarea_active_check.setStyleSheet("font-size: 14px; font-weight: 600; color: #0F172A;")
        input_layout.addWidget(self.subarea_active_check)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.subarea_save_btn = QPushButton("Save")
        self.subarea_save_btn.setFixedHeight(40)
        self.subarea_save_btn.setStyleSheet("""
            QPushButton {
                background: #22C55E;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #16A34A;
            }
            QPushButton:pressed {
                background: #15803D;
            }
        """)
        self.subarea_save_btn.clicked.connect(self.save_subarea)

        self.subarea_clear_btn = QPushButton("Clear")
        self.subarea_clear_btn.setFixedHeight(40)
        self.subarea_clear_btn.setStyleSheet("""
            QPushButton {
                background: #F59E0B;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #D97706;
            }
            QPushButton:pressed {
                background: #B45309;
            }
        """)
        self.subarea_clear_btn.clicked.connect(self.clear_subarea_form)

        button_layout.addWidget(self.subarea_save_btn)
        button_layout.addWidget(self.subarea_clear_btn)
        input_layout.addLayout(button_layout)

        input_layout.addStretch()

        # Right side - Table with search
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(10)

        # Search bar (NO DELETE BUTTON)
        search_layout = QHBoxLayout()
        self.subarea_search_input = QLineEdit()
        self.subarea_search_input.setPlaceholderText("Search sub areas...")
        self.subarea_search_input.setFixedHeight(35)
        self.subarea_search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E2E8F0;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #093573;
            }
        """)

        self.subarea_refresh_btn = QPushButton("Refresh")
        self.subarea_refresh_btn.setFixedSize(120, 35)
        self.subarea_refresh_btn.setStyleSheet("""
            QPushButton {
                background: #093573;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #0B4A8A;
            }
        """)
        self.subarea_refresh_btn.clicked.connect(self.refresh_subareas)

        search_layout.addWidget(self.subarea_search_input)
        search_layout.addWidget(self.subarea_refresh_btn)
        table_layout.addLayout(search_layout)

        # Table view
        self.subarea_table = QTableView()
        self.subarea_table.setAlternatingRowColors(True)
        self.subarea_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.subarea_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.subarea_table.verticalHeader().setVisible(False)
        self.subarea_table.setStyleSheet("""
            QTableView {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                gridline-color: #F1F5F9;
                background: white;
            }
            QTableView::item {
                padding: 8px;
                color: #0F172A;
            }
            QTableView::item:selected {
                background: #BFDBFE;
                color: #0F172A;
            }
            QHeaderView::section {
                background-color: #093573;
                color: white;
                padding: 10px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background-color: #0B4A8A;
            }
        """)

        # Setup model and proxy for subareas
        self.subarea_model = SubAreaTableModel()
        self.subarea_proxy = QSortFilterProxyModel()
        self.subarea_proxy.setSourceModel(self.subarea_model)
        self.subarea_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.subarea_proxy.setFilterKeyColumn(2)  # Search by sub area name

        self.subarea_table.setModel(self.subarea_proxy)
        self.subarea_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.subarea_table.horizontalHeader().setVisible(True)

        # Connect signals
        self.subarea_search_input.textChanged.connect(self.subarea_proxy.setFilterFixedString)
        self.subarea_table.clicked.connect(self.on_subarea_select)

        table_layout.addWidget(self.subarea_table)

        # Add to main layout
        layout.addWidget(input_widget, 1)
        layout.addWidget(table_widget, 3)

        # Load area combobox data
        self.load_area_combo()

    # =========================================================
    # HELPER METHODS
    # =========================================================

    def create_input_field(self, label):
        """Create a labeled input field."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label_widget = QLabel(label)
        label_widget.setFixedWidth(100)
        label_widget.setStyleSheet("font-weight: 600; font-size: 14px; color: #0F172A;")

        input_field = QLineEdit()
        input_field.setFixedHeight(35)
        input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E2E8F0;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 14px;
                color: #0F172A;
                background: white;
            }
            QLineEdit:focus {
                border-color: #093573;
            }
            QLineEdit:disabled {
                background: #F1F5F9;
                color: #64748B;
            }
        """)

        layout.addWidget(label_widget)
        layout.addWidget(input_field)

        return widget, input_field

    def create_combo_field(self, label):
        """Create a labeled combo box field."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label_widget = QLabel(label)
        label_widget.setFixedWidth(100)
        label_widget.setStyleSheet("font-weight: 600; font-size: 14px; color: #0F172A;")

        combo_box = QComboBox()
        combo_box.setFixedHeight(35)
        combo_box.setStyleSheet("""
            QComboBox {
                border: 2px solid #E2E8F0;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 14px;
                color: #0F172A;
                background: white;
            }
            QComboBox:focus {
                border-color: #093573;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """)

        layout.addWidget(label_widget)
        layout.addWidget(combo_box)

        return widget, combo_box

    @handle_errors
    def load_area_combo(self):
        """Load areas into the subarea combo box."""
        try:
            conn, cursor = db.get_connection()
            cursor.execute("SELECT id, area_name FROM areas ORDER BY area_name")
            areas = cursor.fetchall()
            self.subarea_area_combo.clear()
            self.subarea_area_combo.addItem("Select Area", None)
            
            if areas:
                for area in areas:
                    self.subarea_area_combo.addItem(area['area_name'], area['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load areas: {str(e)}")

    # =========================================================
    # AREA CRUD OPERATIONS
    # =========================================================

    @handle_errors
    def save_area(self, checked=False):
        """Save or update area."""
        try:
            area_id = self.area_id_input.text().strip()
            area_name = self.area_name_input.text().strip()
            is_active = self.area_active_check.isChecked()

            if not area_name:
                QMessageBox.warning(self, "Validation Error", "Area name is required!")
                return

            conn, cursor = db.get_connection()
            
            # Check if area name already exists (except current)
            if area_id:
                cursor.execute("SELECT id FROM areas WHERE area_name = %s AND id != %s", (area_name, int(area_id)))
            else:
                cursor.execute("SELECT id FROM areas WHERE area_name = %s", (area_name,))
            
            existing = cursor.fetchone()
            if existing:
                QMessageBox.warning(self, "Duplicate Error", "Area name already exists!")
                return

            if area_id:
                # Update
                query = "UPDATE areas SET area_name = %s, is_active = %s WHERE id = %s"
                params = (area_name, is_active, int(area_id))
                message = "Area updated successfully!"
            else:
                # Insert
                query = "INSERT INTO areas (area_name, is_active) VALUES (%s, %s)"
                params = (area_name, is_active)
                message = "Area added successfully!"

            cursor.execute(query, params)
            conn.commit()
            
            QMessageBox.information(self, "Success", message)
            self.clear_area_form()
            self.refresh_areas()
            self.load_area_combo()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    @handle_errors
    def refresh_areas(self):
        """Refresh area table."""
        self.area_model.load_data()
        self.area_search_input.clear()
        self.area_table.clearSelection()

    @handle_errors
    def clear_area_form(self):
        """Clear area form."""
        self.area_id_input.clear()
        self.area_name_input.clear()
        self.area_active_check.setChecked(True)
        self.area_name_input.setFocus()

    @handle_errors
    def on_area_select(self, index):
        """Load selected area into form."""
        row = self.area_proxy.mapToSource(index).row()
        data = self.area_model._data[row]

        self.area_id_input.setText(str(data['id']))
        self.area_name_input.setText(str(data['area_name']))
        self.area_active_check.setChecked(data['is_active'] == 1)

    # =========================================================
    # SUB AREA CRUD OPERATIONS
    # =========================================================

    @handle_errors
    def save_subarea(self, checked=False):
        """Save or update subarea."""
        try:
            subarea_id = self.subarea_id_input.text().strip()
            area_id = self.subarea_area_combo.currentData()
            subarea_name = self.subarea_name_input.text().strip()
            is_active = self.subarea_active_check.isChecked()

            if not area_id:
                QMessageBox.warning(self, "Validation Error", "Please select an area!")
                return

            if not subarea_name:
                QMessageBox.warning(self, "Validation Error", "Sub area name is required!")
                return

            conn, cursor = db.get_connection()
            
            # Check if subarea name already exists for this area (except current)
            if subarea_id:
                cursor.execute(
                    "SELECT id FROM sub_areas WHERE sub_area_name = %s AND area_id = %s AND id != %s",
                    (subarea_name, area_id, int(subarea_id))
                )
            else:
                cursor.execute(
                    "SELECT id FROM sub_areas WHERE sub_area_name = %s AND area_id = %s",
                    (subarea_name, area_id)
                )
            
            existing = cursor.fetchone()
            if existing:
                QMessageBox.warning(self, "Duplicate Error", "Sub area name already exists in this area!")
                return

            # Get area_name for the foreign key constraint
            cursor.execute("SELECT area_name FROM areas WHERE id = %s", (area_id,))
            area_result = cursor.fetchone()
            area_name = area_result['area_name'] if area_result else ""

            if subarea_id:
                # Update
                query = "UPDATE sub_areas SET area_id = %s, area_name = %s, sub_area_name = %s, is_active = %s WHERE id = %s"
                params = (area_id, area_name, subarea_name, is_active, int(subarea_id))
                message = "Sub area updated successfully!"
            else:
                # Insert
                query = "INSERT INTO sub_areas (area_id, area_name, sub_area_name, is_active) VALUES (%s, %s, %s, %s)"
                params = (area_id, area_name, subarea_name, is_active)
                message = "Sub area added successfully!"

            cursor.execute(query, params)
            conn.commit()
            
            QMessageBox.information(self, "Success", message)
            self.clear_subarea_form()
            self.refresh_subareas()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    @handle_errors
    def refresh_subareas(self):
        """Refresh subarea table."""
        self.subarea_model.load_data()
        self.subarea_search_input.clear()
        self.subarea_table.clearSelection()

    @handle_errors
    def clear_subarea_form(self):
        """Clear subarea form."""
        self.subarea_id_input.clear()
        self.subarea_area_combo.setCurrentIndex(0)
        self.subarea_name_input.clear()
        self.subarea_active_check.setChecked(True)
        self.subarea_name_input.setFocus()

    @handle_errors
    def on_subarea_select(self, index):
        """Load selected subarea into form."""
        row = self.subarea_proxy.mapToSource(index).row()
        data = self.subarea_model._data[row]

        self.subarea_id_input.setText(str(data['id']))
        
        # Set area combo
        idx = self.subarea_area_combo.findData(data['area_id'])
        if idx >= 0:
            self.subarea_area_combo.setCurrentIndex(idx)
        
        self.subarea_name_input.setText(str(data['sub_area_name']))
        self.subarea_active_check.setChecked(data['is_active'] == 1)


# =========================================================
# TABLE MODELS
# =========================================================

class AreaTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._headers = ["ID", "Area Name", "Active"]
        self._data = []
        self.load_data()

    @handle_errors
    def load_data(self):
        """Load data from database."""
        self.beginResetModel()
        try:
            conn, cursor = db.get_connection()
            cursor.execute("SELECT id, area_name, is_active FROM areas ORDER BY area_name")
            result = cursor.fetchall()
            self._data = result if result else []
        except Exception as e:
            print(f"Error loading areas: {e}")
            self._data = []
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            try:
                row = index.row()
                col = index.column()
                key = ["id", "area_name", "is_active"][col]
                value = self._data[row][key]
                
                if col == 2:  # Active column
                    return "✓" if value == 1 else "✗"
                
                return str(value) if value is not None else ""
            except (IndexError, KeyError):
                return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section] if section < len(self._headers) else ""
            return section + 1
        return None


class SubAreaTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._headers = ["ID", "Area", "Sub Area Name", "Active"]
        self._data = []
        self.load_data()

    @handle_errors
    def load_data(self):
        """Load data from database with join to get area name."""
        self.beginResetModel()
        try:
            query = """
                SELECT s.id, s.area_id, a.area_name, s.sub_area_name, s.is_active 
                FROM sub_areas s
                LEFT JOIN areas a ON s.area_id = a.id
                ORDER BY a.area_name, s.sub_area_name
            """
            conn, cursor = db.get_connection()
            cursor.execute(query)
            result = cursor.fetchall()
            self._data = result if result else []
        except Exception as e:
            print(f"Error loading subareas: {e}")
            self._data = []
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            try:
                row = index.row()
                col = index.column()
                
                if col == 0:  # ID
                    return str(self._data[row]['id'])
                elif col == 1:  # Area
                    return str(self._data[row]['area_name']) if self._data[row]['area_name'] else ""
                elif col == 2:  # Sub Area Name
                    return str(self._data[row]['sub_area_name'])
                elif col == 3:  # Active
                    return "✓" if self._data[row]['is_active'] == 1 else "✗"
                
                return ""
            except (IndexError, KeyError):
                return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section] if section < len(self._headers) else ""
            return section + 1
        return None