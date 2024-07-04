from pathlib import Path
from passlib import pwd
import tomllib
from flask import Flask
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_mail import Message, Mail
from flask_session import Session

from route import register_bp


if __name__ == "__main__":
    config = tomllib.load(open("config.toml", "rb"))

    MAIL_SERVER = config["mail"]["server"]
    MAIL_USER = config["mail"]["user"]
    MAIL_PASSWORD = config["mail"]["password"]
    MAIL_PORT = config["mail"]["port"]
    MAIL_SEND_INTERVAL = config["mail"]["mail_send_interval"]

    UPLOAD_FOLDER = config["image"]["upload_folder"]
    ALLOWED_EXTENSIONS = config["image"]["allowed_extensions"]
    SESSION_TYPE = config["session"]["type"]

    app = Flask(__name__)
    app.secret_key = pwd.genword(entropy="secure", charset="ascii_72")

    app.config.update(
        MAIL_SERVER=MAIL_SERVER,
        MAIL_USERNAME=MAIL_USER,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_USE_SSL=True,
        MAIL_USE_TLS=False,
        MAIL_PORT=MAIL_PORT,
    )

    app.config.update(SESSION_TYPE=SESSION_TYPE)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    mail = Mail(app)

    Session(app)

    save_path = Path(UPLOAD_FOLDER)
    save_path.mkdir(exist_ok=True)
    backgrounds = [file for file in Path("static/bkg").iterdir() if file.is_file()]

    app = register_bp()

    app.run(debug=True)
