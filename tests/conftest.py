"""Fixtures."""

import os
from pathlib import Path

import pendulum
import pytest

from timeclock import timeclock
from timeclock.db import create_db
from timeclock.users import delete_user, register_user


@pytest.fixture(scope="session")
def DB():
    db_file = Path(os.getenv("TIMECLOCK_DB", "test.db"))
    create_db(db_file)
    yield
    db_file.unlink()


@pytest.fixture(scope="session")
def existing_user(DB):
    email = "tman@test.com"
    yield register_user(email, "pass123")
    delete_user(email)


@pytest.fixture
def punched_in(DB, existing_user):
    punch_id, clock_in = timeclock.clock_in(existing_user)
    yield punch_id, clock_in
    timeclock._manual_delete_punch(punch_id)


@pytest.fixture(scope="session")
def fake_timesheet(existing_user):
    start_date = pendulum.local(2022, 1, 3)
    work_days = []
    for n in range(14):
        d = start_date.add(days=n)
        if d.weekday() < 4:
            wd = timeclock.WorkDay(n + 1, d.add(hours=8), d.add(hours=16))
            work_days.append(wd)
        elif d.weekday() == 4:
            # start a lil late on fridays
            wd = timeclock.WorkDay(
                n + 1, d.add(hours=8, minutes=10 + n), d.add(hours=15)
            )
            work_days.append(wd)
    timesheet = timeclock.TimeSheet(
        existing_user, start_date=start_date, work_days=work_days
    )
    return timesheet
