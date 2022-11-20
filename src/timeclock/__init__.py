import os
from pathlib import Path
from typing import Optional

from flask import Blueprint, Flask
from flask_login import LoginManager

from . import views
from .db import create_db
from .users import User


def create_app() -> Flask:
    """Create and apply all configuration to the flask application object.

    Config is loaded from environment vars. I use 'TIMECLOCK_' as the
    prefix/namespace instead of 'FLASK_' because I will sometimes run multiple
    flask apps on the same host and want to avoid any collisions.
    """
    FAKE_SECRET_KEY = "fake-secret-key"
    app = Flask(__name__)
    app.config["TESTING"] = bool(os.getenv("TIMECLOCK_TESTING", False))
    if app.config["TESTING"]:
        app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = os.getenv("TIMECLOCK_SECRET_KEY", FAKE_SECRET_KEY)
    db_file = Path(os.getenv("TIMECLOCK_DB", "test.db"))

    # Do not continue if not in DEBUG and a real secret key has not been set
    if not app.config["DEBUG"] and app.config["SECRET_KEY"] == FAKE_SECRET_KEY:
        raise RuntimeError("TIMECLOCK_SECRET_KEY must be set!")

    # Create sqlite3 database if not exists and not in TESTING mode.
    if not db_file.exists() and not app.config["TESTING"]:
        create_db(db_file)

    # Blueprints
    timeclock = Blueprint(
        "timeclock",
        __name__,
        template_folder="templates",
        static_folder="static",
        url_prefix="/timeclock",
    )
    workday = Blueprint(
        "workday",
        __name__,
        template_folder="workday",
        static_folder="static",
        url_prefix="/workday",
    )
    auth = Blueprint(
        "auth",
        __name__,
        template_folder="templates",
        static_folder="static",
        url_prefix="/auth",
    )

    # Plugins
    login_manager = LoginManager()
    login_manager.login_view = "timeclock.auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        """Needed by flask-login. Must return None if no User."""
        try:
            return User.get(user_id)
        except Exception as exc:
            print(exc)
            return None

    # Routes
    timeclock.add_url_rule(
        "/", view_func=views.index, methods=["GET"], strict_slashes=False
    )
    timeclock.add_url_rule("/clock_in", view_func=views.clock_in, methods=["PUT"])
    timeclock.add_url_rule("/clock_out", view_func=views.clock_out, methods=["POST"])
    timeclock.add_url_rule(
        "/timesheet", view_func=views.current_timesheet, methods=["GET"]
    )
    timeclock.add_url_rule(
        "/timesheet", view_func=views.save_timesheet, methods=["POST"]
    )
    timeclock.add_url_rule(
        "/timesheet/<int:id>", view_func=views.timesheet, methods=["GET"]
    )
    timeclock.add_url_rule(
        "/timesheet/overview", view_func=views.overview, methods=["GET"]
    )

    workday.add_url_rule("/<int:id>", view_func=views.get_workday, methods=["GET"])
    workday.add_url_rule("/<int:id>", view_func=views.update_workday, methods=["POST"])
    workday.add_url_rule("/select", view_func=views.select_workday, methods=["POST"])
    workday.add_url_rule(
        "/<int:id>/notes", view_func=views.workday_notes, methods=["POST"]
    )
    workday.add_url_rule(
        "/<int:id>/photo", view_func=views.upload_photo, methods=["PUT"]
    )
    workday.add_url_rule(
        "/<int:id>/photo", view_func=views.delete_photo, methods=["DELETE"]
    )

    auth.add_url_rule("/login", view_func=views.login, methods=["GET", "POST"])
    auth.add_url_rule("/logout", view_func=views.logout, methods=["GET"])

    timeclock.register_blueprint(auth)
    timeclock.register_blueprint(workday)
    app.register_blueprint(timeclock)

    return app
