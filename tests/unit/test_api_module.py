import pytest
from unittest.mock import patch, MagicMock
import sqlite3
import requests
from api_module import (
    add_users, add_banks, add_accounts, modify_user,
    delete_user, transfer_money, assign_random_discounts,
    users_with_debts, biggest_capital, oldest_client,
    most_unique, delete_incomplete_users, last_transactions,
    validate_user_full_name, validate_account_number, validate_enum
)


@pytest.fixture
def mock_db(request):
    mock_connect = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    patcher = patch('sqlite3.connect', mock_connect)
    patcher.start()

    def cleanup():
        patcher.stop()

    request.addfinalizer(cleanup)
    return mock_cursor


@pytest.fixture
def mock_requests(request):
    mock_get = MagicMock()
    patcher = patch('requests.get', mock_get)
    patcher.start()

    def cleanup():
        patcher.stop()

    request.addfinalizer(cleanup)
    return mock_get


def test_validate_user_full_name():
    assert validate_user_full_name("John Doe") == ("John", "Doe")
    with pytest.raises(ValueError):
        validate_user_full_name("John")


def test_validate_account_number():
    valid_id = "ID--AB-12-CDEF5678"
    assert validate_account_number(valid_id) == valid_id
    with pytest.raises(ValueError):
        validate_account_number("invalid")


def test_validate_enum():
    validate_enum("type", "credit", ["credit", "debit"])
    with pytest.raises(ValueError):
        validate_enum("type", "invalid", ["credit", "debit"])


def test_add_users(mock_db):
    with patch('api_module.validate_user_full_name', return_value=("John", "Doe")):
        users = [{"user_full_name": "John Doe", "birth_day": "1990-01-01", "accounts": 1}]
        result = add_users(users)
        assert result["status"] == "success"
        mock_db.execute.assert_called_once()


def test_add_banks(mock_db):
    banks = [{"name": "Test Bank"}]
    result = add_banks(banks)
    assert result["status"] == "success"
    mock_db.execute.assert_called_once()


def test_add_accounts(mock_db):
    with patch('api_module.validate_account_number', return_value="12345678"), \
            patch('api_module.validate_enum'):
        accounts = [{
            "user_id": 1, "type": "credit", "account_number": "12345678",
            "bank_id": 1, "currency": "USD", "amount": 1000
        }]
        result = add_accounts(accounts)
        assert result["status"] == "success"
        mock_db.execute.assert_called_once()


def test_modify_user(mock_db):
    result = modify_user(1, {"name": "New Name"})
    assert result["status"] == "success"
    mock_db.execute.assert_called_once()

def test_delete_user(mock_db):
    result = delete_user(1)
    assert result["status"] == "success"
    mock_db.execute.assert_called_once()

def test_transfer_money_success(mock_db, mock_requests):
    mock_db.fetchone.side_effect = [
        (1000, "USD"),
        ("EUR",)
    ]
    mock_requests.return_value.json.return_value = {'data': {'EUR': 0.85}}

    result = transfer_money(1, 2, 100, "USD")
    assert result["status"] == "success"
    assert mock_db.execute.call_count == 5


def test_transfer_money_insufficient_funds(mock_db):
    mock_db.fetchone.return_value = (50, "USD")
    result = transfer_money(1, 2, 100, "USD")
    assert result["status"] == "failure"

def test_assign_random_discounts(mock_db):
    mock_db.fetchall.return_value = [(1,), (2,), (3,)]
    with patch('random.sample', return_value=[1, 2]), \
            patch('random.choice', return_value=25):
        result = assign_random_discounts()
        assert len(result) == 2


def test_users_with_debts(mock_db):
    mock_db.fetchall.return_value = [("John Doe",)]
    result = users_with_debts()
    assert len(result) == 1


def test_biggest_capital(mock_db):
    mock_db.fetchone.return_value = ("Big Bank", 1000000)
    result = biggest_capital()
    assert result[0] == "Big Bank"


def test_oldest_client(mock_db):
    mock_db.fetchone.return_value = ("Old Bank", "1920-01-01")
    result = oldest_client()
    assert "1920" in result[1]


def test_most_unique(mock_db):
    mock_db.fetchone.return_value = ("Unique Bank", 50)
    result = most_unique()
    assert result[1] == 50


def test_delete_incomplete_users(mock_db):
    result = delete_incomplete_users()
    assert result["status"] == "success"
    assert mock_db.execute.call_count == 2


def test_last_transactions(mock_db):
    mock_db.fetchall.return_value = [(1, 2, 100, "2023-01-01")]
    result = last_transactions(1)
    assert len(result) == 1


from unittest.mock import patch, MagicMock
import sqlite3

@patch("api_module.sqlite3.connect")
def test_db_error_handling(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB error")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    test_user = {
        "user_full_name": "Ivan Smyk",
        "birth_day": "2000-01-01",
        "accounts": "UA1234567890123456"
    }

    result = add_users([test_user])

    assert result["status"] == "failure"



from unittest.mock import patch, MagicMock
import sqlite3

@patch("api_module.requests.get")
@patch("api_module.sqlite3.connect")
def test_transfer_api_fallback(mock_connect, mock_get):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [(1000, "USD"), ("EUR",)]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    mock_get.side_effect = requests.exceptions.RequestException("API error")

    result = transfer_money(1, 2, 100, "USD")
    assert result["status"] == "success"
