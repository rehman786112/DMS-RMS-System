import PyQt6.QtWidgets as q 
from PyQt6.QtWidgets import QMainWindow,QApplication,QGraphicsDropShadowEffect,QLabel,QLineEdit,QCheckBox,QToolButton,QMessageBox
from PyQt6.QtGui import QIcon,QPixmap,QColor,QFont,QAction
from PyQt6.QtCore import Qt,QTimer ,QDate
import sys
from pictures_path_files import resource_path
from error_handling import gui_exception
from table_invoice_widget import InvoiceTable
from stock_managment import stock as stk
from product import products as p
# ==========================================
# IMPORTS
# ==========================================

from PyQt6 import QtWidgets as q
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


# ==========================================
# CUSTOMER TABLE CLASS
# ==========================================

class CustomerTable(q.QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sale_invoice = parent

        self.setSelectionBehavior(
            q.QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            q.QAbstractItemView.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            q.QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.verticalHeader().setVisible(False)

    def keyPressEvent(self, event):

        # ENTER = SELECT CUSTOMER
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):

            row = self.currentRow()

            if row >= 0:
                self.sale_invoice.select_customer(
                    row,
                    self.currentColumn()
                )

            return

        # ESC = CLOSE
        if event.key() == Qt.Key.Key_Escape:

            self.sale_invoice.customer_frame.hide()
            self.sale_invoice.customer_code_entry.setFocus()

            return

        # UP / DOWN
        if event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down
        ):

            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)


# ==========================================
# PRODUCT TABLE CLASS
# ==========================================

class ProductTable(q.QTableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sale_invoice = parent

        self.setSelectionBehavior(
            q.QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            q.QAbstractItemView.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            q.QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.verticalHeader().setVisible(False)

    def keyPressEvent(self, event):

        # ENTER = SELECT PRODUCT
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):

            row = self.currentRow()

            if row >= 0:
                self.sale_invoice.select_product(
                    row,
                    self.currentColumn()
                )

            return

        # ESC = CLOSE
        if event.key() == Qt.Key.Key_Escape:

            self.sale_invoice.product_frame.hide()
            self.sale_invoice.product_search.setFocus()

            return

        # UP / DOWN
        if event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down
        ):

            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)


    # =========================================
    # Invoice NO table 
    # =========================================


class Invoice_no_Table(q.QTableWidget):

      def __init__(self, parent=None):
        super().__init__(parent)

        self.sale_invoice = parent

        self.setSelectionBehavior(
            q.QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            q.QAbstractItemView.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            q.QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.verticalHeader().setVisible(False)

      def keyPressEvent(self, event):

        # ENTER = SELECT PRODUCT
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):

            row = self.currentRow()

            if row >= 0:
                self.sale_invoice.select_invoices(
                    row,
                    self.currentColumn()
                )

            return

        # ESC = CLOSE
        if event.key() == Qt.Key.Key_Escape:

            self.sale_invoice.invoices_frame.hide()
            self.sale_invoice.invoice_no.setFocus()

            return

        # UP / DOWN
        if event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down
        ):

            super().keyPressEvent(event)
            return

        super().keyPressEvent(event)



# ==========================================
# SALE INVOICE CLASS
# ==========================================

