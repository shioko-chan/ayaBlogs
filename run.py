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
from models import ConnectionPool, Usr

if __name__ == "__main__":
    config = tomllib.load(open("config.toml", "rb"))

    MAIL_SERVER = config["mail"]["server"]
    MAIL_USER = config["mail"]["user"]
    MAIL_PASSWORD = config["mail"]["password"]
    MAIL_PORT = config["mail"]["port"]
    MAIL_SEND_INTERVAL = config["mail"]["mail_send_interval"]

    UPLOAD_FOLDER = config["image"]["upload_folder"]
    ALLOWED_EXTENSIONS = config["image"]["allowed_extensions"]
    SESSION_TYPE = config["session"]["session_type"]

    DB_SERVER = config["database"]["server"]
    DB_USER = config["database"]["user"]
    DB_PASSWORD = config["database"]["password"]
    DB_NAME = config["database"]["name"]

    SECRET_KEY = config["recaptcha"]["secret_key"]
    SITE_KEY = config["recaptcha"]["site_key"]

    CODE_MAX_RETRY = config["code"]["max_retry"]

    app = Flask(__name__)
    app.secret_key = pwd.genword(entropy="secure", charset="ascii_72")

    app.config.update(
        MAIL_SERVER=MAIL_SERVER,
        MAIL_USERNAME=MAIL_USER,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_USE_SSL=True,
        MAIL_USE_TLS=False,
        MAIL_PORT=MAIL_PORT,
        MAIL_SEND_INTERVAL=MAIL_SEND_INTERVAL,
    )

    app.config.update(
        DB_SERVER=DB_SERVER,
        DB_USER=DB_USER,
        DB_PASSWORD=DB_PASSWORD,
        DB_NAME=DB_NAME,
    )

    app.config.update(SESSION_TYPE=SESSION_TYPE)

    app.config.update(
        SECRET_KEY=SECRET_KEY,
        SITE_KEY=SITE_KEY,
    )

    app.config.update(
        CODE_MAX_RETRY=CODE_MAX_RETRY,
    )

    save_path = Path(UPLOAD_FOLDER)
    save_path.mkdir(exist_ok=True)
    backgrounds = [file for file in Path("static/bkg").iterdir() if file.is_file()]

    app.config.update(BKG=backgrounds)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return Usr.get_by_id(user_id)

    ConnectionPool(app)

    Mail(app)

    Session(app)

    register_bp(app)

    app.run(debug=True)
