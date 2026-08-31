# customers.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from database import DatabaseManager
from predefined_widgets import Suggestion
from datetime import datetime
from decimal import Decimal
import traceback
import logging
import functools
from Add_Types import AddDetails

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('customer_errors.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

db = DatabaseManager()


# ============================================================
# ERROR HANDLING DECORATOR
# ============================================================
def handle_errors(func):
    """Wrap a widget method: on exception, show a friendly QMessageBox
    instead of crashing, and always log the real traceback."""
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
                self, f"Error - {action}",
                f"Something went wrong while:\n   {action}\n\n"
                f"What this usually means:\n   {explanation}\n\n"
                f"Technical details:\n   {type(e).__name__}: {e}"
            )
            return None
    return wrapper


# ============================================================
# SEARCHABLE COMBOBOX
# ============================================================
class SearchableComboBox(QComboBox):
    """ComboBox with type-to-filter search. `_items` always mirrors the full
    (unfiltered) item list so filtering and refreshing never fall out of
    sync with what's actually shown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._filter_text = ""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self._line_edit = self.lineEdit()
        self._line_edit.textEdited.connect(self._filter_items)
        self._line_edit.returnPressed.connect(self._select_first_match)

        self.setStyleSheet("""
            QComboBox { min-height: 25px; padding: 5px; }
            QComboBox::drop-down { width: 20px; }
            QComboBox QLineEdit { padding: 2px; }
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
        matches = [item for item in self._items if self._filter_text in item.lower()]
        if matches:
            super().addItems(matches)
            self.showPopup()
        else:
            super().addItem("No matches found")
            self.showPopup()

    def _select_first_match(self):
        if self.count() == 0:
            return
        current_text = self._line_edit.text()
        for i in range(self.count()):
            if self.itemText(i).lower() == current_text.lower():
                self.setCurrentIndex(i)
                return
        self.setCurrentIndex(0)

    def setCurrentIndex(self, index):
        super().setCurrentIndex(index)
        if 0 <= index < self.count() and self._line_edit:
            self._line_edit.setText(self.itemText(index))

    def setCurrentText(self, text):
        super().setCurrentText(text)
        if self._line_edit:
            self._line_edit.setText(text)


def parse_date(date_string):
    """Parse DD-MM-YY (or DD-MM-YYYY as a fallback). Empty string -> today."""
    if not date_string or not date_string.strip():
        return datetime.now().date()
    date_string = date_string.strip()
    for fmt in ("%d-%m-%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{date_string}'. Please use DD-MM-YY format (e.g., 25-12-24)")