class SaleInvoice(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sale Invoice")
        self.setWindowIcon(QIcon(resource_path("images/logo.ico")))
        self.create_ui()
        self.add_product()

        # call Products functions move next 
        self.move_next(
        self.product_search,
        self.carton_entry,
        )

       # Data base Connections 
        self.cursor, self.connection = p.database_connection(self)
    
        
    # ==========================================================
    # MAIN UI
    # ==========================================================

    def create_ui(self):

        central = q.QWidget()
        self.setCentralWidget(central)

        main_layout = q.QVBoxLayout(central)
        main_layout.setContentsMargins(3, 3, 3, 5)
        main_layout.setSpacing(1)

        # ======================================================
        # HEADER
        # ======================================================

        header = q.QFrame()
        header.setObjectName("header")
        header.setFixedHeight(50)

        header_layout = q.QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 12)

        title = QLabel("🧾  SALE INVOICE")
        title.setObjectName("title")

        

        title_layout = q.QVBoxLayout()
        title_layout.addWidget(title)
       
        

        invoice_label = QLabel("Invoice #")
        invoice_label.setObjectName("invoice_label")
        
               

        self.invoice_no = QLineEdit()
        self.invoice_no.setPlaceholderText("000001")
        self.invoice_no.setFixedWidth(130)
        self.invoice_no.keyPressEvent = self.invoice_no_key_press

        header_layout.addWidget(invoice_label)
        header_layout.addWidget(self.invoice_no)

        # +++++++++++++++++++ push right space to left
        header_layout.addSpacing(330)

        header_layout.addLayout(title_layout)


        header_layout.addStretch()

        main_layout.addWidget(header)

        # ======================================================
        # INVOICE INFORMATION
        # ======================================================

        info_frame = q.QFrame()
        info_frame.setObjectName("card")
        info_frame.setFixedHeight(130)

        info_layout = q.QGridLayout(info_frame)
        info_layout.setContentsMargins(5, 5, 10, 10)
        info_layout.setHorizontalSpacing(15)
        info_layout.setVerticalSpacing(5)

        # Date
        info_layout.addWidget(
            self.create_label("Invoice Date"),
            0, 0
        )

        self.invoice_date = q.QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        self.invoice_date.setCalendarPopup(True)

        info_layout.addWidget(
            self.invoice_date,
            1, 0
        )

        # Salesman
        info_layout.addWidget(
            self.create_label("Salesman"),
            0, 1
        )

        self.salesman = q.QComboBox()
        self.salesman.addItem("COUNTER SALE")
        self.salesman.addItem("Select Salesman")

        info_layout.addWidget(
            self.salesman,
            1, 1
        )

        # Payment mode
        info_layout.addWidget(
            self.create_label("Payment Mode"),
            0, 2
        )

        self.payment_mode = q.QComboBox()
        self.payment_mode.addItems([
            "Cash",
            "Credit",
        ])

        info_layout.addWidget(
            self.payment_mode,
            1, 2
        )

        # Delivery man
        info_layout.addWidget(
            self.create_label("Delivery Man"),
            0, 3
        )

        self.delivery_man = q.QComboBox()
        self.delivery_man.addItem("Select Delivery Man")

        info_layout.addWidget(
            self.delivery_man,
            1, 3
        )

        # Printer
        info_layout.addWidget(
            self.create_label("Printer"),
            0, 4
        )

        self.printer = q.QComboBox()
        self.printer.addItems(["Large Printer",
                              "Thermal Printer"])

        info_layout.addWidget(
            self.printer,
            1, 4
        )

        # Customer code
        info_layout.addWidget(
            self.create_label("Customer Code"),
            2, 0
        )

        self.customer_code_entry = QLineEdit()
        self.customer_code_entry.setPlaceholderText("Enter code")
        self.customer_code_entry.keyPressEvent = self.customer_code_key_press

        info_layout.addWidget(
            self.customer_code_entry,
            3, 0
        )

        # Customer name
        info_layout.addWidget(
            self.create_label("Customer Name"),
            2, 1
        )

        self.customer_name_entry = QLineEdit()
        self.customer_name_entry.setPlaceholderText("Customer name")
        

        info_layout.addWidget(
            self.customer_name_entry,
            3, 1
        )

        # Address
        info_layout.addWidget(
            self.create_label("Address"),
            2, 2
        )

        self.customer_address_entry = QLineEdit()
        self.customer_address_entry.setPlaceholderText("Customer address")

        info_layout.addWidget(
            self.customer_address_entry,
            3, 2, 1, 2
        )


        # Balance
        info_layout.addWidget(
            self.create_label("Customer Balance"),
            2, 4
        )

        self.customer_balance_entry = QLineEdit()
        self.customer_balance_entry.setText("0.00")
        self.customer_balance_entry.setReadOnly(True)
        self.customer_balance_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(
            self.customer_balance_entry,
            3, 4
        )

        main_layout.addWidget(info_frame)

        # Customer name
        info_layout.addWidget(
            self.create_label("OverAll Balance"),
            2, 5
        )

        self.customer_overall_balance = QLineEdit()
        self.customer_overall_balance.setText("0.00")
        self.customer_overall_balance.setReadOnly(True)
        self.customer_overall_balance.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(
            self.customer_overall_balance,
            3, 5
        )

        # ======================================================
        # PRODUCT ENTRY
        # ======================================================

        product_frame = q.QFrame()
        product_frame.setObjectName("card")

        product_layout = q.QGridLayout(product_frame)
        product_layout.setContentsMargins(0, 5, 18, 15)
        product_layout.setHorizontalSpacing(5)
        product_layout.setVerticalSpacing(0)
    

        

        # Product search
        product_layout.addWidget(
            self.create_label("Search Product"),
            1, 0
        )

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText(
            "Search product..."
        )

        self.product_search.keyPressEvent = self.product_search_key_press

        product_layout.addWidget(
            self.product_search,
            2, 0
        )

        # Carton
        product_layout.addWidget(
            self.create_label("Ctn"),
            1, 1
        )

        self.carton_entry = QLineEdit()
        self.carton_entry.setPlaceholderText(
            "0"
        )
        self.carton_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        product_layout.addWidget(
            self.carton_entry,
            2, 1
        )

        # ===============================
        # call carton quantity entry
        # ===============================

        self.carton_entry.returnPressed.connect(
    self.check_ctn_pcs
        )



        # pcs
        product_layout.addWidget(
            self.create_label("Pcs"),
            1, 2
        )

        self.pcs_entry = QLineEdit()
        self.pcs_entry.setText("0")
        self.pcs_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        # ===============================
        # call pcs quantity entry
        # ===============================
        self.pcs_entry.returnPressed.connect(
        self.product_quantity_check)

        

        product_layout.addWidget(
            self.pcs_entry,
            2, 2
        )

        # Quantity
        product_layout.addWidget(
            self.create_label("Quantity"),
            1, 3
        )

        self.quantity_entry = QLineEdit()
        self.quantity_entry.setText("0")
        self.quantity_entry.setReadOnly(True)
        self.quantity_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
         
        
        self.quantity_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)


        product_layout.addWidget(
            self.quantity_entry,
            2, 3
        )

        # Bonus
        product_layout.addWidget(
            self.create_label("Bonus"),
            1, 4
        )

        self.bonus_entry = QLineEdit()
        self.bonus_entry.setText("0")
        self.bonus_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        product_layout.addWidget(
            self.bonus_entry,
            2, 4
        )
        # ===============================
        # call bonus entry
        # ===============================
        self.bonus_entry.returnPressed.connect(
                self.bonus_entry_
                    )
        
        # Sale Price
        product_layout.addWidget(
            self.create_label("Sale Price"),
            1, 5
        )

        self.sale_price_entry = QLineEdit()
        self.sale_price_entry.setText("0")
        self.sale_price_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        product_layout.addWidget(
            self.sale_price_entry,
            2, 5
        )

        # ===============================
        # call sale_price entry
        # ===============================
        self.sale_price_entry.returnPressed.connect(
                self.sale_price_entry_
                    )
                

        # carton Rate
        product_layout.addWidget(
            self.create_label("Carton Rate"),
            1, 6
        )

        self.carton_rate_entry = QLineEdit()
        self.carton_rate_entry.setText("0")
        self.carton_rate_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.carton_rate_entry.returnPressed.connect(
            self.carton_rate_entry_
                )
        
        
        product_layout.addWidget(
            self.carton_rate_entry,
            2, 6
        )

        # per
        product_layout.addWidget(
            self.create_label("%Per"),
            1, 7
        )

        self.per_entry = QLineEdit()
        self.per_entry.setText("0")
        self.per_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        product_layout.addWidget(
            self.per_entry,
            2, 7
        )
        self.per_entry.returnPressed.connect(
                        self.percntage_entry
                            )

        # Discount
        product_layout.addWidget(
            self.create_label("Discount"),
            1,8
        )

        self.Discount_entry = QLineEdit()
        self.Discount_entry.setText("0.00")
        self.Discount_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        product_layout.addWidget(
            self.Discount_entry,
            2, 8
        )

        self.Discount_entry.returnPressed.connect(
                                self.discount_entry
                                    )
        

        # tax
        product_layout.addWidget(
            self.create_label("Tax"),
            1, 9
        )

        self.tax_entry = QLineEdit()
        self.tax_entry.setText("0")
        self.tax_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tax_entry.returnPressed.connect(
                                self.Tax_entry
                                    )
        
        product_layout.addWidget(
            self.tax_entry,
            2, 9
        )

        # net price
        product_layout.addWidget(
            self.create_label("Total Amount"),
            1,10
        )

        self.total_amount_entry = QLineEdit()
        self.total_amount_entry.setText("0")
        self.total_amount_entry.setReadOnly(True)
        self.total_amount_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        product_layout.addWidget(
            self.total_amount_entry,
            2, 10
        )

        # total Amount
        product_layout.addWidget(
            self.create_label("Net Amount"),
            1, 11
        )

        self.net_amount_entry = QLineEdit()
        self.net_amount_entry.setText("0")
        self.net_amount_entry.setReadOnly(True)
        self.net_amount_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        

        product_layout.addWidget(
            self.net_amount_entry,
            2,11
        )


        main_layout.addWidget(product_frame)


        # ========================================= set width of the entries ===================================
        self.product_search.setFixedWidth(150)
       
        self.carton_entry.setFixedWidth(70)
        self.pcs_entry.setFixedWidth(70)
        self.quantity_entry.setFixedWidth(80)
        self.bonus_entry.setFixedWidth(70)
        self.sale_price_entry.setFixedWidth(70)
        self.carton_rate_entry.setFixedWidth(70)
        self.per_entry.setFixedWidth(70)
        self.Discount_entry.setFixedWidth(80)
        self.tax_entry.setFixedWidth(80)
        self.total_amount_entry.setFixedWidth(130)
        self.net_amount_entry.setFixedWidth(130)
       

        # ======================================================
        # TABLE
        # ======================================================

        table_frame = q.QFrame()
        table_frame.setObjectName("card")
        

        table_layout = q.QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12,12)


        self.table = InvoiceTable()

        self.table.setColumnCount(13)

        self.table.setHorizontalHeaderLabels([
        "ID",
        "Name",
        "Carton",
        "Pcs",
        "Quantity",
        "Bonus",
        "Sale Price",
        "Carton Rate",
        "Per",
        "Discount",
        "Tax",
        "Total Amount",
        "Net Amount"
        ])

        
        # Select complete row
        self.table.setSelectionBehavior(
        q.QAbstractItemView.SelectionBehavior.SelectRows
        )

        # Allow double click / Enter to edit cells
        self.table.setEditTriggers(
        q.QAbstractItemView.EditTrigger.DoubleClicked |
        q.QAbstractItemView.EditTrigger.EditKeyPressed
        )

        # Hide row numbers
        self.table.verticalHeader().setVisible(False)

        # Column width
        header = self.table.horizontalHeader()
        header = self.table.horizontalHeader()

        # IMPORTANT:
        # Make every column fixed width
        header.setSectionResizeMode(
            q.QHeaderView.ResizeMode.Fixed
        )

        # Now widths will work
        self.table.setColumnWidth(0, 80)    # ID
        self.table.setColumnWidth(1, 220)   # Name
        self.table.setColumnWidth(2, 70)    # Carton
        self.table.setColumnWidth(3, 70)    # Pcs
        self.table.setColumnWidth(4, 70)    # Quantity
        self.table.setColumnWidth(5, 74)    # Bonus
        self.table.setColumnWidth(6, 90)    # Sale Price
        self.table.setColumnWidth(7, 100)   # Carton Rate
        self.table.setColumnWidth(8, 70)    # Per
        self.table.setColumnWidth(9, 70)    # Discount
        self.table.setColumnWidth(10, 70)   # Tax
        self.table.setColumnWidth(11, 130)  # Total Amount
        self.table.setColumnWidth(12, 130)  # Net Amount
        

        # Connect cell editing
        self.table.itemChanged.connect(
        self.table_item_changed
        )

        table_layout.addWidget(self.table)

        main_layout.addWidget(
        table_frame,
        1
        )
        # ======================================================
        # TOTALS
        # ======================================================

        totals_frame = q.QFrame()
        totals_frame.setObjectName("card")

        totals_layout = q.QGridLayout(totals_frame)
        totals_layout.setContentsMargins(15, 12, 15, 12)

        self.total_items = self.create_total_box(
            "Total Items",
            "0"
        )

        self.total_carton = self.create_total_box(
            "Cartons",
            "0"
        )

        self.total_pcs = self.create_total_box(
            "Pieces",
            "0"
        )

        self.total_quantity = self.create_total_box(
            "Quantity",
            "0"
        )

        self.bill_total_amount = self.create_total_box(
                    "Total Amount",
                    "0.00"
                )

        self.bill_net_amount = self.create_total_box(
            "Net Amount",
            "0.00",
            
        )
        self.bill_net_amount.setObjectName("bill_net_amount")
        ################################# for whole bill tax,percent,discount ################################# 
        self.bill_per_amount = self.create_total_box(
                                    "Bill %per",
                                    "0.00"
                                )
        self.bill_tax_amount = self.create_total_box(
                    "Bill Tax",
                    "0.00"
                )

        self.bill_discount_amount = self.create_total_box(
            "Bill Discount",
            "0.00"
        )


       
                
        
        totals_layout.addWidget(self.total_items,0,0)
        totals_layout.addWidget(self.total_carton,0,1)
        totals_layout.addWidget(self.total_pcs,0,2)
        totals_layout.addWidget(self.total_quantity,0,3)
        totals_layout.addWidget(self.bill_tax_amount,0,4)
        totals_layout.addWidget(self.bill_discount_amount,0,5)
        totals_layout.addWidget(self.bill_per_amount,0,6)
        totals_layout.addWidget(self.bill_total_amount,0,7)
                
        totals_layout.addWidget(self.bill_net_amount, 0, 8, 2, 1)
    
        totals_frame.setStyleSheet("""
                    QFrame{
                        background:#e0b7e8e3;
                    }
                """)
                        
        totals_layout.addWidget(self.create_label("Total Bill Per:"),1,0)
        self.total_bill_per_entry = QLineEdit()
        self.total_bill_per_entry.setText("0")
        self.total_bill_per_entry.setFixedWidth(100)
        self.total_bill_per_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                
                

        totals_layout.addWidget(self.create_label("Total Bill Tax:"),1,2)        
        self.total_bill_tax_entry = QLineEdit()
        self.total_bill_tax_entry.setText("0")
        self.total_bill_tax_entry.setFixedWidth(100)
        self.total_bill_tax_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                
                

        totals_layout.addWidget(self.create_label("Total Bill Discount:"),1,4)
        self.total_bill_discount_entry = QLineEdit()
        self.total_bill_discount_entry.setText("0")
        self.total_bill_discount_entry.setFixedWidth(100)
        self.total_bill_discount_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
                                
                

        ####################### total entries lables and bill entries #################################
        totals_layout.addWidget(self.total_bill_per_entry,1,1)
        totals_layout.addWidget(self.total_bill_tax_entry,1,3)
        totals_layout.addWidget(self.total_bill_discount_entry,1,5)
                

        


        main_layout.addWidget(totals_frame)

        # ======================================================
        # BUTTONS
        # ======================================================

        button_frame = q.QFrame()
        button_frame.setObjectName("button_frame")

        button_layout = q.QHBoxLayout(button_frame)

        self.clear_btn = q.QPushButton("🗑  Clear")
        self.save_btn = q.QPushButton("💾  Save")
        self.edit_btn = q.QPushButton("✏  Edit")
        self.print_btn =q. QPushButton("🖨  Print Invoice")
        self.ledger_btn = q.QPushButton("📒  Customer Ledger")
        self.sale_summary_btn = q.QPushButton("📒  Sale Summary")
        self.add_customer_btn = q.QPushButton("＋   Add Customers")
        

        # Add button
        self.add_product_btn = q.QPushButton(
            "＋  ADD PRODUCT"
        )

        self.add_product_btn.setObjectName(
            "add_button"
        )

        self.print_btn.setObjectName(
                    "print_button"
                )

        
        self.clear_btn.setObjectName("danger_button")
        self.add_customer_btn.setObjectName("add_customer")
        self.save_btn.setObjectName("success_button")

        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.add_customer_btn,)
        button_layout.addWidget(self.add_product_btn,)
        button_layout.addWidget(self.sale_summary_btn,)
        button_layout.addWidget(self.ledger_btn)
        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.save_btn)

        main_layout.addWidget(button_frame)

        button_frame.setStyleSheet("""
                 QFrame#button_frame{
                        background:black;
                        border: 1px solid #DDD8DF;
                        border-radius: 12px;
                    }""")

        # ======================================================
        # STYLE
        # ======================================================

        self.setStyleSheet("""

        QMainWindow {
            background: #F4F1F5;
        }

        QWidget {
            font-family: "Segoe UI";
            font-size: 13px;
        }

        QFrame#header {
            background: #252B33;
            border-radius: 12px;
        }

        QLabel#title {
            color: white;
            font-size: 23px;
            font-weight: bold;
        }

        QLabel#subtitle {
            color: #C8CBD0;
            font-size: 12px;
        }

        QLabel#invoice_label {
            color: white;
            font-size: 14px;
            font-weight: bold;
        }

        QFrame#card {
            background:#e0b7e8e3;
            border: 1px solid #DDD8DF;
            border-radius: 12px;
        }

        QLabel {
            color: #30343B;
        }

        QLineEdit,
        QComboBox,
        QDateEdit {

            background: #F8F7F9;
            font-size: 15px;
            font-weight: bold;

           

            padding: 2px;

            color: #222;
        }

        QLineEdit:focus,
        QComboBox:focus,
        QDateEdit:focus {

            border: 2px solid #C98DD8;

            background: white;
        }

        QTableWidget {

            background: white;


            gridline-color: #E5E1E7;

            selection-background-color: #E0B7E8;

            selection-color: #222;
        }

        QHeaderView::section {

            background: #252B33;

            color: white;

            padding: 8px;

            border: 2px;

            font-weight: bold;
        }

        QPushButton {

            background: #E0B7E8;

            color: #252B33;

            border: none;

            border-radius: 8px;

            padding: 9px 15px;

            font-weight: bold;
        }

        QPushButton:hover {

            background: #C98DD8;
        }

        QPushButton:pressed {

            background: #B970CC;
        }

        QPushButton#add_button {

            background:#e0b7e8e3;

            color: white;

            min-width: 130px;
        }

        QPushButton#add_button:hover {

            background: #3A424D;
        }

        QPushButton#print_button {
        
                    background:rgb(90, 78, 225);
        
                    color: white;
        
                    min-width: 130px;
                }
        
        

        QPushButton#add_customer {
        
                    background:#e0b7e8e3;
        
                    color: white;
        
                    min-width: 130px;
                }
        
      QPushButton#add_customer :hover {
        
                    background: #3A424D;
                }

        QPushButton#success_button {

            background: #35A66F;

            color: white;

            min-width: 110px;
        }

        QPushButton#danger_button {

            background: #D9534F;

            color: white;

            min-width: 100px;
        }

        """)

    # ==========================================================
    # HELPER FUNCTIONS
    # ==========================================================
        
    def create_label(self, text):
        
                label = QLabel(text)
        
                label.setStyleSheet("""
                    font-weight: bold;
                    color: #555;
                """)
        
                return label
        
    def create_section_title(self, text):
        
                label = QLabel(text)
        
                label.setStyleSheet("""
                    font-size: 16px;
                    font-weight: bold;
                    color: #252B33;
                    padding: 4px;
                """)
        
                return label
        
    def create_total_box(self, title, value):
        
                frame = q.QFrame()
        
                frame.setStyleSheet("""
                    QFrame {
                        background: #252B33;
                        
                    }
                """)
        
                layout = q.QVBoxLayout(frame)
        
                layout.setContentsMargins(15, 8, 15, 8)
        
                title_label = QLabel(title)
        
                title_label.setStyleSheet("""
                    color:white;
                    font-size: 15px;
                """)
                title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
        
                value_label = QLabel(value)
        
                value_label.setStyleSheet("""
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    background:#e0b7e8e3;
                """)
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
                layout.addWidget(title_label)
                layout.addWidget(value_label)
        
                return frame




             
        
        

        ################################## functions for tables ##########################################
        # ==========================================================
        # ADD PRODUCT TO TABLE
        # ==========================================================

    def add_product(self):

            row = self.table.rowCount()

            # Create new row
            self.table.insertRow(row)

            # ------------------------------------------------
            # ONE PRODUCT = ONE ROW
            # ------------------------------------------------

            data = [
                 
                "1001",             # 0  ID
                "Coca Cola 1.5L",   # 1  Name
                "2",                # 2  Carton
                "10",               # 3  Pcs
                "30",               # 4  Quantity
                "2",                # 5  Bonus
                "130",              # 6  Sale Price
                "1200",             # 7  Carton Rate
                "1",                # 8  Per
                "5",                # 9  Discount
                "0",                # 10 Tax
                "0.00",             # 11 Total Amount
                "0.00"              # 12 Net Amount
                 
                "1001",             # 0  ID
                "Coca Cola 1.5L",   # 1  Name
                "2",                # 2  Carton
                "10",               # 3  Pcs
                "30",               # 4  Quantity
                "2",                # 5  Bonus
                "130",              # 6  Sale Price
                "1200",             # 7  Carton Rate
                "1",                # 8  Per
                "5",                # 9  Discount
                "0",                # 10 Tax
                "0.00",             # 11 Total Amount
                "0.00"              # 12 Net Amount
            ]

            # ------------------------------------------------
            # INSERT EVERY CELL
            # ------------------------------------------------

            for column, value in enumerate(data):

                item = q.QTableWidgetItem(str(value))

                self.table.setItem(
                    row,
                    column,
                    item
                )

            # ------------------------------------------------
            # ID READ ONLY
            # ------------------------------------------------

            item = self.table.item(row, 0)

            item.setFlags(
                item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            # ------------------------------------------------
            # PRODUCT READ ONLY
            # ------------------------------------------------

            item = self.table.item(row, 1)

            item.setFlags(
                item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            # ------------------------------------------------
            # CENTER ALL NUMERIC ENTRIES: CARTON ... NET AMOUNT
            # ------------------------------------------------

            for column in range(2, 13):

                item = self.table.item(row, column)

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

            # ------------------------------------------------
            # TOTAL AMOUNT / NET AMOUNT -> READ ONLY (CALCULATED)
            # ------------------------------------------------

            for column in (11, 12):

                item = self.table.item(row, column)

                item.setFlags(
                    item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                )

            

            # ------------------------------------------------
            # CALCULATE
            # ------------------------------------------------

            self.calculate_row(row)

            # ------------------------------------------------
            # SELECT ROW
            # ------------------------------------------------

            self.table.selectRow(row)



        # ==========================================================
        # CALCULATE ROW
        # ==========================================================

    def calculate_row(self, row):

            self._calculating = True

            try:

                quantity = float(
                    self.table.item(row, 4).text() or 0
                )

                price = float(
                    self.table.item(row, 7).text() or 0
                )

                discount = float(
                    self.table.item(row, 9).text() or 0
                )

                tax = float(
                    self.table.item(row, 10).text() or 0
                )

                gross = quantity * price

                discount_amount = gross * discount / 100

                amount_after_discount = gross - discount_amount

                tax_amount = amount_after_discount * tax / 100

                total = amount_after_discount + tax_amount

                self.table.blockSignals(True)

                try:
                    self.table.item(row, 11).setText(f"{total:.2f}")
                    self.table.item(row, 12).setText(f"{total:.2f}")

                    self.table.item(row, 11).setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )
                    self.table.item(row, 12).setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                finally:
                    self.table.blockSignals(False)

            except (ValueError, AttributeError):

                self.table.blockSignals(True)

                if self.table.item(row, 11):
                    self.table.item(row, 11).setText("0.00")

                if self.table.item(row, 12):
                    self.table.item(row, 12).setText("0.00")

            finally:

                self.table.blockSignals(False)

                self._calculating = False

        # ==========================================================
        # WHEN TABLE CELL IS EDITED
        # ==========================================================

    def table_item_changed(self, item):

       # Prevent recursive calculation
       if getattr(self, "_calculating", False):

          return

       row = item.row()
       column = item.column()

       # These columns are editable
       editable_columns = [
        2,  # Carton
        3,  # Pcs
        4,  # Quantity
        5,  # Bonus
        6,
        7,  # Sale Price
        8,  # Carton Rate
        9,  # Per
        10,  # Discount
        11, # Tax
       ]

       if column in editable_columns:

         self.calculate_row(row)


    # Move next widget entry
    def move_next(self, current, next_widget):
        current.returnPressed.connect(
            next_widget.setFocus,
            
        )
        current.returnPressed.connect(
                    next_widget.selectAll,
                    
                )
        


    # ------------------------------------------------
    # CENTER TEXT + SELECT ALL ON FOCUS + AUTO-ZERO IF LEFT EMPTY
    # ------------------------------------------------
    
   ####################################### for customers Frames #############################################################
    def show_customer_list(self):

            # If already open, just focus it
            if hasattr(self, "customer_frame"):

                self.customer_frame.show()
                self.customer_search.setFocus()
                return

            # ==========================================
            # CUSTOMER FRAME
            # ==========================================

            self.customer_frame = q.QFrame(self)

            self.customer_frame.setStyleSheet("""
                QFrame {
                    background:black;
                    border: 1px solid #C8C8C8;
                    border-radius: 10px;
                }

                QLabel {
                    color:#222;
                    border: none;
                }

                QLineEdit {
                    background: white;
                    border: 1px solid #BBBBBB;
                    border-radius: 6px;
                    padding: 6px;
                    font-size: 14px;
                }

                QTableWidget {
                    background:#e0b7e8e3;
                    border: 1px solid #DDDDDD;
                    gridline-color: #E5E5E5;
                    font-size: 13px;
                    selection-background-color: #E0B7E8;
                    selection-color: #222;
                }

                QHeaderView::section {
                    background: #252B33;
                    color: white;
                    padding: 7px;
                    border: none;
                    font-weight: bold;
                }
            """)

            # ==========================================
            # SIZE AND POSITION
            # ==========================================

            self.customer_frame.setFixedSize(750, 450)

            # Center inside Sale Invoice window
            x = (self.width() - self.customer_frame.width()) // 2
            y = (self.height() - self.customer_frame.height()) // 2

            self.customer_frame.move(x, y)

            # ==========================================
            # MAIN LAYOUT
            # ==========================================

            layout = q.QVBoxLayout(self.customer_frame)

            layout.setContentsMargins(15, 15, 15, 15)
            layout.setSpacing(10)

            # ==========================================
            # TITLE
            # ==========================================

            title = q.QLabel("Select Customer")

            title.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color:white;
                }
            """)

            layout.addWidget(title)

            # ==========================================
            # SEARCH ENTRY
            # ==========================================

            self.customer_search = q.QLineEdit()

            self.customer_search.setPlaceholderText(
                "Search by code, name or address..."
            )

            layout.addWidget(self.customer_search)

            # ==========================================
            # CUSTOMER TABLE
            # ==========================================

            self.customer_table = CustomerTable(self)

            self.customer_table.setColumnCount(4)



            self.customer_table.setHorizontalHeaderLabels([
                "Code",
                "Name",
                "Address",
                "Balance"
            ])

            self.customer_table.setSelectionBehavior(
                q.QAbstractItemView.SelectionBehavior.SelectRows
            )

            self.customer_table.setSelectionMode(
                q.QAbstractItemView.SelectionMode.SingleSelection
            )

            self.customer_table.setEditTriggers(
                q.QAbstractItemView.EditTrigger.NoEditTriggers
            )

            self.customer_table.verticalHeader().setVisible(False)

            self.customer_table.setFocusPolicy(
                Qt.FocusPolicy.StrongFocus
            )

            self.customer_table.setCurrentCell(0, 0)
            self.customer_table.selectRow(0)


            
    
            layout.addWidget(self.customer_table)

            # ==========================================
            # LOAD CUSTOMERS
            # ==========================================

            self.load_customers()

            # ==========================================
            # SEARCH
            # ==========================================

            self.customer_search.textChanged.connect(
                self.search_customers
            )

            self.customer_search.keyPressEvent = self.customer_search_key_press

            # ==========================================
            # SELECT CUSTOMER
            # ==========================================

            self.customer_table.cellDoubleClicked.connect(
                self.select_customer
            )

            self.customer_frame.show()

            self.customer_search.setFocus()

    def search_customers(self, text):

            text = text.strip().upper()

            if text == "":

                self.display_customers(
                    self.all_customers
                )

                return

            filtered = []

            for customer in self.all_customers:

                code = str(customer[0]).upper()
                name = str(customer[1]).upper()
                address = str(customer[2]).upper()

                if (
                    text in code
                    or text in name
                    or text in address
                ):

                    filtered.append(customer)

            self.display_customers(filtered)


    def customer_search_key_press(self, event):

            key = event.key()

            # DOWN / UP -> hand focus to the table and let it navigate rows
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):

                self.customer_table.setFocus()

                q.QTableWidget.keyPressEvent(
                    self.customer_table,
                    event
                )

                return

            # ENTER -> select whatever row is currently highlighted
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

                row = self.customer_table.currentRow()

                if row >= 0:
                    self.select_customer(row, 0)

                return

            # ESC -> close the whole customer frame
            if key == Qt.Key.Key_Escape:

                self.customer_frame.hide()
                self.customer_code_entry.setFocus()

                return

            q.QLineEdit.keyPressEvent(
                self.customer_search,
                event
            )


    def load_customers(self):

        customers = [
            ["1001", "ABC Store", "Sahiwal", "25000"],
            ["1002", "Malik Store", "Lahore", "12500"],
            ["1003", "City Mart", "Sahiwal", "8200"],
            ["1004", "Al Madina Store", "Okara", "15000"],
            ["1005", "New Pakistan Store", "Faisalabad", "5200"],
            ["1006", "Usman Traders", "Sahiwal", "18500"],
        ]

        self.all_customers = customers

        self.display_customers(customers)


    def display_customers(self, customers):

            self.customer_table.setRowCount(0)

            for customer in customers:

                row = self.customer_table.rowCount()

                self.customer_table.insertRow(row)

                for column, value in enumerate(customer):

                    item = q.QTableWidgetItem(str(value))

                    self.customer_table.setItem(
                        row,
                        column,
                        item
                    )

            # Column widths

            self.customer_table.setColumnWidth(0, 100)
            self.customer_table.setColumnWidth(1, 220)
            self.customer_table.setColumnWidth(2, 260)
            self.customer_table.setColumnWidth(3, 130)


                    

    def select_customer(self, row, column):

            code = self.customer_table.item(row, 0).text()
            name = self.customer_table.item(row, 1).text()
            address = self.customer_table.item(row, 2).text()
            balance = self.customer_table.item(row, 3).text()

            # ==========================================
            # PUT DATA INTO SALE INVOICE
            # ==========================================

            self.customer_code_entry.setText(code)

            self.customer_name_entry.setText(name)

            self.customer_address_entry.setText(address)

            self.customer_balance_entry.setText(balance)

            # ==========================================
            # CLOSE CUSTOMER FRAME
            # ==========================================

            self.customer_frame.hide()

            # Move focus to next field
            self.product_search.setFocus()


    def customer_code_key_press(self, event):

            if event.key() == Qt.Key.Key_Space:

                self.show_customer_list()

                return

            q.QLineEdit.keyPressEvent(
                self.customer_code_entry,
                event
            )


   ####################################### for products Frames #############################################################

    def product_search_key_press(self, event):

            if event.key() == Qt.Key.Key_Space:

                self.show_product_list()

                return

            q.QLineEdit.keyPressEvent(
                self.product_search,
                event
            )


    def show_product_list(self):

            # If already open, just focus it
            if hasattr(self, "product_frame"):

                self.product_frame.show()
                self.product_list_search.setFocus()
                return

            # ==========================================
            # PRODUCT FRAME
            # ==========================================

            self.product_frame = q.QFrame(self)

            self.product_frame.setStyleSheet("""
                QFrame {
                    background:black;
                    border: 1px solid #C8C8C8;
                    border-radius: 10px;
                }

                QLabel {
                    color: #222;
                    border: none;
                }

                QLineEdit {
                    background:white;
                    border: 1px solid #BBBBBB;
                    border-radius: 6px;
                    padding: 6px;
                    font-size: 14px;
                }

                QTableWidget {
                    background:#e0b7e8e3;
                    border: 1px solid #DDDDDD;
                    gridline-color: #E5E5E5;
                    font-size: 13px;
                    selection-background-color: #E0B7E8;
                    selection-color: #222;
                }

                QHeaderView::section {
                    background: #252B33;
                    color: white;
                    padding: 7px;
                    border: none;
                    font-weight: bold;
                }
            """)

            # ==========================================
            # SIZE AND POSITION
            # ==========================================

            self.product_frame.setFixedSize(1000, 600)

            # Center inside Sale Invoice window
            x = (self.width() - self.product_frame.width()) // 2
            y = (self.height() - self.product_frame.height()) // 2

            self.product_frame.move(x, y)

            # ==========================================
            # MAIN LAYOUT
            # ==========================================

            layout = q.QVBoxLayout(self.product_frame)

            layout.setContentsMargins(15, 10, 15, 15)
            layout.setSpacing(10)

            # ==========================================
            # TITLE
            # ==========================================

            title = q.QLabel("Select Product")

            title.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color:white;
                }
            """)

            layout.addWidget(title)

            # ==========================================
            # SEARCH ENTRY
            # ==========================================

            self.product_list_search = q.QLineEdit()

            self.product_list_search.setPlaceholderText(
                "Search by code, name or company..."
            )

            layout.addWidget(self.product_list_search)

            # ==========================================
            # PRODUCT TABLE
            # ==========================================

            self.product_table = ProductTable(self)

            self.product_table.setColumnCount(7)

            self.product_table.setHorizontalHeaderLabels([
                "ID",
                "Name",
                "Company",
                "Sale Price",
                "Available Stock",
                "Carton",
                "Pcs"
            ])

            self.product_table.setSelectionBehavior(
                q.QAbstractItemView.SelectionBehavior.SelectRows
            )

            self.product_table.setSelectionMode(
                q.QAbstractItemView.SelectionMode.SingleSelection
            )

            self.product_table.setEditTriggers(
                q.QAbstractItemView.EditTrigger.NoEditTriggers
            )

            self.product_table.verticalHeader().setVisible(False)

            self.product_table.setFocusPolicy(
                Qt.FocusPolicy.StrongFocus
            )

            self.product_table.setCurrentCell(0, 0)
            self.product_table.selectRow(0)

            layout.addWidget(self.product_table)

            # ==========================================
            # LOAD PRODUCTS
            # ==========================================

            self.load_products()

            # ==========================================
            # SEARCH
            # ==========================================

            self.product_list_search.textChanged.connect(
                self.search_products
            )

            self.product_list_search.keyPressEvent = self.product_list_search_key_press

            # ==========================================
            # SELECT PRODUCT
            # ==========================================

            self.product_table.cellDoubleClicked.connect(
                self.select_product
            )

            self.product_frame.show()

            self.product_list_search.setFocus()


    def product_list_search_key_press(self, event):

            key = event.key()

            # DOWN / UP -> hand focus to the table and let it navigate rows
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):

                self.product_table.setFocus()

                q.QTableWidget.keyPressEvent(
                    self.product_table,
                    event
                )

                return

            # ENTER -> select whatever row is currently highlighted
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

                row = self.product_table.currentRow()

                if row >= 0:
                    self.select_product(row, 0)

                return

            # ESC -> close the whole product frame
            if key == Qt.Key.Key_Escape:

                self.product_frame.hide()
                self.product_search.setFocus()

                return

            q.QLineEdit.keyPressEvent(
                self.product_list_search,
                event
            )


    def load_products(self):

        products = [
            ["2001", "Coca Cola 1.5L", "Coca Cola Co.", "130", "480", "24", "0"],
            ["2002", "Pepsi 1.5L", "PepsiCo", "125", "360", "24", "0"],
            ["2003", "Sprite 500ml", "Coca Cola Co.", "60", "720", "24", "0"],
            ["2004", "Lays Chips 40g", "PepsiCo", "35", "1200", "48", "0"],
            ["2005", "Nestle Water 1.5L", "Nestle", "45", "600", "12", "0"],
            ["2006", "Fanta 500ml", "Coca Cola Co.", "60", "540", "24", "0"],
        ]

        self.all_products = products

        self.display_products(products)


    def search_products(self, text):

            text = text.strip().upper()

            if text == "":

                self.display_products(
                    self.all_products
                )

                return

            filtered = []

            for product in self.all_products:

                code = str(product[0]).upper()
                name = str(product[1]).upper()
                company = str(product[2]).upper()

                if (
                    text in code
                    or text in name
                    or text in company
                ):

                    filtered.append(product)

            self.display_products(filtered)


    def display_products(self, products):

            self.product_table.setRowCount(0)

            for product in products:

                row = self.product_table.rowCount()

                self.product_table.insertRow(row)

                for column, value in enumerate(product):

                    item = q.QTableWidgetItem(str(value))

                    self.product_table.setItem(
                        row,
                        column,
                        item
                    )

            # Column widths

            self.product_table.setColumnWidth(0, 70)
            self.product_table.setColumnWidth(1, 230)
            self.product_table.setColumnWidth(2, 200)
            self.product_table.setColumnWidth(3, 150)
            self.product_table.setColumnWidth(4, 120)
            self.product_table.setColumnWidth(5, 100)
            self.product_table.setColumnWidth(6, 100)


    def select_product(self, row, column):

            code = self.product_table.item(row, 0).text()
            name = self.product_table.item(row, 1).text()
           

            # ==========================================
            # PUT DATA INTO SALE INVOICE
            # ==========================================

            self.product_search.setText(code)

           

            # ==========================================
            # CLOSE PRODUCT FRAME
            # ==========================================

            self.product_frame.hide()

            # Move focus to next field
            self.carton_entry.setFocus()



    ####################################### For Invoice No Frame #########################################################
    def invoice_no_key_press(self, event):
    
                if event.key() == Qt.Key.Key_Space:
    
                    self.show_invoices_list()
    
                    return
    
                q.QLineEdit.keyPressEvent(
                    self.invoice_no,
                    event
                )
    
    
    def show_invoices_list(self):
    
                # If already open, just focus it
                if hasattr(self, "invoices_frame"):
    
                    self.invoices_frame.show()
                    self.invoices_list_search.setFocus()
                    return
    
                # ==========================================
                # invoice FRAME
                # ==========================================
    
                self.invoices_frame = q.QFrame(self)
    
                self.invoices_frame.setStyleSheet("""
                    QFrame {
                        background:black;
                        border: 1px solid #C8C8C8;
                        border-radius: 10px;
                    }
    
                    QLabel {
                        color: #222;
                        border: none;
                    }
    
                    QLineEdit {
                        background:white;
                        border: 1px solid #BBBBBB;
                        border-radius: 6px;
                        padding: 6px;
                        font-size: 14px;
                    }
    
                    QTableWidget {
                        background:#e0b7e8e3;
                        border: 1px solid #DDDDDD;
                        gridline-color: #E5E5E5;
                        font-size: 13px;
                        selection-background-color: #E0B7E8;
                        selection-color: #222;
                    }
    
                    QHeaderView::section {
                        background: #252B33;
                        color: white;
                        padding: 7px;
                        border: none;
                        font-weight: bold;
                    }
                """)
    
                # ==========================================
                # SIZE AND POSITION
                # ==========================================
    
                self.invoices_frame.setFixedSize(1000,600)
    
                # Center inside Sale Invoice window
                x = (self.width() - self.invoices_frame.width()) // 2
                y = (self.height() - self.invoices_frame.height()) // 2
    
                self.invoices_frame.move(x, y)
    
                # =======================================
                # table Frame
                # =======================================
                table_frame =q.QFrame(self.invoices_frame)
                table_frame.setGeometry(0,90,1000,510)
               

                # ============= table layout ================
                
                layout = q.QVBoxLayout(table_frame)
    
                layout.setContentsMargins(5,5, 15, 15)
                layout.setSpacing(10)

                # ========================= title frame
                title_frame = q.QFrame(self.invoices_frame)
                title_frame.setGeometry(0,0,1000,90)
                               
                
                
                title_layout = q.QGridLayout(title_frame)
                title_layout.setContentsMargins(5,5,5,15)
                title_layout.setSpacing(10)

        

    
                # ==========================================
                # TITLE
                # ==========================================
    
               

                #################### create title label frame #################################
                def create_title_label(text):
                        
                                label = QLabel(text)
                        
                                label.setStyleSheet("""
                                    font-size: 20px;
                                    font-weight:bold;
                                    color:white;
                                """)
                        
                                return label

                

                # ==========================================
                # from date To date entry
                # ==========================================
                self.from_date_entry = q.QDateEdit()
                self.from_date_entry.setDate(QDate.currentDate())
                self.from_date_entry.setCalendarPopup(True)


                # ==========================================
                # from date To date entry
                # ==========================================
                self.to_date_entry = q.QDateEdit()
                self.to_date_entry.setDate(QDate.currentDate())
                self.to_date_entry.setCalendarPopup(True)

                # ============== load button 
                self.preview_btn = q.QPushButton(
                            "Preview"
                )

                # ============== preview  button 
                self.load_btn = q.QPushButton(
                            "Load"
                )

                
                

                title_layout.addWidget(create_title_label("From Date:"),0,0)
                title_layout.addWidget(self.from_date_entry,0,1)
                title_layout.addWidget(create_title_label("To Date:"),1,0)
                title_layout.addWidget(self.to_date_entry,1,1)
                title_layout.addWidget(self.load_btn,0,5)
                title_layout.addWidget(self.preview_btn,1,5)

                title_frame.setStyleSheet("""
                        QDateEdit{
                            border: 2px solid #C98DD8;
                            
                             background: white;
                        }""")

               

                
                

    
                # ==========================================
                # SEARCH ENTRY
                # ==========================================
    
                self.invoices_list_search = q.QLineEdit()
    
                self.invoices_list_search.setPlaceholderText(
                    "Search by Invoices_no, Customer name ......"
                )

    
                layout.addWidget(self.invoices_list_search)
    
                # ==========================================
                # invoice TABLE
                # ==========================================
            
            
            
                self.invoices_table = Invoice_no_Table(self)
 
                self.invoices_table.setColumnCount(7)

                self.invoices_table.setHorizontalHeaderLabels([
                "Date",
                "Inv-No",
                "Cus-ID",
                "Name",
                "Address",
                "Saleman",
                "Invoice Amount",
              ])

                self.invoices_table.setSelectionBehavior(
                q.QAbstractItemView.SelectionBehavior.SelectRows
               )

                self.invoices_table.setSelectionMode(
                q.QAbstractItemView.SelectionMode.SingleSelection
               )

                self.invoices_table.setEditTriggers(
                q.QAbstractItemView.EditTrigger.NoEditTriggers
            )

                self.invoices_table.verticalHeader().setVisible(False)

                self.invoices_table.setFocusPolicy(
                Qt.FocusPolicy.StrongFocus
                )

                self.invoices_table.setCurrentCell(0, 0)
                self.invoices_table.selectRow(0)

                layout.addWidget(self.invoices_table)

            # ==========================================
            # LOAD invoices
            # ==========================================

                self.load_invoices()

            # ==========================================
            # SEARCH
            # ==========================================

                self.invoices_list_search.textChanged.connect(
                self.search_invoices
            )

                self.invoices_list_search.keyPressEvent = self.invoices_list_search_key_press

            # ==========================================
            # SELECT PRODUCT
            # ==========================================

                self.invoices_table.cellDoubleClicked.connect(
                self.select_invoices
            )

                self.invoices_frame.show()

                self.invoices_list_search.setFocus()


    def invoices_list_search_key_press(self, event):

            key = event.key()

            # DOWN / UP -> hand focus to the table and let it navigate rows
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):

                self.invoices_table.setFocus()

                q.QTableWidget.keyPressEvent(
                    self.invoices_table,
                    event
                )

                return

            # ENTER -> select whatever row is currently highlighted
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

                row = self.invoices_table.currentRow()

                if row >= 0:
                    self.select_invoices(row, 0)

                return

            # ESC -> close the whole product frame
            if key == Qt.Key.Key_Escape:

                self.invoices_frame.hide()
                self.invoices_list_search.setFocus()

                return

            q.QLineEdit.keyPressEvent(
                self.invoices_list_search,
                event
            )


    def load_invoices(self):

        invoices = [
            ["2001", "Coca Cola 1.5L", "Coca Cola Co.", "130", "480", "24", "0"],
            ["2002", "Pepsi 1.5L", "PepsiCo", "125", "360", "24", "0"],
            ["2003", "Sprite 500ml", "Coca Cola Co.", "60", "720", "24", "0"],
            ["2004", "Lays Chips 40g", "PepsiCo", "35", "1200", "48", "0"],
            ["2005", "Nestle Water 1.5L", "Nestle", "45", "600", "12", "0"],
            ["2006", "Fanta 500ml", "Coca Cola Co.", "60", "540", "24", "0"],
            ["2004", "Lays Chips 40g", "PepsiCo", "35", "1200", "48", "0"],
            ["2005", "Nestle Water 1.5L", "Nestle", "45", "600", "12", "0"],
            ["2006", "Fanta 500ml", "Coca Cola Co.", "60", "540", "24", "0"],
            ["2004", "Lays Chips 40g", "PepsiCo", "35", "1200", "48", "0"],
            ["2005", "Nestle Water 1.5L", "Nestle", "45", "600", "12", "0"],
            ["2006", "Fanta 500ml", "Coca Cola Co.", "60", "540", "24", "0"],
            ["2004", "Lays Chips 40g", "PepsiCo", "35", "1200", "48", "0"],
            ["2005", "Nestle Water 1.5L", "Nestle", "45", "600", "12", "0"],
            ["2006", "Fanta 500ml", "Coca Cola Co.", "60", "540", "24", "0"],
        ]

        self.all_invoices =invoices

        self.display_invoices(invoices)


    def search_invoices(self, text):

            text = text.strip().upper()

            if text == "":

                self.display_invoices(
                    self.all_invoices
                )

                return

            filtered = []

            for invoice in self.all_invoices:

                invoice_no = str(invoice[1]).upper()
                id = str(invoice[2]).upper()
                name = str(invoice[3]).upper()

                if (
                    text in invoice_no
                    or text in id
                    or text in name
                ):

                    filtered.append(invoice)

            self.display_invoices(filtered)


    def display_invoices(self, invoices):

            self.invoices_table.setRowCount(0)

            for invoice in invoices:

                row = self.invoices_table.rowCount()

                self.invoices_table.insertRow(row)

                for column, value in enumerate(invoice):

                    item = q.QTableWidgetItem(str(value))

                    self.invoices_table.setItem(
                        row,
                        column,
                        item
                    )

            # Column widths

            self.invoices_table.setColumnWidth(0, 100)
            self.invoices_table.setColumnWidth(1, 80)
            self.invoices_table.setColumnWidth(2, 80)
            self.invoices_table.setColumnWidth(3, 180)
            self.invoices_table.setColumnWidth(4, 220)
            self.invoices_table.setColumnWidth(5, 150)
            self.invoices_table.setColumnWidth(6, 150)


    def select_invoices(self, row, column):

            invoice_no = self.invoices_table.item(row, 1).text()
            name = self.invoices_table.item(row, 1).text()
           

            # ==========================================
            # PUT DATA INTO SALE INVOICE
            # ==========================================

            self.invoice_no.setText(invoice_no)

           

            # ==========================================
            # CLOSE PRODUCT FRAME
            # ==========================================

            self.invoices_frame.hide()

            # Move focus to next field
            self.invoice_no.setFocus()



    ############################################## For prd Entries Functions ###############################################
    from PyQt6.QtWidgets import QMessageBox


    def product_quantity_check(self):

      if self.carton_entry.text() == "0" or self.carton_entry.text() == "":

        if self.pcs_entry.text() == "0":

            QMessageBox.critical(
                self,
                "Correction",
                "Pcs should greater then 0"
            )

            self.pcs_entry.setFocus()
            self.pcs_entry.selectAll()

        elif self.pcs_entry.text() == "":

            QMessageBox.critical(
                self,
                "Enter",
                "Enter Valid Pcs"
            )

            self.pcs_entry.setFocus()
            self.pcs_entry.selectAll()

        else:

            if self.pcs_entry.text() == "":

                self.pcs_entry.setText("0")
                self.bonus_entry.setFocus()
                self.bonus_entry.selectAll()

            carton_pcs = self.carton_pcs_from_data_base()
            print("self.carton_entry.text()", self.carton_entry.text())

            quantity = (
                int(carton_pcs) * int(self.carton_entry.text())
            ) + int(self.pcs_entry.text())

            self.quantity_entry.clear()
            self.quantity_entry.setText(str(quantity))

            # ==================================================
            # CHECK STOCK
            # ==================================================

            total_stock = stk.Data_base_stock(self, self.product_search.text())

            if total_stock[0] == 0:

                QMessageBox.critical(
                    self,
                    "Empty",
                    "No Stock is Available"
                )

                #self.prd_detail.destroy()

                self.quantity_entry.clear()
                self.quantity_entry.setText("0")

                self.pcs_entry.clear()
                self.pcs_entry.setText("0")

                self.product_search.setFocus()

            else:

                # ==============================================
                # CHECK TOTAL STOCK AGAINST QUANTITY
                # ==============================================

                total_qty = total_stock[0]

                if int(total_qty) < int(
                    self.quantity_entry.text()
                ):

                    QMessageBox.critical(
                        self,
                        "stock Issue",
                        "Store Stock is Less then this quantity"
                    )

                    #self.prd_detail.destroy()

                    self.quantity_entry.clear()
                    self.quantity_entry.setText("0")

                    self.pcs_entry.clear()
                    self.pcs_entry.setText("0")

                    self.product_search.setFocus()

                else:

                    self.bonus_entry.setFocus()
                    self.bonus_entry.selectAll()

      else:

        if self.pcs_entry.text() == "":

            self.pcs_entry.setText("0")
            self.bonus_entry.setFocus()
            self.bonus_entry.clear()

        carton_pcs = self.carton_pcs_from_data_base()

        quantity = (
            int(carton_pcs) * int(self.carton_entry.text())
        ) + int(self.pcs_entry.text())

        self.quantity_entry.clear()
        self.quantity_entry.setText(str(quantity))

        # ==================================================
        # CHECK STOCK
        # ==================================================

        total_stock = stk.Data_base_stock(self, self.product_search.text())

        if total_stock == 0:

            QMessageBox.critical(
                self,
                "Empty",
                "No Stock is Available"
            )

            #self.prd_detail.destroy()

            self.quantity_entry.clear()
            self.quantity_entry.setText("0")

            self.pcs_entry.clear()
            self.pcs_entry.setText("0")

            self.product_search.setFocus()

        else:

            # ==================================================
            # CHECK TOTAL STOCK AGAINST QUANTITY
            # ==================================================

            total_qty = total_stock[0]

            if int(total_qty) < int(
                self.quantity_entry.text()
            ):

                QMessageBox.critical(
                    self,
                    "stock Issue",
                    "Store Stock is Less then this Quantity"
                )

                #self.prd_detail.destroy()

                self.quantity_entry.clear()
                self.quantity_entry.setText("0")

                self.pcs_entry.clear()
                self.pcs_entry.setText("0")

                self.carton_entry.clear()
                self.carton_entry.setText("0")

                self.product_search.setFocus()

            else:

                self.bonus_entry.setFocus()
                self.bonus_entry.selectAll()


    @gui_exception
    def check_ctn_pcs(self):
