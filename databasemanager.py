# databasemanager.py
import mysql.connector
from mysql.connector import Error
import os
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple


class DatabaseManager:

    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {
            "username": os.environ.get("DB_USER", "rehman"),
            "password": os.environ.get("DB_PASSWORD", "rehman123"),
            "host": os.environ.get("DB_HOST", "localhost"),
            "database": os.environ.get("DB_NAME", "DMS_DB"),
            "autocommit": True,
            "connect_timeout": 5
        }

    def _get_connection(self):
        """Create and return a new database connection."""
        try:
            return mysql.connector.connect(**self._config)
        except Error as e:
            raise ConnectionError(f"Database connection failed: {str(e)}") from e

    def _close_connection(self, conn, cursor):
        """Safely close cursor and connection."""
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn and conn.is_connected():
            try:
                conn.close()
            except:
                pass

    def _execute_query(self, query: str, params: Optional[Tuple] = None, 
                       fetch_one: bool = False, fetch_all: bool = False) -> Any:
        """Execute SELECT query and return results."""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return cursor.rowcount
            
        except Error as e:
            raise RuntimeError(f"Database error: {str(e)}") from e
        finally:
            self._close_connection(conn, cursor)

    def _execute_write(self, query: str, params: Tuple) -> Dict[str, Any]:
        """Execute INSERT/UPDATE/DELETE query."""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            return {
                "success": True,
                "rowcount": cursor.rowcount,
                "lastrowid": cursor.lastrowid
            }
            
        except Error as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            
            error_msg = str(e)
            if "Duplicate entry" in error_msg:
                return {"success": False, "error": "DUPLICATE_ENTRY", "message": error_msg}
            if "foreign key constraint" in error_msg.lower():
                return {"success": False, "error": "FOREIGN_KEY_VIOLATION", "message": error_msg}
            return {"success": False, "error": "DATABASE_ERROR", "message": error_msg}
            
        finally:
            self._close_connection(conn, cursor)

    # =========================================================
    # PRODUCT METHODS
    # =========================================================

    def get_products(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get products from query."""
        try:
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception:
            return None

    def get_product_by_id(self, p_id: int) -> Optional[Dict[str, Any]]:
        """Get single product by ID."""
        try:
            query = """
                SELECT prd_id, prd_code, prd_name, prd_carton_size,
                       prd_cost_price, prd_sale_price, prd_reorder, 
                       prd_barcode, prd_is_active, prd_company_id, prd_cat_id
                FROM products WHERE prd_id = %s
            """
            return self._execute_query(query, (p_id,), fetch_one=True)
        except Exception:
            return None

    def get_product_other_by_id(self, p_id: int) -> Optional[Dict[str, Any]]:
        """Get product with category and company info."""
        try:
            query = """
                SELECT p.prd_name, 
                       c.cat_description, p.prd_cat_id,
                       comp.company_description, p.prd_company_id
                FROM products p
                LEFT JOIN categories c ON p.prd_cat_id = c.cat_code
                LEFT JOIN company_data comp ON p.prd_company_id = comp.company_code
                WHERE p.prd_id = %s
            """
            return self._execute_query(query, (p_id,), fetch_one=True)
        except Exception:
            return None

    def save_update_insert_product(self, product_id: Optional[int], product_code: str,
                                    product_name: str, carton_size: Optional[int],
                                    unit_cost_price: Optional[Decimal], unit_sale_price: Optional[Decimal],
                                    re_order: Optional[int], barcode: Optional[str],
                                    is_active: bool, category_id: int, company_id: int) -> Dict[str, Any]:
        """Insert or update product."""
        try:
            if product_id is not None:
                query = """
                    UPDATE products SET 
                        prd_name=%s, 
                        prd_carton_size=%s, 
                        prd_cost_price=%s,
                        prd_sale_price=%s, 
                        prd_reorder=%s, 
                        prd_barcode=%s, 
                        prd_is_active=%s,
                        prd_cat_id=%s, 
                        prd_company_id=%s 
                    WHERE prd_id=%s
                """
                values = (product_name, carton_size, unit_cost_price, unit_sale_price,
                         re_order, barcode, is_active, category_id, company_id, product_id)
            else:
                query = """
                    INSERT INTO products (
                        prd_code, prd_name, prd_carton_size,
                        prd_cost_price, prd_sale_price, prd_reorder, 
                        prd_barcode, prd_is_active, prd_company_id, prd_cat_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (product_code, product_name, carton_size, unit_cost_price,
                         unit_sale_price, re_order, barcode, is_active, company_id, category_id)

            result = self._execute_write(query, values)
            if not result["success"]:
                return result

            return {
                "success": True,
                "updated": product_id is not None,
                "rowcount": result["rowcount"],
                "lastrowid": result["lastrowid"]
            }
        except Exception as e:
            return {"success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def delete_products(self, code: int) -> bool:
        """Delete product by ID."""
        try:
            result = self._execute_write("DELETE FROM products WHERE prd_id = %s", (code,))
            return result["success"]
        except Exception as e:
            print(f"Error deleting product: {e}")
            return False

    # =========================================================
    # CATEGORY METHODS
    # =========================================================

    def get_category_by_id(self, cat_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID."""
        try:
            query = "SELECT cat_code, cat_description, is_active FROM categories WHERE cat_code = %s"
            return self._execute_query(query, (cat_id,), fetch_one=True)
        except Exception:
            return None

    def get_all_categories(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """Get all categories."""
        try:
            if only_active:
                query = "SELECT cat_code, cat_description FROM categories WHERE is_active = TRUE ORDER BY cat_description"
            else:
                query = "SELECT cat_code, cat_description, is_active FROM categories ORDER BY cat_description"
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception:
            return []

    def save_category(self, category_code: Optional[int], category_description: str, 
                      is_active: bool = True) -> Dict[str, Any]:
        """Insert or update category."""
        try:
            if category_code is not None:
                query = "UPDATE categories SET cat_description = %s, is_active = %s WHERE cat_code = %s"
                values = (category_description, is_active, category_code)
            else:
                query = "INSERT INTO categories (cat_description, is_active) VALUES (%s, %s)"
                values = (category_description, is_active)

            result = self._execute_write(query, values)
            if not result["success"]:
                return result

            return {
                "success": True,
                "updated": category_code is not None,
                "rowcount": result["rowcount"],
                "lastrowid": result["lastrowid"]
            }
        except Exception as e:
            return {"success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def delete_category(self, category_code: int) -> bool:
        """Delete category by ID."""
        try:
            # Check if category is being used by any product
            check_query = "SELECT COUNT(*) as count FROM products WHERE prd_cat_id = %s"
            result = self._execute_query(check_query, (category_code,), fetch_one=True)
            
            if result and result.get('count', 0) > 0:
                return False  # Category is in use
            
            result = self._execute_write("DELETE FROM categories WHERE cat_code = %s", (category_code,))
            return result["success"]
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False

    # =========================================================
    # COMPANY METHODS
    # =========================================================

    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get company by ID."""
        try:
            query = """
                SELECT company_code, company_description, address, city, short_name, is_active 
                FROM company_data WHERE company_code = %s
            """
            return self._execute_query(query, (company_id,), fetch_one=True)
        except Exception:
            return None

    def get_all_companies(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """Get all companies."""
        try:
            if only_active:
                query = "SELECT company_code, company_description FROM company_data WHERE is_active = TRUE ORDER BY company_description"
            else:
                query = "SELECT company_code, company_description, is_active FROM company_data ORDER BY company_description"
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception:
            return []

    def save_company_data(self, company_code: Optional[int], company_description: str,
                          address: Optional[str] = None, city: Optional[str] = None,
                          short_name: Optional[str] = None, is_active: bool = True) -> Dict[str, Any]:
        """Insert or update company."""
        try:
            if company_code is not None:
                query = """
                    UPDATE company_data SET 
                        company_description=%s, 
                        address=%s, 
                        city=%s,
                        short_name=%s, 
                        is_active=%s 
                    WHERE company_code=%s
                """
                values = (company_description, address, city, short_name, is_active, company_code)
            else:
                query = """
                    INSERT INTO company_data (
                        company_description, address, city, short_name, is_active
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                values = (company_description, address, city, short_name, is_active)

            result = self._execute_write(query, values)
            if not result["success"]:
                return result

            return {
                "success": True,
                "updated": company_code is not None,
                "rowcount": result["rowcount"],
                "lastrowid": result["lastrowid"]
            }
        except Exception as e:
            return {"success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def delete_company(self, company_code: int) -> bool:
        """Delete company by ID."""
        try:
            # Check if company is being used by any product
            check_query = "SELECT COUNT(*) as count FROM products WHERE prd_company_id = %s"
            result = self._execute_query(check_query, (company_code,), fetch_one=True)
            
            if result and result.get('count', 0) > 0:
                return False  # Company is in use
            
            result = self._execute_write("DELETE FROM company_data WHERE company_code = %s", (company_code,))
            return result["success"]
        except Exception as e:
            print(f"Error deleting company: {e}")
            return False

    # =========================================================
    # CUSTOMER METHODS
    # =========================================================

    def get_customer_by_id(self, customer_code: int) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        try:
            query = """
                SELECT cus_code, cus_name, cus_email, cus_address, cus_city, 
                       cus_country, cus_type, cus_cnic, cus_area, cus_sub_area,
                       cus_credit_limit, cus_date, phone, cus_whatsapp
                FROM customers WHERE cus_code = %s
            """
            return self._execute_query(query, (customer_code,), fetch_one=True)
        except Exception:
            return None

    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Get all customers."""
        try:
            query = """
                SELECT cus_code, cus_name, cus_email, cus_address, cus_city, 
                       cus_country, cus_type, cus_cnic, cus_area, cus_sub_area,
                       cus_credit_limit, cus_date, phone, cus_whatsapp
                FROM customers ORDER BY cus_name
            """
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception:
            return []

    def insert_update_customers(self, customer_code: Optional[int], customer_name: str,
                                 customer_email: str, customer_address: str, customer_city: str,
                                 customer_country: str, customer_type: str, customer_cnic: str,
                                 customer_area: str, customer_subarea: str, credit_limit: Decimal,
                                 date: Any, is_update: bool, phone: str, whatsapp: Optional[str] = None) -> Dict[str, Any]:
        """Insert or update customer."""
        try:
            if customer_code is not None and is_update:
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
                         customer_subarea, credit_limit, date, phone, whatsapp, customer_code)
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

            result = self._execute_write(query, values)
            if not result["success"]:
                return {"Success": False, "message": result.get("message", "Operation failed"),
                        "error": result.get("error")}

            return {
                "Success": True,
                "updated": customer_code is not None and is_update,
                "rowcount": result["rowcount"],
                "customer_code": result["lastrowid"] if customer_code is None else customer_code
            }
        except Exception as e:
            return {"Success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def delete_customer(self, customer_code: int) -> bool:
        """Delete customer by ID."""
        try:
            result = self._execute_write("DELETE FROM customers WHERE cus_code = %s", (customer_code,))
            return result["success"]
        except Exception as e:
            print(f"Error deleting customer: {e}")
            return False

    # =========================================================
    # VENDOR METHODS
    # =========================================================

    def get_vendor_by_id(self, vendor_code: int) -> Optional[Dict[str, Any]]:
        """Get vendor by ID."""
        try:
            query = """
                SELECT vnd_code, vnd_name, vnd_email, vnd_address, vnd_city, 
                       vnd_country, vnd_phone, vnd_whatsapp, vnd_type, vnd_cnic,
                       vnd_date, vnd_company, vnd_credit_limit
                FROM vendors WHERE vnd_code = %s
            """
            return self._execute_query(query, (vendor_code,), fetch_one=True)
        except Exception:
            return None

    def get_all_vendors(self) -> List[Dict[str, Any]]:
        """Get all vendors."""
        try:
            query = """
                SELECT vnd_code, vnd_name, vnd_email, vnd_address, vnd_city, 
                       vnd_country, vnd_phone, vnd_whatsapp, vnd_type, vnd_cnic,
                       vnd_date, vnd_company, vnd_credit_limit
                FROM vendors ORDER BY vnd_name
            """
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception as e:
            print(f"Error in get_all_vendors: {e}")
            return []

    def insert_update_vendors(self, vendor_code: Optional[int], vendor_name: str,
                               vendor_email: str, vendor_address: str, vendor_city: str,
                               vendor_country: str, phone: str, whatsapp: Optional[str],
                               vendor_type: str, vendor_cnic: str, company: str, 
                               credit_limit: Decimal, date: Any, is_update: bool) -> Dict[str, Any]:
        """Insert or update vendor."""
        try:
            if vendor_code is not None and is_update:
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
                        vnd_company=%s, 
                        vnd_credit_limit=%s,
                        vnd_date=%s
                    WHERE vnd_code=%s
                """
                values = (vendor_name, vendor_email, vendor_address, vendor_city,
                         vendor_country, phone, whatsapp, vendor_type, vendor_cnic,
                         company, credit_limit, date, vendor_code)
            else:
                query = """
                    INSERT INTO vendors (
                        vnd_name, vnd_email, vnd_address, vnd_city,
                        vnd_country, vnd_phone, vnd_whatsapp, vnd_type, 
                        vnd_cnic, vnd_company, vnd_credit_limit, vnd_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (vendor_name, vendor_email, vendor_address, vendor_city,
                         vendor_country, phone, whatsapp, vendor_type, vendor_cnic,
                         company, credit_limit, date)

            result = self._execute_write(query, values)
            if not result["success"]:
                return {"Success": False, "message": result.get("message", "Operation failed"),
                        "error": result.get("error")}

            return {
                "Success": True,
                "updated": vendor_code is not None and is_update,
                "rowcount": result["rowcount"],
                "vendor_code": result["lastrowid"] if vendor_code is None else vendor_code
            }
        except Exception as e:
            return {"Success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def delete_vendor(self, vendor_code: int) -> bool:
        """Delete vendor by ID."""
        try:
            result = self._execute_write("DELETE FROM vendors WHERE vnd_code = %s", (vendor_code,))
            return result["success"]
        except Exception as e:
            print(f"Error deleting vendor: {e}")
            return False

    # =========================================================
    # SALESMAN METHODS
    # =========================================================

    def get_salesman_by_id(self, salesman_code: int) -> Optional[Dict[str, Any]]:
        """Get salesman by ID."""
        try:
            query = """
                SELECT slm_code, slm_name, slm_email, slm_address, slm_city, 
                       slm_country, slm_phone, slm_whatsapp, slm_type, slm_cnic,
                       slm_date, slm_company, slm_credit_limit
                FROM salesmen WHERE slm_code = %s
            """
            return self._execute_query(query, (salesman_code,), fetch_one=True)
        except Exception:
            return None

    def get_all_salesmen(self) -> List[Dict[str, Any]]:
        """Get all salesmen."""
        try:
            query = """
                SELECT slm_code, slm_name, slm_email, slm_address, slm_city, 
                       slm_country, slm_phone, slm_whatsapp, slm_type, slm_cnic,
                       slm_date, slm_company, slm_credit_limit
                FROM salesmen ORDER BY slm_name
            """
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception as e:
            print(f"Error in get_all_salesmen: {e}")
            return []

    def insert_update_salesmen(self, salesman_code: Optional[int], salesman_name: str,
                                salesman_email: str, salesman_address: str, salesman_city: str,
                                salesman_country: str, phone: str, whatsapp: Optional[str],
                                salesman_type: str, salesman_cnic: str, company: str, 
                                credit_limit: Decimal, date: Any, is_update: bool) -> Dict[str, Any]:
        """Insert or update salesman."""
        try:
            if salesman_code is not None and is_update:
                query = """
                    UPDATE salesmen SET 
                        slm_name=%s, 
                        slm_email=%s, 
                        slm_address=%s,
                        slm_city=%s, 
                        slm_country=%s, 
                        slm_phone=%s,
                        slm_whatsapp=%s,
                        slm_type=%s,
                        slm_cnic=%s, 
                        slm_company=%s, 
                        slm_credit_limit=%s,
                        slm_date=%s
                    WHERE slm_code=%s
                """
                values = (salesman_name, salesman_email, salesman_address, salesman_city,
                         salesman_country, phone, whatsapp, salesman_type, salesman_cnic,
                         company, credit_limit, date, salesman_code)
            else:
                query = """
                    INSERT INTO salesmen (
                        slm_name, slm_email, slm_address, slm_city,
                        slm_country, slm_phone, slm_whatsapp, slm_type, 
                        slm_cnic, slm_company, slm_credit_limit, slm_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (salesman_name, salesman_email, salesman_address, salesman_city,
                         salesman_country, phone, whatsapp, salesman_type, salesman_cnic,
                         company, credit_limit, date)

            result = self._execute_write(query, values)
            if not result["success"]:
                return {"Success": False, "message": result.get("message", "Operation failed"),
                        "error": result.get("error")}

            return {
                "Success": True,
                "updated": salesman_code is not None and is_update,
                "rowcount": result["rowcount"],
                "salesman_code": result["lastrowid"] if salesman_code is None else salesman_code
            }
        except Exception as e:
            return {"Success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def delete_salesman(self, salesman_code: int) -> bool:
        """Delete salesman by ID."""
        try:
            result = self._execute_write("DELETE FROM salesmen WHERE slm_code = %s", (salesman_code,))
            return result["success"]
        except Exception as e:
            print(f"Error deleting salesman: {e}")
            return False

    # =========================================================
    # AREA & SUB-AREA METHODS
    # =========================================================

    def get_all_areas(self) -> List[Dict[str, Any]]:
        """Get all areas."""
        try:
            query = "SELECT id, area_name FROM areas ORDER BY area_name"
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except Exception:
            return []

    def get_sub_areas_by_area(self, area_name: str) -> List[Dict[str, Any]]:
        """Get sub-areas by area name."""
        try:
            query = "SELECT id, sub_area_name FROM sub_areas WHERE area_name = %s ORDER BY sub_area_name"
            result = self._execute_query(query, (area_name,), fetch_all=True)
            return result if result is not None else []
        except Exception:
            return []

    def save_area(self, area_name: str) -> Dict[str, Any]:
        """Insert new area."""
        try:
            query = "INSERT INTO areas (area_name) VALUES (%s)"
            result = self._execute_write(query, (area_name,))
            if not result["success"]:
                return result
            return {
                "success": True,
                "rowcount": result["rowcount"],
                "lastrowid": result["lastrowid"]
            }
        except Exception as e:
            return {"success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    def save_sub_area(self, area_name: str, sub_area_name: str) -> Dict[str, Any]:
        """Insert new sub-area."""
        try:
            # First get the area_id
            area = self.get_any_thing("SELECT id FROM areas WHERE area_name = %s", area_name)
            if not area:
                return {"success": False, "error": "AREA_NOT_FOUND", "message": "Area not found"}
            
            area_id = area['id']
            query = "INSERT INTO sub_areas (area_id, area_name, sub_area_name) VALUES (%s, %s, %s)"
            result = self._execute_write(query, (area_id, area_name, sub_area_name))
            if not result["success"]:
                return result
            return {
                "success": True,
                "rowcount": result["rowcount"],
                "lastrowid": result["lastrowid"]
            }
        except Exception as e:
            return {"success": False, "error": "UNEXPECTED_ERROR", "message": str(e)}

    # =========================================================
    # GENERAL QUERY METHODS
    # =========================================================

    def get_any_table(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute query and return all rows."""
        try:
            result = self._execute_query(query, params, fetch_all=True)
            return result if result is not None else []
        except Exception as e:
            print(f"Error in get_any_table: {e}")
            return []

    def get_any_thing(self, query: str, code: Any) -> Optional[Dict[str, Any]]:
        """Execute query and return single row."""
        try:
            return self._execute_query(query, (code,), fetch_one=True)
        except Exception as e:
            print(f"Error in get_any_thing: {e}")
            return None

    def get_any_subarea(self, query: str, code: Any) -> List[Dict[str, Any]]:
        """Execute query and return sub-areas."""
        try:
            result = self._execute_query(query, (code,), fetch_all=True)
            return result if result is not None else []
        except Exception as e:
            print(f"Error in get_any_subarea: {e}")
            return []

    # =========================================================
    # ADMIN METHODS
    # =========================================================

    def admin_data(self) -> List[Dict[str, Any]]:
        """Get all admin data."""
        try:
            result = self._execute_query("SELECT * FROM admin_authority", fetch_all=True)
            return result if result is not None else []
        except Exception:
            return []