# vendors_ui.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from databasemanager import DatabaseManager
from predefined_widgets import Suggestion
from datetime import datetime
from decimal import Decimal
import re

db = DatabaseManager()


def parse_date(date_string):
    if not date_string or date_string.strip() == "":
        return datetime.now().date()
    
    date_string = date_string.strip()
    date_formats = [
        "%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y",
        "%d-%m-%y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%y", "%d.%m.%Y",
        "%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%d %B %Y",
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format).date()
        except ValueError:
            continue
    
    try:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            return datetime.strptime(date_string, "%Y-%m-%d").date()
        elif re.match(r'^\d{2}/\d{2}/\d{4}$', date_string):
            return datetime.strptime(date_string, "%d/%m/%Y").date()
        elif re.match(r'^\d{2}/\d{2}/\d{2}$', date_string):
            return datetime.strptime(date_string, "%d/%m/%y").date()
    except:
        pass
    
    raise ValueError(f"Unable to parse date: '{date_string}'")


class Vendors(QWidget):
    def __init__(self):
        super().__init__()
        self.type_data = ['Corporate', 'Individual', 'Premium', 'Retail', 'WholeSale']
        self.company_data = []  # Changed from areas_data to company_data
        self.vendor_code = None
        self.is_update = False
        self._load_data()
        self.setup_ui()
        self.setup_enter_navigation()

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

        # Input fields - Updated for vendor schema
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
        self.date_widget, self.date_input = self.create_input_field("Date", "Enter today date...")
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        label_widget = QLabel(label)
        label_widget.setObjectName("input_labels_customers")
        label_widget.setMinimumWidth(100)
        label_widget.setMaximumWidth(120)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label_widget)

        combo = QComboBox()
        combo.setMinimumHeight(35)
        combo.setObjectName("input_field_customer")
        combo.addItem(placeholder)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
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

    def _load_data(self):
        """Load company data from vendors table"""
        try:
            # Get unique companies from vendors table
            data = db.get_any_table("SELECT DISTINCT vnd_company FROM vendors WHERE vnd_company IS NOT NULL AND vnd_company != '' ORDER BY vnd_company;")
            self.company_data.clear()
            if data:
                for item in data:
                    self.company_data.append(str(item['vnd_company']))
            self.current_date = datetime.now().strftime("%d/%m/%y")
        except Exception as e:
            print(f"Error loading company data: {e}")
            self.company_data = []
            self.current_date = datetime.now().strftime("%d/%m/%y")

    def get_existing_vendors(self):
        try:
            # Show only vnd_code, vnd_name, vnd_city
            self.vendor_widget = Suggestion(
                "SELECT vnd_code, vnd_name, vnd_city FROM vendors ORDER BY vnd_name", 
                "Vendors",
                display_columns=['vnd_code', 'vnd_name', 'vnd_city']
            )
            self.vendor_widget.show()
            self.vendor_widget.sent_data.connect(self.receive_vendor_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load vendors: {str(e)}")

    def receive_vendor_data(self, data):
        try:
            if not data or len(data) < 3:
                QMessageBox.warning(self, "Error", "Invalid vendor data received")
                return
            
            self.vendor_widget.close()
            
            # Get vendor code from the data
            vendor_code = data[0]
            
            if not vendor_code:
                QMessageBox.warning(self, "Error", "Invalid vendor code")
                return
            
            # Fetch full vendor data by code
            vendor_data = db.get_any_thing(
                "SELECT vnd_code, vnd_name, vnd_email, vnd_address, vnd_city, "
                "vnd_country, vnd_phone, vnd_whatsapp, vnd_type, vnd_cnic, "
                "vnd_date, vnd_company, vnd_credit_limit "
                "FROM vendors WHERE vnd_code = %s",
                vendor_code
            )
            
            if not vendor_data:
                QMessageBox.warning(self, "Error", f"Vendor with code {vendor_code} not found")
                return
            
            # Populate the form with full vendor data
            self.code_input.setText(str(vendor_data.get('vnd_code', '')))
            self.name_input.setText(str(vendor_data.get('vnd_name', '')))
            self.email_input.setText(str(vendor_data.get('vnd_email', '')))
            self.address_input.setText(str(vendor_data.get('vnd_address', '')))
            self.city_input.setText(str(vendor_data.get('vnd_city', '')))
            self.country_input.setText(str(vendor_data.get('vnd_country', '')))
            self.phone_input.setText(str(vendor_data.get('vnd_phone', '')))
            self.whatsapp_input.setText(str(vendor_data.get('vnd_whatsapp', '')))
            
            # Set vendor type
            vendor_type = vendor_data.get('vnd_type', '')
            if vendor_type:
                index = self.type_input.findText(str(vendor_type))
                if index >= 0:
                    self.type_input.setCurrentIndex(index)
            else:
                self.type_input.setCurrentIndex(0)
            
            self.cnic_input.setText(str(vendor_data.get('vnd_cnic', '')))
            
            # Set company
            company = vendor_data.get('vnd_company', '')
            if company:
                index = self.company_input.findText(str(company))
                if index >= 0:
                    self.company_input.setCurrentIndex(index)
            
            self.credit_input.setText(str(vendor_data.get('vnd_credit_limit', '0')))
            
            # Set date
            vnd_date = vendor_data.get('vnd_date')
            if vnd_date:
                if hasattr(vnd_date, 'strftime'):
                    self.date_input.setText(vnd_date.strftime("%d/%m/%y"))
                else:
                    self.date_input.setText(parse_date(str(vnd_date)).strftime("%d/%m/%y"))
            else:
                self.date_input.setText(self.current_date)
            
            self.is_update = True
            self.vendor_code = int(vendor_code)
            
            QMessageBox.information(self, "Success", f"Vendor {vendor_code} loaded successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load vendor data: {str(e)}")

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
        
        return errors

    def save_data(self):
        try:
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

            # Updated with WhatsApp parameter
            res = db.insert_update_vendors(
                self.vendor_code, 
                vendor_name, 
                email, 
                address, 
                city,
                self.country_input.text().strip(), 
                phone,
                self.whatsapp_input.text().strip(),  # WhatsApp
                vendor_type,
                self.cnic_input.text().strip(), 
                company, 
                credit_limit, 
                _date, 
                self.is_update
            )

            if res.get('Success', False):
                QMessageBox.information(self, "Success", "Vendor saved successfully!")
                self.clear_vendor()
                if hasattr(self, 'vendor_widget'):
                    self.vendor_widget.refresh_data()
            else:
                error_msg = res.get('message', 'Failed to save vendor')
                if res.get('error') == 'DUPLICATE_ENTRY':
                    QMessageBox.warning(self, "Duplicate Error", "Vendor Email already exists.")
                else:
                    QMessageBox.critical(self, "Error", error_msg)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save vendor: {str(e)}")

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

    def refresh_vendor(self):
        self._load_data()
        self.company_input.blockSignals(True)
        self.company_input.clear()
        self.company_input.addItem("Choose Company")
        for company in self.company_data:
            self.company_input.addItem(company)
        self.company_input.blockSignals(False)
        self.clear_vendor()
        QMessageBox.information(self, "Info", "Data refreshed successfully")