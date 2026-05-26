import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), "bank_data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            kyc_status TEXT DEFAULT 'Pending',
            credit_score INTEGER,
            verification_code TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_number TEXT PRIMARY KEY,
            customer_id TEXT,
            account_type TEXT CHECK(account_type IN ('savings', 'current', 'fixed_deposit', 'loan')),
            balance REAL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT,
            type TEXT CHECK(type IN ('deposit', 'withdrawal', 'transfer')),
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            FOREIGN KEY(account_number) REFERENCES accounts(account_number)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            loan_id TEXT PRIMARY KEY,
            customer_id TEXT,
            loan_type TEXT CHECK(loan_type IN ('home', 'auto', 'personal', 'education')),
            amount REAL,
            interest_rate REAL,
            outstanding_balance REAL,
            emi_amount REAL,
            next_emi_date TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            policy_content TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database successfully generated with seed data at {db_path}!")

if __name__ == "__main__":
    init_db()
