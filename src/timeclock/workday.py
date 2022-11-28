"""WorkDay class."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import pendulum

from .db import class_row, db_conn, get_queries, transaction
from .users import User

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "test.db"))
Q = get_queries()


@dataclass
class Photo:
    """An uploaded photo.

    Attributes:
        id (int): photo id primary key.
        filename (str): filename of the photo.
    """

    id: int
    filename: str

    @classmethod
    def new(cls, filename: Union[str, Path]) -> Photo:
        filename = Path(filename)
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                photo_id = Q.insert_photo(conn, filename=filename.name)
        return cls(photo_id, filename.name)

    def delete(self) -> bool:
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                Q.delete_photo(conn, photo_id=self.id)
            ret = bool(conn.total_changes)
        return ret


def get_photos(workday_id: int) -> List[Photo]:
    """Return all photos for a given workday."""
    with db_conn(DB_FILE, class_row(Photo)) as conn:
        photos = Q.get_workday_photos(conn, workday_id=workday_id)
    return photos


class WorkDay:
    """Represents a single day of work.

    Attributes:
        clock_in (pendulum.DateTime): Time user clocked in.
        clock_out (Optional[pendulum.DateTime]): Time user clocked out. Defaults
            to None because there might not be a clock_out time.
        notes: (Optional[str]): Optional notes a user can leave for the work day.
        id (int): Primary key on the workday table. Defaults to 0 if not created
            by one of the constructors (current(), from_id()). This means that
            there is no primary key yet.
        photos: (Optional[List[Photo]]): List of photos associated with the
            the workday. Default is None.
    """

    def __init__(
        self,
        clock_in: pendulum.DateTime,
        clock_out: Optional[pendulum.DateTime] = None,
        notes: Optional[str] = None,
        id: int = 0,
        photos: Optional[List[Photo]] = None,
    ):
        """Init WorkDay."""
        self.clock_in = clock_in
        self.clock_out = clock_out
        self.notes = notes
        self.id = id
        self.photos = photos

    @classmethod
    def current(cls, user: User) -> WorkDay:
        """Return the current workday for the user.

        Notes:
            - Does no checking for whether user is clocked in.
        """
        with db_conn(DB_FILE) as conn:
            id, clock_in, clock_out, notes = Q.get_user_current_workday(
                conn, user_id=user.user_id
            )
        # if clock_out: raise what?
        photos = get_photos(workday_id=id)
        notes = notes if notes else ""
        return cls(
            clock_in=clock_in, clock_out=clock_out, notes=notes, id=id, photos=photos
        )

    @classmethod
    def from_id(cls, id: int) -> WorkDay:
        """Return the workday with the given id."""
        with db_conn(DB_FILE) as conn:
            clock_in, clock_out, notes = Q.get_workday(conn, workday_id=id)
        photos = get_photos(workday_id=id)
        notes = notes if notes else ""
        return cls(
            clock_in=clock_in, clock_out=clock_out, notes=notes, id=id, photos=photos
        )

    @property
    def user_id(self) -> int:
        """Return the user_id associated with the workday."""
        if not self.id:
            raise Exception("WorkDay has no id.")
        with db_conn(DB_FILE) as conn:
            _user_id = Q.get_workday_user_id(conn, workday_id=self.id)
        return _user_id

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
        """Returns whether or not the workday is able to be edited."""
        with db_conn(DB_FILE) as conn:
            exists = Q.get_workday_archived(conn, workday_id=self.id)
        return bool(exists)

    def __repr__(self) -> str:
        """Print attributes/properties of the WorkDay instance."""
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
        """Set the workday's notes to a new value and save to database.

        Notes:
            - Ideally get rid of this function and use the more general update()
        """
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                conn.execute(
                    """--sql
                    UPDATE workday SET notes = :notes
                    WHERE id = :id;""",
                    dict(id=self.id, notes=notes),
                )
        self.notes = notes

    def add_photo(self, filename: Union[str, Path]) -> Photo:
        """New photo for the workday.

        Raises:
            sqlite3.IntegrityError: If photo already uploaded.
        """
        photo = Photo.new(filename)
        try:
            self.photos.append(photo)  # type: ignore
        except AttributeError:
            self.photos = [photo]

        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                Q.insert_workday_photo(conn, photo_id=photo.id, workday_id=self.id)

        return photo

    def update(self) -> None:
        """Do an update transaction in the database."""
        with db_conn(DB_FILE) as conn:
            with transaction(conn):
                Q.update_workday(
                    conn,
                    workday_id=self.id,
                    clock_in=self.clock_in,
                    clock_out=self.clock_out,
                    notes=self.notes
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


def _manual_delete_workday(workday_id: int) -> None:
    with db_conn(DB_FILE) as conn:
        with transaction(conn):
            conn.execute(
                "DELETE FROM workday WHERE id = :workday_id",
                dict(workday_id=workday_id),
            )
