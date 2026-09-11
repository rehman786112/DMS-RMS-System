# products_ui.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys
import requests
from decimal import Decimal, InvalidOperation
from database import DatabaseManager
import functools
import traceback
from image_uploader import ImageUploader

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


def load_stylesheet():
    try:
        with open('style.qss', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


db = DatabaseManager()


# ============================================
# BACKGROUND UPLOAD WORKER
# ============================================
class UploadWorker(QThread):
    """Background thread for image upload with REAL progress."""
    progress_signal = pyqtSignal(int)           # percent (0-100)
    finished_signal = pyqtSignal(bool, object)  # success, response

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        result, response = ImageUploader.upload_image(
            None,
            self.image_path,
            progress_callback=self.progress_signal.emit
        )
        self.finished_signal.emit(result, response)


class Products(QMainWindow):
    def __init__(self):
        super().__init__()
        self._is_saving = False
        self._current_product_id = None
        self._selected_row = 0
        self.is_update = False
        self.image_path = None
        self.image_url = None

        # ✅ Image upload state tracking
        self._is_uploading = False
        self._upload_worker = None
        self.progress_bar = None

        try:
            self.setup_ui()
            self.setup_enter_navigation()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize Products window:\n\n{type(e).__name__}: {e}"
            )

    def setup_enter_navigation(self):
        for widget in self.findChildren(QLineEdit):
            if widget.isEnabled():
                widget.installEventFilter(self)
        for widget in self.findChildren(QComboBox):
            if widget.isEnabled():
                widget.installEventFilter(self)
        for widget in self.findChildren(QTableView):
            widget.installEventFilter(self)

    def is_widget_editable(self, widget):
        if not widget.isEnabled():
            return False
        if isinstance(widget, QLineEdit):
            return not widget.isReadOnly()
        if isinstance(widget, QComboBox):
            return widget.isEnabled()
        return True

    def find_next_editable_widget(self, current_widget):
        focus_order = [
            self.p_name,
            self.category_code_value,
            self.company_code_value,
            self.size_code_value,
            self.unit,
            self.pct_hs_code_value,
            self.product_edit_view
        ]
        
        try:
            current_index = focus_order.index(current_widget)
        except ValueError:
            return None
        
        for i in range(current_index + 1, len(focus_order)):
            next_widget = focus_order[i]
            if isinstance(next_widget, QLineEdit):
                if not next_widget.isReadOnly() and next_widget.isEnabled():
                    return next_widget
            elif isinstance(next_widget, QComboBox):
                if next_widget.isEnabled():
                    return next_widget
            elif isinstance(next_widget, QTableView):
                if next_widget.isEnabled():
                    return next_widget
        
        return None

    def auto_capitalize_input(self, widget):
        text = widget.text()
        if text and len(text) > 0:
            widget.blockSignals(True)
            cursor_pos = widget.cursorPosition()
            words = text.split(' ')
            capitalized_words = []
            for word in words:
                if word:
                    capitalized_words.append(word[0].upper() + word[1:].lower())
                else:
                    capitalized_words.append('')
            new_text = ' '.join(capitalized_words)
            if new_text != text:
                widget.setText(new_text)
                widget.setCursorPosition(cursor_pos)
            widget.blockSignals(False)

    def auto_uppercase_input(self, widget):
        text = widget.text()
        if text:
            cursor_pos = widget.cursorPosition()
            new_text = text.upper()
            if new_text != text:
                widget.blockSignals(True)
                widget.setText(new_text)
                widget.setCursorPosition(cursor_pos)
                widget.blockSignals(False)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            
            if isinstance(obj, QLineEdit):
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if obj == self.product_name_search:
                        return True
                    
                    if self.is_widget_editable(obj):
                        next_widget = self.find_next_editable_widget(obj)
                        if next_widget:
                            next_widget.setFocus()
                            if isinstance(next_widget, QLineEdit):
                                next_widget.selectAll()
                            elif isinstance(next_widget, QTableView):
                                self.product_edit_view.setCurrentIndex(
                                    self.product_edit_model.index(0, 1)
                                )
                        return True
                    return True
            
            if isinstance(obj, QComboBox):
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if self.is_widget_editable(obj):
                        next_widget = self.find_next_editable_widget(obj)
                        if next_widget:
                            next_widget.setFocus()
                            if isinstance(next_widget, QLineEdit):
                                next_widget.selectAll()
                            elif isinstance(next_widget, QTableView):
                                self.product_edit_view.setCurrentIndex(
                                    self.product_edit_model.index(0, 1)
                                )
                        return True
            
            if isinstance(obj, QLineEdit) and obj == self.product_name_search:
                row_count = self._search_proxy.rowCount() if hasattr(self, '_search_proxy') else 0
                if row_count == 0:
                    return super().eventFilter(obj, event)
                
                current_index = self.product_detail_view.currentIndex()
                current_row = current_index.row() if current_index.isValid() else -1
                
                if key == Qt.Key.Key_Up:
                    new_row = current_row - 1 if current_row > 0 else row_count - 1
                    self.select_table_row(self.product_detail_view, new_row, self._search_proxy)
                    return True
                elif key == Qt.Key.Key_Down:
                    new_row = current_row + 1 if current_row < row_count - 1 else 0
                    self.select_table_row(self.product_detail_view, new_row, self._search_proxy)
                    return True
            
            if isinstance(obj, QTableView):
                if obj == self.product_detail_view:
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        current_index = obj.currentIndex()
                        if current_index.isValid():
                            self.on_product_select(current_index)
                        return True
                    
                    if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                        current_index = obj.currentIndex()
                        if current_index.isValid():
                            row = current_index.row()
                            col = current_index.column()
                            if key == Qt.Key.Key_Up:
                                new_row = max(0, row - 1)
                            else:
                                new_row = min(obj.model().rowCount() - 1, row + 1)
                            if new_row != row:
                                obj.setCurrentIndex(obj.model().index(new_row, col))
                            return True
                
                elif obj == self.product_edit_view:
                    current_index = obj.currentIndex()
                    
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        if current_index.isValid():
                            row = current_index.row()
                            col = current_index.column()
                            if col not in [0, 2]:
                                obj.edit(current_index)
                            return True
                    
                    if key == Qt.Key.Key_Left:
                        if current_index.isValid():
                            row = current_index.row()
                            col = current_index.column()
                            new_col = col - 1
                            while new_col >= 0 and new_col in [0, 2]:
                                new_col -= 1
                            if new_col >= 0:
                                obj.setCurrentIndex(self.product_edit_model.index(row, new_col))
                            return True
                    
                    if key == Qt.Key.Key_Right:
                        if current_index.isValid():
                            row = current_index.row()
                            col = current_index.column()
                            new_col = col + 1
                            while new_col < self.product_edit_model.columnCount() and new_col in [0, 2]:
                                new_col += 1
                            if new_col < self.product_edit_model.columnCount():
                                obj.setCurrentIndex(self.product_edit_model.index(row, new_col))
                            return True
                    
                    if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                        if current_index.isValid():
                            row = current_index.row()
                            col = current_index.column()
                            if key == Qt.Key.Key_Up:
                                new_row = max(0, row - 1)
                            else:
                                new_row = min(obj.model().rowCount() - 1, row + 1)
                            if new_row != row:
                                obj.setCurrentIndex(self.product_edit_model.index(new_row, col))
                            return True
            
            if isinstance(obj, QPushButton):
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and obj.isEnabled():
                    obj.click()
                    return True
        
        return super().eventFilter(obj, event)

    def select_table_row(self, table_view, row, proxy_model):
        if row < 0 or row >= proxy_model.rowCount():
            return
        model_index = proxy_model.index(row, 0)
        if model_index.isValid():
            table_view.clearSelection()
            table_view.selectRow(row)
            table_view.setCurrentIndex(model_index)
            table_view.scrollTo(model_index, QAbstractItemView.ScrollHint.EnsureVisible)
            table_view.setFocus()

    @handle_errors
    def setup_ui(self):
        self.setup_window()
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label_widget = self.create_header("PRODUCTS", "MainLabel", '35px')
        self.label_widget.setFixedHeight(50)

        self.product_main_widget = QWidget()
        self.product_main_widget.setObjectName("main_products_widget")
        self.product_main_layout = QHBoxLayout(self.product_main_widget)
        self.product_main_layout.setSpacing(0)
        self.product_main_layout.setContentsMargins(10, 5, 5, 10)

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

    @handle_errors
    def product_details(self):
        self.product_detail = QWidget()
        self.product_detail.setFixedWidth(400)
        self.product_detail_layout = QVBoxLayout(self.product_detail)
        self.product_detail_layout.setContentsMargins(0, 0, 0, 0)
        self.product_detail_layout.setSpacing(0)

        self.product_name_search = QLineEdit()
        self.product_name_search.setPlaceholderText("Search product by name...")
        self.product_name_search.setFixedHeight(35)
        self.product_detail_layout.addWidget(self.product_name_search)

        self.product_detail_label_widget = self.create_header("Product Details", "detail-header", '18px')
        self.product_detail_label_widget.setContentsMargins(0, 15, 0, 0)
        self.product_detail_layout.addWidget(self.product_detail_label_widget)

        self.product_detail_view = QTableView()
        self._search_proxy = QSortFilterProxyModel()
        self._search_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_proxy.setFilterKeyColumn(-1)
        self.product_name_search.textChanged.connect(self._search_proxy.setFilterFixedString)

        self.view_model = TableModel("SELECT prd_id, prd_name from products")
        self._search_proxy.setSourceModel(self.view_model)
        self.product_detail_view.setModel(self._search_proxy)
        self.product_detail_view.setAlternatingRowColors(True)
        self.product_detail_view.verticalHeader().setVisible(False)
        self.product_detail_view.horizontalHeader().setVisible(False)
        self.product_detail_view.setColumnHidden(0, True)
        self.product_detail_view.setShowGrid(False)
        self.product_detail_view.doubleClicked.connect(self.on_product_select)

        header = self.product_detail_view.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.product_detail_layout.addWidget(self.product_detail_view)
        self.product_main_layout.addWidget(self.product_detail)

    @handle_errors
    def product_description(self):
        self.product_desc = QWidget()
        self.product_desc_layout = QVBoxLayout(self.product_desc)

        self.product_name_widget = QWidget()
        self.product_name_layout = QVBoxLayout(self.product_name_widget)

        self.product_desc_label_widget = self.create_header("Product Description", 'MainLabel', '20px')
        self.product_desc_label_widget.setFixedSize(200, 30)

        self.p_name_input, self.p_name = self.create_input_field("Product Name:")
        self.p_name.textChanged.connect(self.on_update_product_name)
        self.p_name.textChanged.connect(lambda: self.auto_uppercase_input(self.p_name))
        self.p_name.setFixedWidth(500)
        self.p_name_input.setObjectName("ProductName")
        self.p_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.product_name_layout.addWidget(self.product_desc_label_widget)
        self.product_name_layout.addWidget(self.p_name_input, alignment=Qt.AlignmentFlag.AlignLeft)

        # Category, Company and Size
        self.category_company_size_widget = QWidget()
        self.category_company_size_layout = QVBoxLayout(self.category_company_size_widget)

        self.category_company_size_label = self.create_header("Category / Company / Size", 'MainLabel', '20px')
        self.category_company_size_label.setFixedSize(350, 30)

        self.category_company_size_input_widget = QWidget()
        self.category_company_size_input_layout = QGridLayout(self.category_company_size_input_widget)

        # Category fields
        self.category_code, self.category_code_value = self.create_input_field("Category")
        self.category_code_value.textChanged.connect(lambda: self.on_text_change("category"))
        self.category_name, self.category_name_value = self.create_input_field("Name")
        self.category_name_value.setReadOnly(True)

        # Company fields
        self.company_code, self.company_code_value = self.create_input_field("Company")
        self.company_code_value.textChanged.connect(lambda: self.on_text_change("company"))
        self.company_name, self.company_name_value = self.create_input_field("Name")
        self.company_name_value.setReadOnly(True)

        # Product Size fields
        self.size_code, self.size_code_value = self.create_input_field("Size ID")
        self.size_code_value.textChanged.connect(lambda: self.on_text_change("size"))
        self.size_name, self.size_name_value = self.create_input_field("Size Name")
        self.size_name_value.setReadOnly(True)

        # Unit field
        self.unit_widget = QWidget()
        self.unit_widget_layout = QHBoxLayout(self.unit_widget)
        self.unit_widget_layout.addStretch()
        self.unit_widget_layout.setSpacing(10)

        self.unit_label = QLabel("Unit")
        self.unit_label.setStyleSheet("font-size:16px; font-weight: 700; color: black;")
        self.unit = QComboBox()
        self.unit.setFixedWidth(200)
        self.unit.addItems(["PCS"])
        self.unit_widget_layout.addWidget(self.unit_label)
        self.unit_widget_layout.addWidget(self.unit)

        # PCT/HS Code
        self.pct_hs_code, self.pct_hs_code_value = self.create_input_field("PCT / HS Code")
        self.pct_hs_code_value.textChanged.connect(lambda: self.auto_capitalize_input(self.pct_hs_code_value))

        # Add buttons for new records
        self.add_category_btn = self.create_add_button()
        self.add_category_btn.clicked.connect(lambda: self.add_new("Category"))
        
        self.add_company_btn = self.create_add_button()
        self.add_company_btn.clicked.connect(lambda: self.add_new("company"))
        
        self.add_size_btn = self.create_add_button()
        self.add_size_btn.clicked.connect(lambda: self.add_new("size"))
        
        # product image uploader preview and upload
        self.image_uploader_widget = QWidget()
        self.image_uploader_widget_layout = QVBoxLayout(self.image_uploader_widget) 
        
        # state for image upload
        self.image_upload = False
        # image preview label
        self.image_preview_label = QLabel("Image Preview")
        self.image_preview_label.setStyleSheet("font-size:16px; font-weight: 700; color: black;")
        # previewer
        self.image_preview = QLabel('No Image Selected')
        self.image_preview.setFixedSize(200, 200)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet(
            "border: 2px dashed #b0b0b0; border-radius: 10px; "
            "background: #fafafa; color: #888; font-size: 13px;"
        )
        self.image_preview_label.setBuddy(self.image_preview)
        # image input to choose image
        self.image_input = QPushButton("Choose Image")
        self.image_input.setStyleSheet("""
                                       QPushButton {
                                           background-color: #2196F3;
                                           color: white;
                                           border-radius: 5px;
                                           padding: 5px 10px;
                                       }
                                        QPushButton:hover {
                                           background-color: #1976D2;
                                       }
                                       """)
        self.image_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_input.clicked.connect(self.choose_image_dialouge)
        # upload image button
        self.upload_image_to_cloud_btn = QPushButton("Upload Image")
        self.upload_image_to_cloud_btn.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        """)
        self.upload_image_to_cloud_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_image_to_cloud_btn.clicked.connect(self.upload_image_to_cloud)
        self.upload_image_to_cloud_btn.setEnabled(False)

        # add to layout
        self.image_uploader_widget_layout.addWidget(self.image_preview_label)
        self.image_uploader_widget_layout.addWidget(self.image_preview)
        self.image_uploader_widget_layout.addWidget(self.image_input)
        self.image_uploader_widget_layout.addWidget(self.upload_image_to_cloud_btn)

        # Layout for category, company and size
        self.category_company_size_input_layout.addWidget(self.category_code, 0, 0)
        self.category_company_size_input_layout.addWidget(self.category_name, 0, 1)
        self.category_company_size_input_layout.addWidget(self.add_category_btn, 0, 2)
        
        self.category_company_size_input_layout.addWidget(self.company_code, 1, 0)
        self.category_company_size_input_layout.addWidget(self.company_name, 1, 1)
        self.category_company_size_input_layout.addWidget(self.add_company_btn, 1, 2)
        
        self.category_company_size_input_layout.addWidget(self.size_code, 2, 0)
        self.category_company_size_input_layout.addWidget(self.size_name, 2, 1)
        self.category_company_size_input_layout.addWidget(self.add_size_btn, 2, 2)
        
        self.category_company_size_input_layout.addWidget(self.unit_widget, 3, 0)
        self.category_company_size_input_layout.addWidget(self.pct_hs_code, 3, 1)
        self.category_company_size_input_layout.addWidget(self.image_uploader_widget, 0, 3, 4, 1)

        self.category_company_size_layout.addWidget(self.category_company_size_label)
        self.category_company_size_layout.addWidget(self.category_company_size_input_widget, alignment=Qt.AlignmentFlag.AlignLeft)

        # Product edit table view (9 columns)
        self.product_edit_view = QTableView()
        self.product_edit_model = QStandardItemModel(1, 9)
        self.product_edit_model.setHorizontalHeaderLabels([
            "Product ID", "Product Code", "Product Name", "Carton Size",
            "Unit Cost Price", "Unit Sale Price", "Re Order", "BarCode", "Is Active"
        ])
        self.product_edit_view.verticalHeader().setVisible(False)
        self.product_edit_view.setModel(self.product_edit_model)
        self.product_edit_view.setEditTriggers(QTableView.EditTrigger.DoubleClicked | QTableView.EditTrigger.EditKeyPressed)

        self.product_edit_model.setItem(0, 0, self.create_item(None, readonly=True))
        self.product_edit_model.setItem(0, 2, self.create_item(None, readonly=True))
        self.product_edit_model.setItem(0, 8, self.create_item(True, checkbox=True))

        header = self.product_edit_view.horizontalHeader()
        header.setMinimumSectionSize(150)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.product_desc_layout.addWidget(self.product_name_widget)
        self.product_desc_layout.addWidget(self.category_company_size_widget)
        self.product_desc_layout.addWidget(self.product_edit_view)

        self.product_main_layout.addWidget(self.product_desc)

    # ============================================
    # IMAGE HANDLING
    # ============================================
    def _load_image_preview(self, image_url):
        """Load image from URL (Cloudinary) or local path into preview label."""
        if not image_url:
            self.image_preview.clear()
            self.image_preview.setText("No Image Selected")
            self.image_preview.setStyleSheet(
                "border: 2px dashed #b0b0b0; border-radius: 10px; "
                "background: #fafafa; color: #888; font-size: 13px;"
            )
            return

        try:
            pixmap = QPixmap()

            # Check karo local file hai ya URL
            if image_url.startswith("http://") or image_url.startswith("https://"):
                # Remote image — requests se download karo
                response = requests.get(image_url, timeout=15)
                response.raise_for_status()
                pixmap.loadFromData(response.content)
            else:
                # Local file path
                pixmap.load(image_url)

            if pixmap.isNull():
                print(f"Failed to load image (null pixmap): {image_url}")
                self.image_preview.clear()
                self.image_preview.setText("⚠ Image load failed")
                return

            scaled = pixmap.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled)
            self.image_preview.setText("")
            self.image_preview.setStyleSheet(
                "border: 2px solid #2196F3; border-radius: 10px; "
                "background: #ffffff;"
            )
        except Exception as e:
            print(f"Error loading image preview: {e}")
            self.image_preview.clear()
            self.image_preview.setText("⚠ Image load failed")

    def choose_image_dialouge(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not file_path:
            return

        print(f"Selected image path: {file_path}")
        self.image_path = file_path
        self.image_url = None  # naya image select kiya, purana URL clear
        self.image_upload = True
        self._load_image_preview(file_path)
        self.upload_image_to_cloud_btn.setEnabled(True)

    def upload_image_to_cloud(self):
        """Start image upload in a background thread with REAL progress bar."""
        if not self.image_path:
            QMessageBox.warning(self, "No Image", "Please choose an image first.")
            return

        # Already uploading? ignore
        if self._is_uploading:
            return

        # ✅ Uploading state ON
        self._is_uploading = True

        # ✅ REAL progress bar (0 se 100)
        self.progress_bar = QProgressDialog(
            "Uploading image to cloud...",
            None, 0, 100, self
        )
        self.progress_bar.setWindowTitle("Uploading Image")
        self.progress_bar.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_bar.setCancelButton(None)
        self.progress_bar.setMinimumDuration(0)
        self.progress_bar.setAutoClose(False)
        self.progress_bar.setAutoReset(False)
        self.progress_bar.setMinimumWidth(420)
        self.progress_bar.setValue(0)
        self.progress_bar.setLabelText("Uploading image... 0%")
        self.progress_bar.show()

        # ✅ Buttons disable — save bhi disabled
        self.upload_image_to_cloud_btn.setEnabled(False)
        self.upload_image_to_cloud_btn.setText("Uploading...")
        self.image_input.setEnabled(False)
        self.footer_save_btn.setEnabled(False)
        self.footer_refresh_btn.setEnabled(False)
        self.footer_delete_btn.setEnabled(False)

        # ✅ Worker start
        self._upload_worker = UploadWorker(self.image_path)
        self._upload_worker.progress_signal.connect(self._on_upload_progress)
        self._upload_worker.finished_signal.connect(self._on_upload_finished)
        self._upload_worker.start()

    def _on_upload_progress(self, percent):
        """Worker se aane wali real progress update karo."""
        if self.progress_bar is not None:
            self.progress_bar.setValue(percent)
            self.progress_bar.setLabelText(f"Uploading image... {percent}%")

    def _on_upload_finished(self, success, response):
        """Upload complete hone par UI restore karo."""
        # Progress 100 karke band karo
        if self.progress_bar is not None:
            if success:
                self.progress_bar.setValue(100)
                self.progress_bar.setLabelText("Uploading image... 100%")
            self.progress_bar.close()
            self.progress_bar = None

        # ✅ Uploading state OFF
        self._is_uploading = False

        # ✅ Buttons restore
        self.image_input.setEnabled(True)
        self.footer_save_btn.setEnabled(True)
        self.footer_refresh_btn.setEnabled(True)
        self.footer_delete_btn.setEnabled(True)
        self.upload_image_to_cloud_btn.setText("Upload Image")

        if success:
            QMessageBox.information(self, "Success", "Image uploaded successfully")
            self.image_url = response
            self.image_path = None
            self.upload_image_to_cloud_btn.setEnabled(False)
        else:
            QMessageBox.critical(self, "Error", f"Image upload failed: {response}")
            self.upload_image_to_cloud_btn.setEnabled(True)

    def create_input_field(self, label_name):
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

    def create_add_button(self):
        button = QPushButton("+")
        button.setObjectName("add_btn")
        button.setFixedSize(30, 30)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

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

        self.footer_detail_header = QLabel("Select Row And Press Delete Button For Deleting Row")
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
        self.footer_refresh_btn.clicked.connect(self.refresh_view)
        QShortcut(QKeySequence("Ctrl+r"), self).activated.connect(self.refresh_view)

        self.footer_delete_btn = QPushButton("Delete")
        self.footer_delete_btn.setFixedSize(90, 35)
        self.footer_delete_btn.setCursor(self.btn_cursor)
        self.footer_delete_btn.setObjectName("deletebtn")
        self.footer_delete_btn.clicked.connect(self.delete_product)
        QShortcut(QKeySequence("Ctrl+d"), self).activated.connect(self.delete_product)

        self.footer_save_action = QLabel("CTRL + S")
        self.footer_refresh_action = QLabel("CTRL + R")
        self.footer_delete_action = QLabel("CTRL + D")
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

        self.main_layout.addWidget(self.footer_widget)

    @handle_errors
    def on_update_product_name(self, text=""):
        item = self.product_edit_model.item(0, 2)
        if item is None:
            item = self.create_item("")
            self.product_edit_model.setItem(0, 2, item)
        item.setText(self.p_name.text())

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

    @handle_errors
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
        
        conn, cursor = db.get_connection()
        cursor.execute("SELECT * FROM products where prd_id = %s", (product_id,))
        product_data = cursor.fetchone()
        if product_data is None:
            QMessageBox.critical(self, "Error", "Product not found or database error.")
            return
        
        conn, cursor = db.get_connection()
        cursor.execute("""
                SELECT prd_id, prd_code, prd_name, prd_carton_size, prd_cost_price, prd_sale_price,
                       prd_reorder, prd_barcode, prd_is_active, prd_cat_id, prd_company_id, prd_size_id,
                       image_url, prd_size_name, company_name, cat_name
                FROM products
                WHERE prd_id = %s
            """, (product_id,))
        product_company_data = cursor.fetchone()
        if product_company_data is None:
            QMessageBox.critical(self, "Error", "Product details incomplete.")
            return

        try:
            category_id = product_company_data.get('prd_cat_id')
            category_name = product_company_data.get('cat_name', '')
            company_id = product_company_data.get('prd_company_id')
            company_name = product_company_data.get('company_name', '')
            size_id = product_company_data.get('prd_size_id')
            size_name = product_company_data.get('prd_size_name', '')
            image_url = product_company_data.get('image_url', '')

            print(f'Image URL: {image_url}')

            self.category_code_value.setText(str(category_id) if category_id is not None else "")
            self.category_name_value.setText(category_name if category_name else "")
            self.company_code_value.setText(str(company_id) if company_id is not None else "")
            self.company_name_value.setText(company_name if company_name else "")
            self.size_code_value.setText(str(size_id) if size_id is not None else "")
            self.size_name_value.setText(size_name if size_name else "")

            # ✅ Image preview load karo (URL ya local, dono handle karta hai)
            self._load_image_preview(image_url)

            # State save karo taaki Save pe wahi URL jaaye
            self.image_url = image_url if image_url else None
            self.image_path = None
            self.upload_image_to_cloud_btn.setEnabled(False)
        except Exception as e:
            print(f"Error loading product details: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", "Error loading product in edit view.")
            return

        self._current_product_id = product_id
        self.p_name.setText(product_data.get("prd_name", ""))

        columns = ["prd_id", "prd_code", "prd_name", "prd_carton_size",
                   "prd_cost_price", "prd_sale_price", "prd_reorder", 
                   "prd_barcode", "prd_is_active"]

        for col, key in enumerate(columns):
            value = product_data.get(key)
            if key == "prd_id":
                item = self.create_item(value, readonly=True)
            elif key == "prd_is_active":
                item = self.create_item(value, checkbox=True)
            elif key == "prd_name":
                item = self.create_item(value, readonly=True)
            else:
                item = self.create_item(value)
            self.product_edit_model.setItem(0, col, item)

    @handle_errors
    def delete_product(self):
        if self._current_product_id is None:
            QMessageBox.information(self, "Message", "Please Double click on row to select for Actions")
            return

        reply = QMessageBox.question(self, "Confirm", "Are You Sure to Delete this Product?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del_res = db.delete_products(self._current_product_id)
            if del_res:
                QMessageBox.information(self, "Success", "Product Delete Success...")
                self.refresh_view()
            else:
                QMessageBox.critical(self, "Error", "Unable to delete Record...")
                self.refresh_view()

    @handle_errors
    def refresh_view(self, checked=False):
        self.p_name.setText("")
        self.category_name_value.setText("")
        self.category_code_value.setText("")
        self.company_name_value.setText("")
        self.company_code_value.setText("")
        self.size_name_value.setText("")
        self.size_code_value.setText("")
        self.pct_hs_code_value.setText("")
        
        for col in range(self.product_edit_model.columnCount()):
            if col == 0:
                item = self.create_item(None, readonly=True)
            elif col == 2:
                item = self.create_item(None, readonly=True)
            elif col == 8:
                item = self.create_item(True, checkbox=True)
            else:
                item = self.create_item(None)
            self.product_edit_model.setItem(0, col, item)
        
        self.view_model._load_data("SELECT prd_id, prd_name from products")

        # Reset image section
        self.image_url = None
        self.image_path = None
        self._load_image_preview(None)
        self.upload_image_to_cloud_btn.setEnabled(False)

        self._current_product_id = None
        self.p_name.setFocus()

    @handle_errors
    def clear_all_inputs(self, checked=False):
        self.p_name.setText("")
        self.category_code_value.setText("")
        self.category_name_value.setText("")
        self.company_code_value.setText("")
        self.company_name_value.setText("")
        self.size_code_value.setText("")
        self.size_name_value.setText("")
        self.pct_hs_code_value.setText("")
        
        for col in range(self.product_edit_model.columnCount()):
            if col == 0:
                item = self.create_item(None, readonly=True)
            elif col == 2:
                item = self.create_item(None, readonly=True)
            elif col == 8:
                item = self.create_item(True, checkbox=True)
            else:
                item = self.create_item(None)
            self.product_edit_model.setItem(0, col, item)
        
        self.image_url = None
        self.image_path = None
        self._load_image_preview(None)
        self.upload_image_to_cloud_btn.setEnabled(False)

        self._current_product_id = None
        self.p_name.setFocus()

    @handle_errors
    def save_data(self, checked=False):
        if self._is_saving:
            return

        # ✅ Agar image upload ho rahi ho to save mat karo
        if self._is_uploading:
            QMessageBox.warning(
                self, "Please Wait",
                "Image upload ho rahi hai. Complete hone ke baad save karein."
            )
            return

        self._is_saving = True
        try:
            self.footer_save_btn.setText("Saving...")
            self.footer_save_btn.setDisabled(True)

            row_data = []
            for col in range(self.product_edit_model.columnCount()):
                item = self.product_edit_model.item(0, col)
                row_data.append(self.get_typed_value(item) if item else None)

            product_id = row_data[0]
            product_code = str(row_data[1] or "").strip()
            product_name = str(row_data[2] or "").strip()
            carton_size = row_data[3]
            unit_cost_price = row_data[4]
            unit_sale_price = row_data[5]
            re_order = row_data[6]
            barcode = str(row_data[7] or "").strip()
            is_active = row_data[8] if row_data[8] is not None else True
            company_name = self.company_name_value.text().strip()
            cat_name = self.category_name_value.text().strip()

            if not product_name:
                QMessageBox.warning(self, "Validation Error", "Product Name is required.")
                return

            if not product_code:
                QMessageBox.warning(self, "Validation Error", "Product Code is required.")
                return

            category_id_text = self.category_code_value.text().strip()
            company_id_text = self.company_code_value.text().strip()
            size_id_text = self.size_code_value.text().strip()
            size_name = self.size_name_value.text().strip()

            if not category_id_text:
                QMessageBox.warning(self, "Validation Error", "Please select a Category.")
                return

            if not company_id_text:
                QMessageBox.warning(self, "Validation Error", "Please select a Company.")
                return

            try:
                category_id = int(category_id_text)
                company_id = int(company_id_text)
                size_id_val = int(size_id_text) if size_id_text else None
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Invalid Category, Company or Size ID.")
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

            # Image URL (Cloudinary) — None agar koi image nahi
            image_url_value = self.image_url if self.image_url else None

            conn, cursor = db.get_connection()
            if product_id is None or product_id == "":
                query = """INSERT INTO products (prd_code, prd_name, prd_carton_size, 
                          prd_cost_price, prd_sale_price, prd_reorder, prd_barcode, prd_is_active, 
                          prd_company_id, prd_cat_id, prd_size_id, company_name, cat_name, image_url,prd_size_name) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                values = (product_code, product_name, carton_size, unit_cost_price, 
                         unit_sale_price, re_order, barcode, is_active, company_id, category_id, 
                         size_id_val, company_name, cat_name, image_url_value, size_name)
                message = "Data Inserted Successfully."
            else:
                query = """UPDATE products SET prd_code = %s, prd_name = %s, prd_carton_size = %s, 
                          prd_cost_price = %s, prd_sale_price = %s, prd_reorder = %s, prd_barcode = %s, 
                          prd_is_active = %s, prd_company_id = %s, prd_cat_id = %s, 
                          prd_size_id = %s, company_name = %s, cat_name = %s, image_url = %s, prd_size_name = %s
                          WHERE prd_id = %s"""
                values = (product_code, product_name, carton_size, unit_cost_price, unit_sale_price, 
                         re_order, barcode, is_active, company_id, category_id, 
                         size_id_val, company_name, cat_name, self.image_url, size_name, product_id)
                message = "Data Updated Successfully."
            
            cursor.execute(query, values)
            conn.commit()
            QMessageBox.information(self, "Success", message)
            self.refresh_view()

        except Exception as e:
            raise
        finally:
            self._is_saving = False
            self.footer_save_btn.setDisabled(False)
            self.footer_save_btn.setText("Save")

    @handle_errors
    def on_text_change(self, sender_name):
        if sender_name == "company":
            code = self.company_code_value.text()
            if code == " ":
                self.suggestion_widget = Suggestion(sender_name)
                self.suggestion_widget.show()
                self.company_code_value.setText("")
                self.suggestion_widget.sent_data.connect(lambda data: self.on_receive_data(data, sender_name))
            if code.isdigit():
                code = int(code)
                conn, cursor = db.get_connection()
                query = "SELECT company_description FROM company_data WHERE company_code = %s"
                cursor.execute(query, (code,))
                get_company_name = cursor.fetchone()
                if get_company_name is None:
                    self.company_name_value.setText("Invalid Code")
                    self.company_name_value.setStyleSheet("border:1px solid red; color:red;")
                else:
                    self.company_name_value.setText(str(get_company_name['company_description']))
                    self.company_name_value.setStyleSheet("border:none; color:grey;")
            if code == "":
                self.company_name_value.setText("")
                self.company_name_value.setStyleSheet("border:none; color:grey;")

        if sender_name == "category":
            code = self.category_code_value.text()
            if code == " ":
                self.suggestion_widget = Suggestion(sender_name)
                self.suggestion_widget.show()
                self.category_code_value.setText("")
                self.suggestion_widget.sent_data.connect(lambda data: self.on_receive_data(data, sender_name))
            if code.isdigit():
                code = int(code)
                conn, cursor = db.get_connection()
                query = "SELECT cat_description FROM categories WHERE cat_code = %s"
                cursor.execute(query, (code,))
                get_category_name = cursor.fetchone()
                if get_category_name is None:
                    self.category_name_value.setText("Invalid Code")
                    self.category_name_value.setStyleSheet("border:1px solid red; color:red;")
                else:
                    self.category_name_value.setText(str(get_category_name['cat_description']))
                    self.category_name_value.setStyleSheet("border:none; color:grey;")
            if code == "":
                self.category_name_value.setText("")
                self.category_name_value.setStyleSheet("border:none; color:grey;")

        if sender_name == "size":
            code = self.size_code_value.text()
            if code == " ":
                self.suggestion_widget = Suggestion(sender_name)
                self.suggestion_widget.show()
                self.size_code_value.setText("")
                self.suggestion_widget.sent_data.connect(lambda data: self.on_receive_data(data, sender_name))
            if code.isdigit():
                code = int(code)
                conn, cursor = db.get_connection()
                query = "SELECT size_name FROM prd_size WHERE id = %s"
                cursor.execute(query, (code,))
                get_size_name = cursor.fetchone()
                if get_size_name is None:
                    self.size_name_value.setText("Invalid ID")
                    self.size_name_value.setStyleSheet("border:1px solid red; color:red;")
                else:
                    self.size_name_value.setText(str(get_size_name['size_name']))
                    self.size_name_value.setStyleSheet("border:none; color:grey;")
            if code == "":
                self.size_name_value.setText("")
                self.size_name_value.setStyleSheet("border:none; color:grey;")

    @handle_errors
    def on_receive_data(self, data, sender_name):
        if sender_name == "category":
            self.category_code_value.setText(str(data[0]))
            self.category_name_value.setText(str(data[1]))
            self.category_name_value.setStyleSheet("border:none; color:grey;")
        if sender_name == "company":
            self.company_code_value.setText(str(data[0]))
            self.company_name_value.setText(str(data[1]))
            self.company_name_value.setStyleSheet("border:none; color:grey;")
        if sender_name == "size":
            self.size_code_value.setText(str(data[0]))
            self.size_name_value.setText(str(data[1]))
            self.size_name_value.setStyleSheet("border:none; color:grey;")
        self.suggestion_widget.close()

    @handle_errors
    def add_new(self, sender_name):
        self.add_detail_window = AddDetails(sender_name)
        self.add_detail_window.show()

    def closeEvent(self, event):
        """Window band hone par agar upload chal raha ho to warn karo."""
        if self._is_uploading:
            reply = QMessageBox.question(
                self, "Upload in Progress",
                "Image upload ho rahi hai. Kya aap phir bhi band karna chahte hain?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            if self._upload_worker is not None and self._upload_worker.isRunning():
                self._upload_worker.wait(3000)
        event.accept()


class Suggestion(QWidget):
    sent_data = pyqtSignal(list)

    def __init__(self, sender_name):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setFixedSize(600, 500)
        self.main_layout = QGridLayout(self)

        self.close_window_btn = QPushButton("Close")
        self.close_window_btn.setFixedSize(90, 30)
        self.close_window_btn.setObjectName("deletebtn")
        self.close_window_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_window_btn.clicked.connect(self.close_window)
        self.close_window_btn.setShortcut("Esc")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        
        if sender_name == "company":
            self.data_model = TableModel("SELECT company_code, company_description FROM company_data")
        elif sender_name == "category":
            self.data_model = TableModel("SELECT cat_code, cat_description FROM categories")
        elif sender_name == "size":
            self.data_model = TableModel("SELECT id, size_name FROM prd_size")

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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)
        self.search_input.installEventFilter(self)
        self.table_view.installEventFilter(self)

        self.main_layout.addWidget(self.search_input, 0, 0)
        self.main_layout.addWidget(self.close_window_btn, 0, 1)
        self.main_layout.addWidget(self.table_view, 1, 0, 1, 2)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            
            if obj == self.search_input:
                row_count = self.proxy.rowCount()
                if row_count == 0:
                    return super().eventFilter(obj, event)
                
                current_index = self.table_view.currentIndex()
                current_row = current_index.row() if current_index.isValid() else -1
                
                if key == Qt.Key.Key_Up:
                    new_row = current_row - 1 if current_row > 0 else row_count - 1
                    self.select_table_row(new_row)
                    return True
                elif key == Qt.Key.Key_Down:
                    new_row = current_row + 1 if current_row < row_count - 1 else 0
                    self.select_table_row(new_row)
                    return True
                elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if current_index.isValid():
                        self.on_row_select(current_index)
                        return True
            
            elif obj == self.table_view:
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    current_index = self.table_view.currentIndex()
                    if current_index.isValid():
                        self.on_row_select(current_index)
                        return True
                elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                    current_index = self.table_view.currentIndex()
                    if current_index.isValid():
                        row = current_index.row()
                        col = current_index.column()
                        if key == Qt.Key.Key_Up:
                            new_row = max(0, row - 1)
                        else:
                            new_row = min(self.proxy.rowCount() - 1, row + 1)
                        if new_row != row:
                            new_index = self.proxy.index(new_row, col)
                            self.table_view.setCurrentIndex(new_index)
                            self.table_view.selectRow(new_row)
                        return True
        
        return super().eventFilter(obj, event)

    def select_table_row(self, row):
        if row < 0 or row >= self.proxy.rowCount():
            return
        model_index = self.proxy.index(row, 0)
        if model_index.isValid():
            self.table_view.clearSelection()
            self.table_view.selectRow(row)
            self.table_view.setCurrentIndex(model_index)
            self.table_view.scrollTo(model_index, QAbstractItemView.ScrollHint.EnsureVisible)
            self.table_view.setFocus()

    def close_window(self):
        self.close()

    def on_row_select(self, index):
        row = index.row()
        row_data = []
        model = self.table_view.model()
        for col in range(model.columnCount()):
            item = model.index(row, col).data(Qt.ItemDataRole.DisplayRole)
            if item:
                row_data.append(item)
        self.sent_data.emit(row_data)
        self.close()


