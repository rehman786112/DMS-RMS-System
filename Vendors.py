# vendors_ui.py
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

db = DatabaseManager()


# ============================================
# ERROR HANDLING DECORATOR
# ============================================
def handle_errors(func):
    """Decorator to handle errors in vendor UI methods"""
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
    """ComboBox with search/filter functionality - Same width as QLineEdit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._line_edit = None
        self._filter_text = ""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Get the line edit and setup search
        self._line_edit = self.lineEdit()
        self._line_edit.textEdited.connect(self._filter_items)
        self._line_edit.returnPressed.connect(self._select_first_match)
        
        # Style - same as QLineEdit
        self.setStyleSheet("""
            QComboBox {
                min-height: 25px;
                padding: 5px;
                
            }
            QComboBox::drop-down {
                width: 20px;
                border: none;
            }
            QComboBox::down-arrow {
                image: url("assets/icons/black-arrow.png");
                width: 12px;
                height: 12px;
            }
            QComboBox QLineEdit {
                padding: 2px;
                border: none;
            }
            
        """)
    
    def addItems(self, items):
        """Add items to combobox and store for filtering"""
        self._items = list(items)
        super().clear()
        super().addItems(items)
    
    def addItem(self, text, userData=None):
        """Add single item"""
        self._items.append(text)
        super().addItem(text, userData)
    
    def clear(self):
        """Clear all items"""
        self._items.clear()
        super().clear()
        self._filter_text = ""
        if self._line_edit:
            self._line_edit.setText("")
    
    def _filter_items(self, text):
        """Filter items based on search text"""
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
        """Select first item when Enter pressed"""
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
        """Override to ensure popup shows filtered items"""
        super().showPopup()
    
    def setCurrentIndex(self, index):
        """Set current index and update line edit"""
        super().setCurrentIndex(index)
        if index >= 0 and index < self.count():
            text = self.itemText(index)
            if self._line_edit:
                self._line_edit.setText(text)
    
    def setCurrentText(self, text):
        """Set current text"""
        super().setCurrentText(text)
        if self._line_edit:
            self._line_edit.setText(text)


def parse_date(date_string):
    """
    Parse date from DD-MM-YY format only.
    Returns: date object or raises ValueError
    """
    if not date_string or date_string.strip() == "":
        return datetime.now().date()
    
    date_string = date_string.strip()
    
    # Only support DD-MM-YY format
    try:
        return datetime.strptime(date_string, "%d-%m-%y").date()
    except ValueError:
        pass
    
    # Try with 4-digit year as fallback (DD-MM-YYYY)
    try:
        return datetime.strptime(date_string, "%d-%m-%Y").date()
    except ValueError:
        pass
    
    raise ValueError(f"Invalid date format: '{date_string}'. Please use DD-MM-YY format (e.g., 25-12-24)")


class Vendors(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.type_data = ['Corporate', 'Individual', 'Premium', 'Retail', 'WholeSale']
            self.company_data = []
            self.vendor_code = None
            self.is_update = False
            self._load_data()
            self.setup_ui()
            self.setup_enter_navigation()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize: {str(e)}")

    @handle_errors
    def setup_ui(self):
        self.setObjectName("CustomerWidget")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # Header
        self.label_widget = QWidget()
        self.label_widget.setMaximumHeight(60)
        self.label_layout = QHBoxLayout(self.label_widget)
        
        self.main_label = QLabel("Vendor Registration")
        self.main_label.setStyleSheet("color: black; font-size:30px; font-weight:bold")
        self.main_label.setObjectName("tablabels")
        self.main_label.setFixedHeight(40)
        
        self.existing_btn = QPushButton("Show Existing Vendors")
        self.existing_btn.setFixedSize(200, 40)
        self.existing_btn.clicked.connect(self.get_existing_vendors)
        self.existing_btn.setObjectName("existingcustomerbtn")
        
        self.label_layout.addWidget(self.main_label, alignment=Qt.AlignmentFlag.AlignLeft)
        self.label_layout.addWidget(self.existing_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.label_widget)

        # Registration Widget
        self.registration_widget = QWidget()
        self.registration_widget.setObjectName("registration")
        self.registration_layout = QVBoxLayout(self.registration_widget)
        self.registration_layout.setContentsMargins(0, 0, 0, 0)
        self.registration_layout.setSpacing(10)

        # Vendor Details
        self.detail_label = QLabel("Vendor Details:")
        self.detail_label.setMinimumHeight(40)
        self.detail_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        self.detail_label.setObjectName("customerdetaillabel")
        self.registration_layout.addWidget(self.detail_label)

        self.detail_widget = QWidget()
        self.detail_layout = QGridLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 10, 0, 10)
        self.detail_layout.setVerticalSpacing(15)
        self.detail_layout.setHorizontalSpacing(30)

        # Input fields
        self.code_widget, self.code_input = self.create_input_field("*Code", "Vendor Code..")
        self.code_input.setEnabled(False)
        self.name_widget, self.name_input = self.create_input_field("*Name", "Enter Vendor name....")
        self.address_widget, self.address_input = self.create_input_field("*Address", "Enter Vendor address....")
        self.city_widget, self.city_input = self.create_input_field("*City", "Enter City....")
        self.country_widget, self.country_input = self.create_input_field("Country", "Enter country....")
        self.phone_widget, self.phone_input = self.create_input_field("*Phone", "Enter Vendor Phone number..")
        self.whatsapp_widget, self.whatsapp_input = self.create_input_field("WhatsApp", "Enter WhatsApp number..")
        self.email_widget, self.email_input = self.create_input_field("*Email", "Enter Vendor Email...")
        self.type_widget, self.type_input = self.create_combo_field("*Type", self.type_data, "Select Type")

        # Add to grid
        self.detail_layout.addWidget(self.code_widget, 0, 0)
        self.detail_layout.addWidget(self.name_widget, 0, 1)
        self.detail_layout.addWidget(self.address_widget, 1, 0)
        self.detail_layout.addWidget(self.city_widget, 1, 1)
        self.detail_layout.addWidget(self.country_widget, 2, 0)
        self.detail_layout.addWidget(self.phone_widget, 2, 1)
        self.detail_layout.addWidget(self.whatsapp_widget, 3, 0)
        self.detail_layout.addWidget(self.email_widget, 3, 1)
        self.detail_layout.addWidget(self.type_widget, 4, 0)

        # Additional Details
        self.additional_label = QLabel("Additional Details:")
        self.additional_label.setObjectName("customerdetaillabel")
        self.additional_label.setMinimumHeight(40)
        self.additional_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        self.registration_layout.addWidget(self.additional_label)

        self.additional_widget = QWidget()
        self.additional_layout = QGridLayout(self.additional_widget)
        self.additional_layout.setContentsMargins(0, 10, 0, 10)
        self.additional_layout.setVerticalSpacing(15)
        self.additional_layout.setHorizontalSpacing(30)

        self.cnic_widget, self.cnic_input = self.create_input_field("CNIC", "Enter CNIC...")
        self.company_widget, self.company_input = self.create_combo_field("*Company", self.company_data, "Choose Company")
        self.credit_widget, self.credit_input = self.create_input_field("*Credit limit", "Enter Credit Limit...")
        self.date_widget, self.date_input = self.create_input_field("Date", "Enter today date (e.g., 25-12-24)...")
        self.date_input.setText(self.current_date)

        self.additional_layout.addWidget(self.cnic_widget, 0, 0)
        self.additional_layout.addWidget(self.company_widget, 1, 0)
        self.additional_layout.addWidget(self.credit_widget, 1, 1)
        self.additional_layout.addWidget(self.date_widget, 2, 0)

        self.registration_layout.addWidget(self.detail_widget)
        self.registration_layout.addWidget(self.additional_label)
        self.registration_layout.addWidget(self.additional_widget)
        self.main_layout.addWidget(self.registration_widget)

        # Footer
        self.setup_footer()

        self.detail_layout.setColumnStretch(0, 1)
        self.detail_layout.setColumnStretch(1, 1)
        self.additional_layout.setColumnStretch(0, 1)
        self.additional_layout.setColumnStretch(1, 1)

    @handle_errors
    def setup_footer(self):
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

        self.clear_btn = self.create_button("Clear", "CTRL + Y", "clearbtncustomer", self.clear_vendor)
        self.refresh_btn = self.create_button("Refresh", "CTRL + R", "refreshbtncustomer", self.refresh_vendor)
        self.save_btn = self.create_button("Save", "CTRL + S", "savebtncustomer", self.save_data)

        self.btn_layout.addWidget(self.clear_btn[0])
        self.btn_layout.addWidget(self.refresh_btn[0])
        self.btn_layout.addWidget(self.save_btn[0])
        self.footer_layout.addWidget(self.btn_widget)
        self.main_layout.addWidget(self.footer_widget)

        QShortcut(QKeySequence("Ctrl+y"), self).activated.connect(self.clear_vendor)
        QShortcut(QKeySequence("Ctrl+r"), self).activated.connect(self.refresh_vendor)
        QShortcut(QKeySequence("Ctrl+s"), self).activated.connect(self.save_data)

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
        layout.setContentsMargins(0, 0, 10, 0)  # Same as input field
        layout.setSpacing(15)  # Same as input field

        label_widget = QLabel(label)
        label_widget.setObjectName("input_labels_customers")
        label_widget.setMinimumWidth(100)  # Same as input field
        label_widget.setMaximumWidth(120)  # Same as input field
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label_widget)

        # Use SearchableComboBox
        combo = SearchableComboBox()
        combo.setMinimumHeight(35)  # Same as input field
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
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.focusNextChild()
                return True
        return super().eventFilter(obj, event)

    @handle_errors
    def _load_data(self):
        """Load company data from vendors table"""
        try:
            # Get distinct companies from vendors table
            conn, cursor = db.get_connection()
            cursor.execute("SELECT DISTINCT vnd_company FROM vendors WHERE vnd_company IS NOT NULL AND vnd_company != '' ORDER BY vnd_company;")
            data = cursor.fetchall()
            self.company_data.clear()
            if data:
                for item in data:
                    self.company_data.append(str(item['vnd_company']))
            self.current_date = datetime.now().strftime("%d-%m-%y")
        except Exception as e:
            print(f"Error loading company data: {e}")
            self.company_data = []
            self.current_date = datetime.now().strftime("%d-%m-%y")

    @handle_errors
    def get_existing_vendors(self, checked=False):
        try:
            self.vendor_widget = Suggestion(
                "SELECT vnd_code, vnd_name, vnd_city FROM vendors ORDER BY vnd_name", 
                "Vendors",
                display_columns=['vnd_code', 'vnd_name', 'vnd_city']
            )
            self.vendor_widget.show()
            self.vendor_widget.sent_data.connect(self.receive_vendor_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load vendors: {str(e)}")

    @handle_errors
    def receive_vendor_data(self, data):
        if not data or len(data) < 3:
            QMessageBox.warning(self, "Error", "Invalid vendor data received")
            return
        
        self.vendor_widget.close()
        
        vendor_code = data[0]
        
        if not vendor_code:
            QMessageBox.warning(self, "Error", "Invalid vendor code")
            return
        
        conn, cursor = db.get_connection()
        cursor.execute(
            "SELECT vnd_code, vnd_name, vnd_email, vnd_address, vnd_city, "
            "vnd_country, vnd_phone, vnd_whatsapp, vnd_type, vnd_cnic, "
            "vnd_date, vnd_company, vnd_credit_limit "
            "FROM vendors WHERE vnd_code = %s",
            (vendor_code,)
        )
        vendor_data = cursor.fetchone()
        
        if not vendor_data:
            QMessageBox.warning(self, "Error", f"Vendor with code {vendor_code} not found")
            return
        
        self.code_input.setText(str(vendor_data.get('vnd_code', '')))
        self.name_input.setText(str(vendor_data.get('vnd_name', '')))
        self.email_input.setText(str(vendor_data.get('vnd_email', '')))
        self.address_input.setText(str(vendor_data.get('vnd_address', '')))
        self.city_input.setText(str(vendor_data.get('vnd_city', '')))
        self.country_input.setText(str(vendor_data.get('vnd_country', '')))
        self.phone_input.setText(str(vendor_data.get('vnd_phone', '')))
        self.whatsapp_input.setText(str(vendor_data.get('vnd_whatsapp', '')))
        
        vendor_type = vendor_data.get('vnd_type', '')
        if vendor_type:
            index = self.type_input.findText(str(vendor_type))
            if index >= 0:
                self.type_input.setCurrentIndex(index)
        else:
            self.type_input.setCurrentIndex(0)
        
        self.cnic_input.setText(str(vendor_data.get('vnd_cnic', '')))
        
        company = vendor_data.get('vnd_company', '')
        if company:
            index = self.company_input.findText(str(company))
            if index >= 0:
                self.company_input.setCurrentIndex(index)
        
        self.credit_input.setText(str(vendor_data.get('vnd_credit_limit', '0')))
        
        vnd_date = vendor_data.get('vnd_date')
        if vnd_date:
            if hasattr(vnd_date, 'strftime'):
                self.date_input.setText(vnd_date.strftime("%d-%m-%y"))
            else:
                self.date_input.setText(parse_date(str(vnd_date)).strftime("%d-%m-%y"))
        else:
            self.date_input.setText(self.current_date)
        
        self.is_update = True
        self.vendor_code = int(vendor_code)
        
        QMessageBox.information(self, "Success", f"Vendor {vendor_code} loaded successfully!")

    def validate_data(self):
        errors = []
        if not self.name_input.text().strip():
            errors.append("Vendor Name is required")
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

        vendor_name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        city = self.city_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        
        if not vendor_name or not address or not city or not phone or not email:
            QMessageBox.warning(self, "Validation Error", "Please fill all required fields (*)")
            return

        vendor_type = self.type_input.currentText()
        company = self.company_input.currentText()
        
        if "choose" in vendor_type.lower() or vendor_type == "Select Type":
            QMessageBox.warning(self, "Validation Error", "Please Select the vendor type")
            return
        if "choose" in company.lower() or company == "Choose Company":
            QMessageBox.warning(self, "Validation Error", "Please Select a Company")
            return

        vendor_code_text = self.code_input.text()
        self.vendor_code = int(vendor_code_text) if vendor_code_text else None
        self.is_update = bool(vendor_code_text)

        credit_limit = Decimal(self.credit_input.text().strip() or '0')
        _date = parse_date(self.date_input.text().strip() or self.current_date)
        date_str = _date.strftime("%d-%m-%y")

        conn, cursor = db.get_connection()
        
        if self.is_update:
            query = """
                UPDATE vendors SET 
                    vnd_name=%s, 
                    vnd_email=%s, 
                    vnd_address=%s,
                    vnd_city=%s, 
                    vnd_country=%s, 
                    vnd_phone=%s,
                    vnd_whatsapp=%s,
                    vnd_type=%s, 
                    vnd_cnic=%s,
                    vnd_date=%s,
                    vnd_company=%s,
                    vnd_credit_limit=%s
                WHERE vnd_code=%s
            """
            values = (
                vendor_name, email, address, city,
                self.country_input.text().strip(),
                phone,
                self.whatsapp_input.text().strip(),
                vendor_type,
                self.cnic_input.text().strip(),
                date_str,
                company,
                credit_limit,
                self.vendor_code
            )
            message = "Vendor Updated Successfully!"
        else:
            query = """
                INSERT INTO vendors (
                    vnd_name, vnd_email, vnd_address, vnd_city,
                    vnd_country, vnd_phone, vnd_whatsapp, vnd_type,
                    vnd_cnic, vnd_date, vnd_company, vnd_credit_limit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                vendor_name, email, address, city,
                self.country_input.text().strip(),
                phone,
                self.whatsapp_input.text().strip(),
                vendor_type,
                self.cnic_input.text().strip(),
                date_str,
                company,
                credit_limit
            )
            message = "Vendor Added Successfully!"

        try:
            cursor.execute(query, values)
            conn.commit()
            QMessageBox.information(self, "Success", message)
            self.clear_vendor()
        except Exception as e:
            if "Duplicate" in str(e) or "UNIQUE" in str(e):
                QMessageBox.warning(self, "Duplicate Error", "Vendor Email already exists. Please use a different email.")
            else:
                raise

    @handle_errors
    def clear_vendor(self):
        self.name_input.clear()
        self.code_input.clear()
        self.address_input.clear()
        self.city_input.clear()
        self.country_input.clear()
        self.phone_input.clear()
        self.whatsapp_input.clear()
        self.email_input.clear()
        self.cnic_input.clear()
        self.credit_input.clear()
        
        self.type_input.setCurrentIndex(0)
        self.company_input.setCurrentIndex(0)
        
        self.date_input.setText(self.current_date)
        self.is_update = False
        self.vendor_code = None
        self.name_input.setFocus()

    @handle_errors
    def refresh_vendor(self):
        self._load_data()
        self.company_input.blockSignals(True)
        self.company_input.clear()
        self.company_input.addItem("Choose Company")
        for company in self.company_data:
            self.company_input.addItem(company)
        self.company_input.blockSignals(False)
        
        # Also update type combo if needed
        self.type_input.blockSignals(True)
        self.type_input.clear()
        self.type_input.addItem("Select Type")
        for type_name in self.type_data:
            self.type_input.addItem(type_name)
        self.type_input.blockSignals(False)
        
        self.clear_vendor()
        QMessageBox.information(self, "Info", "Data refreshed successfully")