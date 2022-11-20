"""Create the initial users in the database."""
import os
from pathlib import Path

import pendulum

from timeclock import users
from timeclock.db import create_db
from timeclock.timesheet import TimeSheet  # , _manual_add_timesheet
from timeclock.workday import WorkDay

DB_FILE = Path(os.getenv("TIMECLOCK_DB", "test.db"))
create_db(DB_FILE)


USERS = [
    users.register_user(
        email="dan@dandavis.dev",
        unhashed_password="Coffee32",
        role=users.Role.ADMIN,
        username="duke",
    ),
    users.register_user(
        email="jerry@chamberlainbuildersllc.com",
        unhashed_password="password",
        role=users.Role.OWNER,
        username="jdawg",
    ),
    users.register_user(
        email="dan@chamberlainbuildersllc.com",
        unhashed_password="Coffee32",
        role=users.Role.EMPLOYEE,
        username="danofsteel32",
    ),
]

TIMESHEET = TimeSheet(
    work_days=[
        WorkDay(
            pendulum.local(2022, 11, day, 9),
            pendulum.local(2022, 11, day, 17),
            notes=f"did {n} things",
        )
        for n, day in enumerate(range(14, 19))
    ]
)

print(TIMESHEET)
for wd in TIMESHEET.work_days:
    wd._insert(USERS[2])
