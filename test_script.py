"""Test module for validating the functions in api_module."""
# pylint: disable=no-value-for-parameter

from api_module import add_users, add_banks, add_accounts, transfer_money

print(add_users([
    {"user_full_name": "Ivan Petrov", "birth_day": "1990-01-01", "accounts": "1,2"}
]))

print(add_banks([{"name": "Bank A"}, {"name": "Bank B"}]))

print(add_accounts([
    {
        "user_id": 1,
        "type": "debit",
        "account_number": "ID--xy-12345678-zx",
        "bank_id": 1,
        "currency": "USD",
        "amount": 1000,
        "status": "gold"
    },
    {
        "user_id": 1,
        "type": "credit",
        "account_number": "ID--ab-56783213-cd",
        "bank_id": 2,
        "currency": "EUR",
        "amount": 500,
        "status": "silver"
    }
]))

print(transfer_money(sender_acc_id=1, receiver_acc_id=2, amount=100, currency="USD"))
