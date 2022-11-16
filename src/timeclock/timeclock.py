"""Business logic for managing the timeclock."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pendulum

from .db import class_row, db_conn, transaction
from .users import User

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "timeclock.db"))


class AlreadyClockedInError(Exception):
    """Raised when try to clock in user who is already clocked in."""

    pass


class NotClockedInError(Exception):
    """Raised when try to clock user out but not clocked in."""

    pass


@dataclass
class WorkDay:
    """Container representing a completed workday."""

    punch_id: int
    clock_in: pendulum.DateTime
    clock_out: pendulum.DateTime
    notes: Optional[str] = None


class TimeSheet:
    """Represent an employee's timesheet."""

    def __init__(
        self, user: User, start_date: pendulum.DateTime, work_days: List[WorkDay]
    ) -> None:
        """Inits TimeSheet for the user."""
        self.user = user
        self.start_date = start_date
        self.work_days = work_days

    @property
    def hours(self) -> float:
        """Total hours worked rounded to nearest quarter of an hour."""
        _hours = 0.0
        for wd in self.work_days:
            diff = wd.clock_out - wd.clock_in
            _hours += diff.hours + (diff.minutes / 60)
        return round(_hours * 4.0) / 4.0

    @classmethod
    def from_db(
        cls, user: User, start_date: pendulum.DateTime, pay_period: int = 2
    ) -> TimeSheet:
        """Load user's timesheet from database.

        Args:
            user (User): A user who has punches in the database.
            start_date (pendulum.DateTime): Date of the first clock_in.
            pay_period (int): Number of weeks to fetch from start_date.
                Default is 2

        Returns:
            A new TimeSheet.
        """
        end_date = start_date.add(weeks=pay_period)
        with db_conn(DB_FILE, class_row(WorkDay)) as conn:
            cursor = conn.execute(
                """--sql
                SELECT punch_id, clock_in, clock_out, notes
                FROM timeclock
                WHERE user_id = :user_id
                AND clock_in > :start_date
                AND clock_out < :end_date;""",
                dict(user_id=user.id, start_date=start_date, end_date=end_date),
            )
            work_days = cursor.fetchall()
        return cls(user, start_date, work_days)

    def __repr__(self) -> str:
        """Pretty print."""
        if self.user.username:
            user = self.user.username
        else:
            user = self.user.email
        return f"TimeSheet({user=}, start_date={self.start_date}, hours={self.hours})"


PunchEvent = Tuple[int, pendulum.DateTime]


def clock_in(user: User) -> PunchEvent:
    """Clock the user in.

    Args:
        user (User): A logged in `User`.

    Raises:
        AlreadyClockedInError: If user clocked in already.

    Returns:
        Tuple[int, pendulum.DateTime]: The punch_id and clock in timestamp.
    """
    _punch_id = clocked_in(user)
    if _punch_id:
        raise AlreadyClockedInError(f"{user}")

    now = pendulum.now()
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            cursor = conn.execute(
                """--sql
                INSERT INTO timeclock (user_id, clock_in)
                VALUES (:user_id, :now)
                RETURNING punch_id;""",
                dict(now=now, user_id=user.id),
            )
            punch_id = cursor.fetchone()[0]
    return punch_id, now


def clock_out(user: User) -> PunchEvent:
    """Clock the user out.

    Args:
        user (User): A logged in `User`.

    Raises:
        NotClockedInError: If user clocked in already.

    Returns:
        Tuple[int, pendulum.DateTime]: The clock out timestamp.
    """
    punch_id = clocked_in(user)
    if not punch_id:
        raise NotClockedInError(f"{user}")

    now = pendulum.now()
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                """--sql
                UPDATE timeclock SET clock_out = :now
                WHERE user_id = :user_id and punch_id = :punch_id;""",
                dict(now=now, user_id=user.id, punch_id=punch_id),
            )
    return punch_id, now


def clocked_in(user: User) -> Optional[int]:
    """Return the current punch_id if user clocked in or None."""
    with db_conn(DB_FILE) as conn:
        cursor = conn.execute(
            """--sql
                SELECT punch_id, clock_in, clock_out
                FROM timeclock
                WHERE user_id = :user_id
            ORDER BY clock_in DESC LIMIT 1;""",
            dict(user_id=user.id),
        )
        row = cursor.fetchone()

    if not row:
        return None
    punch_id, clock_in, clock_out = row
    if clock_in and not clock_out:
        return punch_id
    return None


# def get_all_clocked_in() -> Dict[int, User]:
#     with db_conn(DB_FILE) as conn:
#         cursor = conn.execute(
#             """--sql
#                 SELECT u.id, u.username, u.email, t.clock_in, t.clock_out
#                 FROM user u
#                 JOIN timeclock t
#                     ON u.id = t.user_id
#                 WHERE u.clock_in and not u.clock_out
#             GROUP BY u.id
#             ORDER BY u.clock_in DESC;"""
#         )
#         rows = cursor.fetchall()

#     users: Dict[int, User] = {}
#     for id, username, email, clock_in, clock_out in rows:
#         punch = Punch(clock_in, clock_out)
#         users[id] = User(id, email=email, username=username, punches=[punch])
#     return users


def _manual_add_timesheet(timesheet: TimeSheet) -> None:
    values = [
        {"user_id": timesheet.user.id, "clock_in": w.clock_in, "clock_out": w.clock_out}
        for w in timesheet.work_days
    ]
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.executemany(
                """--sql
                INSERT INTO timeclock (user_id, clock_in, clock_out)
                VALUES (:user_id, :clock_in, :clock_out);""",
                values,
            )


def _manual_delete_punch(punch_id: int) -> None:
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                "DELETE FROM timeclock WHERE punch_id = :punch_id",
                dict(punch_id=punch_id),
            )
