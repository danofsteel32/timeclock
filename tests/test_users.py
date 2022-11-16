import sqlite3

import pytest

from timeclock.users import delete_user, register_user, verify_user


def test_duplicate_user(existing_user):
    with pytest.raises(sqlite3.IntegrityError):
        register_user(existing_user.email, "newpass123")


def test_register_user():
    email, username = "someone@email.com", "username32"
    user = register_user(email, "pass123", username)
    assert user.email == email
    assert user.username == username


def test_delete_user_does_not_exist():
    delete_user("fake@email.com")


def test_verify_user_bad_email():
    with pytest.raises(ValueError):
        verify_user("fake@email.com", "pass123")


def test_verify_user_good_pass(existing_user):
    assert verify_user(existing_user.email, "pass123") == existing_user


def test_verify_user_bad_pass(existing_user):
    with pytest.raises(ValueError):
        verify_user(existing_user.email, "badpass")
