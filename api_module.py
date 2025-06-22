"""Database operations and business logic for banking system."""

import sqlite3
import logging
import random
from datetime import datetime, timedelta
from functools import wraps
import requests
import requests.exceptions
from validation_module import (
    validate_user_full_name, validate_account_number,
    validate_enum, validate_datetime
)

DB_PATH = "bank.db"
logging.basicConfig(level=logging.INFO)

API_KEY = "fca_live_sTZKzN8l9YCGX7TQ7IbPoPihy17Tdzgp7Dtj2Mtu"


def with_db_connection(func):
    """Decorator for DB connection and error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            result = func(cursor, *args, **kwargs)
            conn.commit()
            conn.close()
            return result
        except sqlite3.Error as e:
            logging.error("Database error: %s", e)
            return {"status": "failure", "message": str(e)}
    return wrapper


@with_db_connection
def add_users(cursor, *users):
    """Add users to the database."""
    if len(users) == 1 and isinstance(users[0], list):
        users = users[0]

    for user in users:
        name, surname = validate_user_full_name(user["user_full_name"])
        cursor.execute("""
            INSERT INTO User (name, surname, birth_day, accounts)
            VALUES (?, ?, ?, ?)
        """, (name, surname, user.get("birth_day"), user["accounts"]))

    return {"status": "success", "message": f"Added {len(users)} users"}


@with_db_connection
def add_banks(cursor, *banks):
    """Add banks to the database."""
    if len(banks) == 1 and isinstance(banks[0], list):
        banks = banks[0]
    for bank in banks:
        cursor.execute("INSERT INTO Bank (name) VALUES (?)", (bank["name"],))
    return {"status": "success", "message": f"Added {len(banks)} banks"}


@with_db_connection
def add_accounts(cursor, *accounts):
    """Add accounts to the database."""
    if len(accounts) == 1 and isinstance(accounts[0], list):
        accounts = accounts[0]

    for acc in accounts:
        acc_num = validate_account_number(acc["account_number"])
        validate_enum("type", acc["type"], ["credit", "debit"])
        validate_enum("status", acc.get("status", ""), ["gold", "silver", "platinum", ""])

        cursor.execute("""
            INSERT INTO Account (user_id, type, account_number, bank_id, currency, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            acc["user_id"], acc["type"], acc_num, acc["bank_id"],
            acc["currency"], acc["amount"], acc.get("status")
        ))

    return {"status": "success", "message": f"Added {len(accounts)} accounts"}


@with_db_connection
def modify_user(cursor, user_id, updated_data):
    """Update user's data."""
    if "user_full_name" in updated_data:
        name, surname = validate_user_full_name(updated_data["user_full_name"])
        updated_data["name"] = name
        updated_data["surname"] = surname
        del updated_data["user_full_name"]

    set_clause = ", ".join(f"{k} = ?" for k in updated_data)
    values = list(updated_data.values()) + [user_id]

    cursor.execute(f"""
        UPDATE User SET {set_clause} WHERE id = ?
    """, values)
    return {"status": "success", "message": "User updated"}


@with_db_connection
def delete_user(cursor, user_id):
    """Delete user by ID."""
    cursor.execute("DELETE FROM User WHERE id = ?", (user_id,))
    return {"status": "success", "message": f"Deleted user {user_id}"}


def get_exchange_rate(from_currency, to_currency):
    """Fetch exchange rate between two currencies."""
    try:
        url = (f"https://api.freecurrencyapi.com/v1/latest?apikey={API_KEY}&currencies="
               f"{to_currency}&base_currency={from_currency}")

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['data'][to_currency]
    except (requests.exceptions.RequestException, KeyError, ValueError) as e:
        logging.warning("Currency API failed: %s. Using fallback 1.0", e)
        return 1.0


