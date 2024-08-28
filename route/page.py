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
)
from .util import (
    random_image,
    get_articles,
    response,
    allowed_file,
    get_config,
    get_extension,
)
from models import Usr, Passage

page_bp = Blueprint("page", __name__)


@page_bp.route("/rest", methods=["GET"])
def rest():
    return render_template("rest.html", random_background=random_image())


@page_bp.route("/editor", methods=["GET"])
def editor():
    return render_template("edi.html")


@page_bp.route("/", methods=["GET"])
def index():
    user = session.get("user")
    return render_template(
        "index.html",
        user=user,
        is_authenticated=user is not None,
        articles=get_articles(10),
        is_user_page=False,
    )


@page_bp.route("/mainpage/<username>", methods=["GET"])
def mainpage(username):
    user = session.get("user")
    if not (user is not None and user.uname == username):
        uid = query_database("select uid from usr where uname=%s", params=(username,))[
            0
        ]
    else:
        uid = user.uid
    return render_template(
        "index.html",
        user=user,
        mainpage_user=username,
        is_authenticated=user is not None,
        articles=get_articles(
            condition="where author=%d",
            params=(uid,),
        ),
        is_user_page=True,
    )


@page_bp.route("/search", methods=["POST"])
def search():
    if request.json and "query" in request.json.keys():
        keyword = request.json["query"]
        usrs = Usr.search_by_username(keyword)
        articles = Passage.search_by_content(keyword) + Passage.search_by_title(keyword)
        return jsonify({"usrs": usrs, "articles": articles})
    else:
        return response(success=False, mes="请求错误")
