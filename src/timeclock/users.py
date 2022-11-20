"""User management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import bcrypt
from flask_login import UserMixin

from .db import db_conn, transaction

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "test.db"))


class Role(Enum):
    """Different roles have different permissions.

    ADMIN can do anything.
    OWNER can mark timesheets as paid.
    EMPLOYEE can clock in/out and view timesheets.
    """

    ADMIN = "ADMIN"
    OWNER = "OWNER"
    EMPLOYEE = "EMPLOYEE"


@dataclass
class User(UserMixin):
    """Needed for flask-login anyways so reused."""

    id: str
    email: str
    role: Role
    username: str

    @classmethod
    def get(cls, user_id: str) -> User:
        """Load User from database."""
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT id, email, role, username
                FROM user
                WHERE id = :user_id;""",
                dict(user_id=user_id),
            )
            row = cursor.fetchone()
        if not row:
            raise ValueError(f"No user with {user_id=}")
        id, email, role, username = row
        return User(str(id), email, Role[role], username)

    @property
    def user_id(self) -> int:
        return int(self.id)


def register_user(
    email: str, unhashed_password: str, role: Role, username: str
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
                INSERT INTO user (email, password_hash, role, username)
                VALUES (:email, :password_hash, :role, :username)
                RETURNING id;""",
                dict(
                    email=email,
                    password_hash=password_hash,
                    role=role.name,
                    username=username,
                ),
            )
            user_id = cursor.fetchone()[0]

    return User(id=str(user_id), email=email, role=role, username=username)


def delete_user(user_id: int) -> bool:
    """Remove user from database."""
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                """--sql
                DELETE FROM user
                 WHERE id = :user_id;""",
                dict(user_id=user_id),
            )
        ret = bool(conn.total_changes)
    return ret


def verify_user(email: str, unhashed_password: str) -> User:
    """Check that password matches for user.

    Raises:
        ValueError: If email doesn't exist or password does not match
    """
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            cursor = conn.execute(
                """--sql
                SELECT id, email, role, username, password_hash
                  FROM user
                 WHERE email = :email;""",
                dict(email=email),
            )
            row = cursor.fetchone()

    if not row:
        raise ValueError("No user with that email")
    id, email, role, username, password_hash = row

    if not bcrypt.checkpw(unhashed_password.encode(), password_hash.encode()):
        raise ValueError("Bad password")

    return User(id=str(id), email=email, role=Role[role], username=username)
