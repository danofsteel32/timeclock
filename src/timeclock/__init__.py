from flask import Blueprint, Flask
from flask_login import LoginManager

from timeclock.routes import init_routes

__version__ = "0.1.0"


app = Flask(__name__)

timeclock = Blueprint(
    "timeclock", __name__, template_folder="templates", url_prefix="/timeclock"
)
auth = Blueprint("auth", __name__, template_folder="templates", url_prefix="/auth")
timeclock.register_blueprint(auth)
app.register_blueprint(timeclock)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

# init_routes(app, login_manager)
