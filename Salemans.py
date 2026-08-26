# salesmen_ui.py
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
    """
    Parse date from multiple formats:
    - DD/MM/YY or DD/MM/YYYY
    - YYYY-MM-DD
    - MM/DD/YY or MM/DD/YYYY
    - DD-MM-YY or DD-MM-YYYY
    - DD.MM.YY or DD.MM.YYYY
    """
    if not date_string or date_string.strip() == "":
        return datetime.now().date()
    
    date_string = date_string.strip()
    
    # Try different date formats
    date_formats = [
        "%d/%m/%y",      # 20/08/26
        "%d/%m/%Y",      # 20/08/2026
        "%Y-%m-%d",      # 2026-08-20
        "%m/%d/%y",      # 08/20/26
        "%m/%d/%Y",      # 08/20/2026
        "%d-%m-%y",      # 20-08-26
        "%d-%m-%Y",      # 20-08-2026
        "%Y/%m/%d",      # 2026/08/20
        "%d.%m.%y",      # 20.08.26
        "%d.%m.%Y",      # 20.08.2026
        "%b %d, %Y",     # Aug 20, 2026
        "%d %b %Y",      # 20 Aug 2026
        "%B %d, %Y",     # August 20, 2026
        "%d %B %Y",      # 20 August 2026
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format).date()
        except ValueError:
            continue
    
    # If no format matches, try to detect and parse
    try:
        # Try to detect if it's YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            return datetime.strptime(date_string, "%Y-%m-%d").date()
        # Try to detect if it's DD/MM/YYYY format
        elif re.match(r'^\d{2}/\d{2}/\d{4}$', date_string):
            return datetime.strptime(date_string, "%d/%m/%Y").date()
        # Try to detect if it's DD/MM/YY format
        elif re.match(r'^\d{2}/\d{2}/\d{2}$', date_string):
            return datetime.strptime(date_string, "%d/%m/%y").date()
    except:
        pass
    
    # If all fails, raise error
    raise ValueError(f"Unable to parse date: '{date_string}'. Please use DD/MM/YY or YYYY-MM-DD format")


