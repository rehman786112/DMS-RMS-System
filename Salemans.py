# salesmen_ui.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from database import DatabaseManager
from predefined_widgets import Suggestion
from datetime import datetime
from decimal import Decimal
import re
import functools
import traceback
from Add_Types import AddDetails

db = DatabaseManager()


# ============================================
# ERROR HANDLING DECORATOR
# ============================================
def handle_errors(func):
    """Decorator to handle errors in salesman UI methods"""
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


# ============================================
# SEARCHABLE COMBOBOX CLASS
# ============================================
class SearchableComboBox(QComboBox):
    """ComboBox with search/filter functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._line_edit = None
        self._filter_text = ""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        self._line_edit = self.lineEdit()
        self._line_edit.textEdited.connect(self._filter_items)
        self._line_edit.returnPressed.connect(self._select_first_match)
        
        self.setStyleSheet("""
            QComboBox {
                min-height: 25px;
                padding: 5px;
            }
            QComboBox::drop-down {
                width: 20px;
            }
            QComboBox QLineEdit {
                padding: 2px;
            }
        """)
    
    def addItems(self, items):
        self._items = list(items)
        super().clear()
        super().addItems(items)
    
    def addItem(self, text, userData=None):
        self._items.append(text)
        super().addItem(text, userData)
    
    def clear(self):
        self._items.clear()
        super().clear()
        self._filter_text = ""
        if self._line_edit:
            self._line_edit.setText("")
    
    def _filter_items(self, text):
        self._filter_text = text.lower().strip()
        super().clear()
        
        if not self._filter_text:
            super().addItems(self._items)
            return
        
        matches = []
        for item in self._items:
            if self._filter_text in item.lower():
                matches.append(item)
        
        if matches:
            super().addItems(matches)
            self.showPopup()
        else:
            super().addItem("No matches found")
            self.showPopup()
    
    def _select_first_match(self):
        if self.count() > 0:
            current_text = self._line_edit.text()
            for i in range(self.count()):
                item_text = self.itemText(i)
                if item_text.lower() == current_text.lower():
                    self.setCurrentIndex(i)
                    break
            else:
                if self.count() > 0:
                    self.setCurrentIndex(0)
    
    def showPopup(self):
        super().showPopup()
    
    def setCurrentIndex(self, index):
        super().setCurrentIndex(index)
        if index >= 0 and index < self.count():
            text = self.itemText(index)
            if self._line_edit:
                self._line_edit.setText(text)
    
    def setCurrentText(self, text):
        super().setCurrentText(text)
        if self._line_edit:
            self._line_edit.setText(text)


def parse_date(date_string):
    if not date_string or date_string.strip() == "":
        return datetime.now().date()
    
    date_string = date_string.strip()
    
    try:
        return datetime.strptime(date_string, "%d-%m-%y").date()
    except ValueError:
        pass
    
    try:
        return datetime.strptime(date_string, "%d-%m-%Y").date()
    except ValueError:
        pass
    
    raise ValueError(f"Invalid date format: '{date_string}'. Please use DD-MM-YY format (e.g., 25-12-24)")


class Salemans(QWidget):
    # ---- placeholders ----
    TYPE_PLACEHOLDER = "Select Type"
    COMPANY_PLACEHOLDER = "Choose Company"

    def __init__(self):
        super().__init__()
        try:
            # 1. plain python state
            self.type_data = []
            self.company_data = []
            self.salesman_code = None
            self.is_update = False

            # 2. current date
            self.current_date = datetime.now().strftime("%d-%m-%y")

            # 3. database connection
            self.conn, self._cursor = db.get_connection()

            # 4. load data into plain python lists (no widgets exist yet)
            self.load_types()
            self.load_companies()

            # 5. build the UI
            self.setup_ui()

            # 6. populate the comboboxes from the lists we already loaded
            self.update_type_combo(preserve_selection=False)
            self.update_company_combo(preserve_selection=False)

            # 7. wiring / shortcuts / tab order
            self.setup_enter_navigation()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize: {str(e)}")

    # ================================================================
    # DATABASE HELPERS
    # ================================================================
    def _fresh_cursor(self):
        """Return a cursor guaranteed to see the latest committed data."""
        try:
            self.conn, self._cursor = db.get_connection()
        except Exception as e:
            print(f"Could not obtain a fresh connection: {e}")
        try:
            self.conn.commit()
        except Exception:
            pass
        return self._cursor

    def execute_query(self, query, params=None, fetch="all"):
        cursor = self._fresh_cursor()
        cursor.execute(query, params or ())
        if fetch == "all":
            return cursor.fetchall() or []
        if fetch == "one":
            return cursor.fetchone()
        return None

    # ================================================================
    # DATA LOADING
    # ================================================================
    def load_types(self):
        try:
            rows = self.execute_query("SELECT type_name FROM salesmen_type WHERE is_active = true ORDER BY type_name")
            self.type_data = [str(r['type_name']) for r in rows]
        except Exception as e:
            print(f"load_types error: {e}")
            self.type_data = []

    def load_companies(self):
        try:
            rows = self.execute_query("SELECT DISTINCT slm_company FROM salesmen WHERE slm_company IS NOT NULL AND slm_company != '' ORDER BY slm_company")
            self.company_data = [str(r['slm_company']) for r in rows]
        except Exception as e:
            print(f"load_companies error: {e}")
            self.company_data = []

    # ================================================================
    # COMBOBOX UPDATES
    # ================================================================
    def _rebuild_combo(self, combo, placeholder, items, preserve_selection):
        current_text = combo.currentText() if preserve_selection else None
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(placeholder)
        for item in items:
            combo.addItem(item)
        if current_text:
            index = combo.findText(current_text)
            combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def update_type_combo(self, preserve_selection=True):
        self._rebuild_combo(self.type_input, self.TYPE_PLACEHOLDER, self.type_data, preserve_selection)

    def update_company_combo(self, preserve_selection=True):
        self._rebuild_combo(self.company_input, self.COMPANY_PLACEHOLDER, self.company_data, preserve_selection)

    @handle_errors
    def refresh_types(self):
        """Connected to AddDetails.save_signal — fires right after a new type is committed."""
        self.load_types()
        self.update_type_combo()

    # ================================================================
    # ADD TYPE
    # ================================================================
    @handle_errors
    def save_type_data(self, checked=False):
        self.add_type_widget = AddDetails('salesmen_type')
        self.add_type_widget.save_signal.connect(self.refresh_types)
        self.add_type_widget.show()

    # ================================================================
    # UI CONSTRUCTION
    # ================================================================
    @handle_errors
    def setup_ui(self):
        self.setObjectName("CustomerWidget")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        self._build_header()
        self._build_registration_section()
        self._build_footer()

        QShortcut(QKeySequence("Ctrl+y"), self).activated.connect(self.clear_salesman)
        QShortcut(QKeySequence("Ctrl+r"), self).activated.connect(self.refresh_salesman)
        QShortcut(QKeySequence("Ctrl+s"), self).activated.connect(self.save_data)

    def _build_header(self):
        self.label_widget = QWidget()
        self.label_widget.setMaximumHeight(60)
        self.label_layout = QHBoxLayout(self.label_widget)

        self.main_label = QLabel("Salesman Registration")
        self.main_label.setStyleSheet("color: black; font-size:30px; font-weight:bold")
        self.main_label.setObjectName("tablabels")
        self.main_label.setFixedHeight(40)

        self.existing_btn = QPushButton("Show Existing Salesmen")
        self.existing_btn.setFixedSize(200, 40)
        self.existing_btn.clicked.connect(self.get_existing_salesmen)
        self.existing_btn.setObjectName("existingcustomerbtn")

        self.add_type_btn = QPushButton("Add New Type")
        self.add_type_btn.setFixedSize(200, 40)
        self.add_type_btn.clicked.connect(self.save_type_data)
        self.add_type_btn.setObjectName('add_type_btn')

        self.label_layout.addWidget(self.main_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.label_layout.addWidget(self.existing_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.label_layout.addWidget(self.add_type_btn)
        self.main_layout.addWidget(self.label_widget)

    def _build_registration_section(self):
        self.registration_widget = QWidget()
        self.registration_widget.setObjectName("registration")
        self.registration_layout = QVBoxLayout(self.registration_widget)
        self.registration_layout.setContentsMargins(0, 0, 0, 0)
        self.registration_layout.setSpacing(10)

        # --- Salesman Details ---
        self.detail_label = QLabel("Salesman Details:")
        self.detail_label.setMinimumHeight(40)
        self.detail_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        self.detail_label.setObjectName("customerdetaillabel")
        self.registration_layout.addWidget(self.detail_label)

        self.detail_widget = QWidget()
        self.detail_layout = QGridLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 10, 0, 10)
        self.detail_layout.setVerticalSpacing(15)
        self.detail_layout.setHorizontalSpacing(30)

        self.code_widget, self.code_input = self.create_input_field("*Code", "Salesman Code..")
        self.code_input.setEnabled(False)
        self.name_widget, self.name_input = self.create_input_field("*Name", "Enter Salesman name....")
        self.address_widget, self.address_input = self.create_input_field("*Address", "Enter Salesman address....")
        self.city_widget, self.city_input = self.create_input_field("*City", "Enter City....")
        self.country_widget, self.country_input = self.create_input_field("Country", "Enter country....")
        self.phone_widget, self.phone_input = self.create_input_field("*Phone", "Enter Salesman Phone number..")
        self.whatsapp_widget, self.whatsapp_input = self.create_input_field("WhatsApp", "Enter WhatsApp number..")
        self.email_widget, self.email_input = self.create_input_field("*Email", "Enter Salesman Email...")
        self.type_widget, self.type_input = self.create_combo_field("*Type", self.type_data, self.TYPE_PLACEHOLDER)

        self.detail_layout.addWidget(self.code_widget, 0, 0)
        self.detail_layout.addWidget(self.name_widget, 0, 1)
        self.detail_layout.addWidget(self.address_widget, 1, 0)
        self.detail_layout.addWidget(self.city_widget, 1, 1)
        self.detail_layout.addWidget(self.country_widget, 2, 0)
        self.detail_layout.addWidget(self.phone_widget, 2, 1)
        self.detail_layout.addWidget(self.whatsapp_widget, 3, 0)
        self.detail_layout.addWidget(self.email_widget, 3, 1)
        self.detail_layout.addWidget(self.type_widget, 4, 0)
        self.detail_layout.setColumnStretch(0, 1)
        self.detail_layout.setColumnStretch(1, 1)

        # --- Additional Details ---
        self.additional_label = QLabel("Additional Details:")
        self.additional_label.setObjectName("customerdetaillabel")
        self.additional_label.setMinimumHeight(40)
        self.additional_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")

        self.additional_widget = QWidget()
        self.additional_layout = QGridLayout(self.additional_widget)
        self.additional_layout.setContentsMargins(0, 10, 0, 10)
        self.additional_layout.setVerticalSpacing(15)
        self.additional_layout.setHorizontalSpacing(30)

        self.cnic_widget, self.cnic_input = self.create_input_field("CNIC", "Enter CNIC...")
        self.company_widget, self.company_input = self.create_combo_field("*Company", self.company_data, self.COMPANY_PLACEHOLDER)
        self.credit_widget, self.credit_input = self.create_input_field("*Credit limit", "Enter Credit Limit...")
        self.date_widget, self.date_input = self.create_input_field("Date", "Enter today date (e.g., 25-12-24)...")
        self.date_input.setText(self.current_date)

        self.additional_layout.addWidget(self.cnic_widget, 0, 0)
        self.additional_layout.addWidget(self.company_widget, 1, 0)
        self.additional_layout.addWidget(self.credit_widget, 1, 1)
        self.additional_layout.addWidget(self.date_widget, 2, 0)
        self.additional_layout.setColumnStretch(0, 1)
        self.additional_layout.setColumnStretch(1, 1)

        self.registration_layout.addWidget(self.detail_widget)
        self.registration_layout.addWidget(self.additional_label)
        self.registration_layout.addWidget(self.additional_widget)
        self.main_layout.addWidget(self.registration_widget)

    def _build_footer(self):
        self.footer_widget = QWidget()
        self.footer_widget.setObjectName("footerwidgetcustomer")
        self.footer_widget.setFixedHeight(70)
        self.footer_layout = QHBoxLayout(self.footer_widget)
        self.footer_layout.setContentsMargins(5, 5, 5, 5)

        self.info_widget = QWidget()
        self.info_layout = QVBoxLayout(self.info_widget)
        self.info_label = QLabel("Short Keys")
        self.info_label.setStyleSheet("font-size:18px;font-weight:bold;")
        self.info_layout.addWidget(self.info_label)
        self.detail_info = QLabel("The Fields that contain * is Necessary.")
        self.detail_info.setObjectName("footerlabelscustomers")
        self.info_layout.addWidget(self.detail_info)
        self.footer_layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        self.btn_widget = QWidget()
        self.btn_widget.setFixedHeight(60)
        self.btn_widget.setFixedWidth(500)
        self.btn_layout = QHBoxLayout(self.btn_widget)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)

        self.clear_btn = self.create_button("Clear", "CTRL + Y", "clearbtncustomer", self.clear_salesman)
        self.refresh_btn = self.create_button("Refresh", "CTRL + R", "refreshbtncustomer", self.refresh_salesman)
        self.save_btn = self.create_button("Save", "CTRL + S", "savebtncustomer", self.save_data)

        self.btn_layout.addWidget(self.clear_btn[0])
        self.btn_layout.addWidget(self.refresh_btn[0])
        self.btn_layout.addWidget(self.save_btn[0])
        self.footer_layout.addWidget(self.btn_widget)
        self.main_layout.addWidget(self.footer_widget)

    # ---- small reusable widget factories ----
    def create_input_field(self, label, placeholder):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(15)

        label_widget = QLabel(label)
        label_widget.setObjectName("input_labels_customers")
        label_widget.setMinimumWidth(100)
        label_widget.setMaximumWidth(120)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label_widget)

        input_field = QLineEdit()
        input_field.setMinimumHeight(35)
        input_field.setPlaceholderText(placeholder)
        input_field.setObjectName("input_fields_customers")
        input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(input_field)
        return widget, input_field

    def create_combo_field(self, label, data, placeholder):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(15)

        label_widget = QLabel(label)
        label_widget.setObjectName("input_labels_customers")
        label_widget.setMinimumWidth(100)
        label_widget.setMaximumWidth(120)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label_widget)

        combo = SearchableComboBox()
        combo.setMinimumHeight(35)
        combo.setObjectName("input_fields_customers")
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.addItem(placeholder)
        for item in data:
            combo.addItem(item)
        layout.addWidget(combo)
        return widget, combo

    def create_button(self, text, shortcut, object_name, callback):
        widget = QWidget()
        widget.setFixedHeight(60)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(80, 30)
        btn.setObjectName(object_name)
        btn.clicked.connect(callback)

        label = QLabel(shortcut)
        label.setStyleSheet("color:black;font-size:12px;")

        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        return widget, btn

    def setup_enter_navigation(self):
        for widget in self.findChildren(QLineEdit):
            widget.installEventFilter(self)
        for widget in self.findChildren(QComboBox):
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextChild()
            return True
        return super().eventFilter(obj, event)

    # ================================================================
    # EXISTING SALESMAN LOOKUP
    # ================================================================
    @handle_errors
    def get_existing_salesmen(self, checked=False):
        self.salesman_widget = Suggestion(
            "SELECT slm_code, slm_name, slm_city FROM salesmen ORDER BY slm_name",
            "Salesmen",
            display_columns=['slm_code', 'slm_name', 'slm_city']
        )
        self.salesman_widget.sent_data.connect(self.receive_salesman_data)
        self.salesman_widget.show()

    @handle_errors
    def receive_salesman_data(self, data):
        if not data or len(data) < 3:
            QMessageBox.warning(self, "Error", "Invalid salesman data received")
            return

        self.salesman_widget.close()
        salesman_code = data[0]
        if not salesman_code:
            QMessageBox.warning(self, "Error", "Invalid salesman code")
            return

        salesman_data = self.execute_query(
            "SELECT slm_code, slm_name, slm_email, slm_address, slm_city, "
            "slm_country, slm_phone, slm_whatsapp, slm_type, slm_cnic, "
            "slm_date, slm_company, slm_credit_limit "
            "FROM salesmen WHERE slm_code = %s",
            (salesman_code,), fetch="one"
        )
        if not salesman_data:
            QMessageBox.warning(self, "Error", f"Salesman with code {salesman_code} not found")
            return

        self.code_input.setText(str(salesman_data.get('slm_code', '')))
        self.name_input.setText(str(salesman_data.get('slm_name', '')))
        self.email_input.setText(str(salesman_data.get('slm_email', '')))
        self.address_input.setText(str(salesman_data.get('slm_address', '')))
        self.city_input.setText(str(salesman_data.get('slm_city', '')))
        self.country_input.setText(str(salesman_data.get('slm_country', '')))
        self.phone_input.setText(str(salesman_data.get('slm_phone', '')))
        self.whatsapp_input.setText(str(salesman_data.get('slm_whatsapp', '')))

        salesman_type = salesman_data.get('slm_type', '')
        if salesman_type:
            index = self.type_input.findText(str(salesman_type))
            self.type_input.setCurrentIndex(index if index >= 0 else 0)
        else:
            self.type_input.setCurrentIndex(0)

        self.cnic_input.setText(str(salesman_data.get('slm_cnic', '')))

        company = salesman_data.get('slm_company', '')
        if company:
            index = self.company_input.findText(str(company))
            if index >= 0:
                self.company_input.setCurrentIndex(index)

        self.credit_input.setText(str(salesman_data.get('slm_credit_limit', '0')))

        slm_date = salesman_data.get('slm_date')
        if slm_date:
            if hasattr(slm_date, 'strftime'):
                self.date_input.setText(slm_date.strftime("%d-%m-%y"))
            else:
                self.date_input.setText(parse_date(str(slm_date)).strftime("%d-%m-%y"))
        else:
            self.date_input.setText(self.current_date)

        self.is_update = True
        self.salesman_code = int(salesman_code)

        QMessageBox.information(self, "Success", f"Salesman {salesman_code} loaded successfully!")

    # ================================================================
    # VALIDATION / SAVE
    # ================================================================
    def validate_data(self):
        errors = []
        if not self.name_input.text().strip():
            errors.append("Salesman Name is required")
        if not self.address_input.text().strip():
            errors.append("Address is required")
        if not self.city_input.text().strip():
            errors.append("City is required")
        if not self.phone_input.text().strip():
            errors.append("Phone number is required")
        if not self.email_input.text().strip():
            errors.append("Email is required")

        email = self.email_input.text().strip()
        if email and ('@' not in email or '.' not in email):
            errors.append("Invalid email format")

        date_text = self.date_input.text().strip()
        if date_text:
            try:
                parse_date(date_text)
            except ValueError as e:
                errors.append(str(e))
        return errors

    @handle_errors
    def save_data(self, checked=False):
        errors = self.validate_data()
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(f"• {err}" for err in errors))
            return

        salesman_name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        city = self.city_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()

        if not salesman_name or not address or not city or not phone or not email:
            QMessageBox.warning(self, "Validation Error", "Please fill all required fields (*)")
            return

        salesman_type = self.type_input.currentText()
        company = self.company_input.currentText()

        if salesman_type == self.TYPE_PLACEHOLDER or not salesman_type:
            QMessageBox.warning(self, "Validation Error", "Please Select the salesman type")
            return
        if company == self.COMPANY_PLACEHOLDER or not company:
            QMessageBox.warning(self, "Validation Error", "Please Select a Company")
            return

        salesman_code_text = self.code_input.text()
        self.salesman_code = int(salesman_code_text) if salesman_code_text else None
        self.is_update = bool(salesman_code_text)

        credit_limit = Decimal(self.credit_input.text().strip() or '0')
        _date = parse_date(self.date_input.text().strip() or self.current_date)
        date_str = _date.strftime("%d-%m-%y")

        values_common = (
            salesman_name,
            email,
            address,
            city,
            self.country_input.text().strip(),
            phone,
            self.whatsapp_input.text().strip(),
            salesman_type,
            self.cnic_input.text().strip(),
            date_str,
            company,
            credit_limit,
        )

        if self.is_update:
            query = """
                UPDATE salesmen SET 
                    slm_name=%s, slm_email=%s, slm_address=%s,
                    slm_city=%s, slm_country=%s, slm_phone=%s,
                    slm_whatsapp=%s, slm_type=%s, slm_cnic=%s,
                    slm_date=%s, slm_company=%s, slm_credit_limit=%s
                WHERE slm_code=%s
            """
            values = values_common + (self.salesman_code,)
            message = "Salesman Updated Successfully!"
        else:
            query = """
                INSERT INTO salesmen (
                    slm_name, slm_email, slm_address, slm_city,
                    slm_country, slm_phone, slm_whatsapp, slm_type,
                    slm_cnic, slm_date, slm_company, slm_credit_limit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = values_common
            message = "Salesman Added Successfully!"

        cursor = self._fresh_cursor()
        cursor.execute(query, values)
        self.conn.commit()
        QMessageBox.information(self, "Success", message)
        self.clear_salesman()

    # ================================================================
    # CLEAR / REFRESH
    # ================================================================
    @handle_errors
    def clear_salesman(self):
        for field in (self.name_input, self.code_input, self.address_input, self.city_input,
                      self.country_input, self.phone_input, self.whatsapp_input,
                      self.email_input, self.cnic_input, self.credit_input):
            field.clear()

        self.type_input.setCurrentIndex(0)
        self.company_input.setCurrentIndex(0)

        self.date_input.setText(self.current_date)
        self.is_update = False
        self.salesman_code = None
        self.name_input.setFocus()

    @handle_errors
    def refresh_salesman(self, checked=False):
        self.current_date = datetime.now().strftime("%d-%m-%y")
        self.load_types()
        self.load_companies()
        self.update_company_combo(preserve_selection=False)
        self.update_type_combo(preserve_selection=False)
        self.clear_salesman()
        QMessageBox.information(self, "Info", "Data refreshed successfully")
