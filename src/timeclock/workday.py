"""WorkDay class."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pendulum

from .db import db_conn, transaction
from .users import User

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "test.db"))


@dataclass
class Photo:
    """An uploaded photo.

    Attributes:
        id (int): photo id primary key.
        filename (str): filename of the photo.
    """

    id: int
    filename: str

    @property
    def filepath(self) -> Path:
        """Full file path."""
        return Path(self.filename)


class WorkDay:
    """Represents a single day of work.

    Attributes:
        clock_in (pendulum.DateTime): Time user clocked in.
        clock_out (Optional[pendulum.DateTime]): Time user clocked out.
        notes: (Optional[str]): Optional notes a user can leave for the work day.
        id (Optional[int]): Primary key on the workday table.
    """

    def __init__(
        self,
        clock_in: pendulum.DateTime,
        clock_out: Optional[pendulum.DateTime] = None,
        notes: Optional[str] = None,
        id: int = 0,
        photos: Optional[List[Photo]] = None,
    ):
        self.clock_in = clock_in
        self.clock_out = clock_out
        self.notes = notes
        self.id = id
        self.photos = photos

    @classmethod
    def current(cls, user: User) -> WorkDay:
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT id, clock_in, clock_out, notes
                FROM workday
                WHERE user_id = :user_id
                ORDER BY clock_in DESC LIMIT 1;""",
                dict(user_id=user.user_id),
            )
            id, clock_in, clock_out, notes = cursor.fetchone()
            cursor.execute(
                """--sql
                SELECT p.id, p.filename
                FROM photo p
                JOIN workday_photo wp
                ON p.id = wp.photo_id
                WHERE wp.workday_id = :id;""",
                dict(id=id),
            )
            photo_rows = cursor.fetchall()
        photos = []
        for photo_id, filename in photo_rows:
            photos.append(Photo(photo_id, filename))
        return cls(
            clock_in=clock_in, clock_out=clock_out, notes=notes, id=id, photos=photos
        )

    @classmethod
    def from_id(cls, id: int) -> WorkDay:
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT clock_in, clock_out, notes
                FROM workday
                WHERE id = :id;""",
                dict(id=id),
            )
            clock_in, clock_out, notes = cursor.fetchone()
            cursor.execute(
                """--sql
                SELECT p.id, p.filename
                FROM photo p
                JOIN workday_photo wp
                ON p.id = wp.photo_id
                WHERE wp.workday_id = :id;""",
                dict(id=id),
            )
            photo_rows = cursor.fetchall()
        photos = []
        for photo_id, filename in photo_rows:
            photos.append(Photo(photo_id, filename))
        return cls(
            clock_in=clock_in, clock_out=clock_out, notes=notes, id=id, photos=photos
        )

    @property
    def user_id(self) -> int:
        if not self.id:
            raise Exception("can't get user if no id.")
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT user_id
                FROM workday
                WHERE id = :id;""",
                dict(id=self.id),
            )
            return cursor.fetchone()[0]

    @property
    def date(self) -> pendulum.Date:
        """Just the date.

        Returns:
            pendulum.Date: The date clock_in happened.
        """
        return self.clock_in.date()

    @property
    def hours(self) -> float:
        """Returns The total number of hours worked.

        Returns:
            float: Hours worked rounded to the nearest quarter of an hour.
        """
        if self.clock_out:
            diff = self.clock_out - self.clock_in
        else:
            diff = pendulum.now() - self.clock_in
        _hours = diff.hours + (diff.minutes / 60)
        return round(_hours * 4.0) / 4.0

    @property
    def archived(self) -> bool:
        with db_conn(DB_FILE) as conn:
            cursor = conn.execute(
                """--sql
                SELECT EXISTS (
                    SELECT 1
                    FROM timesheet_workday
                    WHERE workday_id = :id);""",
                dict(id=self.id),
            )
            exists = cursor.fetchone()[0]
        return exists

    def __repr__(self) -> str:
        """Print all attributes of the WorkDay instance."""
        return (
            f"WorkDay(id={self.id} clock_in={self.clock_in}, "
            f"clock_out={self.clock_out}, notes={self.notes})"
        )

    def __str__(self) -> str:
        """Pretty print for human consumption."""
        date = self.date.format("ddd M/DD/YY")
        ci = self.clock_in.format("h:mmA")
        if self.clock_out:
            co = self.clock_out.format("h:mmA")
            hours = f"{self.hours}hrs"
            return f"{date} {ci} - {co} {hours:8}"
        else:
            return f"{date} {ci}"

    def update_notes(self, notes: str) -> None:
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                conn.execute(
                    """--sql
                    UPDATE workday SET notes = :notes
                    WHERE id = :id;""",
                    dict(id=self.id, notes=notes),
                )
        self.notes = notes

    def update(self) -> None:
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                conn.execute(
                    """--sql
                    UPDATE workday SET
                        clock_in = :clock_in,
                        clock_out = :clock_out,
                        notes = :notes
                    WHERE id = :id;""",
                    dict(
                        id=self.id,
                        clock_in=self.clock_in,
                        clock_out=self.clock_out,
                        notes=self.notes,
                    ),
                )

    def _insert(self, user: User) -> None:
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                cursor = conn.execute(
                    """--sql
                    INSERT INTO workday (user_id, clock_in, clock_out, notes)
                    VALUES (:user_id, :clock_in, :clock_out, :notes)
                    RETURNING id;""",
                    dict(
                        user_id=user.user_id,
                        clock_in=self.clock_in,
                        clock_out=self.clock_out,
                        notes=self.notes,
                    ),
                )
                self.id = cursor.fetchone()[0]
                # TODO photos


def _manual_delete_workday(workday_id: int) -> None:
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                "DELETE FROM workday WHERE id = :workday_id",
                dict(workday_id=workday_id),
            )
