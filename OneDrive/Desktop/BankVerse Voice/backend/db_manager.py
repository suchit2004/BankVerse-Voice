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

def get_customer_accounts(customer_id: str):
    """ Get all accounts associated with a customer. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_account_balance(account_number: str):
    """ Get the balance of a specific account. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (account_number,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_recent_transactions(account_number: str, limit: int = 5):
    """ Get the most recent transactions for an account. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE account_number = ? ORDER BY timestamp DESC LIMIT ?",
        (account_number, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_loan_details(customer_id: str):
    """ Get loan details for a customer. """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM loans WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def transfer_funds(from_account: str, to_account: str, amount: float, description: str = "Transfer") -> dict:
    """ Perform a fund transfer from one account to another in an atomic transaction. """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Lock and check balance of sender
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (from_account,))
        from_row = cursor.fetchone()
        if not from_row:
            return {"success": False, "error": f"Sender account {from_account} not found"}
        
        from_balance = from_row[0]
        if from_balance < amount:
            return {"success": False, "error": "Insufficient funds"}
            
        # Check receiver
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (to_account,))
        to_row = cursor.fetchone()
        if not to_row:
            return {"success": False, "error": f"Recipient account {to_account} not found"}
            
        # Debit sender
        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_number = ?",
            (amount, from_account)
        )
        # Credit receiver
        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE account_number = ?",
            (amount, to_account)
        )
        
        # Log transaction for sender
        cursor.execute(
            "INSERT INTO transactions (account_number, type, amount, description) VALUES (?, 'transfer', ?, ?)",
            (from_account, amount, f"Sent to {to_account}: {description}")
        )
        
        # Log transaction for receiver
        cursor.execute(
            "INSERT INTO transactions (account_number, type, amount, description) VALUES (?, 'deposit', ?, ?)",
            (to_account, amount, f"Received from {from_account}: {description}")
        )
        
        conn.commit()
        return {"success": True, "new_balance": from_balance - amount}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
