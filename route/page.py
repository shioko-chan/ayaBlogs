from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    send_from_directory,
    current_app,
    abort,
)
from flask_login import current_user, login_required
from .util import (
    random_image,
    response,
    allowed_file,
    get_config,
    get_extension,
    get_avatar,
    get_digest_for_each,
)
from models import User, Passage
from enum import Enum
from time import time
from math import ceil, floor
from functools import wraps


class statusCode(Enum):
    TooFrequent = 1


def timing(limit=5, interval=30, cooldown_window=5):
    def decorator(func):
        key = f"{func.__name__}_state"

        @wraps(func)
        def wrapper(*args, **kwargs):
            current = time()
            state = session.get(key, {"t": 0.0, "c": 0, "l": current})
            time_remain = state["t"] + interval - current
            if time_remain > 0:
                return response(
                    success=False,
                    code=statusCode.TooFrequent.value,
                    data={"limit": ceil(time_remain)},
                )
            res = func(*args, **kwargs)
            if current - state["l"] <= cooldown_window:
                state["c"] += 1
            if state["c"] >= limit:
                state["t"] = time()
                state["c"] = 0
            state["l"] = current
            session[key] = state
            return res

        return wrapper

    return decorator


page_bp = Blueprint("page", __name__)


@page_bp.context_processor
def inject():
    return {"statusCode": {item.value: item.name for item in statusCode}}


@page_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return "没有文件被上传"

    file = request.files.getlist("file")
    print(file)
    abort(404)
    if file.filename == "":
        return "没有选择文件"

    if file and allowed_file(file.filename):
        # file.save(f"{app.config['UPLOAD_FOLDER']}/{file.filename}")
        print(1)
        return "文件上传成功"

    return "文件类型不被允许"


@page_bp.route("/rest", methods=["GET"])
def rest():
    return render_template("rest.html", random_background=random_image())


@page_bp.route("/editor", methods=["GET"])
def editor():
    return render_template("edi.html", upload_max_size=get_config("UPLOAD_MAX_SIZE"))


@page_bp.route("/", methods=["GET"])
def index():
    if request.args.get("next"):
        iter = session.get("page_gen")
        if iter:
            passages = next(iter, [])
            if not passages:
                session.pop("page_gen")
            return response(success=True, data={"passages": passages})
        else:
            return response(success=False, mes="请求错误")

    order_by = request.args.get("order_by")
    order_direction = request.args.get("order_direction")
    if order_by and order_direction:
        order_by = "time" if order_by.lower() == "time" else "vote_up"
        order_direction = order_direction.upper() == "DESC"
        page_gen = Passage.retrieve_passages_paged(
            25, order_by=order_by, desc=order_direction
        )
    else:
        page_gen = Passage.retrieve_passages_paged(25)

    session["page_gen"] = page_gen

    return render_template(
        "index.html",
        user=current_user,
        passages=next(page_gen, []),
    )


@page_bp.route("/space", methods=["GET"])
def space_index():
    if current_user.is_authenticated:
        return redirect(url_for("page.space", uid=current_user.id))
    else:
        return redirect(url_for("auth.login"))


@page_bp.route("/space/<int:uid>", methods=["GET"])
def space(uid):
    if current_user.is_authenticated and uid == current_user.id:
        is_draft = request.args.get("query") == "draft"
        user = current_user
        is_current_user = True
        avatar = get_avatar(current_user.avatar)
    else:
        is_draft = False
        user = User.get_by_id(uid)
        if user is None:
            abort(404)
        avatar = get_avatar(user.avatar)
        is_current_user = False

    return render_template(
        "space.html",
        user=user,
        passages=Passage.retrieve_passages_by_author_id(user.id, is_draft=is_draft),
        random_background=random_image(),
        avatar=avatar,
        is_draft=is_draft,
        is_current_user=is_current_user,
    )


@page_bp.route("/passage/<int:pid>", methods=["GET"])
def passage(pid):
    pass


@timing(limit=5, interval=30)
def intro_edit(uid):
    intro = request.json["sign"]
    if intro != current_user.intro:
        try:
            User.update_intro(intro, uid)
        except Exception as e:
            current_app.logger.error("In intro_edit, an error occurred: %s", e)
            return response(success=False)
    return response(success=True)


@page_bp.route("/edit/<string:service>/<int:uid>", methods=["POST"])
@page_bp.route("/edit/<string:service>/<int:uid>/<int:item_id>", methods=["POST"])
@login_required
def edit(service, uid, item_id=None):
    if not request.json:
        abort(404)
    if uid != current_user.id:
        abort(404)
    match service:
        case "passage":
            pass
        case "diary":
            pass
        case "question":
            pass
        case "comment":
            pass
        case "answer":
            pass
        case "intro":
            return intro_edit(uid)
        case _:
            abort(404)
    return response(success=True)


@page_bp.route(
    "/delete/<string:service>/<int:uid>/<int:item_id>", methods=["GET", "POST"]
)
@login_required
def delete(service, uid, item_id):
    if uid != current_user.id:
        abort(404)
    match service:
        case "passage":
            Passage.delete_by_id(item_id)
        case "diary":
            pass
        case "question":
            pass
        case "comment":
            pass
        case "answer":
            pass
        case _:
            abort(404)
    return response(success=True)


@page_bp.route("/search", methods=["POST"])
@page_bp.route("/search/user", methods=["POST"])
@timing(limit=10, interval=30, cooldown_window=4)
def search():
    keys = request.json.keys()
    if request.json and "query" in keys and "type" in keys:
        tp = request.json["type"]
        keyword = request.json["query"]
        match tp:
            case "all":
                usrs = User.search_by_username(keyword, topk=10, desc=False)
                passages = Passage.search_by_content(
                    keyword, topk=10, is_draft=False, order_by="vote_up"
                )
                return response(
                    success=True,
                    data={
                        "usrs": get_digest_for_each(usrs, keyword),
                        "passages": get_digest_for_each(passages, keyword),
                    },
                )
            case "user":
                usrs = User.search_by_username(keyword, topk=10, desc=False)
                return response(
                    success=True, data={"usrs": get_digest_for_each(usrs, keyword)}
                )
            case "passage":
                passages = Passage.search_by_content(
                    keyword, topk=10, is_draft=False, order_by="vote_up"
                )
                return response(
                    success=True,
                    data={
                        "passages": get_digest_for_each(passages, keyword),
                    },
                )
            case _:
                return response(success=False, mes="请求错误")

    else:
        return response(success=False, mes="请求错误")