class AddDetails(QWidget):
    def __init__(self, sender_name):
        super().__init__()
        self.setWindowTitle(f"Add {sender_name}")
        self.setFixedSize(700, 600)
        self.setWindowIcon(QIcon("assets/icons/icon.png"))
        self.sender_name = sender_name
        self.company_id = None
        self.category_id = None
        self.size_id = None
        self.row_data = []
        self._is_saving = False

        try:
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(0, 0, 0, 0)
            
            self.label = self.create_header(f"{sender_name}", "MainLabel", '25px')
            self.label.setFixedHeight(60)

            self._data = QWidget()
            self._data_layout = QHBoxLayout(self._data)

            self._detail_widget = QWidget()
            self._detail_widget.setObjectName("input_widget")
            self._detail_widget.setFixedSize(300, 250)
            self._detail_layout = QVBoxLayout(self._detail_widget)
            self._detail_layout.addStretch()
            self._detail_layout.addSpacing(10)

            self.detail_label_widget = self.create_header(f"{sender_name} Details", "MainLabel", '20px')
            self.detail_label_widget.setFixedSize(160, 30)
            self._detail_layout.addWidget(self.detail_label_widget)

            self.is_active_widget = QCheckBox("Active")
            self.is_active_widget.setChecked(True)
            self._detail_layout.addWidget(self.is_active_widget, alignment=Qt.AlignmentFlag.AlignRight)

            self.name_input_widget, self.name_input_value = self.create_input_field("Name")
            self.name_input_value.textChanged.connect(lambda: self.auto_uppercase_input(self.name_input_value))
            self._detail_layout.addWidget(self.name_input_widget)

            self.address_input_widget = None
            self.address_input_value = None
            self.city_input_widget = None
            self.city_input_value = None
            self.short_name_input_widget = None
            self.short_name_value = None

            if sender_name == 'company':
                self.data_model = TableModel("SELECT * FROM company_data")
                self.address_input_widget, self.address_input_value = self.create_input_field("Address")
                self.city_input_widget, self.city_input_value = self.create_input_field("City")
                self.short_name_input_widget, self.short_name_value = self.create_input_field("Short Name")
                self._detail_layout.addWidget(self.address_input_widget)
                self._detail_layout.addWidget(self.city_input_widget)
                self._detail_layout.addWidget(self.short_name_input_widget)
            elif sender_name == 'Category':
                self.data_model = TableModel("SELECT * FROM categories")
            elif sender_name == 'size':
                self.data_model = TableModel("SELECT * FROM prd_size")

            self.existing_data_view = QTableView()
            self.existing_data_view.setWordWrap(True)
            self.existing_data_view.setAlternatingRowColors(True)
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
            self.setup_enter_navigation()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize AddDetails window:\n\n{type(e).__name__}: {e}"
            )

    def auto_uppercase_input(self, widget):
        text = widget.text()
        if text:
            cursor_pos = widget.cursorPosition()
            new_text = text.upper()
            if new_text != text:
                widget.blockSignals(True)
                widget.setText(new_text)
                widget.setCursorPosition(cursor_pos)
                widget.blockSignals(False)

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
            if self.sender_name == "company":
                self.company_id = int(self.row_data[0])
                self.name_input_value.setText(str(self.row_data[1]) if self.row_data[1] is not None else "")
                self.address_input_value.setText(str(self.row_data[2]) if self.row_data[2] is not None else "")
                self.city_input_value.setText(str(self.row_data[3]) if self.row_data[3] is not None else "")
                self.short_name_value.setText(str(self.row_data[4]) if self.row_data[4] is not None else "")
                active = self.row_data[5] if len(self.row_data) > 5 else 1
                self.is_active_widget.setChecked(active in (1, True, "1"))
            elif self.sender_name == "Category":
                self.category_id = int(self.row_data[0])
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

            if self.sender_name == "company":
                company_name = self.name_input_value.text().strip()
                if not company_name:
                    QMessageBox.warning(self, "Validation Error", "Company Name is required.")
                    return
                if self.company_id is not None and self.company_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                address = self.address_input_value.text().strip() or None
                city = self.city_input_value.text().strip() or None
                short_name = self.short_name_value.text().strip() or None
                is_active = self.is_active_widget.isChecked()
                
                conn, cursor = db.get_connection()
                if is_update:
                    query = 'UPDATE company_data SET company_description = %s, address = %s, city = %s, short_name = %s, is_active = %s WHERE company_code = %s'
                    values = (company_name, address, city, short_name, is_active, self.company_id)
                else:
                    query = "INSERT INTO company_data (company_description, address, city, short_name, is_active) VALUES (%s, %s, %s, %s, %s)"
                    values = (company_name, address, city, short_name, is_active)
                cursor.execute(query, values)
                conn.commit()
                QMessageBox.information(self, "Success", message)
                self.refresh_data()

            elif self.sender_name == "Category":
                category_name = self.name_input_value.text().strip()
                if not category_name:
                    QMessageBox.warning(self, "Validation Error", "Category Name is required.")
                    return

                is_active = self.is_active_widget.isChecked()
                if self.category_id is not None and self.category_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                
                conn, cursor = db.get_connection()
                if is_update:
                    query = 'UPDATE categories SET cat_description=%s, is_active = %s WHERE cat_code = %s'
                    values = (category_name, is_active, self.category_id)
                else:
                    query = """INSERT INTO categories ( cat_description, is_active) VALUES (%s, %s)"""
                    values = (category_name, is_active)
                cursor.execute(query, values)
                conn.commit()
                self.refresh_data()
                QMessageBox.information(self, 'Success', message)

            elif self.sender_name == "size":
                size_name = self.name_input_value.text().strip()
                if not size_name:
                    QMessageBox.warning(self, "Validation Error", "Size Name is required.")
                    return

                is_active = self.is_active_widget.isChecked()
                if self.size_id is not None and self.size_id != "":
                    is_update = True
                    message = 'Record Updated Success..'
                
                conn, cursor = db.get_connection()
                if is_update:
                    query = 'UPDATE prd_size SET size_name=%s, is_active = %s WHERE id = %s'
                    values = (size_name, is_active, self.size_id)
                else:
                    query = """INSERT INTO prd_size (size_name, is_active) VALUES (%s, %s)"""
                    values = (size_name, is_active)
                cursor.execute(query, values)
                conn.commit()
                self.refresh_data()
                QMessageBox.information(self, 'Success', message)
                
        except Exception as e:
            raise
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
    def refresh_data(self):
        if self.sender_name == "company":
            self.data_model._load_data("SELECT * FROM company_data")
            self.name_input_value.setText("")
            self.address_input_value.setText("")
            self.city_input_value.setText("")
            self.short_name_value.setText("")
            self.company_id = None
        elif self.sender_name == "Category":
            self.data_model._load_data("SELECT * FROM categories")
            self.name_input_value.setText("")
            self.category_id = None
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