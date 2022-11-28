"""Fixtures."""

import os
from pathlib import Path

import pendulum
import pytest
from flask_login import FlaskLoginClient

from timeclock import create_app, timeclock, timesheet, users, workday
from timeclock.db import create_db


@pytest.fixture(scope="session")
def DB():
    db_file = Path(os.getenv("TIMECLOCK_DB", "test.db"))
    create_db(db_file)
    yield
    db_file.unlink()


@pytest.fixture(scope="session")
def admin_user(DB):
    yield users.register_user(
        "admin@test.com", "adminpass", users.Role.ADMIN, "adminator"
    )


@pytest.fixture(scope="session")
def owner_user(DB):
    yield users.register_user("owner@test.com", "ownerpass", users.Role.OWNER, "owned")


@pytest.fixture(scope="session")
def employee_user(DB):
    yield users.register_user(
        "employee@test.com", "employeepass", users.Role.EMPLOYEE, "employed"
    )


@pytest.fixture
def employee_workday(DB, employee_user):
    wd = timeclock.clock_in(employee_user)
    yield wd
    workday._manual_delete_workday(wd.id)


@pytest.fixture(scope="session")
def fake_timesheet(employee_user):
    start_date = pendulum.local(2022, 1, 3)
    work_days = []
    for n in range(14):
        d = start_date.add(days=n)
        if d.weekday() < 4:
            wd = workday.WorkDay(clock_in=d.add(hours=8), clock_out=d.add(hours=16))
            work_days.append(wd)
        elif d.weekday() == 4:
            # start a lil late on fridays
            wd = workday.WorkDay(
                clock_in=d.add(hours=8, minutes=10 + n), clock_out=d.add(hours=15)
            )
            work_days.append(wd)
    ts = timesheet.TimeSheet(work_days=work_days)
    return ts


@pytest.fixture(scope="session")
def fake_timesheet_db(employee_user, fake_timesheet):
    for wd in fake_timesheet.work_days:
        wd._insert(employee_user)


@pytest.fixture(scope="session")
def saved_timesheet(employee_user, fake_timesheet, fake_timesheet_db):
    workday_ids = {wd.id for wd in fake_timesheet.work_days}
    fake_timesheet.save(user=employee_user, notes="test", workday_ids=workday_ids)


@pytest.fixture
def app(DB):
    app = create_app()
    if not app.config["TESTING"]:
        raise RuntimeError("TIMECLOCK_TESTING=1 must be set!")
    app.test_client_class = FlaskLoginClient
    yield app