# ============================================================
# CUSTOMERS WIDGET
# ============================================================
class Customers(QWidget):

    # ---- placeholders used consistently everywhere the combos are built ----
    TYPE_PLACEHOLDER = "Select Type"
    AREA_PLACEHOLDER = "Choose customer area"
    SUB_AREA_PLACEHOLDER = "Choose Sub Area"

    def __init__(self):
        super().__init__()
        try:
            # 1. plain python state
            self.type_data = []
            self.areas_data = []
            self.sub_areas_data = []
            self.customer_code = None
            self.is_update = False

            # 2. current date
            self.current_date = datetime.now().strftime("%d-%m-%y")

            # 3. database connection
            self.conn, self._cursor = db.get_connection()

            # 4. load data into plain python lists (no widgets exist yet)
            self.load_areas()
            self.load_types()

            # 5. build the UI
            self.setup_ui()

            # 6. populate the comboboxes from the lists we already loaded
            self.update_type_combo(preserve_selection=False)
            self.update_area_combo(preserve_selection=False)

            # 7. wiring / shortcuts / tab order
            self.setup_enter_navigation()
        except Exception as e:
            logger.error(f"Error in __init__: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize: {str(e)}")

    # ================================================================
    # DATABASE HELPERS
    # ================================================================
    def _fresh_cursor(self):
        """Return a cursor guaranteed to see the latest committed data.

        Two different things can make a widget "not see" a row another
        window just inserted, even after that window has committed:
          1. This widget's own connection is sitting inside an open
             transaction (REPEATABLE READ), so it keeps re-using the
             snapshot it took on its *first* query.
          2. The connection object itself is stale / recycled.

        Re-asking DatabaseManager for a connection AND committing first
        defends against both, regardless of how DatabaseManager is
        implemented internally.
        """
        try:
            self.conn, self._cursor = db.get_connection()
        except Exception as e:
            logger.error(f"Could not obtain a fresh connection: {e}")
        try:
            self.conn.commit()
        except Exception:
            pass
        return self._cursor

    def execute_query(self, query, params=None, fetch="all"):
        """Run a query with a guaranteed-fresh cursor.
        fetch: 'all' | 'one' | None (None = no fetch, e.g. INSERT/UPDATE)"""
        cursor = self._fresh_cursor()
        cursor.execute(query, params or ())
        if fetch == "all":
            return cursor.fetchall() or []
        if fetch == "one":
            return cursor.fetchone()
        return None

    # ================================================================
    # DATA LOADING — pure data, never touches a widget
    # ================================================================
    def load_areas(self):
        try:
            rows = self.execute_query("SELECT area_name FROM areas ORDER BY area_name")
            self.areas_data = [str(r['area_name']) for r in rows]
        except Exception as e:
            logger.error(f"load_areas error: {e}")
            self.areas_data = []

    def load_types(self):
        try:
            rows = self.execute_query("SELECT type_name FROM customer_type WHERE is_active = true ORDER BY type_name")
            self.type_data = [str(r['type_name']) for r in rows]
        except Exception as e:
            logger.error(f"load_types error: {e}")
            self.type_data = []

    def load_sub_areas(self, area_name):
        try:
            rows = self.execute_query(
                "SELECT sub_area_name FROM sub_areas WHERE area_name = %s ORDER BY sub_area_name",
                (area_name,)
            )
            return [str(r['sub_area_name']) for r in rows]
        except Exception as e:
            logger.error(f"load_sub_areas error: {e}")
            return []

    # ================================================================
    # COMBOBOX UPDATES — the only place that touches type_input/area_input
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

    def update_area_combo(self, preserve_selection=True):
        self._rebuild_combo(self.area_input, self.AREA_PLACEHOLDER, self.areas_data, preserve_selection)

    @handle_errors
    def refresh_types(self):
        """Connected to AddDetails.save_signal — fires right after a new
        type is committed to the DB, so the combo updates immediately."""
        self.load_types()
        self.update_type_combo()

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

        QShortcut(QKeySequence("Ctrl+y"), self).activated.connect(self.clear_customer)
        QShortcut(QKeySequence("Ctrl+r"), self).activated.connect(self.refresh_customer)
        QShortcut(QKeySequence("Ctrl+s"), self).activated.connect(self.save_data)

    def _build_header(self):
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

        # --- Customer Details ---
        self.detail_label = QLabel("Customer Details:")
        self.detail_label.setMinimumHeight(40)
        self.detail_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        self.detail_label.setObjectName("customerdetaillabel")
        self.registration_layout.addWidget(self.detail_label)

        self.detail_widget = QWidget()
        self.detail_layout = QGridLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 10, 0, 10)
        self.detail_layout.setVerticalSpacing(15)
        self.detail_layout.setHorizontalSpacing(30)

        self.code_widget, self.code_input = self.create_input_field("*Code", "Customer Code..")
        self.code_input.setEnabled(False)
        self.name_widget, self.name_input = self.create_input_field("*Name", "Enter customer name....")
        self.address_widget, self.address_input = self.create_input_field("*Address", "Enter customer address....")
        self.city_widget, self.city_input = self.create_input_field("*City", "Enter City....")
        self.country_widget, self.country_input = self.create_input_field("Country", "Enter country....")
        self.phone_widget, self.phone_input = self.create_input_field("*Phone", "Enter Customer Phone number..")
        self.whatsapp_widget, self.whatsapp_input = self.create_input_field("WhatsApp", "Enter WhatsApp number..")
        self.email_widget, self.email_input = self.create_input_field("*Email", "Enter Customer Email...")
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
        self.area_widget, self.area_input = self.create_combo_field("*Area", self.areas_data, self.AREA_PLACEHOLDER)
        self.area_input.currentTextChanged.connect(self._on_area_select)
        self.sub_area_widget, self.sub_area_input = self.create_combo_field("*Sub Area", [], self.SUB_AREA_PLACEHOLDER)
        self.credit_widget, self.credit_input = self.create_input_field("*Credit limit", "Enter Credit Limit...")
        self.date_widget, self.date_input = self.create_input_field("Date", "Enter today date (e.g., 25-12-24)...")
        self.date_input.setText(self.current_date)

        self.additional_layout.addWidget(self.cnic_widget, 0, 0)
        self.additional_layout.addWidget(self.area_widget, 1, 0)
        self.additional_layout.addWidget(self.sub_area_widget, 1, 1)
        self.additional_layout.addWidget(self.credit_widget, 2, 0)
        self.additional_layout.addWidget(self.date_widget, 2, 1)
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
    # ADD TYPE
    # ================================================================
    @handle_errors
    def save_type_data(self, checked=False):
        """Open the 'Add Type' window. AddDetails only emits save_signal
        AFTER its DB commit, so refresh_types() always sees the new row."""
        self.add_type_widget = AddDetails('customer_type')
        self.add_type_widget.save_signal.connect(self.refresh_types)
        self.add_type_widget.show()

    # ================================================================
    # EXISTING CUSTOMER LOOKUP
    # ================================================================
    @handle_errors
    def get_existing_customers(self, checked=False):
        self.customer_widget = Suggestion(
            "SELECT * FROM customers ORDER BY cus_name",
            "Customer",
            display_columns=['cus_code', 'cus_name', 'cus_city']
        )
        self.customer_widget.sent_data.connect(self.receive_customer_data)
        self.customer_widget.show()

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

        customer_data = self.execute_query(
            "SELECT cus_code, cus_name, cus_email, cus_address, cus_city, cus_country, "
            "cus_type, cus_cnic, cus_area, cus_sub_area, cus_credit_limit, cus_date, "
            "phone, cus_whatsapp FROM customers WHERE cus_code = %s",
            (customer_code,), fetch="one"
        )
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
            self.type_input.setCurrentIndex(index if index >= 0 else 0)
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

    # ================================================================
    # VALIDATION / SAVE
    # ================================================================
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

        if area == self.AREA_PLACEHOLDER or not area:
            QMessageBox.warning(self, "Validation Error", "Please select a valid Area")
            return
        if sub_area == self.SUB_AREA_PLACEHOLDER or not sub_area:
            QMessageBox.warning(self, "Validation Error", "Please select a valid Sub Area")
            return

        customer_id = self.code_input.text().strip()
        self.customer_code = int(customer_id) if customer_id else None
        self.is_update = bool(customer_id)

        credit_limit = Decimal(self.credit_input.text().strip() or '0')
        _date = parse_date(self.date_input.text().strip() or self.current_date)
        date = _date.strftime("%d-%m-%y")

        values_common = (
            self.name_input.text().strip(),
            self.email_input.text().strip(),
            self.address_input.text().strip(),
            self.city_input.text().strip(),
            self.country_input.text().strip(),
            self.type_input.currentText(),
            self.cnic_input.text(),
            area,
            sub_area,
            credit_limit,
            date,
            self.phone_input.text(),
            self.whatsapp_input.text(),
        )

        if self.is_update:
            query = """
                UPDATE customers SET
                    cus_name=%s, cus_email=%s, cus_address=%s, cus_city=%s,
                    cus_country=%s, cus_type=%s, cus_cnic=%s, cus_area=%s,
                    cus_sub_area=%s, cus_credit_limit=%s, cus_date=%s,
                    phone=%s, cus_whatsapp=%s
                WHERE cus_code=%s
            """
            values = values_common + (customer_id,)
            message = 'Record Updated Success...'
        else:
            query = """
                INSERT INTO customers (
                    cus_name, cus_email, cus_address, cus_city, cus_country,
                    cus_type, cus_cnic, cus_area, cus_sub_area,
                    cus_credit_limit, cus_date, phone, cus_whatsapp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = values_common
            message = 'Record Added Success...'

        cursor = self._fresh_cursor()
        cursor.execute(query, values)
        self.conn.commit()
        QMessageBox.information(self, 'Success', message)
        self.clear_customer()

    # ================================================================
    # AREA / SUB-AREA CASCADE
    # ================================================================
    @handle_errors
    def _on_area_select(self, text):
        self.sub_area_input.clear()
        self.sub_area_input.addItem(self.SUB_AREA_PLACEHOLDER)

        if not text or text == self.AREA_PLACEHOLDER:
            return

        for sub_area in self.load_sub_areas(text):
            self.sub_area_input.addItem(sub_area)

    # ================================================================
    # CLEAR / REFRESH
    # ================================================================
    @handle_errors
    def clear_customer(self):
        for field in (self.name_input, self.code_input, self.address_input, self.city_input,
                      self.country_input, self.phone_input, self.whatsapp_input,
                      self.email_input, self.cnic_input, self.credit_input):
            field.clear()

        self.type_input.setCurrentIndex(0)
        self.area_input.setCurrentIndex(0)

        self.sub_area_input.blockSignals(True)
        self.sub_area_input.clear()
        self.sub_area_input.addItem(self.SUB_AREA_PLACEHOLDER)
        self.sub_area_input.blockSignals(False)

        self.date_input.setText(self.current_date)
        self.is_update = False
        self.customer_code = None
        self.name_input.setFocus()

    @handle_errors
    def refresh_customer(self, checked=False):
        self.current_date = datetime.now().strftime("%d-%m-%y")
        self.load_areas()
        self.load_types()
        self.update_area_combo(preserve_selection=False)
        self.update_type_combo(preserve_selection=False)
        self.clear_customer()
        QMessageBox.information(self, "Info", "Data refreshed successfully")
