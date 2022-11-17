from flask import Flask
from flask_login import LoginManager

from timeclock.routes import init_routes

__version__ = "0.1.0"


def create_app(config: str = "dev") -> Flask:
    app = Flask(__name__)
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    init_routes(app, login_manager)
    return app
