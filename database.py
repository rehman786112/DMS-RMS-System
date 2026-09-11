import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseManager:
    def get_connection(self):
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DATABASE_HOST"),
                user=os.getenv("DATABASE_USER"),
                password=os.getenv("DATABASE_PASSWORD"),
                database=os.getenv("DATABASE_NAME"),
                port=os.getenv("DATABASE_PORT")
            )
            cursor = conn.cursor(dictionary=True)
            return conn, cursor
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None, None