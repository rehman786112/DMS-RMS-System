# customers_ui.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from database import DatabaseManager
from predefined_widgets import Suggestion
from datetime import datetime
from decimal import Decimal
import traceback
import logging
import re
import functools

# Setup logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('customer_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

db = DatabaseManager()


# ============================================
# ERROR HANDLING DECORATOR
# ============================================
def handle_errors(func):
    """Decorator to handle errors in customer UI methods"""
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
        self._popup_view = None
        self._line_edit = None
        self._filter_text = ""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Get the line edit and setup search
        self._line_edit = self.lineEdit()
        self._line_edit.textEdited.connect(self._filter_items)
        self._line_edit.returnPressed.connect(self._select_first_match)
        
        # Style to match QLineEdit
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
        
        # Clear and re-add matching items
        super().clear()
        
        if not self._filter_text:
            super().addItems(self._items)
            return
        
        # Find matches (case insensitive)
        matches = []
        for item in self._items:
            if self._filter_text in item.lower():
                matches.append(item)
        
        if matches:
            super().addItems(matches)
            # Show popup with matches
            self.showPopup()
        else:
            # No matches - show empty popup or placeholder
            super().addItem("No matches found")
            self.showPopup()
    
    def _select_first_match(self):
        """Select first item when Enter pressed"""
        if self.count() > 0:
            current_text = self._line_edit.text()
            # Find exact or partial match
            for i in range(self.count()):
                item_text = self.itemText(i)
                if item_text.lower() == current_text.lower():
                    self.setCurrentIndex(i)
                    break
            else:
                # No exact match, select first
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


