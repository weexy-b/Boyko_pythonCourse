"""Initial database setup script for bank system."""

import sqlite3
import sys

enable_unique_name = '--unique-name' in sys.argv

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Bank (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    birth_day TEXT,
    accounts TEXT NOT NULL,
    CONSTRAINT UNIQUE(name, surname)
)
""")

if enable_unique_name:
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_user_name_surname
    ON User(name, surname)
    """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS Account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    account_number TEXT NOT NULL UNIQUE,
    bank_id INTEGER NOT NULL,
    currency TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT,
    FOREIGN KEY(user_id) REFERENCES User(id),
    FOREIGN KEY(bank_id) REFERENCES Bank(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS BankTransactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Bank_sender_name TEXT NOT NULL,
    Account_sender_id INTEGER NOT NULL,
    Bank_receiver_name TEXT NOT NULL,
    Account_receiver_id INTEGER NOT NULL,
    Sent_Currency TEXT NOT NULL,
    Sent_Amount REAL NOT NULL,
    Datetime TEXT
)
""")

conn.commit()
conn.close()

print(
    "Database initialized with UNIQUE constraint on User(name, surname)."
    if enable_unique_name else
    "Database initialized without unique constraint on User(name, surname)."
)
