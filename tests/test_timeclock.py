import pytest

from timeclock import timeclock


def test_clock_in_but_already_clocked_in(employee_user, employee_workday):
    with pytest.raises(timeclock.AlreadyClockedInError):
        timeclock.clock_in(employee_user)


def test_clock_out_but_not_clocked_in(employee_user):
    with pytest.raises(timeclock.NotClockedInError):
        timeclock.clock_out(employee_user)


def test_clock_out(employee_user, employee_workday):
    assert timeclock.clock_out(employee_user) == employee_workday.id


def test_clocked_in(employee_user, employee_workday):
    assert timeclock.clocked_in(employee_user) is True
