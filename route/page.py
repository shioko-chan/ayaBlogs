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


page_bp = Blueprint("page", __name__)


@page_bp.route("/rest", methods=["GET"])
def rest():
    return render_template("rest.html", random_background=random_image())


@page_bp.route("/editor", methods=["GET"])
def editor():
    return render_template("editor.html")


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
        order_by = "time" if order_by.lower() == "time" else "heat"
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


@page_bp.route("/userprofile/edit/<int:uid>", methods=["POST"])
@login_required
def edit_user_profile(uid):
    if uid == current_user.id and request.json:
        intro = request.json["sign"]
        User.update_intro(intro, uid)
        return response(success=True)
    abort(404)


@page_bp.route("/delete/<int:uid>/<int:pid>", methods=["POST"])
@login_required
def delete(uid, pid):
    if uid == current_user.id:
        Passage.delete_by_id(pid)
        return response(success=True)
    abort(404)


@page_bp.route("/search", methods=["POST"])
def search():
    keys = request.json.keys()
    if request.json and "query" in keys and "type" in keys:
        tp = request.json["type"]
        keyword = request.json["query"]
        match tp:
            case "all":
                usrs = User.search_by_username(keyword, topk=10, desc=False)
                passages = Passage.search_by_content(
                    keyword, topk=10, is_draft=False, order_by="heat"
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
                    keyword, topk=10, is_draft=False, order_by="heat"
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


@page_bp.route("/edit")
def edit():
    pass
