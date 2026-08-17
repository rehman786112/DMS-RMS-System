import mysql.connector
from mysql.connector import Error
import os
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union, Tuple


class DatabaseManager:
    
    def __init__(self, config: Optional[Dict] = None):
        self._config = config or {
            'username': os.environ.get('DB_USER', 'rehman'),
            'password': os.environ.get('DB_PASSWORD', 'rehman123'),
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'DMS_DB'),
            'autocommit': False,
            'connect_timeout': 5,
            'pool_name': 'dms_pool',
            'pool_size': 3
        }
        self._connection = None
    
    def get_connection(self):
        try:
            if self._connection and self._connection.is_connected():
                try:
                    self._connection.ping(reconnect=True)
                    return self._connection
                except Error:
                    self._connection = None
            
            self._connection = mysql.connector.connect(**self._config)
            return self._connection
        except Error as e:
            raise ConnectionError(f"Database connection failed: {str(e)}") from e
    
    def _execute_query(self, query: str, params: Optional[Tuple] = None, fetch_one: bool = False, fetch_all: bool = False) -> Any:
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount
            
        except Error as e:
            if conn:
                try:
                    conn.rollback()
                except Error:
                    pass
            raise RuntimeError(f"Database error: {str(e)}") from e
        finally:
            if cursor:
                try:
                    cursor.close()
                except Error:
                    pass
    
    def _execute_write(self, query: str, params: Tuple) -> Dict[str, Any]:
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return {
                'success': True,
                'rowcount': cursor.rowcount,
                'lastrowid': cursor.lastrowid
            }
        except Error as e:
            if conn:
                try:
                    conn.rollback()
                except Error:
                    pass
            error_msg = str(e)
            if 'Duplicate entry' in error_msg:
                return {'success': False, 'error': 'DUPLICATE_ENTRY', 'message': error_msg}
            elif 'foreign key constraint' in error_msg.lower():
                return {'success': False, 'error': 'FOREIGN_KEY_VIOLATION', 'message': error_msg}
            else:
                return {'success': False, 'error': 'DATABASE_ERROR', 'message': error_msg}
        finally:
            if cursor:
                try:
                    cursor.close()
                except Error:
                    pass

    def admin_data(self) -> List[Dict[str, Any]]:
        try:
            query = "SELECT * FROM admin_authority"
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except (ConnectionError, RuntimeError):
            return []

    def get_products(self, query: str) -> Optional[List[Dict[str, Any]]]:
        try:
            result = self._execute_query(query, fetch_all=True)
            return result if result is not None else []
        except (ConnectionError, RuntimeError):
            return None

    def get_product_by_id(self, p_id: int) -> Optional[Dict[str, Any]]:
        try:
            query = """
                SELECT
                    product_id,
                    product_code,
                    product_name,
                    carton_size,
                    unit_cost_price,
                    unit_sale_price,
                    re_order,
                    barcode,
                    is_active
                FROM products
                WHERE product_id = %s
            """
            return self._execute_query(query, (p_id,), fetch_one=True)
        except (ConnectionError, RuntimeError):
            return None

    def get_product_other_by_id(self, p_id: int) -> Optional[Dict[str, Any]]:
        try:
            query = """
                SELECT
                    p.product_name,
                    g.group_description,
                    p.group_id,
                    c.company_description,
                    p.company_id
                FROM products p
                INNER JOIN Group_data g
                    ON p.group_id = g.group_code
                INNER JOIN company_data c
                    ON p.company_id = c.company_code
                WHERE p.product_id = %s
            """
            return self._execute_query(query, (p_id,), fetch_one=True)
        except (ConnectionError, RuntimeError):
            return None

    def save_update_insert_product(
        self,
        product_id: Optional[int],
        product_code: str,
        product_name: str,
        carton_size: Optional[int],
        unit_cost_price: Optional[Decimal],
        unit_sale_price: Optional[Decimal],
        re_order: Optional[int],
        barcode: Optional[str],
        is_active: bool,
        group_id: int,
        company_id: int
    ) -> Dict[str, Any]:
        try:
            if product_id is not None:
                query = """
                    UPDATE products
                    SET
                        product_name = %s,
                        carton_size = %s,
                        unit_cost_price = %s,
                        unit_sale_price = %s,
                        re_order = %s,
                        barcode = %s,
                        is_active = %s,
                        group_id = %s,
                        company_id = %s
                    WHERE product_id = %s
                """
                values = (
                    product_name,
                    carton_size,
                    unit_cost_price,
                    unit_sale_price,
                    re_order,
                    barcode,
                    is_active,
                    group_id,
                    company_id,
                    product_id
                )
            else:
                query = """
                    INSERT INTO products (
                        product_code,
                        product_name,
                        carton_size,
                        unit_cost_price,
                        unit_sale_price,
                        re_order,
                        barcode,
                        is_active,
                        company_id,
                        group_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    product_code,
                    product_name,
                    carton_size,
                    unit_cost_price,
                    unit_sale_price,
                    re_order,
                    barcode,
                    is_active,
                    company_id,
                    group_id
                )
            
            result = self._execute_write(query, values)
            if result['success']:
                return {'success': True, 'updated': product_id is not None}
            else:
                return result
        except Exception as e:
            return {'success': False, 'error': 'UNEXPECTED_ERROR', 'message': str(e)}

    def save_company_data(
        self,
        company_code: Optional[int],
        company_description: str,
        address: Optional[str],
        city: Optional[str],
        short_name: Optional[str],
        is_active: bool
    ) -> Dict[str, Any]:
        try:
            if company_code is None:
                query = """
                    INSERT INTO company_data (
                        company_description,
                        address,
                        city,
                        short_name,
                        is_active
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (company_description, address, city, short_name, is_active)
            else:
                query = """
                    UPDATE company_data
                    SET
                        company_description = %s,
                        address = %s,
                        city = %s,
                        short_name = %s,
                        is_active = %s
                    WHERE company_code = %s
                """
                values = (company_description, address, city, short_name, is_active, company_code)
            
            result = self._execute_write(query, values)
            if result['success']:
                return {'success': True, 'updated': company_code is not None}
            else:
                return result
        except Exception as e:
            return {'success': False, 'error': 'UNEXPECTED_ERROR', 'message': str(e)}

    def save_group(
        self,
        group_code: Optional[int],
        group_description: str,
        is_active: bool
    ) -> Dict[str, Any]:
        try:
            if group_code is None:
                query = """
                    INSERT INTO Group_data (group_description, is_active)
                    VALUES (%s, %s)
                """
                values = (group_description, is_active)
            else:
                query = """
                    UPDATE Group_data
                    SET group_description = %s, is_active = %s
                    WHERE group_code = %s
                """
                values = (group_description, is_active, group_code)
            
            result = self._execute_write(query, values)
            if result['success']:
                return {'success': True, 'updated': group_code is not None}
            else:
                return result
        except Exception as e:
            return {'success': False, 'error': 'UNEXPECTED_ERROR', 'message': str(e)}
    def get_any_thing(self,query,code):
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query,(code,))
            data = cursor.fetchone()

            return data
        except Exception as e:
            return None
    def delete_products(self,code):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = "DELETE FROM products where product_id = %s"
            cursor.execute(query,(code,))
            conn.commit()
            return True
        except Exception as e:
            print(e)
            return False
