"""TimeSheet class."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Set

import pendulum

from .db import class_row, db_conn, transaction
from .users import User
from .workday import WorkDay

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "test.db"))


class TimeSheet:
    """Represent an employee's timesheet.

    Note:
        - Need a classmethod to get all punches not associated with a saved timesheet.

    Attributes:
        work_days (List[WorkDay]): All work days on this timesheet.
    """

    def __init__(self, work_days: List[WorkDay], id: int = 0, notes: str = "") -> None:
        """Inits TimeSheet for the user."""
        self.work_days = work_days
        self.id = id
        self.notes = notes

    @classmethod
    def from_id(cls, id: int) -> TimeSheet:
        work_days = []
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT wd.id
                FROM workday wd
                WHERE wd.id IN (
                    SELECT workday_id
                    FROM timesheet_workday
                    WHERE timesheet_id = :id);""",
                dict(id=id),
            )
            wd_ids = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                """--sql
                SELECT notes
                FROM timesheet
                WHERE id = :id;""",
                dict(id=id),
            )
            notes = cursor.fetchone()[0]
        for wd_id in wd_ids:
            work_days.append(WorkDay.from_id(wd_id))
        return cls(work_days, id, notes)

    @classmethod
    def current(cls, user: User) -> TimeSheet:
        """Get the current timesheet for the user."""
        work_days = []
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT wd.id
                FROM workday wd
                WHERE wd.user_id = :user_id
                AND wd.clock_out
                AND wd.id NOT IN (SELECT workday_id FROM timesheet_workday);""",
                dict(user_id=user.user_id),
            )
            wd_ids = [row[0] for row in cursor.fetchall()]
        for wd_id in wd_ids:
            work_days.append(WorkDay.from_id(wd_id))
        return cls(work_days)

    def save(self, user: User, notes: str, workday_ids: Set[int]) -> None:
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                cursor = conn.execute(
                    """--sql
                    INSERT INTO timesheet (user_id, notes)
                    VALUES (:user_id, :notes)
                    RETURNING id;""",
                    dict(user_id=user.user_id, notes=notes),
                )
                ts_id = cursor.fetchone()[0]
                for wd_id in workday_ids:
                    conn.execute(
                        """--sql
                        INSERT INTO timesheet_workday (timesheet_id, workday_id)
                        VALUES (:ts_id, :wd_id);""",
                        dict(ts_id=ts_id, wd_id=wd_id),
                    )

    @property
    def start_id(self) -> int:
        return self.work_days[0].id

    @property
    def end_id(self) -> int:
        return self.work_days[-1].id

    @property
    def hours(self) -> float:
        """Total hours worked rounded to nearest quarter of an hour."""
        _hours = 0.0
        for wd in self.work_days:
            _hours += wd.hours
        return _hours

    @property
    def start_date(self) -> pendulum.Date:
        """First work day in the TimeSheet."""
        return self.work_days[0].clock_in.date()

    @property
    def end_date(self) -> pendulum.Date:
        """Last work day in the TimeSheet."""
        return self.work_days[-1].clock_in.date()

    def __repr__(self) -> str:
        """A not so standard repr."""
        return (
            f"TimeSheet(start_date={str(self.start_date)}, "
            f"end_date={str(self.end_date)}, hours={self.hours})"
        )

    def __str__(self) -> str:
        """Pretty print for human consumption."""
        out = "TimeSheet:\n"
        for wd in self.work_days:
            out += f"  {wd}\n"
        out += f"Hours: {self.hours}"
        return out


def get_overview() -> List[Dict]:
    overview = []
    with db_conn(DB_FILE, class_row(User)) as conn:
        cursor = conn.execute(
            """--sql
            SELECT id, username, role, email
            FROM user
            WHERE role = 'EMPLOYEE';"""
        )
        user_rows = cursor.fetchall()
    for user in user_rows:
        overview.append(
            dict(
                id=user.id,
                username=user.username,
                email=user.email,
                hours=TimeSheet.current(user).hours,
            )
        )
    return overview


def get_past_timesheets(user: User) -> List[TimeSheet]:
    past_timesheets = []
    with db_conn(DB_FILE) as conn:
        cursor = conn.execute(
            """--sql
            SELECT id
            FROM timesheet
            WHERE user_id = :user_id
            ORDER BY id DESC;""",
            dict(user_id=user.user_id),
        )
        ts_ids = [r[0] for r in cursor.fetchall()]
        for ts_id in ts_ids:
            past_timesheets.append(TimeSheet.from_id(ts_id))
    return past_timesheets
