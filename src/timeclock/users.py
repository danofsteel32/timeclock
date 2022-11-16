"""User management."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import bcrypt
from flask_login import UserMixin

from .db import class_row, db_conn, transaction

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "timeclock.db"))


@dataclass
class User(UserMixin):
    """Needed for flask-login anyways so reused."""

    id: str
    email: str
    username: Optional[str] = None

    @classmethod
    def get(cls, user_id: str) -> "User":
        with db_conn(DB_FILE, class_row(User)) as conn:
            cursor = conn.execute(
                """--sql
                SELECT id, email, username
                FROM user
                WHERE id = :user_id;""",
                dict(user_id=user_id)
            )
            user = cursor.fetchone()
        return user


def register_user(
    email: str, unhashed_password: str, username: Optional[str] = None
) -> User:
    """Create a new user in the database.

    Raises:
        sqlite3.IntegrityError: If email already registered
    """
    hash = bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt())
    password_hash = hash.decode()

    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            cursor = conn.execute(
                """--sql
                INSERT INTO user (email, password_hash, username)
                VALUES (:email, :password_hash, :username)
                RETURNING id;""",
                dict(email=email, password_hash=password_hash, username=username),
            )
            user_id = cursor.fetchone()[0]

    return User(str(user_id), email, username)


def delete_user(email: str) -> None:
    """Remove user from database."""
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                """--sql
                DELETE FROM user
                 WHERE email = :email;""",
                dict(email=email),
            )


def verify_user(email: str, unhashed_password: str) -> User:
    """Check that password matches for user.

    Raises:
        ValueError: If email doesn't exist or password does not match
    """
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            cursor = conn.execute(
                """--sql
                SELECT id, email, username, password_hash
                  FROM user
                 WHERE email = :email;""",
                dict(email=email),
            )
            row = cursor.fetchone()

    if not row:
        raise ValueError("No user with that email")
    id, email, username, password_hash = row

    if not bcrypt.checkpw(unhashed_password.encode(), password_hash.encode()):
        raise ValueError("Bad password")

    return User(str(id), email, username)