# try:
      if self.product_search.text() == "":
        QMessageBox.critical(self, "Select", "Select Products before Enter Carton")
        self.product_search.setFocus()
      else:
        if self.carton_entry.text() == "":
            self.carton_entry.setText("0")
            self.pcs_entry.setFocus()
            self.pcs_entry.selectAll()
        else:
            ############################# check stock if it less then the stock in inventory ########################################
            cursor, connection = p.database_connection(self)

            total_stock = stk.Data_base_stock(self, self.product_search.text())

            if total_stock[0] == 0:
                QMessageBox.critical(self, "Empty", "No Stock is Available")
                #self.prd_detail.destroy()
                self.carton_entry.clear()
                self.carton_entry.setText("0")
                self.product_search.setFocus()
            else:
                print("************* total stock ", total_stock[0])

                #################### for carton qty #############
                ################## for sale price #################
                cursor.execute("use dbms")
                cursor.execute("select prd_cart from prd_data where prd_id = %s", (self.product_search.text()))
                carton_pcs = cursor.fetchall()[0]

                #############################3 for divvide total stock into carton or pcs #####################
                total_qty = total_stock[0]
                prd_carton = carton_pcs[0]

                total_carton = int(total_qty / prd_carton)

                if int(total_carton) < int(self.carton_entry.text()):
                    QMessageBox.critical(self, "stock Issue", "Store Stock is Less then this Quantity")
                    #self.prd_detail.destroy()
                    self.carton_entry.clear()
                    self.carton_entry.setText("0")
                    self.product_search.setFocus()

                else:
                    self.pcs_entry.setFocus()
                    self.pcs_entry.selectAll()

    def carton_pcs_from_data_base(self):
         cursor, self.connection = p.database_connection(self)
        

         cursor.execute("use dbms")
         cursor.execute("select prd_cart from prd_data where prd_id = %s",(self.product_search.text()))
         prd_carton = cursor.fetchall()

         print(prd_carton[0][0])
         return prd_carton[0][0]



    # ============================= for prd bonus =================================
    def bonus_entry_(self):
     cursor, connection = p.database_connection(self)

     try:

        if self.bonus_entry.text() == "":

            self.bonus_entry.setText("0")
            self.sale_price_entry.setFocus()
            self.sale_price_entry.selectAll()


        # ==============================================
        # MANAGE PRODUCT PRICE ENTRY
        # ==============================================

        self.sale_price_entry.clear()

        self.prices = self.check_prd_Prices_from_data_base()

        prd_sale_price = self.prices[0]


        # ==============================================
        # GET PREVIOUS SALE PRICE
        # ==============================================
        cursor.execute("use dbms")
        cursor.execute(
            """
            SELECT prd_sale_price
            FROM invoice_data dat
            JOIN invoice_prd p
                ON p.invoice_no = dat.invoice_no
            WHERE saleman = %s
            AND cus_code = %s
            AND prd_id = %s
            """,
            (
                self.salesman.currentText(),
                self.customer_code_entry.text(),
                self.product_search.text()
            )
        )

        pre_rate = cursor.fetchall()


        # ==============================================
        # PREVIOUS RATE EXISTS
        # ==============================================

        if len(pre_rate) != 0:

            pre = int(
                pre_rate[len(pre_rate) - 1][0]
            )

            self.sale_price_entry.setText(str(pre))
            self.sale_price_entry.setFocus()


        # ==============================================
        # NO PREVIOUS RATE
        # ==============================================

        else:

            self.sale_price_entry.setText(
                str(prd_sale_price)
            )

            self.sale_price_entry.setFocus()


     except Exception as e:

        QMessageBox.critical(
            self,
            "bonus_entry",
            f"Bonus Entry Error :{e}"
        )


    def check_prd_Prices_from_data_base(self):

    

        # ==================================================
        # CHECK PRODUCT COST PRICE FOR DATA SAVE
        # ==================================================

        cursor, connection = p.database_connection(self)

        if not cursor or not self.connection:
            return None

        cursor.execute("USE dbms")

        cursor.execute(
            """
            SELECT prd_cost, prd_sale
            FROM prd_data
            WHERE prd_id = %s
            """,
            (self.product_search.text(),)
        )

        records = cursor.fetchall()

        print(records)

        self.prd_cost_price = float(records[0][0])
        self.prd_sale_price = float(records[0][1])

        return self.prd_sale_price, self.prd_cost_price


    @gui_exception
    def sale_price_entry_(self):
            cursor, connection = p.database_connection(self)

            # try:
            self.prices = self.check_prd_Prices_from_data_base()

            #######################################################
            # for previous rate insert in product sale price entry
            #######################################################

            cursor.execute("USE dbms")

            cursor.execute(
                """
                SELECT prd_sale_price
                FROM invoice_data dat
                JOIN invoice_prd p
                    ON p.invoice_no = dat.invoice_no
                WHERE saleman = %s
                AND cus_code = %s
                AND prd_id = %s
                """,
                (
                    self.salesman.currentText(),
                    self.customer_code_entry.text(),
                    self.product_search.text()
                )
            )

            pre_rate = cursor.fetchall()

            if len(pre_rate) == 0:

                print("no last price")

                prd_sale_price = self.prices[0]
                self.prd_cost_price = self.prices[1]

                if float(self.prd_cost_price) > float(
                    self.sale_price_entry.text()
                ):

                    QMessageBox.critical(
                        self,
                        "Less",
                        "product Sale Price is Less then the cost Price"
                    )

                    self.sale_price_entry.clear()
                    self.sale_price_entry.setText(str(prd_sale_price))
                    self.sale_price_entry.setFocus()

                else:

                    ############################
                    # manage bonus
                    ############################

                    if self.bonus_entry.text() == "0":

                        total_amount = int(
                            int(self.quantity_entry.text())
                            * float(self.sale_price_entry.text())
                        )

                        self.net_amount_entry.clear()
                        self.net_amount_entry.setText(str(total_amount))

                        self.total_amount_entry.clear()
                        self.total_amount_entry.setText(str(total_amount))

                        prd_sale_price = self.sale_price_entry.text()
                        prd_ctn_size = self.carton_pcs_from_data_base()

                        

                        carton_rate = float(prd_sale_price)*int(prd_ctn_size)
                        self.carton_rate_entry.setText(str(round(float(carton_rate),1)))
                        self.per_entry.setFocus()
                        self.per_entry.selectAll()
                    else:

                        total = int(
                            int(self.quantity_entry.text())
                            * float(self.sale_price_entry.text())
                        )

                        bonus = int(
                            int(self.bonus_entry.text())
                            * float(self.sale_price_entry.text())
                        )

                        total_bonus = total - bonus

                        self.net_amount_entry.clear()
                        self.net_amount_entry.setText(str(total))

                        self.total_amount_entry.clear()
                        self.total_amount_entry.setText(str(total_bonus))

                        prd_sale_price = self.sale_price_entry.text()
                        prd_ctn_size = self.carton_pcs_from_data_base()

                       

                        carton_rate = float(prd_sale_price)*int(prd_ctn_size)
                        self.carton_rate_entry.setText(str(round(float(carton_rate),1)))
                        self.per_entry.setFocus()
                        self.per_entry.selectAll()
            else:

                print("last price")

                pre = int(pre_rate[len(pre_rate) - 1][0])

                if float(self.sale_price_entry.text()) != float(pre):

                    ask = QMessageBox.question(
                        self,
                        "Confirm",
                        "Are you want to change previous rate",
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                    )

                    ############################
                    # manage bonus
                    ############################

                    if ask == QMessageBox.StandardButton.Yes:

                        prd_sale_price = self.prices[0]
                        self.prd_cost_price = self.prices[1]

                        if float(self.prd_cost_price) > float(
                            self.sale_price_entry.text()
                        ):

                            QMessageBox.critical(
                                self,
                                "Less",
                                "product Sale Price is Less then the cost Price"
                            )

                            self.sale_price_entry.clear()
                            self.sale_price_entry.setText(
                                str(prd_sale_price)
                            )
                            self.sale_price_entry.setFocus()

                        if self.bonus_entry.text() == "0":

                            total_amount = int(
                                int(self.quantity_entry.text())
                                * float(self.sale_price_entry.text())
                            )

                            self.net_amount_entry.clear()
                            self.net_amount_entry.setText(str(total_amount))

                            self.total_amount_entry.clear()
                            self.total_amount_entry.setText(str(total_amount))

                            prd_sale_price = self.sale_price_entry.text()
                            prd_ctn_size = self.carton_pcs_from_data_base()
    
                            
    
                            carton_rate = float(prd_sale_price)*int(prd_ctn_size)
                            self.carton_rate_entry.setText(str(round(float(carton_rate),1)))
                            self.per_entry.setFocus()
                            self.per_entry.selectAll()

                        else:

                            total = int(
                                int(self.quantity_entry.text())
                                * float(self.sale_price_entry.text())
                            )

                            bonus = int(
                                int(self.bonus_entry.text())
                                * float(self.sale_price_entry.text())
                            )

                            total_bonus = total - bonus

                            self.net_amount_entry.clear()
                            self.net_amount_entry.setText(str(total))

                            self.total_amount_entry.clear()
                            self.total_amount_entry.setText(str(total_bonus))

                            prd_sale_price = self.sale_price_entry.text()
                            prd_ctn_size = self.carton_pcs_from_data_base()
    
                            
    
                            carton_rate = int(prd_sale_price)*int(prd_ctn_size)
                            self.carton_rate_entry.setText(str(round(float(carton_rate),1)))
                            self.per_entry.setFocus()
                            self.per_entry.selectAll()
                else:

                    self.sale_price_entry.clear()
                    self.sale_price_entry.setText(str(pre))
                    self.sale_price_entry.setFocus()

                    prd_sale_price = self.prices[0]
                    self.prd_cost_price = self.prices[1]

                    if float(self.prd_cost_price) > float(
                        self.sale_price_entry.text()
                    ):

                        QMessageBox.critical(
                            self,
                            "Less",
                            "product Sale Price is Less then the cost Price"
                        )

                        self.sale_price_entry.clear()
                        self.sale_price_entry.setText(
                            str(prd_sale_price)
                        )
                        self.sale_price_entry.setFocus()

                    if self.bonus_entry.text() == "0":

                        total_amount = int(
                            int(self.quantity_entry.text())
                            * float(self.sale_price_entry.text())
                        )

                        self.net_amount_entry.clear()
                        self.net_amount_entry.setText(str(total_amount))

                        self.total_amount_entry.clear()
                        self.total_amount_entry.setText(str(total_amount))

                        
                        prd_sale_price = self.sale_price_entry.text()
                        prd_ctn_size = self.carton_pcs_from_data_base()


                        carton_rate = float(prd_sale_price)*int(prd_ctn_size)
                        self.carton_rate_entry.setText(str(round(float(carton_rate),1)))
                        self.per_entry.setFocus()
                        self.per_entry.selectAll()

                    else:

                        total = int(
                            int(self.quantity_entry.text())
                            * float(self.sale_price_entry.text())
                        )

                        bonus = int(
                            int(self.bonus_entry.text())
                            * float(self.sale_price_entry.text())
                        )

                        total_bonus = total - bonus

                        self.net_amount_entry.clear()
                        self.net_amount_entry.setText(str(total))

                        self.total_amount_entry.clear()
                        self.total_amount_entry.setText(str(total_bonus))

                    
                        prd_sale_price = self.sale_price_entry.text()
                        prd_ctn_size = self.carton_pcs_from_data_base()

                      

                        carton_rate = float(prd_sale_price)*int(prd_ctn_size)
                        self.carton_rate_entry.setText(str(round(float(carton_rate),1)))
                        self.per_entry.setFocus()
                        self.per_entry.selectAll()

            # except:
            #     QMessageBox.critical(
            #         self,
            #         "Enter Price",
            #         "Enter Product Price"
            #     )
            

    def carton_rate_entry_(self):
      if self.carton_rate_entry.text() == "":
         QMessageBox.critical(self,"Empty Issue", "Carton Rate should Not Empty ")
      else:
         sale_price,cost_price = self.check_prd_Prices_from_data_base()
         carton_size = self.carton_pcs_from_data_base()

         cost_carton_rate = int(carton_size)*float(cost_price)
         if cost_carton_rate >= float(self.carton_rate_entry.text()):
            QMessageBox.critical(self, "Cost Issue", "Carton Rate is less then the Cost Price")
            self.carton_rate_entry.setFocus()
            self.carton_rate_entry.selectAll()
         else:
              carton_rate = float(self.carton_rate_entry.text())
              unit_price = carton_rate/carton_size
              self.sale_price_entry.clear()
              self.sale_price_entry.setText(str(round(float(unit_price),1)))
              self.sale_price_entry.setFocus()
              self.sale_price_entry.selectAll()



    @gui_exception
    def percntage_entry(self):

        try:

            ######### for move next entry previous should 0 #########
            print(self.per_entry.text())
            if self.per_entry.text() == "":
                self.per_entry.setText("0")
                self.Discount_entry.setFocus()
                self.Discount_entry.selectAll()

            net_amount = int(self.total_amount_entry.text())

            percentage = int(
                net_amount * int(self.per_entry.text()) / 100
            )

            print("==per==",percentage)

            total_amount = net_amount - percentage

            self.total_amount_entry.clear()
            self.total_amount_entry.setText(str(total_amount))

            self.Discount_entry.clear()
            self.Discount_entry.setFocus()
            self.Discount_entry.selectAll()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Percentage_error",
                "Percentage Error"
            )


    @gui_exception
    def discount_entry(self):

     try:

        if self.Discount_entry.text() == "":
            self.Discount_entry.setText("0")
            self.tax_entry.setFocus()

        ############# for manage discount entry #################

        net_amount = int(self.total_amount_entry.text())

        total_amount = net_amount - int(
            self.Discount_entry.text()
        )

        self.total_amount_entry.clear()
        self.total_amount_entry.setText(str(total_amount))

        ########## for manage tax entry ###########

        self.tax_entry.clear()
        self.tax_entry.setFocus()

     except Exception as e:

        QMessageBox.critical(
            self,
            "Discount",
            "Discount Error"
        )


    @gui_exception
    def Tax_entry(self):

        try:

            if self.tax_entry.text() == "":
                self.tax_entry.setText("0")
                self.tax_entry.setFocus()

            ####### for manage tax entry ##############

            net_amount = int(
                int(self.total_amount_entry.text())
                * int(self.tax_entry.text())
                / 100
            )

            total_amount = net_amount + int(
                self.total_amount_entry.text()
            )

            self.total_amount_entry.clear()
            self.total_amount_entry.setText(str(total_amount))

        except Exception as e:

            QMessageBox.critical(
                self,
                "TAx",
                "TAX Error"
            )


