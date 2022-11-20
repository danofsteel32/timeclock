from timeclock.workday import WorkDay


def test_workday_current_for_user(employee_user, employee_workday):
    wd = WorkDay.current(employee_user)
    assert wd.id == employee_workday.id
    assert wd.clock_in == employee_workday.clock_in


def test_workday_from_id(employee_workday):
    wd = WorkDay.from_id(employee_workday.id)
    assert wd.id == employee_workday.id
    assert wd.clock_in == employee_workday.clock_in


def test_workday_update_notes(employee_workday):
    employee_workday.update_notes("new notes")
    assert employee_workday.notes == "new notes"
