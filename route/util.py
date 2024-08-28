from flask import jsonify, current_app, url_for
from random import choice
from models import Passage


def response(success, mes=None, code=0, data=None):
    return jsonify({"success": success, "message": mes, "code": code, "data": data})


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def random_image():
    return url_for(
        "static",
        filename="bkg/" + choice(current_app.config["BKG"]).name,
    )


def get_config(key, default=None):
    return current_app.config.get(key, default)


def get_extension(key, default=None):
    return current_app.extensions.get(key, default)


def get_articles(num, order="latest"):
    if order == "latest":
        return Passage.get_latest(num)
    elif order == "hottest":
        return Passage.get_hottest(num)
    else:
        raise NotImplementedError
