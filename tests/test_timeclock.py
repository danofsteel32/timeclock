import pytest

from timeclock import timeclock


def test_clock_in_but_already_clocked_in(existing_user, punched_in):
    with pytest.raises(timeclock.AlreadyClockedInError):
        timeclock.clock_in(existing_user)


def test_clock_out_but_not_clocked_in(existing_user):
    with pytest.raises(timeclock.NotClockedInError):
        timeclock.clock_out(existing_user)


def test_clock_out(existing_user, punched_in):
    timeclock.clock_out(existing_user)


def test_clocked_in(existing_user, punched_in):
    expected_punch_id, _ = punched_in
    assert expected_punch_id == timeclock.clocked_in(existing_user)


def test_timesheet_hours(fake_timesheet):
    assert fake_timesheet.hours == 77.5


def test_timesheet_from_db(fake_timesheet):
    timeclock._manual_add_timesheet(fake_timesheet)
    timesheet = timeclock.TimeSheet.from_db(
        fake_timesheet.user, fake_timesheet.start_date
    )
    assert (timesheet.start_date, timesheet.hours) == (
        fake_timesheet.start_date,
        fake_timesheet.hours,
    )
