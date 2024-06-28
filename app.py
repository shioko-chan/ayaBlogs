from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
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


app = Flask(__name__)
app.secret_key = pwd.genword(charset="ascii_72")

app.config["SESSION_TYPE"] = "filesystem"

login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"

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

mail = Mail(app)

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


def query_database(query, params=None) -> list:
    connection = pool.connection()
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        connection.close()


@login_manager.user_loader
def load_user(user_id):
    usr = query_database("select * from usr where uid=%d", (user_id,))
    assert len(usr) == 1, "wrong response, uid must be unique"
    usr = usr[0]
    return usr


def get_articles(condition=None, params=None) -> list:
    query = "select pid,content,title,author,createAt from passage {}"
    list = query_database(
        query.format(condition) if condition else query.format(""), params=params
    )
    return [
        {
            "title": title,
            "content": content,
            "images": query_database(
                "select imgpath from images where containBy=%d", (pid,)
            ),
            "timestamp": createAt,
            "author": author,
        }
        for pid, content, title, author, createAt in list
    ]


@login_required
@app.route("/register/validate")
def validate_mail():
    if request.json and "email" in request.json.keys():
        email = request.json["email"]
        validateCode = random.randint(100000, 999999)
        message = message = Message(
            subject="ayaBlogs 验证码",
            sender=MAIL_USER,
            recipients=[email],
            body=f"[ayaBlogs] 你好，欢迎注册ayaBlogs，你的验证码是 {validateCode}",
        )
        mail.send(message)
        return jsonify({"id": 123})


@app.route("/")
def index():
    return render_template(
        "index.html",
        user=current_user,
        articles=get_articles(),
    )


@app.route("/mainpage/<username>")
def mainpage(username):
    uid = query_database("select uid from usr where uname=%s", (username,))[0][0]
    return render_template(
        "index.html",
        user=current_user,
        articles=get_articles(
            condition="where author=%d",
            params=(uid,),
        ),
    )


@app.route("/search", methods=["POST"])
def search():
    if request.form:
        keyword = request.form["search"]
        return render_template(
            "index.html",
            user=current_user,
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
                    ("%" + keyword + "%",) * 2,
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
                ("%" + keyword + "%",) * 2,
            )
            articles = query_database(
                "select title from passage where title like %s union select content from passage where content like %s",
                ("%" + keyword + "%",) * 2,
            )
            return jsonify({"usrs": usrs, "articles": articles})
        else:
            return "request unknown", 400


def random_image():
    return url_for("static", filename="bkg/" + random.choice(backgrounds).name)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pass
    else:
        return render_template(
            "login.html",
            user=current_user,
            random_background=random_image(),
            is_login=True,
        )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pass
    else:
        return render_template(
            "login.html",
            usr=current_user,
            random_background=random_image(),
            is_login=False,
        )


if __name__ == "__main__":
    app.run(debug=True)
