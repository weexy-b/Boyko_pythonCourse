"""Main script for triggering core banking operations from api_module."""
# pylint: disable=no-value-for-parameter

import logging

from api_module import (
    assign_random_discounts, users_with_debts, biggest_capital,
    oldest_client, most_unique, delete_incomplete_users, last_transactions
)

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    try:
        print("⬛ Assigning discounts:")
        print(assign_random_discounts())

        print("⬛ Users with debts:")
        print(users_with_debts())

        print("⬛ Bank with biggest capital:")
        print(biggest_capital())

        print("⬛ Bank with oldest client:")
        print(oldest_client())

        print("⬛ Bank with most outbound users:")
        print(most_unique())

        print("⬛ Cleaning incomplete users/accounts:")
        print(delete_incomplete_users())

        print("⬛ Transactions for user ID 1 (last 3 months):")
        print(last_transactions(1))

    except (ValueError, RuntimeError) as e:
        logging.error("Unexpected error occurred: %s", e)