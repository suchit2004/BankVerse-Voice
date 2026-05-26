import sqlite3
import os

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), "bank_data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Drop existing tables to ensure clean rebuild with new schema
    cursor.execute('DROP TABLE IF EXISTS transactions')
    cursor.execute('DROP TABLE IF EXISTS loans')
    cursor.execute('DROP TABLE IF EXISTS accounts')
    cursor.execute('DROP TABLE IF EXISTS policies')
    cursor.execute('DROP TABLE IF EXISTS customers')
    
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
    
    # Clear any existing data for a clean seed
    cursor.execute('DELETE FROM transactions')
    cursor.execute('DELETE FROM loans')
    cursor.execute('DELETE FROM accounts')
    cursor.execute('DELETE FROM policies')
    cursor.execute('DELETE FROM customers')
    
    # Seed Customers
    customers = [
        ("C1001", "Rajesh Kumar", "+919876543210", "rajesh.kumar@bankverse.com", "Verified", 780, "1234"),
        ("C1002", "Priya Sharma", "+919812345678", "priya.sharma@bankverse.com", "Verified", 740, "5678"),
        ("C1003", "Amit Patel", "+919900990099", "amit.patel@bankverse.com", "Pending", 620, "9999")
    ]
    cursor.executemany('''
        INSERT INTO customers (customer_id, name, phone, email, kyc_status, credit_score, verification_code)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', customers)
    
    # Seed Accounts
    accounts = [
        ("ACC88102", "C1001", "savings", 78500.50, "active"),
        ("ACC88103", "C1001", "current", 125000.00, "active"),
        ("ACC77201", "C1002", "savings", 42350.75, "active"),
        ("ACC77202", "C1002", "loan", -150000.00, "active"),
        ("ACC66301", "C1003", "savings", 1500.00, "active")
    ]
    cursor.executemany('''
        INSERT INTO accounts (account_number, customer_id, account_type, balance, status)
        VALUES (?, ?, ?, ?, ?)
    ''', accounts)
    
    # Seed Transactions
    transactions = [
        ("ACC88102", "deposit", 10000.00, "Monthly Interest Credit"),
        ("ACC88102", "withdrawal", 2500.00, "ATM Cash Withdrawal - Mumbai"),
        ("ACC88102", "transfer", 5000.00, "Sent to Priya Sharma (ACC77201)"),
        ("ACC88103", "deposit", 50000.00, "Business Invoice Payment received"),
        ("ACC77201", "deposit", 5000.00, "Received from Rajesh Kumar (ACC88102)"),
        ("ACC77201", "withdrawal", 1200.00, "Online Shopping - Amazon"),
        ("ACC66301", "deposit", 500.00, "Cash Deposit at Branch")
    ]
    cursor.executemany('''
        INSERT INTO transactions (account_number, type, amount, description)
        VALUES (?, ?, ?, ?)
    ''', transactions)
    
    # Seed Loans
    loans = [
        ("L4412", "C1001", "home", 2500000.00, 8.5, 2350000.00, 18500.00, "2026-06-05"),
        ("L4413", "C1002", "auto", 500000.00, 9.2, 150000.00, 9500.00, "2026-06-10")
    ]
    cursor.executemany('''
        INSERT INTO loans (loan_id, customer_id, loan_type, amount, interest_rate, outstanding_balance, emi_amount, next_emi_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', loans)
    
    # Seed Policies
    policies = [
        ("POL001", "loan", "Home & Personal Loan Policy", "BankVerse Loan Policy: Minimum credit score of 650 required. Required documentation: Aadhar Card, PAN Card, salary slips of last 3 months, and bank statements of last 6 months. Home loan interest rates start at 8.5% p.a., personal loan rates at 11.0% p.a."),
        ("POL002", "card", "Credit Card Policy", "BankVerse Credit Card Guidelines: Credit score of 750 or above qualifies for premium cards with zero annual fees for the first year. Required documents: ID proof, address proof, and latest Income Tax Return (ITR) or Form 16."),
        ("POL003", "close", "Account Closure Policy", "BankVerse Account Closure Guidelines: The customer must visit their home branch in person. They must submit a signed account closure request form, return all unused checkbooks, debit cards, and original passbook, and settle any outstanding loan balances.")
    ]
    cursor.executemany('''
        INSERT INTO policies (policy_id, topic, policy_name, policy_content)
        VALUES (?, ?, ?, ?)
    ''', policies)
    
    conn.commit()
    conn.close()
    
    print(f"Database successfully generated with seed data at {db_path}!")

if __name__ == "__main__":
    init_db()
