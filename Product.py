from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
from decimal import Decimal, InvalidOperation
from databasemanager import DatabaseManager


def load_stylesheet():
    with open('style.qss', 'r', encoding='utf-8') as f:
        return f.read()


db = DatabaseManager()


class Products(QMainWindow):
    def __init__(self):
        super().__init__()
        self._is_saving = False
        self._current_product_id = None
        self._selected_row = 0
        self.setup_ui()

    def setup_ui(self):
        self.setup_window()

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label_widget = self.Create_headers("PRODUCTS", "MainLabel", '35px')
        self.label_widget.setFixedHeight(50)

        self.product_main_widget = QWidget()
        self.product_main_layout = QHBoxLayout(self.product_main_widget)
        self.product_main_layout.setSpacing(0)
        self.product_main_layout.setContentsMargins(10, 5, 5, 10)
        self.product_main_widget.setObjectName("main_products_widget")

        self.product_details()
        self.product_description()

        self.main_layout.addWidget(self.label_widget)
        self.main_layout.addWidget(self.product_main_widget)

        self.footer_window()

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def setup_window(self):
        self.setWindowTitle("Products")
        self.setWindowIcon(QIcon("assets/icons/icon.png"))
        self.setMinimumSize(1500, 900)

    def product_details(self):
        self.product_detail = QWidget()
        self.product_detail.setFixedWidth(400)
        self.product_detail_layout = QVBoxLayout(self.product_detail)
        self.product_detail_layout.setContentsMargins(0, 0, 0, 0)
        self.product_detail_layout.setSpacing(0)

        self.product_name_search = QLineEdit()
        self.product_name_search.setFixedHeight(35)
        self.product_detail_layout.addWidget(self.product_name_search)

        self.product_detail_label_widget = self.Create_headers("Product Details", "detail-header", '18px')
        self.product_detail_label_widget.setContentsMargins(0, 15, 0, 0)
        self.product_detail_layout.addWidget(self.product_detail_label_widget)

        self.product_detail_view = QTableView()

        self._search_proxy = QSortFilterProxyModel()
        self._search_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_proxy.setFilterKeyColumn(-1)
        self.product_name_search.textChanged.connect(self._search_proxy.setFilterFixedString)

        self.view_model = TableModel("SELECT product_id, product_name from products")
        self._search_proxy.setSourceModel(self.view_model)
        self.product_detail_view.setModel(self._search_proxy)
        self.product_detail_layout.addWidget(self.product_detail_view)
        self.product_detail_view.verticalHeader().setVisible(False)
        self.product_detail_view.horizontalHeader().setVisible(False)
        self.product_detail_view.setColumnHidden(0, True)

        header = self.product_detail_view.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.product_detail_view.setShowGrid(False)
        self.product_detail_view.doubleClicked.connect(self.on_product_select)

        self.product_main_layout.addWidget(self.product_detail)

    def product_description(self):
        self.product_desc = QWidget()
        self.product_desc_layout = QVBoxLayout(self.product_desc)

        self.product_name_widget = QWidget()
        self.product_name_layout = QVBoxLayout(self.product_name_widget)

        self.product_desc_label_widget = self.Create_headers("Product Description", 'MainLabel', '20px')
        self.product_desc_label_widget.setFixedSize(200, 30)

        self.p_name_input, self.p_name = self._input_fields("Product Name:")
        self.p_name.textChanged.connect(self.on_update_product_name)
        self.p_name.setFixedWidth(500)
        self.p_name_input.setObjectName("ProductName")
        self.p_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.product_name_layout.addWidget(self.product_desc_label_widget)
        self.product_name_layout.addWidget(self.p_name_input, alignment=Qt.AlignmentFlag.AlignLeft)

        self.company_widget = QWidget()
        self.company_widget_layout = QVBoxLayout(self.company_widget)

        self.company_label = self.Create_headers("Group / Company / Gender / Unit", 'MainLabel', '20px')
        self.company_label.setFixedSize(320, 30)

        self.group_input_widget_company = QWidget()
        self.group_input_layout_company = QGridLayout(self.group_input_widget_company)

        self.group_code, self.group_code_value = self._input_fields("Group")
        self.group_code_value.textChanged.connect(lambda:self.on_text_change("group"))
        self.group_name, self.group_name_value = self._input_fields("Name")
        self.group_name_value.setReadOnly(True)

        self.company_code, self.company_code_value = self._input_fields("Company")
        self.company_code_value.textChanged.connect(lambda:self.on_text_change("company"))
        self.company_name, self.company_name_value = self._input_fields("Name")
        self.company_name_value.setReadOnly(True)

        self.gender_code, self.gender_code_value = self._input_fields("Gender")
        self.gender_code_value.textChanged.connect(lambda:self.on_text_change("gender"))
        self.gender_name, self.gender_name_value = self._input_fields("Name")
        self.gender_name_value.setReadOnly(True)

        self.unit_widget = QWidget()
        self.unit_widget_layout = QHBoxLayout(self.unit_widget)
        self.unit_widget_layout.addStretch()
        self.unit_widget_layout.setSpacing(10)

        self.unit_label = QLabel("Unit")
        self.unit_label.setStyleSheet("""
            font-size:16px;
            font-weight: 700;
            color: black;
        """)

        self.unit = QComboBox()
        self.unit.setFixedWidth(200)
        self.unit.addItems(["PCS"])
        self.unit_widget_layout.addWidget(self.unit_label)
        self.unit_widget_layout.addWidget(self.unit)

        self.pct_hs_code, self.pct_hs_code_value = self._input_fields("PCT / HS Code")

        self.add_group_btn = self.add_new_value_btns()
        self.add_group_btn.clicked.connect(lambda: self.add_new("Group"))
        self.add_company_btn = self.add_new_value_btns()
        self.add_company_btn.clicked.connect(lambda: self.add_new("company"))
        self.add_gender_btn = self.add_new_value_btns()
        self.add_gender_btn.clicked.connect(lambda: self.add_new("Gender"))

        self.group_input_layout_company.addWidget(self.group_code, 0, 0)
        self.group_input_layout_company.addWidget(self.group_name, 0, 1)
        self.group_input_layout_company.addWidget(self.add_group_btn, 0, 2)
        self.group_input_layout_company.addWidget(self.company_code, 1, 0)
        self.group_input_layout_company.addWidget(self.company_name, 1, 1)
        self.group_input_layout_company.addWidget(self.add_company_btn, 1, 2)
        self.group_input_layout_company.addWidget(self.gender_code, 2, 0)
        self.group_input_layout_company.addWidget(self.gender_name, 2, 1)
        self.group_input_layout_company.addWidget(self.add_gender_btn, 2, 2)
        self.group_input_layout_company.addWidget(self.unit_widget, 3, 0)
        self.group_input_layout_company.addWidget(self.pct_hs_code, 3, 1)

        self.company_widget_layout.addWidget(self.company_label)
        self.company_widget_layout.addWidget(self.group_input_widget_company, alignment=Qt.AlignmentFlag.AlignLeft)

        self.product_edit_view = QTableView()
        self.product_edit_model = QStandardItemModel(1, 9)
        self.product_edit_model.setHorizontalHeaderLabels([
            "Product ID", "Product Code", "Product Name", "Carton Size",
            "Unit Cost Price", "Unit Sale Price", "Re Order", "BarCode", "Is Active"
        ])
        self.product_edit_view.verticalHeader().setVisible(False)
        self.product_edit_view.setModel(self.product_edit_model)
        self.product_edit_view.setEditTriggers(QTableView.EditTrigger.DoubleClicked)

        self.product_edit_model.setItem(0, 0, self.create_item(None, readonly=True))
        self.product_edit_model.setItem(0, 2, self.create_item(None, readonly=True))
        self.product_edit_model.setItem(0, 8, self.create_item(True, checkbox=True))

        header = self.product_edit_view.horizontalHeader()
        header.setMinimumSectionSize(150)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.product_desc_layout.addWidget(self.product_name_widget)
        self.product_desc_layout.addWidget(self.company_widget)
        self.product_desc_layout.addWidget(self.product_edit_view)

        self.product_main_layout.addWidget(self.product_desc)

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
        self.footer_short_keys_header.setStyleSheet("font-size:15px; font-weight:bold;")

        self.footer_detail_header = QLabel("Select Row And Press Delete Button For Deleting Row")
        self.footer_detail_header.setStyleSheet("font-size:15px;")

        self.footer_detail_layout.addWidget(self.footer_short_keys_header)
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
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+s"),self)
        self.save_shortcut.activated.connect(self.save_data)
        self.footer_save_btn.clicked.connect(self.save_data)
        self.footer_save_btn.setObjectName("savebtn")

        self.footer_refresh_btn = QPushButton("Refresh")
        self.footer_refresh_btn.setFixedSize(90, 35)
        self.footer_refresh_btn.setCursor(self.btn_cursor)
        self.refresh_shortcut = QShortcut(QKeySequence("Ctrl+r"),self)
        self.refresh_shortcut.activated.connect(self.refresh_view)
        self.footer_refresh_btn.setObjectName("refreshbtn")
        self.footer_refresh_btn.clicked.connect(self.refresh_view)

        self.footer_delete_btn = QPushButton("Delete")
        self.footer_delete_btn.setFixedSize(90, 35)
        self.delete_shortcut = QShortcut(QKeySequence("Ctrl+d"),self)
        self.delete_shortcut.activated.connect(self.delete_product)
        self.footer_delete_btn.clicked.connect(self.delete_product)
        self.footer_delete_btn.setCursor(self.btn_cursor)
        self.footer_delete_btn.setObjectName("deletebtn")

        self.footer_save_action = QLabel("CTRL + S")
        self.footer_refresh_action = QLabel("CTRL + R")
        self.footer_delete_action = QLabel("CTRL + D")

        self.buttons_layout_footer.addWidget(self.footer_save_btn, 0, 0)
        self.buttons_layout_footer.addWidget(self.footer_refresh_btn, 0, 1)
        self.buttons_layout_footer.addWidget(self.footer_delete_btn, 0, 2)
        self.buttons_layout_footer.addWidget(self.footer_save_action, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.buttons_layout_footer.addWidget(self.footer_refresh_action, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.buttons_layout_footer.addWidget(self.footer_delete_action, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        self.footer_layout.addWidget(self.footer_detail_widget)
        self.footer_layout.addWidget(self.buttons_widget_footer)

        self.main_layout.addWidget(self.footer_widget)

    def add_new_value_btns(self):
        button = QPushButton("+")
        button.setObjectName("add_btn")
        button.setFixedSize(30, 30)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button
    def on_update_product_name(self):
        item = self.product_edit_model.item(0,2)
        if item == None:
            item = self.create_item("")
            self.product_edit_model.setItem(0,2,item)
        text = self.p_name.text()
        item.setText(text)
    def Create_headers(self, label_name, object_name_widget, font_size):
        header = QWidget()
        header.setObjectName(object_name_widget)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        label = QLabel(label_name)
        label.setStyleSheet(f"""
            color:white;
            font-weight:bold;
            font-size:{font_size}
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(label)

        return header

    def _input_fields(self, label_name):
        input_widget = QWidget()
        input_widget_layout = QHBoxLayout(input_widget)
        input_widget_layout.setSpacing(10)
        input_widget_layout.setContentsMargins(20, 0, 0, 0)
        input_widget_layout.addStretch()

        input_label = QLabel(label_name)
        input_label.setStyleSheet("color:black; font-size:16px; font-weight:700")

        line_edit = QLineEdit()
        line_edit.setFixedSize(250, 30)
        line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        input_widget_layout.addWidget(input_label)
        input_widget_layout.addWidget(line_edit)

        return input_widget, line_edit

    def add_new(self, _name):
        self.add_widget = AddDetails(_name)
        self.add_widget.show()

    def create_item(self, value, readonly=False, checkbox=False):
        item = QStandardItem()
        item.setText("" if value is None else str(value))
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        item.setData(value, Qt.ItemDataRole.UserRole)

        if readonly:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        if checkbox:
            item.setCheckable(True)
            item.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)
            item.setText("")

        return item

    def get_typed_value(self, item):
        if item is None:
            return None

        if item.isCheckable():
            return item.checkState() == Qt.CheckState.Checked

        text = item.text().strip()
        original_value = item.data(Qt.ItemDataRole.UserRole)

        if text == "":
            return None

        if isinstance(original_value, bool):
            return text.lower() in ("true", "1", "yes")

        if isinstance(original_value, int):
            try:
                return int(text)
            except ValueError:
                return None

        if isinstance(original_value, Decimal):
            try:
                return Decimal(text)
            except InvalidOperation:
                return None

        if isinstance(original_value, float):
            try:
                return float(text)
            except ValueError:
                return None

        return text

    def on_product_select(self, index):
        proxy = self.product_detail_view.model()
        if not proxy:
            return

        source_index = proxy.mapToSource(index)
        if not source_index.isValid():
            return

        product_id = proxy.index(index.row(), 0).data()
        if product_id is None:
            return

        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            return

        product_data = db.get_product_by_id(product_id)
        if product_data is None:
            QMessageBox.critical(self, "Error", "Product not found or database error.")
            return

        product_company_data = db.get_product_other_by_id(product_id)
        if product_company_data is None:
            QMessageBox.critical(self, "Error", "Product details incomplete.")
            return

        try:
            company_id = product_company_data.get('company_id')
            company_name = product_company_data.get('company_description', '')
            group_id = product_company_data.get('group_id')
            group_name = product_company_data.get('group_description', '')

            self.company_code_value.setText(str(company_id) if company_id is not None else "")
            self.company_name_value.setText(company_name)
            self.group_code_value.setText(str(group_id) if group_id is not None else "")
            self.group_name_value.setText(group_name)
        except Exception:
            QMessageBox.critical(self, "Error", "Error loading product in edit view.")
            return

        self._current_product_id = product_id
        self.p_name.setText(product_data.get("product_name", ""))

        columns = [
            "product_id",
            "product_code",
            "product_name",
            "carton_size",
            "unit_cost_price",
            "unit_sale_price",
            "re_order",
            "barcode",
            "is_active",
        ]

        for col, key in enumerate(columns):
            value = product_data.get(key)
            if key == "product_id":
                item = self.create_item(value, readonly=True)
            elif key == "is_active":
                item = self.create_item(value, checkbox=True)
            elif key == "product_name":
                item = self.create_item(value,readonly=True)
            else:
                item = self.create_item(value)
            self.product_edit_model.setItem(0, col, item)
    def delete_product(self):
        if self._current_product_id == None:
            QMessageBox.information(self,"Message","Please Double click on row to select for Actions")
        else:
            reply = QMessageBox.question(self,"Confirm","Are You Sure to Delete this Product?",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del_res = db.delete_products(self._current_product_id)
                if del_res:
                    QMessageBox.information(self,"Success","Product Delete Success...")
                    self.refresh_view()
                else:
                    QMessageBox.critical(self,"Error","Unable to delete Record...")
                    self.refresh_view()
            else:
                return
    def refresh_view(self):
        self.p_name.setText("")
        self.company_name_value.setText("")
        self.company_code_value.setText("")
        self.group_name_value.setText("")
        self.group_code_value.setText("")
        self.gender_name_value.setText("")
        self.gender_code_value.setText("")
        for col in range(self.product_edit_model.columnCount()):
            if col == 0:
                item = self.create_item(None,readonly=True)
            elif col == 2:
                item = self.create_item(None,readonly=True)
            elif col == 8:
                item = self.create_item(True,checkbox=True)
            else:
                item = self.create_item(None)
            self.product_edit_model.setItem(0,col,item)
        self.view_model._load_data("SELECT product_id, product_name from products")

    def save_data(self):
        if self._is_saving:
            return

        self._is_saving = True
        try:
            self.footer_save_btn.setText("Saving...")
            self.footer_save_btn.setDisabled(True)

            row_data = []
            for col in range(self.product_edit_model.columnCount()):
                item = self.product_edit_model.item(0, col)
                if item:
                    value = self.get_typed_value(item)
                    row_data.append(value)
                else:
                    row_data.append(None)

            product_id = row_data[0]
            product_code = str(row_data[1] or "").strip()
            product_name = str(row_data[2] or "").strip()
            carton_size = row_data[3]
            unit_cost_price = row_data[4]
            unit_sale_price = row_data[5]
            re_order = row_data[6]
            barcode = str(row_data[7] or "").strip()
            is_active = row_data[8] if row_data[8] is not None else True

            if not product_name:
                QMessageBox.warning(self, "Validation Error", "Product Name is required.")
                return

            if not product_code:
                QMessageBox.warning(self, "Validation Error", "Product Code is required.")
                return

            group_id_text = self.group_code_value.text().strip()
            company_id_text = self.company_code_value.text().strip()

            if not group_id_text:
                QMessageBox.warning(self, "Validation Error", "Please select a Group.")
                return

            if not company_id_text:
                QMessageBox.warning(self, "Validation Error", "Please select a Company.")
                return

            try:
                group_id = int(group_id_text)
                company_id = int(company_id_text)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Invalid Group or Company ID.")
                return

            if carton_size is not None:
                try:
                    carton_size = int(carton_size)
                    if carton_size < 0:
                        QMessageBox.warning(self, "Validation Error", "Carton Size cannot be negative.")
                        return
                except (ValueError, TypeError):
                    QMessageBox.warning(self, "Validation Error", "Carton Size must be a valid number.")
                    return

            if unit_cost_price is not None:
                try:
                    unit_cost_price = Decimal(str(unit_cost_price))
                    if unit_cost_price < 0:
                        QMessageBox.warning(self, "Validation Error", "Unit Cost Price cannot be negative.")
                        return
                except (InvalidOperation, ValueError):
                    QMessageBox.warning(self, "Validation Error", "Unit Cost Price must be a valid number.")
                    return

            if unit_sale_price is not None:
                try:
                    unit_sale_price = Decimal(str(unit_sale_price))
                    if unit_sale_price < 0:
                        QMessageBox.warning(self, "Validation Error", "Unit Sale Price cannot be negative.")
                        return
                except (InvalidOperation, ValueError):
                    QMessageBox.warning(self, "Validation Error", "Unit Sale Price must be a valid number.")
                    return

            if re_order is not None:
                try:
                    re_order = int(re_order)
                    if re_order < 0:
                        QMessageBox.warning(self, "Validation Error", "Re-Order value cannot be negative.")
                        return
                except (ValueError, TypeError):
                    QMessageBox.warning(self, "Validation Error", "Re-Order must be a valid number.")
                    return

            if barcode and not barcode.strip():
                barcode = None

            save_res = db.save_update_insert_product(
                product_id,
                product_code,
                product_name,
                carton_size,
                unit_cost_price,
                unit_sale_price,
                re_order,
                barcode,
                is_active,
                group_id,
                company_id
            )

            if save_res.get('success'):
                QMessageBox.information(self, "Success", "Data saved successfully.")
                self.view_model._load_data("SELECT product_id, product_name from products")
                self._current_product_id = None
                if product_id is None and save_res.get('lastrowid'):
                    new_id = save_res.get('lastrowid')
                    self.product_edit_model.setItem(0, 0, self.create_item(new_id, readonly=True))
            else:
                error_msg = save_res.get('message', 'Unknown error')
                if save_res.get('error') == 'DUPLICATE_ENTRY':
                    QMessageBox.warning(self, "Duplicate Error", "Product Code or Barcode already exists.")
                elif save_res.get('error') == 'FOREIGN_KEY_VIOLATION':
                    QMessageBox.warning(self, "Reference Error", "Invalid Group or Company reference.")
                else:
                    QMessageBox.critical(self, "Error", f"Error saving data: {error_msg}")
    
        except Exception:
            QMessageBox.critical(self, "Error", "An unexpected error occurred while saving.")
        finally:
            self._is_saving = False
            self.footer_save_btn.setDisabled(False)
            self.footer_save_btn.setText("Save")
    def on_text_change(self,sender_name):
        if sender_name == "company":
            code = self.company_code_value.text()
            if code == " ":
                self.suggestion_widget = Suggestion(sender_name)
                self.suggestion_widget.show()
                self.company_code_value.setText("")
                self.suggestion_widget.sent_data.connect(lambda data:self.on_receive_data(data,sender_name))
            if code.isdigit():
                code = int(code)
                get_company_name = db.get_any_thing("SELECT company_description from company_data where company_code = %s and is_active = True",code)
                if get_company_name == None:
                    self.company_name_value.setText("Invalid Code")
                    self.company_name_value.setStyleSheet("""border:1px solid red;
                    color:red;""")
                    
                else:
                    self.company_name_value.setText(str(get_company_name['company_description']))
                    self.company_name_value.setStyleSheet("""border:none;color:grey;""")
            if code == "":
                self.company_name_value.setText("")
                self.company_name_value.setStyleSheet("""border:none;color:grey;""")
        if sender_name == "group":
            code = self.group_code_value.text()
            if code == " ":
                self.suggestion_widget = Suggestion(sender_name)
                self.suggestion_widget.show()
                self.group_code_value.setText("")
                self.suggestion_widget.sent_data.connect(lambda data:self.on_receive_data(data,sender_name))
            if code.isdigit():
                code = int(code)
                get_group_name = db.get_any_thing("SELECT group_description FROM Group_data where group_code = %s and is_active = True",code)
                if get_group_name == None:
                    self.group_name_value.setText("Invalid Code")
                    self.group_name_value.setStyleSheet("""border:1px solid red;color:red;""")
                else:
                    self.group_name_value.setText(str(get_group_name['group_description']))
                    self.group_name_value.setStyleSheet("""border:none;color:grey""")
            if code == "":
                self.group_name_value.setText("")
                self.group_name_value.setStyleSheet("""border:none;color:grey""")
        if sender_name == "gender":
            code = self.gender_code_value.text()
            if code == " ":
                self.suggestion_widget = Suggestion(sender_name)
                self.suggestion_widget.show()
                self.gender_code_value.setText("")
                self.suggestion_widget.sent_data.connect(lambda data:self.on_receive_data(data,sender_name))
            if code.isdigit():
                code = int(code)
                get_gender_name = db.get_any_thing("SELECT gender_description from gender_data where gender_code = %s and is_active = true",code)
                if get_gender_name == None:
                    self.gender_name_value.setText("Invalid Code")
                    self.gender_name_value.setStyleSheet("""border:1px solid red;color:red;""")
                else:
                    self.gender_name_value.setText(str(get_gender_name['gender_description']))
                    self.gender_name_value.setStyleSheet("""border:none;color:grey;""")
        if code == "":
            self.gender_name_value.setText("")
            self.gender_name_value.setStyleSheet("""border:none;color:grey;""")
        
    def on_receive_data(self,data,sender_name):
        if sender_name == "group":
            self.group_code_value.setText(str(data[0]))
            self.group_name_value.setText(str(data[1]))
            self.group_name_value.setStyleSheet("""border:none;color:grey""")
        if sender_name == "company":
            self.company_code_value.setText(str(data[0]))
            self.company_name_value.setText(str(data[1]))
            self.company_name_value.setStyleSheet("""border:none;color:grey;""")
        if sender_name == "gender":
            self.gender_code_value.setText(str(data[0]))
            self.group_name_value.setText(str(data[1]))
            self.gender_name_value.setStyleSheet("""border:none;color:grey;""")
        self.suggestion_widget.close()
class Suggestion(QWidget):
    sent_data = pyqtSignal(list)
    def __init__(self,sender_name):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setFixedSize(600,500)
        self.main_layout = QGridLayout(self)

        self.close_window_btn = QPushButton("Close")
        self.close_window_btn.setFixedSize(90,30)
        self.close_window_btn.setObjectName("deletebtn")
        self.close_window_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_window_btn.clicked.connect(self.close_window)
        self.close_window_btn.setShortcut("Esc")

        self.search_input = QLineEdit()
        if sender_name == "company":
            self.data_model = TableModel("SELECT company_code, company_description from company_data WHERE is_active = True")
        if sender_name == "group":
            self.data_model = TableModel("SELECT group_code, group_description from Group_data where is_active = True")
        if sender_name == "gender":
            self.data_model = TableModel("SELECT gender_code, gender_description from gender_data where is_active = True")

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.data_model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.clicked.connect(self.on_row_select)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)
        self.main_layout.addWidget(self.search_input,0,0)
        self.main_layout.addWidget(self.close_window_btn,0,1)
        self.main_layout.addWidget(self.table_view,1,0,1,2)
    def close_window(self):
        self.close()
    def on_row_select(self,index):
        row = index.row()
        row_data = []
        model = self.table_view.model()
        for col in range(model.columnCount()):
            item = model.index(row,col).data(Qt.ItemDataRole.DisplayRole )
            if item:
                row_data.append(item)

        self.sent_data.emit(row_data)


class AddDetails(QWidget):
    def __init__(self, sender_name):
        super().__init__()
        self.setWindowTitle(f"Add {sender_name}")
        self.setFixedSize(700, 600)
        self.setWindowIcon(QIcon("assets/icons/icon.png"))
        self.sender_name = sender_name
        self.company_id = None
        self.group_id = None
        self.gender_id = None
        self.row_data = []
        self._is_saving = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setFixedHeight(60)

        self._data = QWidget()
        self._data_layout = QHBoxLayout(self._data)

        self._detail_widget = QWidget()
        self._detail_widget.setObjectName("input_widget")
        self._detail_widget.setFixedSize(300, 200)
        self._detail_layout = QVBoxLayout(self._detail_widget)
        self._detail_layout.addStretch()
        self._detail_layout.addSpacing(10)

        self.detail_label_widget = self.Create_headers(f"{sender_name} Details", "MainLabel", '20px')
        self.detail_label_widget.setFixedSize(160, 30)
        self._detail_layout.addWidget(self.detail_label_widget)

        self.is_active_widget = QCheckBox("Active")
        self.is_active_widget.setChecked(True)
        self._detail_layout.addWidget(self.is_active_widget, alignment=Qt.AlignmentFlag.AlignRight)

        self.name_input_widget, self.name_input_value = self._input_fields("Name")
        self._detail_layout.addWidget(self.name_input_widget)

        self.address_input_widget = None
        self.address_input_value = None
        self.city_input_widget = None
        self.city_input_value = None
        self.short_name_input_widget = None
        self.short_name_value = None

        if sender_name == 'company':
            self.label = self.Create_headers("PRODUCT COMPANIES", "MainLabel", '25px')
            self.data_model = TableModel("SELECT * FROM company_data")
            self.address_input_widget, self.address_input_value = self._input_fields("Address")
            self.city_input_widget, self.city_input_value = self._input_fields("City")
            self.short_name_input_widget, self.short_name_value = self._input_fields("Short Name")
            self._detail_layout.addWidget(self.address_input_widget)
            self._detail_layout.addWidget(self.city_input_widget)
            self._detail_layout.addWidget(self.short_name_input_widget)

        elif sender_name == 'Group':
            self.label = self.Create_headers("PRODUCT GROUP", "MainLabel", '25px')
            self.data_model = TableModel("SELECT * FROM Group_data")

        elif sender_name == 'Gender':
            self.label = self.Create_headers("PRODUCT GENDER", "MainLabel", '25px')
            self.data_model = TableModel("SELECT * FROM gender_data")

        self.existing_data_view = QTableView()
        self.existing_data_view.setWordWrap(True)
        self.existing_data_view.setModel(self.data_model)
        header = self.existing_data_view.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setMinimumSectionSize(100)
        self.existing_data_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.existing_data_view.verticalHeader().setVisible(False)
        self.existing_data_view.clicked.connect(self.on_row_click)

        self._data_layout.addWidget(self._detail_widget)
        self._data_layout.addWidget(self.existing_data_view)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self._data)
        self.footer_window()

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
            if self.sender_name == "company":
                self.company_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                self.address_input_value.setText(str(self.row_data[2]) if self.row_data[2] is not None else "")
                self.city_input_value.setText(str(self.row_data[3]) if self.row_data[3] is not None else "")
                self.short_name_value.setText(str(self.row_data[4]) if self.row_data[4] is not None else "")
                active = self.row_data[5] if len(self.row_data) > 5 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))

            elif self.sender_name == "Gender":
                self.gender_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                active = self.row_data[2] if len(self.row_data) > 2 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))

            elif self.sender_name == "Group":
                self.group_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                active = self.row_data[2] if len(self.row_data) > 2 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))

        except (ValueError, TypeError, IndexError):
            QMessageBox.warning(self, "Error", "Error loading record data.")

    def save_data(self):
        if self._is_saving:
            return

        self._is_saving = True
        try:
            self.footer_save_btn.setText("Saving...")
            self.footer_save_btn.setDisabled(True)

            if self.sender_name == "company":
                company_name = self.name_input_value.text().strip()
                if not company_name:
                    QMessageBox.warning(self, "Validation Error", "Company Name is required.")
                    return

                address = self.address_input_value.text().strip() or None
                city = self.city_input_value.text().strip() or None
                short_name = self.short_name_value.text().strip() or None
                is_active = self.is_active_widget.isChecked()

                save_res = db.save_company_data(
                    self.company_id,
                    company_name,
                    address,
                    city,
                    short_name,
                    is_active
                )

                if save_res.get('success'):
                    QMessageBox.information(self, "Success", "Record saved successfully.")
                    self.refresh_data()
                else:
                    error_msg = save_res.get('message', 'Unknown error')
                    if save_res.get('error') == 'DUPLICATE_ENTRY':
                        QMessageBox.warning(self, "Duplicate Error", "Company name already exists.")
                    else:
                        QMessageBox.critical(self, "Error", f"Error saving data: {error_msg}")

            elif self.sender_name == "Group":
                group_name = self.name_input_value.text().strip()
                if not group_name:
                    QMessageBox.warning(self, "Validation Error", "Group Name is required.")
                    return

                is_active = self.is_active_widget.isChecked()
                save_res = db.save_group(self.group_id, group_name, is_active)

                if save_res.get('success'):
                    QMessageBox.information(self, "Success", "Record saved successfully.")
                    self.refresh_data()
                else:
                    error_msg = save_res.get('message', 'Unknown error')
                    if save_res.get('error') == 'DUPLICATE_ENTRY':
                        QMessageBox.warning(self, "Duplicate Error", "Group name already exists.")
                    else:
                        QMessageBox.critical(self, "Error", f"Error saving data: {error_msg}")

            else:
                QMessageBox.information(self, "Info", f"Save for {self.sender_name} not implemented.")

        except Exception:
            QMessageBox.critical(self, "Error", "An unexpected error occurred while saving.")
        finally:
            self._is_saving = False
            self.footer_save_btn.setDisabled(False)
            self.footer_save_btn.setText("Save")

    def _input_fields(self, label_name):
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

    def Create_headers(self, label_name, object_name_widget, font_size):
        header = QWidget()
        header.setObjectName(object_name_widget)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        label = QLabel(label_name)
        label.setStyleSheet(f"""
            color:white;
            font-weight:bold;
            font-size:{font_size}
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(label)

        return header

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
        self.footer_short_keys_header.setStyleSheet("font-size:15px; font-weight:bold;")

        self.footer_detail_header = QLabel("Double Click On Any Row to Edit Record")
        self.footer_detail_header.setStyleSheet("font-size:15px;")

        self.footer_detail_layout.addWidget(self.footer_short_keys_header)
        self.footer_detail_layout.addWidget(self.footer_detail_header)

        self.buttons_widget_footer = QWidget()
        self.buttons_widget_footer.setFixedWidth(300)
        self.buttons_layout_footer = QGridLayout(self.buttons_widget_footer)
        self.buttons_layout_footer.setSpacing(5)
        self.buttons_layout_footer.setContentsMargins(10, 5, 10, 5)

        self.btn_cursor = Qt.CursorShape.PointingHandCursor

        self.footer_save_btn = QPushButton("Save")
        self.footer_save_btn.setFixedSize(90, 35)
        self.footer_save_btn.clicked.connect(self.save_data)
        self.footer_save_btn.setCursor(self.btn_cursor)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+s"),self)
        self.save_shortcut.activated.connect(self.save_data)
        self.footer_save_btn.setObjectName("savebtn")

        self.footer_refresh_btn = QPushButton("Refresh")
        self.footer_refresh_btn.setFixedSize(90, 35)
        self.refresh_shortcut = QShortcut(QKeySequence("Ctrl+r"),self)
        self.refresh_shortcut.activated.connect(self.refresh_data)
        self.footer_refresh_btn.setCursor(self.btn_cursor)
        self.footer_refresh_btn.setObjectName("refreshbtn")
        self.footer_refresh_btn.clicked.connect(self.refresh_data)

        self.footer_delete_btn = QPushButton("Close")
        self.footer_delete_btn.setFixedSize(90, 35)
        self.footer_delete_btn.setCursor(self.btn_cursor)
        self.footer_delete_btn.clicked.connect(self.closeWindow)
        self.footer_delete_btn.setShortcut("Esc")
        self.footer_delete_btn.setObjectName("deletebtn")

        self.footer_save_action = QLabel("CTRL + S")
        self.footer_refresh_action = QLabel("CTRL + R")
        self.footer_delete_action = QLabel("Esc")

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

    def refresh_data(self):
        try:
            if self.sender_name == "company":
                self.data_model._load_data("SELECT * FROM company_data")
                self.name_input_value.setText("")
                self.address_input_value.setText("")
                self.city_input_value.setText("")
                self.short_name_value.setText("")
                self.company_id = None
            elif self.sender_name == "Group":
                self.data_model._load_data("SELECT * FROM Group_data")
                self.name_input_value.setText("")
                self.group_id = None
            elif self.sender_name == "Gender":
                self.data_model._load_data("SELECT * FROM gender_data")
                self.name_input_value.setText("")
                self.gender_id = None
            self.is_active_widget.setChecked(True)
        except Exception:
            QMessageBox.critical(self, "Error", "Error refreshing data.")


class TableModel(QAbstractTableModel):
    def __init__(self, query):
        super().__init__()
        self._data = []
        self._headers = []
        self._load_data(query)

    def _load_data(self, query):
        self.beginResetModel()
        try:
            result = db.get_products(query)
            if result is None:
                self._data = []
                self._headers = []
            else:
                self._data = result
                self._headers = list(self._data[0].keys()) if self._data else []
        except Exception:
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
                return str(value) if value is not None else ""
            except (IndexError, KeyError):
                return None

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                try:
                    header = self._headers[section]
                    return header.split("_")[-1].title()
                except IndexError:
                    return ""
            return section + 1
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())
    window = Products()
    window.showMaximized()
    sys.exit(app.exec())