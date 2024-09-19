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
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_mail import Message, Mail
from flask_session import Session

from dns import resolver as dns_resolver
from pathlib import Path
from passlib import pwd

import tomllib
import random
import time
import hashlib
import secrets

config = tomllib.load(open("config.toml", "rb"))

MAIL_SERVER = config["mail"]["server"]
MAIL_USER = config["mail"]["user"]
MAIL_PASSWORD = config["mail"]["password"]
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
    MAIL_PORT=465,
)

app.config.update(SESSION_TYPE=SESSION_TYPE)

login_manager = LoginManager()
login_manager.init_app(app)

mail = Mail(app)

Session(app)

save_path = Path(UPLOAD_FOLDER)
save_path.mkdir(exist_ok=True)
backgrounds = [file for file in Path("static/bkg").iterdir() if file.is_file()]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_articles(condition=None, params=None) -> list:
    query = "select pid,content,title,author,createAt from passage {}"
    list = query_database(
        query.format(condition) if condition else query.format(""), params=params
    )
    return [
        {
            "title": title,
            "content": content,
            "images": [
                {"name": img[0], "describe": img[1]}
                for img in query_database(
                    "select imgname,describe from image where containBy=%d",
                    params=(pid,),
                )
            ],
            "timestamp": createAt,
            "author_id": author,
            "author_name": query_database(
                "select uname from usr where uid=%d", params=(author,)
            )[0][0],
        }
        for pid, content, title, author, createAt in list
    ]


def check_email_service(email):
    domain = email.split("@")[1]
    try:
        mx_records = dns_resolver.resolve(domain, "MX")
        if mx_records:
            return True
    except (dns_resolver.NoAnswer, dns_resolver.NXDOMAIN):
        return False
    except dns_resolver.LifetimeTimeout:
        return False

    return False


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form:
            try:
                uname = request.form["username"]
                upassword = request.form["password"]
                users = query_database(
                    "select passwordhash,salt,uid,uname from usr where uname=%s",
                    params=(uname,),
                )
                if not users:
                    return jsonify({"status": "user-not-exist"})
                print(users[0][0], users[0][1], hash_password(upassword, users[0][1]))
                if hash_password(upassword, users[0][1]) != users[0][0]:
                    return jsonify({"status": "password-error"})

                session["user"] = User(users[0][2], users[0][3])
                return jsonify({"status": "success"})
            except Exception as e:
                print(e)
                return jsonify({"status": "error"})
        return jsonify({"status": "error"})
    else:
        return render_template(
            "login.html",
            random_background=random_image(),
            is_login=True,
        )


@app.route("/logout")
def logout():
    session.pop("user")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form:
            try:
                uname = request.form["username"]
                upassword = request.form["password"]
                uemail = request.form["email"]
                uvalidate = request.form["code"]
                code = session.get("validate_code")
                print(code, uvalidate)
                if code != int(uvalidate):
                    return jsonify({"status": "invalid-code"})

                salt = secrets.token_bytes(64)
                query_database(
                    "insert into usr(passwordhash, salt, uname, uemail) values(CONVERT(varbinary(64), %s),CONVERT(varbinary(64), %s),%s,%s)",
                    returns=False,
                    params=(hash_password(upassword, salt), salt, uname, uemail),
                )
                return jsonify({"status": "success"})
            except Exception as e:
                print(e)
                return jsonify({"status": "error"})
        return jsonify({"status": "error"})
    else:
        return render_template(
            "login.html",
            random_background=random_image(),
            is_login=False,
        )


@app.route("/storage/<filename>")
def storage(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/register/validate", methods=["POST"])
def validate_mail():
    if request.json and "email" in request.json.keys():
        email = request.json["email"]
        timestamp = session.get("request_timestamp")
        if timestamp and timestamp + 120 > time.time():
            return jsonify({"status": "error"})
        else:
            session["request_timestamp"] = time.time()

        if not check_email_service(email):
            return jsonify({"status": "error"})

        if query_database("select * from usr where uemail=%s", params=(email,)):
            return jsonify({"status": "email-duplicate"})
        try:
            validateCode = random.randint(100000, 999999)
            message = Message(
                subject="ayaBlogs 验证码",
                sender=MAIL_USER,
                recipients=[email],
                body=f"[ayaBlogs] 你好，欢迎注册ayaBlogs，你的验证码是 {validateCode}",
            )
            mail.send(message)
            print(f"send validate code to {email} success")
            session["validate_code"] = validateCode
        except Exception as e:
            print(e)
            return jsonify({"status": "error"})
        return jsonify({"status": "success"})


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


@app.route("/space/<username>")
def space(username):
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
        space_user=username,
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


def random_image():
    return url_for("static", filename="bkg/" + random.choice(backgrounds).name)


def hash_password(password, salt):
    salted_password = salt + password.encode()
    hashed_password = hashlib.sha512(salted_password).digest()
    return hashed_password


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
    return redirect(url_for("space", username=user.uname) or url_for("index"))


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


@app.route("/space/<username>/management")
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
