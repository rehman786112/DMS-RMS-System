# Add_Types.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from database import DatabaseManager
import functools
import traceback
from decimal import Decimal, InvalidOperation

db = DatabaseManager()


# ============================================
# ERROR HANDLING DECORATOR
# ============================================
def handle_errors(func):
    """Decorator to handle errors in product UI methods"""
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
            elif isinstance(e, InvalidOperation):
                explanation = "Invalid number format. Please enter a valid decimal number."

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


class AddDetails(QWidget):
    save_signal = pyqtSignal()
    
    def __init__(self, sender_name):
        super().__init__()
        self.setWindowTitle(f"Add {sender_name.capitalize()}")
        self.setFixedSize(700, 600)
        self.conn, self._cursor = db.get_connection()
        self.setWindowIcon(QIcon("assets/icons/icon.png"))
        self.sender_name = sender_name
        self.vendor_type_id = None      # For vendor_type
        self.salesmen_type_id = None    # For salesmen_type
        self.customer_type_id = None    # For customer_type
        self.size_id = None
        self.row_data = []
        self._is_saving = False

        try:
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(0, 0, 0, 0)

            self.label = self.create_header(f"{sender_name.capitalize()}", "MainLabel", '25px')
            self.label.setFixedHeight(60)

            self._data = QWidget()
            self._data_layout = QHBoxLayout(self._data)

            self._detail_widget = QWidget()
            self._detail_widget.setObjectName("input_widget")
            self._detail_widget.setFixedSize(300, 250)
            self._detail_layout = QVBoxLayout(self._detail_widget)
            self._detail_layout.addStretch()
            self._detail_layout.addSpacing(10)

            self.detail_label_widget = self.create_header(f"{sender_name.capitalize()} Details", "MainLabel", '20px')
            self.detail_label_widget.setFixedSize(260, 30)
            self._detail_layout.addWidget(self.detail_label_widget)

            self.is_active_widget = QCheckBox("Active")
            self.is_active_widget.setChecked(True)
            self._detail_layout.addWidget(self.is_active_widget, alignment=Qt.AlignmentFlag.AlignRight)

            self.name_input_widget, self.name_input_value = self.create_input_field("Name")
            self.name_input_value.textChanged.connect(lambda: self.name_input_value.setText(self.name_input_value.text().upper()))
            self._detail_layout.addWidget(self.name_input_widget)

            # Determine which table to use
            if sender_name == 'vendor_type':
                self.data_model = TableModel("SELECT * FROM vendor_type")
                
            elif sender_name == 'salesmen_type':
                self.data_model = TableModel("SELECT * FROM salesmen_type")
                
            elif sender_name == 'customer_type':
                self.data_model = TableModel("SELECT * FROM customer_type")
                
            elif sender_name == 'size':
                self.data_model = TableModel("SELECT * FROM prd_size")

            self.existing_data_view = QTableView()
            self.existing_data_view.setWordWrap(True)
            self.existing_data_view.setAlternatingRowColors(True)
            self.existing_data_view.setModel(self.data_model)

            # Set column widths to fit properly
            header = self.existing_data_view.horizontalHeader()
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID column
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Name column
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Active column

            self.existing_data_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.existing_data_view.verticalHeader().setVisible(False)
            self.existing_data_view.clicked.connect(self.on_row_click)

            self._data_layout.addWidget(self._detail_widget)
            self._data_layout.addWidget(self.existing_data_view)
            self.layout.addWidget(self.label)
            self.layout.addWidget(self._data)
            self.footer_window()
            self.setup_enter_navigation()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize AddDetails window:\n\n{type(e).__name__}: {e}"
            )

    def create_header(self, label_name, object_name, font_size):
        header = QWidget()
        header.setObjectName(object_name)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        label = QLabel(label_name)
        label.setStyleSheet(f"color:white; font-weight:bold; font-size:{font_size}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(label)
        return header

    def create_input_field(self, label_name):
        input_widget = QWidget()
        input_widget_layout = QHBoxLayout(input_widget)
        input_widget_layout.setSpacing(10)
        input_widget_layout.setContentsMargins(20, 0, 0, 0)
        input_widget_layout.addStretch()

        input_label = QLabel(label_name)
        input_label.setStyleSheet("color:black; font-size:16px; font-weight:700")

        line_edit = QLineEdit()
        line_edit.setFixedSize(180, 30)
        line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        input_widget_layout.addWidget(input_label)
        input_widget_layout.addWidget(line_edit)

        return input_widget, line_edit

    def setup_enter_navigation(self):
        for widget in self.findChildren(QLineEdit):
            if widget.isEnabled():
                widget.installEventFilter(self)
        for widget in self.findChildren(QComboBox):
            if widget.isEnabled():
                widget.installEventFilter(self)
        self.existing_data_view.installEventFilter(self)

    def is_widget_editable(self, widget):
        if not widget.isEnabled():
            return False
        if isinstance(widget, QLineEdit):
            return not widget.isReadOnly()
        if isinstance(widget, QComboBox):
            return widget.isEnabled()
        return True

    def find_next_editable_widget(self, current_widget):
        focus_widgets = []
        for widget in self.findChildren(QWidget):
            if widget.focusPolicy() != Qt.FocusPolicy.NoFocus:
                if isinstance(widget, (QLineEdit, QComboBox, QPushButton, QCheckBox)):
                    if self.is_widget_editable(widget):
                        focus_widgets.append(widget)

        focus_widgets.append(self.existing_data_view)

        try:
            current_index = focus_widgets.index(current_widget)
        except ValueError:
            return None

        for i in range(current_index + 1, len(focus_widgets)):
            next_widget = focus_widgets[i]
            if self.is_widget_editable(next_widget) or isinstance(next_widget, QTableView):
                return next_widget

        for i in range(0, current_index):
            next_widget = focus_widgets[i]
            if self.is_widget_editable(next_widget) or isinstance(next_widget, QTableView):
                return next_widget

        return None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if isinstance(obj, (QLineEdit, QComboBox)):
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if self.is_widget_editable(obj):
                        next_widget = self.find_next_editable_widget(obj)
                        if next_widget:
                            next_widget.setFocus()
                            if isinstance(next_widget, QLineEdit):
                                next_widget.selectAll()
                    return True

            elif isinstance(obj, QTableView):
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    current_index = obj.currentIndex()
                    if current_index.isValid():
                        self.on_row_click(current_index)
                    return True
                elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                    current_index = obj.currentIndex()
                    if current_index.isValid():
                        row = current_index.row()
                        col = current_index.column()
                        model = obj.model()
                        if key == Qt.Key.Key_Up:
                            new_row = max(0, row - 1)
                        else:
                            new_row = min(model.rowCount() - 1, row + 1)
                        if new_row != row:
                            new_index = model.index(new_row, col)
                            obj.setCurrentIndex(new_index)
                            obj.selectRow(new_row)
                        return True

        return super().eventFilter(obj, event)

    @handle_errors
    def on_row_click(self, index):
        model = self.existing_data_view.model()
        if not model:
            return

        row = index.row()
        self.row_data = []
        for column in range(model.columnCount()):
            value = model.index(row, column).data(Qt.ItemDataRole.DisplayRole)
            self.row_data.append(value)

        if not self.row_data:
            return

        try:
            if self.sender_name == "vendor_type":
                self.vendor_type_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                active = self.row_data[2] if len(self.row_data) > 2 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))
                
            elif self.sender_name == "salesmen_type":
                self.salesmen_type_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                active = self.row_data[2] if len(self.row_data) > 2 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))
                
            elif self.sender_name == "customer_type":
                self.customer_type_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                active = self.row_data[2] if len(self.row_data) > 2 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))
                
            elif self.sender_name == "size":
                self.size_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                active = self.row_data[2] if len(self.row_data) > 2 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))
                
        except (ValueError, TypeError, IndexError):
            QMessageBox.warning(self, "Error", "Error loading record data.")

    @handle_errors
    def save_data(self, checked=False):
        if self._is_saving:
            return
        is_update = False
        message = 'Record Added Success...'
        self._is_saving = True
        try:
            self.footer_save_btn.setText("Saving...")
            self.footer_save_btn.setDisabled(True)

            # ========================================
            # VENDOR TYPE
            # ========================================
            if self.sender_name == "vendor_type":
                type_name = self.name_input_value.text().strip()
                if not type_name:
                    QMessageBox.warning(self, "Validation Error", "Type Name is required.")
                    return
                
                is_active = self.is_active_widget.isChecked()
                
                if self.vendor_type_id is not None and self.vendor_type_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                    query = 'UPDATE vendor_type SET type_name = %s, is_active = %s WHERE id = %s'
                    values = (type_name, is_active, self.vendor_type_id)
                else:
                    is_update = False
                    message = 'Record Added Success..'
                    query = 'INSERT INTO vendor_type (type_name, is_active) VALUES (%s, %s)'
                    values = (type_name, is_active)
                
                self._cursor.execute(query, values)
                self.conn.commit()
                self.save_signal.emit()
                self.refresh_data()
                QMessageBox.information(self, 'Success', message)

            # ========================================
            # SALESMEN TYPE
            # ========================================
            elif self.sender_name == "salesmen_type":
                type_name = self.name_input_value.text().strip()
                if not type_name:
                    QMessageBox.warning(self, "Validation Error", "Type Name is required.")
                    return
                
                is_active = self.is_active_widget.isChecked()
                
                if self.salesmen_type_id is not None and self.salesmen_type_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                    query = 'UPDATE salesmen_type SET type_name = %s, is_active = %s WHERE id = %s'
                    values = (type_name, is_active, self.salesmen_type_id)
                else:
                    is_update = False
                    message = 'Record Added Success..'
                    query = 'INSERT INTO salesmen_type (type_name, is_active) VALUES (%s, %s)'
                    values = (type_name, is_active)
                
                self._cursor.execute(query, values)
                self.conn.commit()
                self.save_signal.emit()
                self.refresh_data()
                QMessageBox.information(self, 'Success', message)

            # ========================================
            # CUSTOMER TYPE
            # ========================================
            elif self.sender_name == "customer_type":
                type_name = self.name_input_value.text().strip()
                if not type_name:
                    QMessageBox.warning(self, "Validation Error", "Type Name is required.")
                    return

                is_active = self.is_active_widget.isChecked()
                
                if self.customer_type_id is not None and self.customer_type_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                    query = 'UPDATE customer_type SET type_name = %s, is_active = %s WHERE id = %s'
                    values = (type_name, is_active, self.customer_type_id)
                else:
                    is_update = False
                    message = 'Record Added Success..'
                    query = 'INSERT INTO customer_type (type_name, is_active) VALUES (%s, %s)'
                    values = (type_name, is_active)
                
                self._cursor.execute(query, values)
                self.conn.commit()
                self.save_signal.emit()
                self.refresh_data()
                QMessageBox.information(self, 'Success', message)

            # ========================================
            # SIZE
            # ========================================
            elif self.sender_name == "size":
                size_name = self.name_input_value.text().strip()
                if not size_name:
                    QMessageBox.warning(self, "Validation Error", "Size Name is required.")
                    return

                is_active = self.is_active_widget.isChecked()
                
                if self.size_id is not None and self.size_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                    query = 'UPDATE prd_size SET size_name=%s, is_active = %s WHERE id = %s'
                    values = (size_name, is_active, self.size_id)
                else:
                    is_update = False
                    message = 'Record Added Success..'
                    query = 'INSERT INTO prd_size (size_name, is_active) VALUES (%s, %s)'
                    values = (size_name, is_active)
                
                self._cursor.execute(query, values)
                self.conn.commit()
                self.save_signal.emit()
                self.refresh_data()
                QMessageBox.information(self, 'Success', message)

        except Exception as e:
            print(f"Error in save_data: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, 'Error', str(e))
        finally:
            self._is_saving = False
            self.footer_save_btn.setDisabled(False)
            self.footer_save_btn.setText("Save")

    @handle_errors
    def footer_window(self):
        self.footer_widget = QWidget()
        self.footer_widget.setFixedHeight(80)
        self.footer_widget.setObjectName("footerWidget")
        self.footer_layout = QHBoxLayout(self.footer_widget)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)

        self.footer_detail_widget = QWidget()
        self.footer_detail_layout = QVBoxLayout(self.footer_detail_widget)
        self.footer_detail_layout.setSpacing(10)

        self.footer_short_keys_header = QLabel("Short Keys")
        self.footer_short_keys_header.setStyleSheet("font-size:15px; font-weight:bold; color: white;")
        self.footer_detail_layout.addWidget(self.footer_short_keys_header)

        self.footer_detail_header = QLabel("Double Click On Any Row to Edit Record")
        self.footer_detail_header.setStyleSheet("font-size:15px; color: white;")
        self.footer_detail_layout.addWidget(self.footer_detail_header)

        self.buttons_widget_footer = QWidget()
        self.buttons_widget_footer.setFixedWidth(300)
        self.buttons_layout_footer = QGridLayout(self.buttons_widget_footer)
        self.buttons_layout_footer.setSpacing(5)
        self.buttons_layout_footer.setContentsMargins(10, 5, 10, 5)

        self.btn_cursor = Qt.CursorShape.PointingHandCursor

        self.footer_save_btn = QPushButton("Save")
        self.footer_save_btn.setFixedSize(90, 35)
        self.footer_save_btn.setCursor(self.btn_cursor)
        self.footer_save_btn.setObjectName("savebtn")
        self.footer_save_btn.clicked.connect(self.save_data)
        QShortcut(QKeySequence("Ctrl+s"), self).activated.connect(self.save_data)

        self.footer_refresh_btn = QPushButton("Refresh")
        self.footer_refresh_btn.setFixedSize(90, 35)
        self.footer_refresh_btn.setCursor(self.btn_cursor)
        self.footer_refresh_btn.setObjectName("refreshbtn")
        self.footer_refresh_btn.clicked.connect(self.refresh_data)
        QShortcut(QKeySequence("Ctrl+r"), self).activated.connect(self.refresh_data)

        self.footer_delete_btn = QPushButton("Close")
        self.footer_delete_btn.setFixedSize(90, 35)
        self.footer_delete_btn.setCursor(self.btn_cursor)
        self.footer_delete_btn.setObjectName("deletebtn")
        self.footer_delete_btn.clicked.connect(self.closeWindow)
        self.footer_delete_btn.setShortcut("Esc")

        self.footer_save_action = QLabel("CTRL + S")
        self.footer_refresh_action = QLabel("CTRL + R")
        self.footer_delete_action = QLabel("Esc")
        self.footer_save_action.setStyleSheet("color: white;")
        self.footer_refresh_action.setStyleSheet("color: white;")
        self.footer_delete_action.setStyleSheet("color: white;")

        self.buttons_layout_footer.addWidget(self.footer_save_btn, 0, 0)
        self.buttons_layout_footer.addWidget(self.footer_refresh_btn, 0, 1)
        self.buttons_layout_footer.addWidget(self.footer_delete_btn, 0, 2)
        self.buttons_layout_footer.addWidget(self.footer_save_action, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.buttons_layout_footer.addWidget(self.footer_refresh_action, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.buttons_layout_footer.addWidget(self.footer_delete_action, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        self.footer_layout.addWidget(self.footer_detail_widget)
        self.footer_layout.addWidget(self.buttons_widget_footer)

        self.layout.addWidget(self.footer_widget)

    def closeWindow(self):
        self.close()

    @handle_errors
    def refresh_data(self, checked=False):
        if self.sender_name == "vendor_type":
            self.data_model._load_data("SELECT * FROM vendor_type")
            self.name_input_value.setText("")
            self.vendor_type_id = None
        elif self.sender_name == "salesmen_type":
            self.data_model._load_data("SELECT * FROM salesmen_type")
            self.name_input_value.setText("")
            self.salesmen_type_id = None
        elif self.sender_name == "customer_type":
            self.data_model._load_data("SELECT * FROM customer_type")
            self.name_input_value.setText("")
            self.customer_type_id = None
        elif self.sender_name == "size":
            self.data_model._load_data("SELECT * FROM prd_size")
            self.name_input_value.setText("")
            self.size_id = None
        self.is_active_widget.setChecked(True)


class TableModel(QAbstractTableModel):
    def __init__(self, query):
        super().__init__()
        self._data = []
        self._headers = []
        self._load_data(query)

    def _load_data(self, query):
        self.beginResetModel()
        try:
            conn, cursor = db.get_connection()
            cursor.execute(query)
            result = cursor.fetchall()
            if result is None:
                self._data = []
                self._headers = []
            else:
                self._data = result
                self._headers = list(self._data[0].keys()) if self._data else []
        except Exception as e:
            print(f"Error loading data: {e}")
            self._data = []
            self._headers = []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            try:
                key = self._headers[index.column()]
                value = self._data[index.row()].get(key)
                
                # Check if this is the is_active column (column index 2)
                if index.column() == 2:
                    if value in (1, True, "1", "true", "True"):
                        return "✓"  # Tick mark for active
                    else:
                        return "✗"  # Cross mark for inactive
                
                return str(value) if value is not None else ""
            except (IndexError, KeyError):
                return None

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                try:
                    header = self._headers[section]
                    # Clean up header names
                    if header == "is_active":
                        return "Active"
                    return header.replace("_", " ").title()
                except IndexError:
                    return ""
            return section + 1
        return None