import pendulum

from timeclock.workday import Photo, WorkDay, get_photos


def test_photo_new_and_delete(DB):
    photo = Photo.new(filename="test-photo.jpeg")
    assert isinstance(photo, Photo)
    assert photo.delete() is True


def test_workday_current_for_user(employee_user, employee_workday):
    wd = WorkDay.current(employee_user)
    assert wd.id == employee_workday.id
    assert wd.clock_in == employee_workday.clock_in


def test_workday_from_id(employee_workday):
    wd = WorkDay.from_id(employee_workday.id)
    assert wd.id == employee_workday.id
    assert wd.clock_in == employee_workday.clock_in


def test_workday_user_id(employee_user, employee_workday):
    assert employee_user.user_id == employee_workday.user_id


def test_workday_date(employee_workday):
    assert employee_workday.date == pendulum.now().date()


def test_workday_hours():
    clock_in = pendulum.datetime(2022, 1, 1, 8)
    clock_out = pendulum.datetime(2022, 1, 1, 16, 16)
    workday = WorkDay(clock_in, clock_out)
    assert workday.hours == 8.25


def test_workday_archived_false(employee_workday):
    assert employee_workday.archived is False


def test_workday_archived_true(fake_timesheet, saved_timesheet):
    workday = fake_timesheet.work_days.pop()
    assert workday.archived is True


def test_workday_update_notes(employee_workday):
    employee_workday.update_notes("new notes")
    assert employee_workday.notes == "new notes"


def test_workday_update(employee_workday):
    employee_workday.notes = "new new notes"
    employee_workday.update()
    workday = WorkDay.from_id(employee_workday.id)
    assert workday.notes == "new new notes"


def test_workday_add_photo_and_get_photos(employee_workday):
    pic1 = employee_workday.add_photo("pic1.jpeg")
    pic2 = employee_workday.add_photo("pic2.jpeg")
    p1, p2 = get_photos(employee_workday.id)
    assert pic1 == p1
    assert pic2 == p2
    p1.delete()
    p2.delete()
