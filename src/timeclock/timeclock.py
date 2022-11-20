"""Business logic for managing the timeclock."""
from __future__ import annotations

import os
from pathlib import Path

import pendulum

from .db import db_conn, transaction
from .users import User
from .workday import WorkDay

# from typing import Dict, List, Optional, Tuple


DB_FILE = Path(os.getenv("TIMECLOCK_DB", "test.db"))


class AlreadyClockedInError(Exception):
    """Raised when try to clock in user who is already clocked in."""

    pass


class NotClockedInError(Exception):
    """Raised when try to clock user out but not clocked in."""

    pass


def clocked_in(user: User) -> bool:
    """Return whether the user is logged in.

    Args:
        user (User): A logged in `User`.

    Returns:
        bool: Whether the user is logged in.
    """
    with db_conn(DB_FILE) as conn:
        cursor = conn.execute(
            """--sql
                SELECT id, clock_in, clock_out
                FROM workday
                WHERE user_id = :user_id
            ORDER BY clock_in DESC LIMIT 1;""",
            dict(user_id=user.id),
        )
        row = cursor.fetchone()
    if row:
        punch_id, clock_in, clock_out = row
        if clock_in and not clock_out:
            return True
    return False


def clock_in(user: User) -> WorkDay:
    """Clock the user in.

    Args:
        user (User): A logged in `User`.

    Raises:
        AlreadyClockedInError: If user clocked in already.

    Returns:
        WorkDay: The workday created.
    """
    if clocked_in(user):
        raise AlreadyClockedInError(f"{user}")

    now = pendulum.now()
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            cursor = conn.execute(
                """--sql
                INSERT INTO workday (user_id, clock_in)
                VALUES (:user_id, :now)
                RETURNING id;""",
                dict(now=now, user_id=user.id),
            )
            id = cursor.fetchone()[0]
    return WorkDay(id=id, clock_in=now)


def clock_out(user: User) -> int:
    """Clock the user out.

    Args:
        user (User): A logged in `User`.

    Raises:
        NotClockedInError: If user clocked in already.

    Returns:
        int: The workday id being clocked out on.
    """
    if not clocked_in(user):
        raise NotClockedInError(f"{user}")

    workday = WorkDay.current(user)
    now = pendulum.now()
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                """--sql
                UPDATE workday SET clock_out = :now
                WHERE id = :id;""",
                dict(now=now, id=workday.id),
            )
    return workday.id
