# predefined_widgets.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from database import DatabaseManager
db = DatabaseManager()

class Suggestion(QWidget):
    sent_data = pyqtSignal(list)
    
    def __init__(self, query, sender_name, refresh_callback=None, display_columns=None):
        super().__init__()
        self.query = query
        self.sender_name = sender_name
        self.refresh_callback = refresh_callback
        self.display_columns = display_columns  # New parameter for custom display columns
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setFixedSize(800, 650)
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setVerticalSpacing(15)
        self.main_layout.setHorizontalSpacing(10)
        
        self.main_label_widget = QWidget()
        self.main_label_widget.setFixedHeight(60)
        self.main_label_widget.setObjectName("mainlabelwidget")
        self.main_label_layout = QHBoxLayout(self.main_label_widget)
        self.main_label_widget.setStyleSheet(
            """
            QWidget#mainlabelwidget{
                background-color: rgba(251, 191, 36, 0.5) ;
                border-radius: 10px;
                border: 2px solid #cc8b00;
            }
            """
        )
        self.main_label_layout.setContentsMargins(0, 0, 0, 0)

        self.main_label = QLabel(f"Search and Choose {sender_name} to edit")
        self.main_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F172A;")
        self.main_label_layout.addWidget(self.main_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.main_label_widget, 0, 0, 1, 2)
        
        # Create button container for refresh and close buttons
        self.button_container = QWidget()
        self.button_container.setFixedHeight(40)
        self.button_container_layout = QHBoxLayout(self.button_container)
        self.button_container_layout.setContentsMargins(0, 0, 0, 0)
        self.button_container_layout.setSpacing(10)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedSize(120, 35)
        self.refresh_btn.setObjectName("refreshbtn")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        
        self.close_window_btn = QPushButton("Close")
        self.close_window_btn.setFixedSize(100, 35)
        self.close_window_btn.setObjectName("deletebtn")
        self.close_window_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_window_btn.clicked.connect(self.close_window)
        self.close_window_btn.setShortcut("Esc")
        self.close_window_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        
        self.button_container_layout.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.button_container_layout.addWidget(self.close_window_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, code, phone or email...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 14px;
                background-color: #F8FAFC;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background-color: white;
            }
        """)
        
        # Create the table model with the query
        self.data_model = TableModel(self.query)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.data_model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.clicked.connect(self.on_row_select)
        self.table_view.setAlternatingRowColors(True)
        
        header = self.table_view.horizontalHeader()
        header.setMinimumSectionSize(100)
        
        # If display_columns is provided, hide other columns
        if self.display_columns:
            # Get all column headers
            all_headers = self.data_model._headers
            for idx, header_name in enumerate(all_headers):
                if header_name not in self.display_columns:
                    self.table_view.setColumnHidden(idx, True)
        
        self.search_input.textChanged.connect(self.proxy.setFilterFixedString)
        
        self.main_layout.addWidget(self.search_input, 1, 0)
        self.main_layout.addWidget(self.button_container, 1, 1, Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.table_view, 2, 0, 1, 2)
        
        # Install event filter on search input to capture arrow keys
        self.search_input.installEventFilter(self)
        
        # Install event filter on table view to capture Enter key
        self.table_view.installEventFilter(self)
        
        # Flag to track if data is being loaded
        self._loading = False
        
    def refresh_data(self):
        """Refresh the table data"""
        if self._loading:
            return
        
        self._loading = True
        try:
            # Store current search text
            current_search = self.search_input.text()
            
            # Clear the current selection
            self.table_view.clearSelection()
            self.table_view.clearFocus()
            
            # Reload data from database directly into the model
            self.data_model.beginResetModel()
            try:
                result = db.get_any_table(self.query)
                if result is None:
                    self.data_model._data = []
                    self.data_model._headers = []
                else:
                    print(f"Data refreshed: {len(result)} records")
                    self.data_model._data = result
                    self.data_model._headers = list(result[0].keys()) if result else []
            except Exception as e:
                print(f"Error refreshing data: {e}")
                self.data_model._data = []
                self.data_model._headers = []
            self.data_model.endResetModel()
            
            # Update the proxy model
            self.proxy.setSourceModel(None)
            self.proxy.setSourceModel(self.data_model)
            self.proxy.invalidate()
            
            # Restore search if there was one
            if current_search:
                self.search_input.setText(current_search)
                self.proxy.setFilterFixedString(current_search)
            
            # Update column visibility
            if self.display_columns and self.data_model._headers:
                for idx, header_name in enumerate(self.data_model._headers):
                    if header_name not in self.display_columns:
                        self.table_view.setColumnHidden(idx, True)
                    else:
                        self.table_view.setColumnHidden(idx, False)
            
            # Force the table view to update
            self.table_view.update()
            self.table_view.repaint()
            self.table_view.viewport().update()
            
            # Show success message
            QMessageBox.information(self, "Success", 
                                   f"Data refreshed successfully!\n\nTotal records: {self.proxy.rowCount()}")
            
            # Call the refresh callback if provided
            if self.refresh_callback:
                try:
                    self.refresh_callback()
                except Exception as e:
                    print(f"Error in refresh callback: {e}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")
        finally:
            self._loading = False
        
    def eventFilter(self, obj, event):
        """Handle arrow keys in search input and Enter key in table view"""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            
            # Handle search input events
            if obj == self.search_input:
                # Get the current row count
                row_count = self.proxy.rowCount()
                if row_count == 0:
                    return super().eventFilter(obj, event)
                
                # Get current selection
                current_index = self.table_view.currentIndex()
                current_row = current_index.row() if current_index.isValid() else -1
                
                # Handle Up arrow
                if key == Qt.Key.Key_Up:
                    if current_row <= 0:
                        new_row = row_count - 1
                    else:
                        new_row = current_row - 1
                    
                    self.select_table_row(new_row)
                    return True
                
                # Handle Down arrow
                elif key == Qt.Key.Key_Down:
                    if current_row >= row_count - 1:
                        new_row = 0
                    else:
                        new_row = current_row + 1
                    
                    self.select_table_row(new_row)
                    return True
                
                # Handle Enter key from search input
                elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                    if current_index.isValid():
                        self.on_row_select(current_index)
                        return True
            
            # Handle table view events
            elif obj == self.table_view:
                # Handle Enter key on selected row in table
                if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                    current_index = self.table_view.currentIndex()
                    if current_index.isValid():
                        self.on_row_select(current_index)
                        return True
                # Handle Escape key to close
                elif key == Qt.Key.Key_Escape:
                    self.close_window()
                    return True
        
        return super().eventFilter(obj, event)
    
    def select_table_row(self, row):
        """Select a specific row in the table view"""
        if row < 0 or row >= self.proxy.rowCount():
            return
        
        # Get the model index for the row
        model_index = self.proxy.index(row, 0)
        if model_index.isValid():
            # Clear current selection
            self.table_view.clearSelection()
            # Select the row
            self.table_view.selectRow(row)
            # Set current index
            self.table_view.setCurrentIndex(model_index)
            # Scroll to the selected row
            self.table_view.scrollTo(model_index, QAbstractItemView.ScrollHint.EnsureVisible)
            # Set focus to table view
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


class TableModel(QAbstractTableModel):
    def __init__(self, query):
        super().__init__()
        self._data = []
        self._headers = []
        self.conn, self.cursor = db.get_connection()
        self._query = query
        self._load_data(query)

    def load_data(self, query):
        """Public method to reload data"""
        self._query = query
        self._load_data(query)

    def _load_data(self, query):
        """Private method to load data from database"""
        self.beginResetModel()
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            
            if result is None:
                print(f"No data returned for query: {query}")
                self._data = []
                self._headers = []
            else:
                print(f"Data loaded: {len(result)} records")
                self._data = result
                self._headers = list(self._data[0].keys()) if self._data else []
                
        except Exception as e:
            print(f"Error loading data: {e}")
            self._data = []
            self._headers = []
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
                    # Clean up header names
                    header = header.replace('vnd_', '').replace('slm_', '').replace('cus_', '')
                    return header.split("_")[-1].title()
                except IndexError:
                    return ""
            return section + 1
        return None