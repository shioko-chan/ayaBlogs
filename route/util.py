from flask import jsonify, current_app, url_for, abort, session
from random import choice
from models import Passage, Avatar, User
from typing import Optional, Union


def response(success, mes=None, code=0, data=None):
    return jsonify({"success": success, "message": mes, "code": code, "data": data})


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in get_config(
        "ALLOWED_EXTENSIONS"
    )


def random_image():
    return url_for(
        "static",
        service="bkg",
        filename=choice(get_config("BKG")),
    )


def get_avatar(avatar_id: Optional[int]):
    if not avatar_id:
        return url_for("static", service="default", filename="avatar.jpg")
    avatar = Avatar.get_by_id(avatar_id)
    return url_for("static", service="avatar", filename=f"{avatar.uuid}.jpg")


def get_config(key, default=None):
    return current_app.config.get(key, default)


def get_extension(key, default=None):
    return current_app.extensions.get(key, default)


def get_digest(obj: Union[User, Passage], keyword):
    match obj:
        case User(username=username, id=id):
            return {
                "url": url_for("page.space", uid=id),
                "content": username,
            }
        case Passage(content=content, id=id):
            start = max(content.find(keyword) - 5, 0)
            end = start + len(keyword) + 100
            return {
                "url": url_for("page.passage", pid=id),
                "content": content[start:end],
            }
        case _:
            raise ValueError("Unsupported Type")


def get_digest_for_each(li, keyword):
    return [get_digest(item, keyword) for item in li]