class Salemans(QWidget):
    def __init__(self):
        super().__init__()

        # Global data
        self.type_data = ['Corporate', 'Individual', 'Premium', 'Retail', 'WholeSale']
        self.company_data = []  # Changed from areas_data to company_data
        self.salesman_code = None
        self.is_update = False
        self._load_data()

        # Initialize data
        self.setObjectName("CustomerWidget")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # Salesman Registration
        self.registration_widget = QWidget()
        self.registration_layout = QVBoxLayout(self.registration_widget)
        self.registration_layout.setContentsMargins(0, 0, 0, 0)
        self.registration_layout.setSpacing(10)
        self.registration_widget.setObjectName("registration")

        # Salesman detail Label
        self.salesman_detail_label = QLabel("Salesman Details:")
        self.salesman_detail_label.setMinimumHeight(40)
        self.salesman_detail_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #1E293B;"
        )
        self.registration_layout.addWidget(self.salesman_detail_label)
        self.salesman_detail_label.setObjectName("customerdetaillabel")

        # Salesman Detail Widget
        self.salesman_detail_widget = QWidget()
        self.salesman_detail_layout = QGridLayout(self.salesman_detail_widget)
        self.salesman_detail_layout.setContentsMargins(0, 10, 0, 10)
        self.salesman_detail_layout.setVerticalSpacing(15)
        self.salesman_detail_layout.setHorizontalSpacing(30)

        # Salesman code field
        self.salesman_code_widget, self.salesman_code_value = self.input_fields(
            "*Code", "Salesman Code.."
        )
        self.salesman_code_value.setEnabled(False)

        # Salesman name field
        self.salesman_name_widget, self.salesman_name_value = self.input_fields(
            "*Name", "Enter Salesman name...."
        )

        # Salesman address field
        self.salesman_address_widget, self.salesman_address_value = self.input_fields(
            "*Address", "Enter Salesman address...."
        )

        # Salesman City Widget
        self.salesman_city_widget, self.salesman_city_value = self.input_fields(
            "*City", "Enter City...."
        )

        # Salesman Country input Widget
        self.salesman_country_widget, self.salesman_country_value = self.input_fields(
            "Country", "Enter country...."
        )

        # Salesman phone
        self.salesman_phone_widget, self.salesman_phone_value = self.input_fields(
            "*Phone", "Enter Salesman Phone number.."
        )

        # Salesman WhatsApp
        self.salesman_whatsapp_widget, self.salesman_whatsapp_value = self.input_fields(
            "WhatsApp", "Enter WhatsApp number.."
        )

        # Salesman Email
        self.salesman_email_widget, self.salesman_email_value = self.input_fields(
            "*Email", "Enter Salesman Email..."
        )

        # Salesman Type
        self.salesman_type_widget, self.salesman_type_value = self.selection_input(
            "*Type", self.type_data, "Select Type"
        )

        # Adding all input Widgets into details layout
        self.salesman_detail_layout.addWidget(self.salesman_code_widget, 0, 0)
        self.salesman_detail_layout.addWidget(self.salesman_name_widget, 0, 1)
        self.salesman_detail_layout.addWidget(self.salesman_address_widget, 1, 0)
        self.salesman_detail_layout.addWidget(self.salesman_city_widget, 1, 1)
        self.salesman_detail_layout.addWidget(self.salesman_country_widget, 2, 0)
        self.salesman_detail_layout.addWidget(self.salesman_phone_widget, 2, 1)
        self.salesman_detail_layout.addWidget(self.salesman_whatsapp_widget, 3, 0)
        self.salesman_detail_layout.addWidget(self.salesman_email_widget, 3, 1)
        self.salesman_detail_layout.addWidget(self.salesman_type_widget, 4, 0)

        self.salesman_additional_detail_label = QLabel("Additional Details:")
        self.salesman_additional_detail_label.setObjectName("customerdetaillabel")
        self.salesman_additional_detail_label.setMinimumHeight(40)
        self.salesman_additional_detail_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #1E293B;"
        )

        # Additional Detail Widget
        self.salesman_additional_detail_widget = QWidget()
        self.salesman_additional_detail_layout = QGridLayout(
            self.salesman_additional_detail_widget
        )
        self.salesman_additional_detail_layout.setContentsMargins(0, 10, 0, 10)
        self.salesman_additional_detail_layout.setVerticalSpacing(15)
        self.salesman_additional_detail_layout.setHorizontalSpacing(30)

        # CNIC input Widget
        self.salesman_cnic_widget, self.salesman_cnic_value = self.input_fields(
            "CNIC", "Enter CNIC..."
        )

        self.salesman_area_widget, self.salesman_area_value = self.selection_input(
            "*Company", self.company_data, "Choose Company"
        )

        self.salesman_credit_limit_widget, self.salesman_credit_limit_value = self.input_fields(
            "*Credit limit", "Enter Credit Limit..."
        )

        self.salesman_date_widget, self.salesman_date_value = self.input_fields(
            "Date", "Enter today date..."
        )
        self.salesman_date_value.setText(self.current_date)

        # adding to additional
        self.salesman_additional_detail_layout.addWidget(
            self.salesman_cnic_widget, 0, 0
        )
        self.salesman_additional_detail_layout.addWidget(
            self.salesman_area_widget, 1, 0
        )
        self.salesman_additional_detail_layout.addWidget(
            self.salesman_credit_limit_widget, 1, 1
        )
        self.salesman_additional_detail_layout.addWidget(
            self.salesman_date_widget, 2, 0
        )

        # Buttons footer Widgets
        self.footer_widget = QWidget()
        self.footer_widget.setObjectName("footerwidgetcustomer")
        self.footer_widget.setFixedHeight(70)
        self.footer_widget_layout = QHBoxLayout(self.footer_widget)
        self.footer_widget_layout.setContentsMargins(5, 5, 5, 5)

        self.info_labels_widget = QWidget()
        self.info_labels_layout = QVBoxLayout(self.info_labels_widget)

        self.info_label_ = QLabel("Short Keys")
        self.info_label_.setStyleSheet("""font-size:18px;font-weight:bold;""")

        self.info_labels_layout.addWidget(self.info_label_)

        self.detail_info_label_ = QLabel(
            "The Fields that contain * is Necessary."
        )
        self.detail_info_label_.setObjectName("footerlabelscustomers")
        self.info_labels_layout.addWidget(self.detail_info_label_)

        # Buttons with Short Keys
        self.shrt_buttons_widget = QWidget()
        self.shrt_buttons_widget.setFixedHeight(60)
        self.shrt_buttons_widget.setFixedWidth(500)
        self.shrt_buttons_widget.setStyleSheet("")
        self.shrt_buttons_layout = QHBoxLayout(self.shrt_buttons_widget)
        self.shrt_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.clear_btn_widget, self.clear_btn = self.buttons_with_shortkeys(
            "Clear", "CTRL + Y"
        )
        self.clear_btn.setObjectName("clearbtncustomer")

        self.refresh_btn_widget, self.refresh_btn = self.buttons_with_shortkeys(
            "Refresh", "CTRL + R"
        )
        self.refresh_btn.setObjectName("refreshbtncustomer")

        self.save_btn_widget, self.save_btn = self.buttons_with_shortkeys(
            "Save", "CTRL + S"
        )
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setObjectName("savebtncustomer")

        self.clear_btn.clicked.connect(self.clear_salesman)
        self.clear_shortcut = QShortcut(QKeySequence("Ctrl+y"), self)
        self.clear_shortcut.activated.connect(self.clear_salesman)
        self.refresh_btn.clicked.connect(self.refresh_salesman)
        self.refresh_shortcut = QShortcut(QKeySequence("Ctrl+r"), self)
        self.refresh_shortcut.activated.connect(self.refresh_salesman)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+s"), self)
        self.save_shortcut.activated.connect(self.save_data)

        # adding to footer Widget
        self.footer_widget_layout.addWidget(
            self.info_labels_widget,
            alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.shrt_buttons_layout.addWidget(self.clear_btn_widget)
        self.shrt_buttons_layout.addWidget(self.refresh_btn_widget)
        self.shrt_buttons_layout.addWidget(self.save_btn_widget)
        self.footer_widget_layout.addWidget(self.shrt_buttons_widget)

        # Adding salesman detail Widget into reg widget
        self.registration_layout.addWidget(self.salesman_detail_widget)
        self.registration_layout.addWidget(self.salesman_additional_detail_label)
        self.registration_layout.addWidget(self.salesman_additional_detail_widget)

        # Main Label
        self.label_widget = QWidget()
        self.label_widget_layout = QHBoxLayout(self.label_widget)
        self.label_widget.setMaximumHeight(60)

        self.main_label = QLabel("Salesman Registration")
        self.main_label.setStyleSheet(
            """color: black;
            font-size:30px;
            font-weight:bold"""
        )
        self.main_label.setObjectName("tablabels")
        self.main_label.setFixedHeight(40)

        self.get_existing_salesmen_button = QPushButton(
            "Show Existing Salesmen"
        )
        self.get_existing_salesmen_button.setFixedSize(200, 40)
        self.get_existing_salesmen_button.clicked.connect(
            self.get_existing_salesmen
        )
        self.get_existing_salesmen_button.setObjectName(
            "existingcustomerbtn"
        )

        self.label_widget_layout.addWidget(
            self.main_label,
            alignment=Qt.AlignmentFlag.AlignLeft
        )
        self.label_widget_layout.addWidget(
            self.get_existing_salesmen_button,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.main_layout.addWidget(self.label_widget)
        self.main_layout.addWidget(self.registration_widget)
        self.main_layout.addWidget(self.footer_widget)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.main_layout.setStretchFactor(self.label_widget, 0)
        self.main_layout.setStretchFactor(self.registration_widget, 1)

        self.salesman_detail_layout.setColumnStretch(0, 1)
        self.salesman_detail_layout.setColumnStretch(1, 1)
        self.salesman_additional_detail_layout.setColumnStretch(0, 1)
        self.salesman_additional_detail_layout.setColumnStretch(1, 1)

        # Setup Enter key navigation for all input widgets
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

    def buttons_with_shortkeys(self, button_name, shrt_key):
        button_widget = QWidget()
        button_widget.setFixedHeight(60)
        button_widget_layout = QVBoxLayout(button_widget)
        button_widget_layout.setContentsMargins(0, 0, 0, 0)
        button_widget_layout.setSpacing(10)

        button = QPushButton(button_name)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(80, 30)

        label = QLabel(shrt_key)
        label.setStyleSheet("""color:black;font-size:12px;""")

        button_widget_layout.addWidget(
            button,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        button_widget_layout.addWidget(
            label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        return button_widget, button

    def get_existing_salesmen(self):
        try:
            # Show only slm_code, slm_name, slm_city
            self.salesman_widget = Suggestion(
                "SELECT slm_code, slm_name, slm_city FROM salesmen ORDER BY slm_name",
                "Salesmen",
                display_columns=['slm_code', 'slm_name', 'slm_city']
            )
            self.salesman_widget.show()
            self.salesman_widget.sent_data.connect(
                self.receive_salesman_data
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load salesmen: {str(e)}")

    def receive_salesman_data(self, data):
        try:
            if not data or len(data) < 3:
                QMessageBox.warning(self, "Error", "Invalid salesman data received")
                return
            
            self.salesman_widget.close()
            
            # Get salesman code from the data
            salesman_code = data[0]
            
            if not salesman_code:
                QMessageBox.warning(self, "Error", "Invalid salesman code")
                return
            
            # Fetch full salesman data by code
            salesman_data = db.get_any_thing(
                "SELECT slm_code, slm_name, slm_email, slm_address, slm_city, "
                "slm_country, slm_phone, slm_whatsapp, slm_type, slm_cnic, "
                "slm_date, slm_company, slm_credit_limit "
                "FROM salesmen WHERE slm_code = %s",
                salesman_code
            )
            
            if not salesman_data:
                QMessageBox.warning(self, "Error", f"Salesman with code {salesman_code} not found")
                return
            
            # Populate the form with full salesman data
            self.salesman_code_value.setText(str(salesman_data.get('slm_code', '')))
            self.salesman_name_value.setText(str(salesman_data.get('slm_name', '')))
            self.salesman_email_value.setText(str(salesman_data.get('slm_email', '')))
            self.salesman_address_value.setText(str(salesman_data.get('slm_address', '')))
            self.salesman_city_value.setText(str(salesman_data.get('slm_city', '')))
            self.salesman_country_value.setText(str(salesman_data.get('slm_country', '')))
            self.salesman_phone_value.setText(str(salesman_data.get('slm_phone', '')))
            self.salesman_whatsapp_value.setText(str(salesman_data.get('slm_whatsapp', '')))
            
            # Set salesman type
            salesman_type = salesman_data.get('slm_type', '')
            if salesman_type:
                index = self.salesman_type_value.findText(str(salesman_type))
                if index >= 0:
                    self.salesman_type_value.setCurrentIndex(index)
            else:
                self.salesman_type_value.setCurrentIndex(0)
            
            self.salesman_cnic_value.setText(str(salesman_data.get('slm_cnic', '')))
            
            # Set company
            company = salesman_data.get('slm_company', '')
            if company:
                index = self.salesman_area_value.findText(str(company))
                if index >= 0:
                    self.salesman_area_value.setCurrentIndex(index)
            
            self.salesman_credit_limit_value.setText(str(salesman_data.get('slm_credit_limit', '0')))
            
            # Set date
            slm_date = salesman_data.get('slm_date')
            if slm_date:
                if hasattr(slm_date, 'strftime'):
                    self.salesman_date_value.setText(slm_date.strftime("%d/%m/%y"))
                else:
                    self.salesman_date_value.setText(parse_date(str(slm_date)).strftime("%d/%m/%y"))
            else:
                self.salesman_date_value.setText(self.current_date)
            
            self.is_update = True
            self.salesman_code = int(salesman_code)
            
            QMessageBox.information(self, "Success", f"Salesman {salesman_code} loaded successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load salesman data: {str(e)}")

    def save_data(self):
        try:
            # Get salesman code
            salesman_code_text = self.salesman_code_value.text()
            
            # Get other values
            salesman_name = self.salesman_name_value.text().strip()
            salesman_email = self.salesman_email_value.text().strip()
            address = self.salesman_address_value.text().strip()
            city = self.salesman_city_value.text().strip()
            country = self.salesman_country_value.text().strip()
            phone = self.salesman_phone_value.text().strip()
            whatsapp = self.salesman_whatsapp_value.text().strip()
            salesman_type = self.salesman_type_value.currentText()
            cnic = self.salesman_cnic_value.text().strip()
            company = self.salesman_area_value.currentText()
            
            # Validate required fields
            if not salesman_name or not address or not city or not phone or not salesman_email:
                QMessageBox.warning(self, "Validation Error", 
                                  "Please fill all required fields (*)")
                return
            
            # Validate email format
            if salesman_email and ('@' not in salesman_email or '.' not in salesman_email):
                QMessageBox.warning(self, "Validation Error", "Invalid email format")
                return
            
            if "choose" in salesman_type.lower() or salesman_type == "Select Type":
                QMessageBox.warning(self, "Validation Error", "Please Select the salesman type")
                return
            if "choose" in company.lower() or company == "Choose Company":
                QMessageBox.warning(self, "Validation Error", "Please Select a Company")
                return
                
            try:
                credit_limit = Decimal(self.salesman_credit_limit_value.text().strip() or '0')
                if credit_limit < 0:
                    QMessageBox.warning(self, "Validation Error", "Credit limit cannot be negative")
                    return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid credit limit: {e}")
                return
            
            # Parse date with multiple format support
            try:
                date_str = self.salesman_date_value.text().strip()
                if not date_str:
                    date_str = self.current_date
                _date = parse_date(date_str)
            except ValueError as e:
                QMessageBox.critical(self, "Error", 
                                   f"Invalid date format: {str(e)}\n\nPlease use DD/MM/YY or YYYY-MM-DD format")
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Date error: {str(e)}")
                return

            # Set salesman_code and is_update
            if salesman_code_text == "" or salesman_code_text is None:
                self.salesman_code = None
                self.is_update = False
            else:
                self.salesman_code = int(salesman_code_text)
                self.is_update = True
                
            if self.is_update:
                message = "Data Updated Successfully."
            else:
                message = "New Salesman Added Successfully"
                
            # Updated with WhatsApp parameter
            res = db.insert_update_salesmen(
                self.salesman_code,
                salesman_name,
                salesman_email,
                address,
                city,
                country,
                phone,
                whatsapp,  # WhatsApp
                salesman_type,
                cnic,
                company,
                credit_limit,
                _date,
                self.is_update
            )
            
            if res.get('Success', False):
                QMessageBox.information(self, "Success", f"{message}")
                self.clear_salesman()
                if hasattr(self, 'salesman_widget'):
                    self.salesman_widget.refresh_data()
            else:
                error_msg = res.get('message', 'Failed to save salesman')
                if res.get('error') == 'DUPLICATE_ENTRY':
                    QMessageBox.warning(self, "Duplicate Error", "Salesman Email already exists.")
                else:
                    QMessageBox.critical(self, "Error", error_msg)
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")

    def _load_data(self):
        """Load company data from salesmen table"""
        try:
            # Get unique companies from salesmen table
            data = db.get_any_table("SELECT DISTINCT slm_company FROM salesmen WHERE slm_company IS NOT NULL AND slm_company != '' ORDER BY slm_company;")
            self.company_data.clear()
            if data:
                for item in data:
                    self.company_data.append(str(item['slm_company']))
            
            from datetime import date
            self.current_date = date.today().strftime("%d/%m/%y")
        except Exception as e:
            print(f"Error loading company data: {e}")
            self.company_data = []
            self.current_date = datetime.now().strftime("%d/%m/%y")

    def clear_salesman(self):
        self.salesman_name_value.clear()
        self.salesman_code_value.clear()
        self.salesman_address_value.clear()
        self.salesman_city_value.clear()
        self.salesman_country_value.clear()
        self.salesman_phone_value.clear()
        self.salesman_whatsapp_value.clear()
        self.salesman_email_value.clear()
        self.salesman_cnic_value.clear()
        self.salesman_credit_limit_value.clear()

        self.salesman_type_value.setCurrentIndex(0)

        self.salesman_area_value.blockSignals(True)
        self.salesman_area_value.setCurrentIndex(0)
        self.salesman_area_value.blockSignals(False)

        self.salesman_date_value.setText(self.current_date)
        self.is_update = False
        self.salesman_code = None

        self.salesman_name_value.setFocus()

    def refresh_salesman(self):
        self._load_data()

        self.salesman_area_value.blockSignals(True)
        self.salesman_area_value.clear()
        self.salesman_area_value.addItem("Choose Company")

        for company in self.company_data:
            self.salesman_area_value.addItem(company)

        self.salesman_area_value.blockSignals(False)

        self.clear_salesman()
        QMessageBox.information(self, "Info", "Data refreshed successfully")

    def input_fields(self, label_name, placeholder):
        inputs_widget = QWidget()
        inputs_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        inputs_widget_layout = QHBoxLayout(inputs_widget)
        inputs_widget_layout.setContentsMargins(0, 0, 10, 0)
        inputs_widget_layout.setSpacing(15)

        input_label = QLabel(label_name)
        input_label.setObjectName("input_labels_customers")
        input_label.setMinimumWidth(100)
        input_label.setMaximumWidth(120)
        input_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )
        inputs_widget_layout.addWidget(input_label)

        input_field = QLineEdit()
        input_field.setMinimumHeight(35)
        input_field.setPlaceholderText(placeholder)
        input_field.setObjectName('input_fields_customers')
        input_field.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        inputs_widget_layout.addWidget(input_field)

        return inputs_widget, input_field

    def selection_input(self, label_name, data, placeholder):
        combo_input_widget = QWidget()
        combo_input_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        combo_input_layout = QHBoxLayout(combo_input_widget)
        combo_input_layout.setContentsMargins(0, 0, 0, 0)
        combo_input_layout.setSpacing(15)

        combo_label = QLabel(label_name)
        combo_label.setObjectName("input_labels_customers")
        combo_label.setMinimumWidth(100)
        combo_label.setMaximumWidth(120)
        combo_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )
        combo_input_layout.addWidget(combo_label)

        combo_input = QComboBox()
        combo_input.setMinimumHeight(35)
        combo_input.setObjectName("input_field_customer")
        combo_input.addItem(placeholder)
        combo_input.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        combo_input_layout.addWidget(combo_input)

        for i in data:
            combo_input.addItem(i)

        return combo_input_widget, combo_input