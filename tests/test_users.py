import sqlite3

import pytest

from timeclock import users


def test_user_get_real_id(employee_user):
    user = users.User.get(employee_user.id)
    assert employee_user == user


def test_user_get_bad_id(DB):
    with pytest.raises(ValueError):
        users.User.get(6999)


def test_duplicate_user(employee_user):
    with pytest.raises(sqlite3.IntegrityError):
        users.register_user(
            employee_user.email, "newpass123", users.Role.EMPLOYEE, "sameusername"
        )


def test_register_user():
    email, username = "someone@email.com", "username32"
    user = users.register_user(email, "pass123", users.Role.EMPLOYEE, username)
    assert user.email == email
    assert user.username == username
    assert users.delete_user(user.user_id) is True


def test_delete_user_does_not_exist():
    assert users.delete_user(6999) is False


def test_verify_user_bad_email():
    with pytest.raises(ValueError):
        users.verify_user("fake@email.com", "pass123")


def test_verify_user_good_pass(employee_user):
    assert users.verify_user(employee_user.email, "employeepass") == employee_user


def test_verify_user_bad_pass(employee_user):
    with pytest.raises(ValueError):
        users.verify_user(employee_user.email, "badpass")
