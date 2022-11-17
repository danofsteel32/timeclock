"""Configure url routing."""

from typing import Optional

from flask import Blueprint, Flask
from flask_login import LoginManager

from timeclock.users import User


def init_routes(app: Flask, login_manager: LoginManager) -> None:
    """Setup Blueprint's and assign url routes and pemissions."""
    from timeclock import views

    # /timeclock
    timeclock = Blueprint(
        "timeclock",
        __name__,
        template_folder="templates",
        static_folder="static",
        url_prefix="/timeclock",
    )
    # /timeclock/auth
    auth = Blueprint(
        "auth",
        __name__,
        template_folder="templates",
        static_folder="static",
        url_prefix="/auth",
    )

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        """Needed by flask-login. Must return None if no User."""
        try:
            return User.get(user_id)
        except Exception as exc:
            print(exc)
            return None

    timeclock.add_url_rule("/", view_func=views.index, methods=["GET"])
    timeclock.add_url_rule("/clock_in", view_func=views.clock_in, methods=["PUT"])
    timeclock.add_url_rule("/clock_out", view_func=views.clock_out, methods=["PUT"])
    timeclock.add_url_rule("/timesheet", view_func=views.timesheet, methods=["GET"])

    auth.add_url_rule("/login", view_func=views.login, methods=["GET", "POST"])
    auth.add_url_rule("/logout", view_func=views.logout, methods=["POST"])

    timeclock.register_blueprint(auth)
    app.register_blueprint(timeclock)
    return None
