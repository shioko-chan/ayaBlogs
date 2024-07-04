from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    send_from_directory,
)


from models import Usr, Passage, Announcement, Vote, OptionItem, Comment


import tomllib
import random
import time
import secrets


from utilities import response, check_email_service, hash_password


@app.route("/storage/<filename>")
def storage(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/")
def index():
    user = session.get("user")
    return render_template(
        "index.html",
        user=user,
        is_authenticated=user is not None,
        articles=get_articles(),
        is_user_page=False,
    )


@app.route("/mainpage/<username>")
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


@app.route("/search/<username>", methods=["POST"])
def search_in_user(username):
    if request.form:
        keyword = request.form["search"]
        user = session.get("user")
        return render_template(
            "index.html",
            is_authenticated=user is not None,
            search_user=[
                {
                    "uname": uname,
                    "uemail": uemail,
                    "ubirthday": ubirthday,
                    "usex": usex,
                    "uintro": uintro,
                }
                for uname, uemail, ubirthday, usex, uintro in query_database(
                    "select uname,uemail,ubirthday,usex,uintro from usr where uname like %s or uemail like %s",
                    params=("%" + keyword + "%",) * 2,
                )
            ],
            articles=get_articles(
                "where title like %s or content like %s",
                ("%" + keyword + "%",) * 2,
            ),
        )
    else:
        if request.json and "query" in request.json.keys():
            keyword = request.json["query"]
            usrs = query_database(
                "select uname from usr where uname like %s union select uemail from usr where uemail like %s",
                params=("%" + keyword + "%",) * 2,
            )
            articles = query_database(
                "select title from passage where title like %s union select content from passage where content like %s",
                params=("%" + keyword + "%",) * 2,
            )
            return jsonify({"usrs": usrs, "articles": articles})
        else:
            return "request unknown", 400


@app.route("/search", methods=["POST"])
def search():
    if request.form:
        keyword = request.form["search"]
        user = session.get("user")
        return render_template(
            "index.html",
            user=user,
            is_authenticated=user is not None,
            search_user=[
                {
                    "uname": uname,
                    "uemail": uemail,
                    "ubirthday": ubirthday,
                    "usex": usex,
                    "uintro": uintro,
                }
                for uname, uemail, ubirthday, usex, uintro in query_database(
                    "select uname,uemail,ubirthday,usex,uintro from usr where uname like %s or uemail like %s",
                    params=("%" + keyword + "%",) * 2,
                )
            ],
            articles=get_articles(
                "where title like %s or content like %s",
                ("%" + keyword + "%",) * 2,
            ),
        )
    else:
        if request.json and "query" in request.json.keys():
            keyword = request.json["query"]
            usrs = query_database(
                "select uname from usr where uname like %s union select uemail from usr where uemail like %s",
                params=("%" + keyword + "%",) * 2,
            )
            articles = query_database(
                "select title from passage where title like %s union select content from passage where content like %s",
                params=("%" + keyword + "%",) * 2,
            )
            return jsonify({"usrs": usrs, "articles": articles})
        else:
            return "request unknown", 400


@app.route("/editor", methods=["GET", "POST"])
def editor():
    user = session.get("user")
    return render_template(
        "editor.html",
        random_background=random_image(),
        user=user,
        is_authenticated=user is not None,
    )


@app.route("/veditor")
def veditor():
    user = session.get("user")
    return render_template(
        "veditor.html",
        random_background=random_image(),
        user=user,
        is_authenticated=user is not None,
    )


@app.route("/publish", methods=["POST"])
def publish():
    if request.form:
        user = session.get("user")
        if not user:
            return jsonify({"status": "unauthorized"})
        title = request.form["title"]
        content = request.form["content"]
        article_id = query_database(
            """declare @pid bigint;
                exec insertarticle @title=%s,@content=%s,@author=%s,@pid=@pid output;
                select @pid as pid;""",
            params=(title, content, user.uid),
        )[0][0]
        print(request.files)
        if "images" in request.files:
            images = request.files.getlist("images")
            image_descriptions = request.form.getlist("imageDescriptions[]")

            saved_files = []
            for idx, image in enumerate(images):
                if image.filename == "":
                    continue
                if allowed_file(image.filename):
                    filename = image.filename
                    image_path = save_path / filename
                    image.save(image_path)
                    description = (
                        image_descriptions[idx]
                        if idx < len(image_descriptions)
                        and len(image_descriptions[idx]) != 0
                        else filename
                    )
                    query_database(
                        "insert into image(imgname,containBy,describe) values(%s,convert(bigint,%s),%s)",
                        returns=False,
                        params=(filename, article_id, description),
                    )
                else:
                    flash("图片错误！", "success")
                    return redirect(request.referrer or url_for("index"))

    flash("提交成功！", "success")
    return redirect(url_for("mainpage", username=user.uname) or url_for("index"))


@app.route("/article/<int:pid>")
def article(pid):
    user = session.get("user")
    return render_template(
        "article.html",
        random_background=random_image(),
        user=user,
        article=get_articles("where pid=%d", (pid,))[0],
        is_authenticated=user is not None,
    )


@app.route("/mainpage/<username>/management")
def manage(username):
    user = session.get("user")
    if not user or user.uname != username:
        return redirect(url_for("index"))

    passages = query_database(
        "select * from passage where author=%d", params=(user.uid,)
    )
    announcements = query_database(
        "select * from announcement where author=%d", params=(user.uid,)
    )
    polls = query_database("select * from vote where creator=%d", params=(user.uid,))
    images = query_database("select * from image where ownedBy=%d", params=(user.uid,))
    user = query_database("select * from usr where uid=%d", params=(user.uid,))
    return render_template(
        "manage.html",
        passages=[
            {"title": item[2], "author": item[4], "timestamp": item[3], "pid": item[0]}
            for item in passages
        ],
        announcements=[
            {"title": item[1], "timestamp": item[3], "aid": item[0]}
            for item in announcements
        ],
        polls=[
            {"title": item[2], "timestamp": item[6], "vid": item[0]} for item in polls
        ],
        images=[
            {"imgname": item[1], "describe": item[4], "imgid": item[0]}
            for item in images
        ],
        user={
            "uname": user[0][3],
            "uemail": user[0][4],
            "ubirthday": user[0][5],
            "usex": user[0][6],
            "uintro": user[0][7],
        },
    )


if __name__ == "__main__":
    app.run(debug=True)