class Customers(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.type_data = []
            self.areas_data = []
            self.conn, self._cursor = db.get_connection()
            self.customer_code = None
            self.sub_areas_data = []
            self.is_update = False
            self._load_data()
            self.setup_ui()
            self.setup_enter_navigation()
        except Exception as e:
            logger.error(f"Error in __init__: {e}\n{traceback.format_exc()}")
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
        
        self.main_label = QLabel("Customer Registration")
        self.main_label.setStyleSheet("color: black; font-size:30px; font-weight:bold")
        self.main_label.setObjectName("tablabels")
        self.main_label.setFixedHeight(40)
        
        self.existing_btn = QPushButton("Show Existing Customers")
        self.existing_btn.setFixedSize(200, 40)
        self.existing_btn.clicked.connect(self.get_existing_customers)
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

        # Customer Details
        self.detail_label = QLabel("Customer Details:")
        self.detail_label.setMinimumHeight(40)
        self.detail_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        self.detail_label.setObjectName("customerdetaillabel")
        self.registration_layout.addWidget(self.detail_label)

        # Detail Grid
        self.detail_widget = QWidget()
        self.detail_layout = QGridLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 10, 0, 10)
        self.detail_layout.setVerticalSpacing(15)
        self.detail_layout.setHorizontalSpacing(30)

        # Input fields
        self.code_widget, self.code_input = self.create_input_field("*Code", "Customer Code..")
        self.code_input.setEnabled(False)
        
        self.name_widget, self.name_input = self.create_input_field("*Name", "Enter customer name....")
        self.address_widget, self.address_input = self.create_input_field("*Address", "Enter customer address....")
        self.city_widget, self.city_input = self.create_input_field("*City", "Enter City....")
        self.country_widget, self.country_input = self.create_input_field("Country", "Enter country....")
        self.phone_widget, self.phone_input = self.create_input_field("*Phone", "Enter Customer Phone number..")
        self.whatsapp_widget, self.whatsapp_input = self.create_input_field("WhatsApp", "Enter WhatsApp number..")
        self.email_widget, self.email_input = self.create_input_field("*Email", "Enter Customer Email...")
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
        self.area_widget, self.area_input = self.create_combo_field("*Area", self.areas_data, "Choose customer area")
        self.area_input.currentTextChanged.connect(self._on_area_select)
        self.sub_area_widget, self.sub_area_input = self.create_combo_field("*Sub Area", [], "Choose Sub Area")
        self.credit_widget, self.credit_input = self.create_input_field("*Credit limit", "Enter Credit Limit...")
        self.date_widget, self.date_input = self.create_input_field("Date", "Enter today date (e.g., 25-12-24)...")
        self.date_input.setText(self.current_date)

        self.additional_layout.addWidget(self.cnic_widget, 0, 0)
        self.additional_layout.addWidget(self.area_widget, 1, 0)
        self.additional_layout.addWidget(self.sub_area_widget, 1, 1)
        self.additional_layout.addWidget(self.credit_widget, 2, 0)
        self.additional_layout.addWidget(self.date_widget, 2, 1)

        self.registration_layout.addWidget(self.detail_widget)
        self.registration_layout.addWidget(self.additional_label)
        self.registration_layout.addWidget(self.additional_widget)
        self.main_layout.addWidget(self.registration_widget)

        # Footer
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
        self.detail_info = QLabel("First Choose the Area to Show related Sub areas")
        self.detail_info.setObjectName("footerlabelscustomers")
        self.info_layout.addWidget(self.detail_info)
        self.footer_layout.addWidget(self.info_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        self.btn_widget = QWidget()
        self.btn_widget.setFixedHeight(60)
        self.btn_widget.setFixedWidth(500)
        self.btn_layout = QHBoxLayout(self.btn_widget)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)

        self.clear_btn = self.create_button("Clear", "CTRL + Y", "clearbtncustomer", self.clear_customer)
        self.refresh_btn = self.create_button("Refresh", "CTRL + R", "refreshbtncustomer", self.refresh_customer)
        self.save_btn = self.create_button("Save", "CTRL + S", "savebtncustomer", self.save_data)

        self.btn_layout.addWidget(self.clear_btn[0])
        self.btn_layout.addWidget(self.refresh_btn[0])
        self.btn_layout.addWidget(self.save_btn[0])
        self.footer_layout.addWidget(self.btn_widget)
        self.main_layout.addWidget(self.footer_widget)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+y"), self).activated.connect(self.clear_customer)
        QShortcut(QKeySequence("Ctrl+r"), self).activated.connect(self.refresh_customer)
        QShortcut(QKeySequence("Ctrl+s"), self).activated.connect(self.save_data)

        # Stretch
        self.detail_layout.setColumnStretch(0, 1)
        self.detail_layout.setColumnStretch(1, 1)
        self.additional_layout.setColumnStretch(0, 1)
        self.additional_layout.setColumnStretch(1, 1)

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
        layout.setContentsMargins(0, 0, 10, 0)  # Same margins as input field
        layout.setSpacing(15)  # Same spacing as input field

        label_widget = QLabel(label)
        label_widget.setObjectName("input_labels_customers")
        label_widget.setMinimumWidth(100)  # Same as input field label
        label_widget.setMaximumWidth(120)  # Same as input field label
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label_widget)

        # Use SearchableComboBox instead of QComboBox
        combo = SearchableComboBox()
        combo.setMinimumHeight(35)  # Same as input field
        combo.setObjectName("input_fields_customers")  # Same object name for styling
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
        try:
            self._cursor.execute("SELECT area_name FROM areas ORDER BY area_name;")
            data = self._cursor.fetchall()
            self.areas_data.clear()
            if data:
                for item in data:
                    self.areas_data.append(str(item['area_name']))
            self.current_date = datetime.now().strftime("%d-%m-%y")
        except Exception as e:
            logger.error(f"Error in _load_data: {e}")
            self.areas_data = []
            self.current_date = datetime.now().strftime("%d-%m-%y")
        try:
            self._cursor.execute("SELECT type_name FROM customer_type")
            areas = self._cursor.fetchall()
            self.type_data.clear()
            for i in areas:
                self.type_data.append(i['type_name'])
        except Exception as e:
            print(e)

    @handle_errors
    def get_existing_customers(self,checked=False):
        self.customer_widget = Suggestion(
            "SELECT * FROM customers ORDER BY cus_name", 
            "Customer",
            display_columns=['cus_code', 'cus_name', 'cus_city']
        )
        self.customer_widget.show()
        self.customer_widget.sent_data.connect(self.receive_customer_data)

    @handle_errors
    def receive_customer_data(self, data):
        if not data or len(data) < 3:
            QMessageBox.warning(self, "Error", "Invalid customer data received")
            return
        
        self.customer_widget.close()
        
        customer_code = data[0]
        
        if not customer_code:
            QMessageBox.warning(self, "Error", "Invalid customer code")
            return
        
        self._cursor.execute(
            "SELECT cus_code, cus_name, cus_email, cus_address, cus_city, cus_country, "
            "cus_type, cus_cnic, cus_area, cus_sub_area, cus_credit_limit, cus_date, "
            "phone, cus_whatsapp FROM customers WHERE cus_code = %s",
            (customer_code,)
        )
        customer_data = self._cursor.fetchone()
        
        if not customer_data:
            QMessageBox.warning(self, "Error", f"Customer with code {customer_code} not found")
            return
        
        self.code_input.setText(str(customer_data.get('cus_code', '')))
        self.name_input.setText(str(customer_data.get('cus_name', '')))
        self.email_input.setText(str(customer_data.get('cus_email', '')))
        self.address_input.setText(str(customer_data.get('cus_address', '')))
        self.city_input.setText(str(customer_data.get('cus_city', '')))
        self.country_input.setText(str(customer_data.get('cus_country', '')))
        
        customer_type = customer_data.get('cus_type', '')
        if customer_type:
            index = self.type_input.findText(str(customer_type))
            if index >= 0:
                self.type_input.setCurrentIndex(index)
        else:
            self.type_input.setCurrentIndex(0)
        
        self.cnic_input.setText(str(customer_data.get('cus_cnic', '')))
        
        area = customer_data.get('cus_area', '')
        if area:
            index = self.area_input.findText(str(area))
            if index >= 0:
                self.area_input.setCurrentIndex(index)
        
        sub_area = customer_data.get('cus_sub_area', '')
        if sub_area:
            QTimer.singleShot(100, lambda: self._set_sub_area(sub_area))
        
        self.credit_input.setText(str(customer_data.get('cus_credit_limit', '0')))
        
        cus_date = customer_data.get('cus_date')
        if cus_date:
            if hasattr(cus_date, 'strftime'):
                self.date_input.setText(cus_date.strftime("%d-%m-%y"))
            else:
                self.date_input.setText(parse_date(str(cus_date)).strftime("%d-%m-%y"))
        else:
            self.date_input.setText(self.current_date)
        
        self.phone_input.setText(str(customer_data.get('phone', '')))
        self.whatsapp_input.setText(str(customer_data.get('cus_whatsapp', '')))
        
        self.is_update = True
        self.customer_code = int(customer_code)
        
        QMessageBox.information(self, "Success", f"Customer {customer_code} loaded successfully!")

    @handle_errors
    def _set_sub_area(self, sub_area):
        if sub_area:
            index = self.sub_area_input.findText(str(sub_area))
            if index >= 0:
                self.sub_area_input.setCurrentIndex(index)

    def validate_data(self):
        errors = []
        if not self.name_input.text().strip():
            errors.append("Customer Name is required")
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

        area = self.area_input.currentText()
        sub_area = self.sub_area_input.currentText()
        
        if area == "Choose customer area" or not area:
            QMessageBox.warning(self, "Validation Error", "Please select a valid Area")
            return
        if sub_area == "Choose Sub Area" or not sub_area:
            QMessageBox.warning(self, "Validation Error", "Please select a valid Sub Area")
            return

        customer_id = self.code_input.text().strip()
        self.customer_code = int(customer_id) if customer_id else None
        self.is_update = bool(customer_id)

        credit_limit = Decimal(self.credit_input.text().strip() or '0')
        _date = parse_date(self.date_input.text().strip() or self.current_date)
        customer_name = self.name_input.text().strip()
        customer_email = self.email_input.text().strip()
        customer_address = self.address_input.text().strip()
        customer_city = self.city_input.text().strip()
        customer_country = self.country_input.text().strip()
        customer_type = self.type_input.currentText()
        customer_cnic = self.cnic_input.text()
        customer_area = self.area_input.currentText()
        customer_subarea = self.sub_area_input.currentText()
        date = _date.strftime("%d-%m-%y")
        phone = self.phone_input.text()
        whatsapp = self.whatsapp_input.text()

        if self.is_update:
            query = """
                UPDATE customers SET 
                    cus_name=%s, 
                    cus_email=%s, 
                    cus_address=%s,
                    cus_city=%s, 
                    cus_country=%s, 
                    cus_type=%s, 
                    cus_cnic=%s,
                    cus_area=%s, 
                    cus_sub_area=%s, 
                    cus_credit_limit=%s,
                    cus_date=%s, 
                    phone=%s,
                    cus_whatsapp=%s
                WHERE cus_code=%s
                """
            values = (customer_name, customer_email, customer_address, customer_city,
                     customer_country, customer_type, customer_cnic, customer_area,
                     customer_subarea, credit_limit, date, phone, whatsapp, customer_id)
            message = 'Record Updated Success...'
        else:
            query = """
                INSERT INTO customers (
                    cus_name, cus_email, cus_address, cus_city,
                    cus_country, cus_type, cus_cnic, cus_area, 
                    cus_sub_area, cus_credit_limit, cus_date, phone, cus_whatsapp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (customer_name, customer_email, customer_address, customer_city,
                     customer_country, customer_type, customer_cnic, customer_area,
                     customer_subarea, credit_limit, date, phone, whatsapp)
            message = 'Record Added Success...'
        
        self._cursor.execute(query, values)
        self.conn.commit()
        QMessageBox.information(self, 'Success', message)
        self.clear_customer()

    @handle_errors
    def _on_area_select(self, text):
        self.sub_area_input.clear()
        self.sub_area_input.addItem("Choose Sub Area")
        
        if not text or "choose" in text.lower():
            return

        self._cursor.execute(
            "SELECT sub_area_name FROM sub_areas WHERE area_name = %s ORDER BY sub_area_name",
            (str(text),)
        )
        sub_areas = self._cursor.fetchall()
        
        for item in sub_areas or []:
            self.sub_area_input.addItem(str(item['sub_area_name']))

    @handle_errors
    def clear_customer(self):
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
        self.area_input.setCurrentIndex(0)
        
        self.sub_area_input.blockSignals(True)
        self.sub_area_input.clear()
        self.sub_area_input.addItem("Choose Sub Area")
        self.sub_area_input.blockSignals(False)
        
        self.date_input.setText(self.current_date)
        self.is_update = False
        self.customer_code = None
        self.name_input.setFocus()

    @handle_errors
    def refresh_customer(self):
        self._load_data()
        self.area_input.blockSignals(True)
        self.area_input.clear()
        self.area_input.addItem("Choose customer area")
        for area in self.areas_data:
            self.area_input.addItem(area)
        self.area_input.blockSignals(False)
        
        # Also update type combo
        self.type_input.blockSignals(True)
        self.type_input.clear()
        self.type_input.addItem("Select Type")
        for type_name in self.type_data:
            self.type_input.addItem(type_name)
        self.type_input.blockSignals(False)
        
        self.clear_customer()
        QMessageBox.information(self, "Info", "Data refreshed successfully")