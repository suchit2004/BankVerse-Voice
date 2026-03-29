import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), "bank_data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            account_type TEXT,
            balance REAL
        )
    ''')
    
    cursor.execute('DELETE FROM accounts')
    
    accounts = [
        ("Default User", "savings", 78500.50),
        ("Default User", "current", 125000.0),
        ("Default User", "loan", -15000.0)
    ]
    
    cursor.executemany('INSERT INTO accounts (customer_name, account_type, balance) VALUES (?, ?, ?)', accounts)
    conn.commit()
    conn.close()
    
    print(f"Database successfully generated with seed data at {db_path}!")

if __name__ == "__main__":
    init_db()
