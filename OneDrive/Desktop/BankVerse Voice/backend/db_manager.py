import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bank_data.db")

def get_db_connection():
    """ Establish a connection to the SQLite database. """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_customer_by_id(customer_id: str):
    """ Fetch customer details by customer_id. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_customer_by_name(name: str):
    """ Fetch customer details by matching name (case-insensitive). """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_customer_code(customer_id: str, verification_code: str) -> bool:
    """ Verify the OTP / PIN code for the given customer. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM customers WHERE customer_id = ? AND verification_code = ?",
        (customer_id, verification_code)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None
