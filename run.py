from pathlib import Path
from passlib import pwd
from flask import Flask, render_template, abort, send_from_directory, request
from flask_cors import CORS
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
from models import ConnectionPool, User

import os, tomllib, logging

if __name__ == "__main__":
    config_path = os.getenv("CONFIG_PATH")
    config = tomllib.load(open(config_path, "rb"))

    MAIL_SERVER = config["mail"]["server"]
    MAIL_USER = config["mail"]["user"]
    MAIL_PASSWORD = config["mail"]["password"]
    MAIL_PORT = config["mail"]["port"]
    MAIL_SEND_INTERVAL = config["mail"]["mail_send_interval"]

    STATIC_FOLDER = config["storage"]["static_folder"]
    BACKGROUND_FOLDER = config["storage"]["background_folder"]
    AVATAR_FOLDER = config["storage"]["avatar_folder"]
    IMAGE_FOLDER = config["storage"]["image_folder"]
    ES_MODULE_FOLDER = config["storage"]["es_module_folder"]
    ALLOWED_EXTENSIONS = config["storage"]["allowed_extensions"]

    SESSION_TYPE = config["session"]["session_type"]
    SESSION_DIR = config["session"]["session_dir"]

    DB_SERVER = config["database"]["server"]
    DB_USER = config["database"]["user"]
    DB_PASSWORD = config["database"]["password"]
    DB_NAME = config["database"]["name"]

    SECRET_KEY = config["recaptcha"]["secret_key"]
    SITE_KEY = config["recaptcha"]["site_key"]
    RECAPTCHA_INTERVAL = config["recaptcha"]["recaptcha_interval"]
    RECAPTCHA_MAX_RETRY = config["recaptcha"]["max_retry_without_interval"]

    CODE_MAX_RETRY = config["code"]["max_retry"]

    app = Flask(__name__, static_folder=None)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

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

    app.config.update(
        SESSION_TYPE=SESSION_TYPE,
        SESSION_FILE_DIR=SESSION_DIR,
    )

    app.config.update(
        SECRET_KEY=SECRET_KEY,
        SITE_KEY=SITE_KEY,
        RECAPTCHA_INTERVAL=RECAPTCHA_INTERVAL,
        RECAPTCHA_MAX_RETRY=RECAPTCHA_MAX_RETRY,
    )

    app.config.update(
        CODE_MAX_RETRY=CODE_MAX_RETRY,
    )

    AVATAR_FOLDER = Path(AVATAR_FOLDER)
    IMAGE_FOLDER = Path(IMAGE_FOLDER)
    ES_MODULE_FOLDER = Path(ES_MODULE_FOLDER)
    STATIC_FOLDER = Path(STATIC_FOLDER)
    BACKGROUND_FOLDER = Path(BACKGROUND_FOLDER)

    AVATAR_FOLDER.mkdir(exist_ok=True)
    IMAGE_FOLDER.mkdir(exist_ok=True)

    backgrounds = [file.name for file in BACKGROUND_FOLDER.iterdir() if file.is_file()]

    app.config.update(
        BKG=backgrounds,
        ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS,
    )

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    @app.context_processor
    def lang():
        user_language = request.accept_languages.best_match(["en", "zh"]) or "en"
        return {"lang": user_language}

    CORS(app)

    ConnectionPool(app)

    Mail(app)

    Session(app)

    register_bp(app)

    @app.errorhandler(404)
    def page_not_found(error):
        return (
            render_template(
                "404.html", insert="<script>alert('fucking inserted')</script>"
            ),
            404,
        )

    @app.route("/static/<string:service>/<path:filename>", methods=["GET"])
    def static(service, filename):
        match service:
            case "bkg":
                return send_from_directory(
                    BACKGROUND_FOLDER, filename, mimetype="image/png"
                )
            case "js":
                return send_from_directory(
                    STATIC_FOLDER / "js",
                    filename,
                    mimetype="application/javascript",
                )
            case "css":
                return send_from_directory(
                    STATIC_FOLDER / "css", filename, mimetype="text/css"
                )
            case "image":
                return send_from_directory(IMAGE_FOLDER, filename)
            case "avatar":
                return send_from_directory(
                    AVATAR_FOLDER, filename, mimetype="image/png"
                )
            case "es_module":
                return send_from_directory(
                    ES_MODULE_FOLDER,
                    filename,
                    mimetype="application/javascript",
                )
            case "default":
                return send_from_directory(
                    STATIC_FOLDER / "default",
                    filename,
                    mimetype="image/png",
                )
            case _:
                abort(404)

    app.run(debug=True)
