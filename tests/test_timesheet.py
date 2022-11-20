from timeclock.timesheet import TimeSheet


def test_timesheet_hours(fake_timesheet):
    assert fake_timesheet.hours == 77.5


def test_timesheet_current(employee_user, fake_timesheet_db):
    assert TimeSheet.current(employee_user).hours == 77.5