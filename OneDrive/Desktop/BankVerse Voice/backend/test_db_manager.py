import os
import sqlite3
from init_db import init_db
from db_manager import (
    get_customer_by_name,
    get_customer_by_id,
    verify_customer_code,
    get_customer_accounts,
    get_account_balance,
    get_recent_transactions,
    get_loan_details,
    transfer_funds
)

def run_tests():
    print("Running db_manager tests...")
    
    # 1. Setup DB
    init_db()
    
    # 2. Test get_customer_by_name
    customer = get_customer_by_name("Rajesh")
    assert customer is not None, "Failed: get_customer_by_name"
    assert customer["customer_id"] == "C1001", "Failed: ID mismatch in get_customer_by_name"
    assert customer["kyc_status"] == "Verified", "Failed: kyc mismatch"
    print("[OK] test_get_customer_by_name passed")
    
    # 3. Test get_customer_by_id
    customer = get_customer_by_id("C1002")
    assert customer is not None, "Failed: get_customer_by_id"
    assert customer["name"] == "Priya Sharma", "Failed: Name mismatch"
    print("[OK] test_get_customer_by_id passed")
    
    # 4. Test verify_customer_code
    assert verify_customer_code("C1001", "1234") is True, "Failed verify code true"
    assert verify_customer_code("C1001", "0000") is False, "Failed verify code false"
    print("[OK] test_verify_customer_code passed")
    
    # 5. Test get_customer_accounts
    accounts = get_customer_accounts("C1001")
    assert len(accounts) == 2, "Failed: account count"
    types = [a["account_type"] for a in accounts]
    assert "savings" in types and "current" in types, "Failed account types search"
    print("[OK] test_get_customer_accounts passed")
    
    # 6. Test get_account_balance
    balance = get_account_balance("ACC88102")
    assert balance == 78500.50, f"Failed: balance was {balance}"
    print("[OK] test_get_account_balance passed")
    
    # 7. Test get_recent_transactions
    transactions = get_recent_transactions("ACC88102")
    assert len(transactions) > 0, "Failed transactions empty"
    assert transactions[0]["account_number"] == "ACC88102", "Failed transaction acc"
    print("[OK] test_get_recent_transactions passed")
    
    # 8. Test get_loan_details
    loans = get_loan_details("C1001")
    assert len(loans) == 1, "Failed loans size"
    assert loans[0]["loan_id"] == "L4412", "Failed loan id"
    print("[OK] test_get_loan_details passed")
    
    # 9. Test transfer_funds
    initial_sender_bal = get_account_balance("ACC88102")
    initial_receiver_bal = get_account_balance("ACC77201")
    
    res = transfer_funds("ACC88102", "ACC77201", 500.0, "Test Transfer")
    assert res["success"] is True, f"Failed transfer valid: {res.get('error')}"
    assert res["new_balance"] == initial_sender_bal - 500.0, "Failed sender balance math"
    assert get_account_balance("ACC88102") == initial_sender_bal - 500.0, "Failed sender db balance"
    assert get_account_balance("ACC77201") == initial_receiver_bal + 500.0, "Failed receiver db balance"
    
    res2 = transfer_funds("ACC88102", "ACC77201", 999999.0, "Overdraft Attempt")
    assert res2["success"] is False, "Failed: overdraft should fail"
    assert "Insufficient funds" in res2["error"], "Failed error message"
    print("[OK] test_transfer_funds passed")
    
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
