"""All database classes and functions."""

import sqlite3
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Callable, Generator, Tuple, Type, Union

import pendulum

# Store pendulum.DateTime as iso string when writing to database
sqlite3.register_adapter(pendulum.DateTime, lambda val: val.isoformat(" "))
# Convert iso string back to pendulum.DateTime when reading from database
sqlite3.register_converter("TIMESTAMP", lambda s: pendulum.parse(s.decode()))


SCHEMA = """
--sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash BLOB NOT NULL,
    username TEXT
);
--sql
CREATE TABLE timeclock (
    punch_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    clock_in TIMESTAMP NOT NULL,
    clock_out TIMESTAMP,
    notes TEXT,
    UNIQUE (punch_id, user_id),
    FOREIGN KEY (user_id) REFERENCES user(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
"""


@lru_cache
def _names(desc: Tuple[str]) -> Tuple[str, ...]:
    return tuple(d[0] for d in desc)


def class_row(cls: Type) -> Callable:
    """Generate a row factory to represent rows as instances of the class *cls*.

    The class must support every output column name as a keyword parameter.
    Inspired by https://github.com/psycopg/psycopg/blob/master/psycopg/psycopg/rows.py

    Args:
        cls (Type): The class to adapt each each row to. It must support the
            fields returned by the query as keyword arguments.

    Returns:
        Callable[Type]: A callable that will map rows to the cls Type.
    """
    def _class_row(cursor: sqlite3.Cursor, row: Tuple) -> Type:
        desc = cursor.description
        return cls(**dict(zip(_names(desc), row)))
    return _class_row


RowFactoryType = Union[Callable[[Type], Callable], Type[sqlite3.Row]]


@contextmanager
def db_conn(
    db_file: Path, row_factory: RowFactoryType = sqlite3.Row
) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for sqlite connections.

    Fixes the weird default behavior of transactions, enable reads while
    a transaction is open, improve write performance, enforce foreign keys,
    set detect_types arg so that columns of type timestamp will be parsed
    into a python datetime and run `pragma optimize` on connection close to
    keep query planner statistics as up to date as possible.

    Args:
        db_file (str, Path): A str or pathlib.Path representing the database file.
        row_factory (RowFactoryType): A function for mapping rows to types.
            Default is sqlite3.Row.
    """
    conn = sqlite3.connect(
        db_file,
        isolation_level=None,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.execute("pragma journal_mode=wal;")
    conn.execute("pragma synchronous = normal;")
    conn.execute("pragma temp_store = memory;")
    conn.execute("PRAGMA foreign_keys = on;")
    conn.row_factory = row_factory

    try:
        yield conn
    finally:
        conn.execute("pragma analysis_limit=400;")
        conn.execute("pragma optimize;")
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[None, None, None]:
    """Context manager for explict transactions."""
    # We must issue a "BEGIN" explicitly when running in auto-commit mode.
    conn.execute("BEGIN")
    try:
        # Yield control back to the caller.
        yield
    except:  # noqa: E722
        conn.rollback()  # Roll back all changes if an exception occurs.
        raise
    else:
        conn.commit()


def create_db(db_file: Path) -> None:
    """Create the database."""
    with db_conn(db_file) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