@with_db_connection
def transfer_money(cursor, sender_acc_id, receiver_acc_id, amount, currency, **kwargs):
    """Transfer money between accounts."""
    dt = validate_datetime(kwargs.get('dt'))

    cursor.execute("SELECT amount, currency FROM Account WHERE id = ?", (sender_acc_id,))
    sender_data = cursor.fetchone()
    if not sender_data:
        return {"status": "failure", "message": "Sender not found"}

    balance = sender_data[0]
    if balance < amount:
        return {"status": "failure", "message": "Insufficient funds"}

    cursor.execute("SELECT currency FROM Account WHERE id = ?", (receiver_acc_id,))
    receiver_data = cursor.fetchone()
    if not receiver_data:
        return {"status": "failure", "message": "Receiver not found"}

    receiver_currency = receiver_data[0]
    rate = get_exchange_rate(currency, receiver_currency)
    converted_amount = amount * rate

    cursor.execute("UPDATE Account SET amount = amount - ? WHERE id = ?", (amount, sender_acc_id))
    cursor.execute("UPDATE Account SET amount = amount + ? WHERE id = ?", (converted_amount, receiver_acc_id))

    cursor.execute("""
        INSERT INTO BankTransactions (
            Bank_sender_name, Account_sender_id, 
            Bank_receiver_name, Account_receiver_id, 
            Sent_Currency, Sent_Amount, Datetime
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("Bank A", sender_acc_id, "Bank B", receiver_acc_id, currency, amount, dt))

    return {"status": "success", "message": f"Transferred {amount} {currency} at rate {rate:.2f}"}


@with_db_connection
def assign_random_discounts(cursor):
    """Assign random discounts to random users."""
    cursor.execute("SELECT id FROM User")
    users = [row[0] for row in cursor.fetchall()]
    selected = random.sample(users, min(10, len(users)))
    discounts = {user_id: random.choice([25, 30, 50]) for user_id in selected}
    logging.info("Assigned discounts: %s", discounts)
    return discounts


@with_db_connection
def users_with_debts(cursor):
    """Get list of users with negative balances."""
    cursor.execute("""
        SELECT DISTINCT u.name || ' ' || u.surname 
        FROM User u 
        JOIN Account a ON u.id = a.user_id 
        WHERE a.amount < 0
    """)
    return cursor.fetchall()


@with_db_connection
def biggest_capital(cursor):
    """Find bank with highest total capital."""
    cursor.execute("""
        SELECT b.name, SUM(a.amount) AS total 
        FROM Bank b 
        JOIN Account a ON b.id = a.bank_id 
        GROUP BY b.id 
        ORDER BY total DESC 
        LIMIT 1
    """)
    return cursor.fetchone()


@with_db_connection
def oldest_client(cursor):
    """Find bank with the oldest user."""
    cursor.execute("""
        SELECT b.name, u.birth_day 
        FROM Bank b 
        JOIN Account a ON b.id = a.bank_id 
        JOIN User u ON u.id = a.user_id 
        ORDER BY u.birth_day ASC 
        LIMIT 1
    """)
    return cursor.fetchone()


@with_db_connection
def most_unique(cursor):
    """Find bank with most unique transaction senders."""
    cursor.execute("""
        SELECT t.Bank_sender_name, COUNT(DISTINCT a.user_id) AS users 
        FROM BankTransactions t 
        JOIN Account a ON a.id = t.Account_sender_id 
        GROUP BY t.Bank_sender_name 
        ORDER BY users DESC 
        LIMIT 1
    """)
    return cursor.fetchone()


@with_db_connection
def delete_incomplete_users(cursor):
    """Remove users/accounts with incomplete data."""
    cursor.execute("""
        DELETE FROM Account 
        WHERE user_id IS NULL OR type IS NULL 
        OR account_number IS NULL OR bank_id IS NULL 
        OR currency IS NULL OR amount IS NULL
    """)
    cursor.execute("""
        DELETE FROM User 
        WHERE name IS NULL OR surname IS NULL OR accounts IS NULL
    """)
    logging.info("Deleted incomplete users and accounts.")
    return {"status": "success"}


@with_db_connection
def last_transactions(cursor, user_id):
    """Return user's transactions from last 3 months."""
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM BankTransactions 
        WHERE Account_sender_id IN (
            SELECT id FROM Account WHERE user_id = ?
        ) AND datetime >= ?
    """, (user_id, three_months_ago))
    return cursor.fetchall()