################################################### insert products in table #################################################
    @gui_exception
    def move_prd_entry_insert_data_in_table(self):

      try:

        # ==========================================================
        # CHECK EMPTY PRODUCT ENTRIES
        # ==========================================================

        if (
            self.carton_entry.text() == ""
            or self.pcs_entry.text() == ""
            or self.quantity_entry.text() == ""
            or self.sale_price_entry.text() == ""
            or self.carton_rate_entry.text() == ""
            or self.bonus_entry.text() == ""
            or self.per_entry.text() == ""
            or self.Discount_entry.text() == ""
            or self.tax_entry.text() == ""
            or self.net_amount_entry.text() == ""
            or self.total_amount_entry.text() == ""
        ):

            QMessageBox.critical(
                self,
                "Empty",
                "Product Entry is Empty"
            )

            return


        # ==========================================================
        # PRODUCT ID FROM SEARCH
        # ==========================================================

        id_frm_entry = int(
            self.product_search.text()
        )


        # ==========================================================
        # CHECK PRODUCT ALREADY EXISTS IN QTABLE
        # ==========================================================

        present = False

        for row in range(self.table.rowCount()):

            item = self.table.item(row, 0)

            if item is not None:

                existing_prd_id = int(
                    item.text()
                )

                if existing_prd_id == id_frm_entry:

                    present = True
                    break


        # ==========================================================
        # PRODUCT ALREADY EXISTS
        # ==========================================================

        if present:

            QMessageBox.critical(
                self,
                "Exists",
                "Product Already Exist!"
            )

            # ------------------------------------------------------
            # RESET PRODUCT ENTRIES
            # ------------------------------------------------------

            self.carton_entry.clear()
            self.carton_entry.setText("0")

            self.pcs_entry.clear()
            self.pcs_entry.setText("0")

            self.quantity_entry.clear()
            self.quantity_entry.setText("0")

            self.sale_price_entry.clear()
            self.sale_price_entry.setText("0")

            self.carton_rate_entry.clear()
            self.carton_rate_entry.setText("0")

            self.bonus_entry.clear()
            self.bonus_entry.setText("0")

            self.per_entry.clear()
            self.per_entry.setText("0")

            self.Discount_entry.clear()
            self.Discount_entry.setText("0")

            self.tax_entry.clear()
            self.tax_entry.setText("0")

            self.net_amount_entry.clear()
            self.net_amount_entry.setText("0")

            self.total_amount_entry.clear()
            self.total_amount_entry.setText("0")

            # ------------------------------------------------------
            # MOVE TO PRODUCT SEARCH
            # ------------------------------------------------------

            self.product_search.clear()
            self.product_search.setFocus()

            if hasattr(self, "product_frame"):

                self.product_frame.hide()

            return


          # ==========================================================
          # GET PRODUCT INFORMATION FROM DATABASE
          # ==========================================================

        self.cursor.execute("USE dbms")

        self.cursor.execute(
            """
            SELECT prd_id, prd_name
            FROM prd_data
            WHERE prd_id = %s
            """,
            (self.product_search.text(),)
        )

        records = self.cursor.fetchall()


        if not records:

            QMessageBox.critical(
                self,
                "Product",
                "Product not found."
            )

            return


        prd_id = records[0][0]
        prd_name = records[0][1]


        # ==========================================================
        # PRODUCT DATA
        #
        # EXACT ORDER:
        #
        # 0  ID
        # 1  Name
        # 2  Carton
        # 3  Pcs
        # 4  Quantity
        # 5  Bonus
        # 6  Sale Price
        # 7  Carton Rate
        # 8  Per
        # 9  Discount
        # 10 Tax
        # 11 Net Amount
        # 12 Total Amount
        # ==========================================================

        product_data = [

            prd_id,

            prd_name,

            int(
                self.carton_entry.text()
            ),

            int(
                self.pcs_entry.text()
            ),

            int(
                self.quantity_entry.text()
            ),

            int(
                self.bonus_entry.text()
            ),

            float(
                self.sale_price_entry.text()
            ),

            float(
                self.carton_rate_entry.text()
            ),

            int(
                self.per_entry.text()
            ),

            int(
                self.Discount_entry.text()
            ),

            int(
                self.tax_entry.text()
            ),

            int(
                self.net_amount_entry.text()
            ),

            int(
                self.total_amount_entry.text()
            )
        ]


        # ==========================================================
        # INSERT PRODUCT INTO QTABLE
        # ==========================================================

        row = self.table.rowCount()

        self.table.insertRow(row)


        for column, value in enumerate(product_data):

            item = q.QTableWidgetItem(
                str(value)
            )

            self.table.setItem(
                row,
                column,
                item
            )


        # ==========================================================
        # SELECT INSERTED ROW
        # ==========================================================
        # ------------------------------------------------
        # ID READ ONLY
        # ------------------------------------------------

        item = self.table.item(row, 0)

        item.setFlags(
            item.flags()
            & ~Qt.ItemFlag.ItemIsEditable
        )

        # ------------------------------------------------
        # PRODUCT READ ONLY
        # ------------------------------------------------

        item = self.table.item(row, 1)

        item.setFlags(
            item.flags()
            & ~Qt.ItemFlag.ItemIsEditable
        )

        # ------------------------------------------------
        # CENTER ALL NUMERIC ENTRIES: CARTON ... NET AMOUNT
        # ------------------------------------------------

        for column in range(2, 13):

            item = self.table.item(row, column)

            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

        # ------------------------------------------------
        # TOTAL AMOUNT / NET AMOUNT -> READ ONLY (CALCULATED)
        # ------------------------------------------------

        for column in (11, 12):

            item = self.table.item(row, column)

            item.setFlags(
                item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

        

        # ------------------------------------------------
        # CALCULATE
        # ------------------------------------------------

        self.calculate_row(row)

        # ------------------------------------------------
        # SELECT ROW
        # ------------------------------------------------

        self.table.selectRow(row)


       


        # ==========================================================
        # MANAGE BILL TOTALS
        # ==========================================================

        #self.after_edit_prd_manage_bill_labels()


        # ==========================================================
        # RESET PRODUCT ENTRIES
        # ==========================================================

        self.carton_entry.clear()
        self.carton_entry.setText("0")

        self.pcs_entry.clear()
        self.pcs_entry.setText("0")

        self.quantity_entry.clear()
        self.quantity_entry.setText("0")

        self.sale_price_entry.clear()
        self.sale_price_entry.setText("0")

        self.carton_rate_entry.clear()
        self.carton_rate_entry.setText("0")

        self.bonus_entry.clear()
        self.bonus_entry.setText("0")

        self.per_entry.clear()
        self.per_entry.setText("0")

        self.Discount_entry.clear()
        self.Discount_entry.setText("0")

        self.tax_entry.clear()
        self.tax_entry.setText("0")

        self.net_amount_entry.clear()
        self.net_amount_entry.setText("0")

        self.total_amount_entry.clear()
        self.total_amount_entry.setText("0")


        # ==========================================================
        # MOVE BACK TO PRODUCT SEARCH
        # ==========================================================

        self.product_search.clear()
        self.product_search.setFocus()


        # ==========================================================
        # CLOSE PRODUCT FRAME
        # ==========================================================

        if (
            hasattr(self, "product_frame")
            and self.product_frame
            and not self.product_frame.isHidden()
        ):

            self.product_frame.hide()


      except Exception as e:

        QMessageBox.critical(
            self,
            "Insert_table",
            f"Insert_table Error: {e}"
        )


            

            


























        
# ==============================================================
# TEST
# ==============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = SaleInvoice()

    window.showMaximized()

    sys.exit(app.exec())