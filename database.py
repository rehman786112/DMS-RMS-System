import mysql.connector

class DatabaseManager():
    def get_connection(self):
        try:
            conn = mysql.connector.connect(
                username = 'rehman',
                password = 'rehman123',
                host = 'localhost',
                database = 'DMS_db'
            )
            cursor = conn.cursor(dictionary=True)

            return conn, cursor
        except Exception as e:
            return e


