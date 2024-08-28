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
from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user,
    AnonymousUserMixin,
)
from flask_mail import Message

from dns import resolver as dns_resolver
from pathlib import Path
from passlib import pwd
import hashlib
import secrets
from time import time
from random import randint
from requests import request as req
from models import Usr
from .util import response, allowed_file, random_image, get_config, get_extension

auth_bp = Blueprint("auth", __name__)


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


def hash_password(password, salt):
    salted_password = salt + password.encode()
    hashed_password = hashlib.sha512(salted_password).digest()
    return hashed_password


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template(
            "login.html",
            random_background=random_image(),
            site_key=get_config("SITE_KEY"),
        )
    elif request.json:
        try:
            name = request.json["username"].strip()
            password = request.json["password"]
            if not name:
                return response(success=False, mes="请输入用户名")
            user = Usr.get_by_username(username=name)
            if not user:
                return response(success=False, mes="用户不存在")
            if hash_password(password, user.salt) != user.password_hash:
                return response(success=False, mes="用户名或密码错误")
            if login_user(user, remember=True):
                return response(
                    success=True,
                    data={
                        "mainpage": url_for(
                            "page.mainpage", username=current_user.username
                        ),
                    },
                )
            else:
                return response(success=False, mes="登录失败, 内部错误")
        except Exception as e:
            print(e)
            return response(success=False, mes="内部错误")
    return response(success=False, mes="请求错误")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("page_bp.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template(
            "register.html",
            random_background=random_image(),
            mail_send_interval=get_config("MAIL_SEND_INTERVAL"),
            site_key=get_config("SITE_KEY"),
        )
    if request.json:
        try:
            email = session.get("valid_email")
            if not email:
                return response(success=False, mes="请验证邮箱", code=1)

            name = request.json["username"].strip()
            if not name:
                return response(success=False, mes="请输入用户名", code=2)
            if Usr.exists_username(name):
                return response(success=False, mes="用户名已存在", code=3)
            if Usr.exists_email(email):
                return response(success=False, mes="邮箱已注册", code=5)
            password = request.json["password"]
            if not password:
                return response(success=False, mes="请输入密码", code=4)

            salt = secrets.token_bytes(64)
            password_hash = hash_password(password, salt)
            Usr(
                id=0, password_hash=password_hash, salt=salt, username=name, email=email
            ).insert_into_db()
            return response(success=True)
        except Exception as e:
            auth_bp.logger.error(e)
            return response(success=False, mes="请求错误", code=100)
    return response(success=False, mes="请求错误", code=100)


@auth_bp.route("/register/validate", methods=["POST"])
def validate():
    if request.json:
        if "email" in request.json.keys():
            timestamp = session.get("request_timestamp")
            if timestamp and timestamp + get_config("MAIL_SEND_INTERVAL") > time():
                return response(
                    success=False,
                    mes="请求过于频繁",
                    code=1,
                    data={"timestamp": timestamp},
                )

            email = request.json["email"]
            email_former = session.get("email")
            if not email_former or email_former != email:
                session["email"] = email
                if not check_email_service(email):
                    return response(success=False, mes="邮箱地址不可用", code=2)
            if Usr.exists_email(email):
                return response(success=False, mes="邮箱已经注册", code=3)

            validateCode = randint(100000, 999999)
            message = Message(
                subject="ayaBlogs 验证码",
                sender=get_config("MAIL_USERNAME"),
                recipients=[email],
                body=f"[ayaBlogs] 你好，欢迎注册ayaBlogs，你的验证码是 {validateCode}",
            )
            try:
                get_extension("mail").send(message)
            except Exception as e:
                auth_bp.logger.error(e)
                session.pop("email")
                return response(success=False, mes="请求错误", code=100)
            session["validate_code"] = str(validateCode)
            session["retry_times"] = 0
            session["request_timestamp"] = time()
            return response(success=True, mes="验证码发送成功")

        elif "validate_code" in request.json.keys():
            validate_code = session.get("validate_code")
            if not validate_code:
                return response(success=False, mes="验证码已过期或尚未获取", code=11)

            input_code = request.json["validate_code"].strip()
            if validate_code != input_code:
                session["retry_times"] += 1
                if session["retry_times"] > get_config("CODE_MAX_RETRY"):
                    session.pop("retry_times")
                    session.pop("validate_code")
                    session.pop("email")
                    return response(success=False, mes="验证码错误次数过多", code=12)
                return response(
                    success=False,
                    mes="验证码错误",
                    code=13,
                    data={
                        "opportunity": get_config("CODE_MAX_RETRY")
                        - session["retry_times"]
                    },
                )
            session.pop("retry_times")
            session.pop("validate_code")
            session["valid_email"] = session.pop("email")
            return response(success=True, mes="验证码正确")
    return response(success=False, mes="请求错误", code=100)


@auth_bp.route("/register/recaptcha", methods=["POST"])
def recaptcha():
    if request.json:
        recaptcha = request.json["recaptcha"]
        if not recaptcha:
            return response(success=False, mes="请完成验证")

        resp = req(
            method="POST",
            url="https://www.google.com/recaptcha/api/siteverify",
            params={"secret": get_config("SECRET_KEY"), "response": recaptcha},
        )
        if resp.json()["success"]:
            return response(success=True, mes="验证成功")
        return response(success=False, mes="验证失败", code=1)
    return response(success=False, mes="请求错误", code=100)


@auth_bp.route("/admin")
def admin():
    if (
        not current_user
        or isinstance(current_user, AnonymousUserMixin)
        or not current_user.is_administrator
    ):
        return redirect(url_for("page.index"))

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
