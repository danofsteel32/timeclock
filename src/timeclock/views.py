"""View functions."""

from flask import abort, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug import Response

from timeclock import timeclock
from timeclock.users import verify_user


def index() -> Response:
    """The main page for timeclock app.

    If `current_user` is anonymous then redirect to login page.
    Return a link to login page if no user logged in.
    """
    if current_user.is_anonymous:
        return redirect(url_for("timeclock.auth.login"))
    clocked_in = bool(timeclock.clocked_in(current_user))
    # if clocked_in: lookup punch_id and return the amount of time clocked in
    return make_response(render_template("index.html", clocked_in=clocked_in))


@login_required
def clock_in() -> Response:
    """Clock the current_user in if not already clocked in.

    Should return a template partial containing the clock in timestamp.
    """
    try:
        punch_id, timestamp = timeclock.clock_in(current_user)
    except timeclock.AlreadyClockedInError:
        abort(400)
    return make_response(render_template("clock_in.html", timestamp=timestamp))


@login_required
def clock_out() -> Response:
    """Clock the current_user out if clocked in.

    Should return a template partial containing the clocked in length.
    Or maybe redirect to timesheet.
    """
    try:
        punch_id, timestamp = timeclock.clock_out(current_user)
    except timeclock.NotClockedInError:
        abort(400)
    return make_response(render_template("clock_out.html", timestamp=timestamp))


@login_required
def timesheet() -> Response:
    """Show detailed timesheet info.

    I think it needs to take a query param for start_date.
    """
    if not current_user.is_anonymous:
        redirect(url_for("timeclock.auth.login"))
    return make_response(render_template("timesheet.html"))


def login() -> Response:
    """Log the user in."""
    if request.method == "GET":
        return make_response(render_template("login.html"))

    if not request.json:
        abort(400)
    email = request.json.get("email", None)
    unhashed_password = request.json.get("unhashed_password", None)
    if not email and unhashed_password:
        abort(400)
    try:
        user = verify_user(email, unhashed_password)
    except ValueError:
        abort(401)
    login_user(user)
    return redirect(url_for("timeclock.index"))


@login_required
def logout() -> Response:
    """TODO what happens when current_user is anonymous?"""
    logout_user()
    return redirect(url_for("timeclock.auth.login"))
