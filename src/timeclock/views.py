"""View functions."""
from typing import Tuple

import pendulum
from flask import abort, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug import Response

from . import timeclock
from .timesheet import TimeSheet, get_overview, get_past_timesheets
from .users import Role, User, verify_user
from .workday import WorkDay

# returning a html string and status code
PartialResponse = Tuple[str, int]


def index() -> Response:
    """The main page for timeclock app.

    If `current_user` is anonymous then redirect to login page.
    Return a link to login page if no user logged in.
    """
    if current_user.is_anonymous:
        return redirect(url_for("timeclock.auth.login"))

    if current_user.role == Role.OWNER:
        return redirect(url_for("timeclock.overview"))
    elif current_user.role == Role.EMPLOYEE:
        clocked_in = timeclock.clocked_in(current_user)
        unpaid_hours = 0.0
        ytd_hours = 0.0
        if clocked_in:
            workday = WorkDay.current(current_user)
        else:
            workday = None
        rendered = render_template(
            "index.html",
            unpaid_hours=unpaid_hours,
            ytd_hours=ytd_hours,
            clocked_in=clocked_in,
            workday=workday,
        )
        return make_response(rendered)
    else:
        abort(400)


@login_required
def clock_in() -> PartialResponse:
    """Clock the current_user in if not already clocked in.

    Notes:
        - Creates a new WorkDay
    """
    try:
        workday = timeclock.clock_in(current_user)
    except timeclock.AlreadyClockedInError:
        abort(400)
    return render_template("clock_in_partial.html", workday=workday), 201


@login_required
def clock_out() -> PartialResponse:
    """Clock the current_user out if clocked in."""
    try:
        timeclock.clock_out(current_user)
    except timeclock.NotClockedInError:
        abort(400)
    clock_in_url = url_for("timeclock.clock_in")
    return (
        f"""
    <button
      hx-swap="innerHTML"
      hx-target="#current_clock_state"
      hx-put="{clock_in_url}">CLOCK IN</button>
    """,
        200,
    )


@login_required
def current_timesheet() -> Response:
    """Show the current timesheet for the user."""
    try:
        user_id = request.args.get("user_id")
        user = User.get(user_id)
    except (KeyError, ValueError):
        abort(400)

    ts = TimeSheet.current(user)
    past_timesheets = get_past_timesheets(user)
    if current_user.role == Role.OWNER:
        return make_response(
            render_template(
                "owner_current_timesheet.html",
                timesheet=ts,
                user=user,
                past_timesheets=past_timesheets,
            )
        )
    # Trying to view a user don't have permission for
    if current_user.id != user_id:
        abort(403)
    return make_response(
        render_template(
            "current_timesheet.html", timesheet=ts, past_timesheets=past_timesheets
        )
    )


@login_required
def timesheet(id: int) -> Response:
    """Show detailed timesheet info."""
    ts = TimeSheet.from_id(id)
    # check current_user has permission to view
    return make_response(render_template("timesheet.html", timesheet=ts))


@login_required
def overview() -> Response:
    if current_user.role != Role.OWNER:
        abort(403)
    employees = get_overview()
    return make_response(render_template("overview.html", employees=employees))


@login_required
def get_workday(id: int) -> Response:
    wd = WorkDay.from_id(id)
    # check that user has permission to edit
    if wd.user_id != current_user.user_id and current_user.role != Role.OWNER:
        abort(403)
    # check that id is not in timesheet_workday (archived)
    edit = False if wd.archived else True
    return make_response(render_template("workday.html", workday=wd, edit=edit))


@login_required
def update_workday(id: int) -> PartialResponse:
    """Update the workday from the posted form."""
    wd = WorkDay.from_id(id)
    # check that user has permission to edit
    if wd.user_id != current_user.user_id and current_user.role != Role.OWNER:
        abort(403)
    # check that id is not in timesheet_workday (archived)
    if wd.archived:
        abort(403)

    print(request.json)

    def parse_time(key: str) -> pendulum.DateTime:
        """Go from 08:00AM -> a datetime."""
        posted = pendulum.parse(request.json.get(key))
        original = wd.__getattribute__(key)
        return pendulum.local(
            original.year, original.month, original.day, posted.hour, posted.minute
        )

    clock_in, clock_out = parse_time("clock_in"), parse_time("clock_out")
    new_wd = WorkDay(
        id=id,
        clock_in=clock_in,
        clock_out=clock_out,
        notes=request.json["notes"],
    )
    new_wd.update()
    return render_template("alert.html", msg="Success"), 200


@login_required
def select_workday() -> PartialResponse:
    if current_user.role != Role.OWNER:
        abort(403)
    user_id = request.json.get("user_id")
    timesheet = TimeSheet.current(User.get(user_id))

    workday_ids = set()
    for key in request.json:
        try:
            workday_ids.add(int(key))
        except (TypeError, ValueError):
            continue

    hours = 0.0
    for wd in timesheet.work_days:
        if wd.id in workday_ids:
            hours += wd.hours

    return (
        f'<h3 id="hours_selected" hx-swap-oob="true">Hours Selected: {hours}</h3>',
        200,
    )


@login_required
def workday_notes(id: int) -> PartialResponse:
    wd = WorkDay.from_id(id)
    wd.update_notes(request.json["notes"])
    return render_template("alert.html", msg="Success"), 200


@login_required
def save_timesheet() -> Response:
    if current_user.role != Role.OWNER:
        abort(403)
    user_id = request.json.get("user_id")
    user = User.get(user_id)
    notes = request.json.get("notes")
    timesheet = TimeSheet.current(user)

    workday_ids = set()
    for key in request.json:
        try:
            workday_ids.add(int(key))
        except (TypeError, ValueError):
            continue

    timesheet.save(user, notes, workday_ids)
    resp = make_response("")
    resp.status_code = 201
    resp.headers["HX-Refresh"] = "true"
    return resp


@login_required
def upload_photo() -> Response:
    abort(400)


@login_required
def delete_photo() -> Response:
    abort(400)


def login() -> Response:
    """Log the user in."""
    if request.method == "GET":
        return make_response(render_template("login.html"))

    if not request.form:
        abort(400)
    email = request.form.get("email", None)
    unhashed_password = request.form.get("unhashed_password", None)
    if not email and unhashed_password:
        abort(400)
    try:
        user = verify_user(email, unhashed_password)
    except ValueError:
        abort(401)
    login_user(user)
    resp = redirect(url_for("timeclock.index"))
    resp.headers["HX-Redirect"] = url_for("timeclock.index")
    resp.headers["HX-Refresh"] = "true"
    return resp


@login_required
def logout() -> Response:
    """TODO what happens when current_user is anonymous?"""
    logout_user()
    return redirect(url_for("timeclock.auth.login"))
