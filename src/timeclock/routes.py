from typing import Optional

from flask import Flask
from flask_login import LoginManager

from timeclock.users import User


def init_routes(app: Flask, login_manager: LoginManager) -> None:

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        try:
            return User.get(user_id)
        except Exception as exc:
            print(exc)
            return None
    return None