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
from flask_mail import Message, Mail
import pymssql
from flask_cors import CORS
import make_response
import tomllib
import random
from dbutils.pooled_db import PooledDB
from pathlib import Path
from passlib import pwd
from flask_session import Session
import time
import dns.resolver
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = pwd.genword(charset="ascii_72")

UPLOAD_FOLDER = "storage"
app.config["SESSION_TYPE"] = "filesystem"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
save_path = Path(UPLOAD_FOLDER)
save_path.mkdir(exist_ok=True)


config = tomllib.load(open("config.toml", "rb"))

DB_SERVER = config["database"]["server"]
DB_USER = config["database"]["user"]
DB_PASSWORD = config["database"]["password"]
DB_NAME = config["database"]["name"]

MAIL_SERVER = config["mail"]["server"]
MAIL_USER = config["mail"]["user"]
MAIL_PASSWORD = config["mail"]["password"]

app.config.update(
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_USERNAME=MAIL_USER,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_PORT=465,
)

pool = PooledDB(
    creator=pymssql,
    mincached=2,
    maxcached=10,
    host=DB_SERVER,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset="utf8",
)

backgrounds = [file for file in Path("static/bkg").iterdir() if file.is_file()]

mail = Mail(app)


Session(app)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class User:
    def __init__(self, uid, uname) -> None:
        self.uid = uid
        self.uname = uname


def query_database(query, returns=True, params=None):
    connection = pool.connection()
    cursor = connection.cursor()
    res = None
    try:
        connection.begin()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if returns:
            res = cursor.fetchall()
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    return res


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
        mx_records = dns.resolver.resolve(domain, "MX")
        if mx_records:
            return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False
    except dns.resolver.LifetimeTimeout:
        return False

    return False


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


def random_image():
    return url_for("static", filename="bkg/" + random.choice(backgrounds).name)


def hash_password(password, salt):
    salted_password = salt + password.encode()
    hashed_password = hashlib.sha512(salted_password).digest()
    return hashed_password


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


@app.route("/editor", methods=["GET", "POST"])
def editor():
    user = session.get("user")
    return render_template(
        "editor.html",
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
    return render_template(
        "manage.html",
    )


if __name__ == "__main__":
    app.run(debug=True)
