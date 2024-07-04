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
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_mail import Message

from dns import resolver as dns_resolver
from pathlib import Path
from passlib import pwd
import hashlib
import secrets
from time import time
from random import randint

from models import Usr, Passage, Announcement, Vote, OptionItem, Comment
from util import response, allowed_file, random_image

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
            "login.html", random_background=random_image(), user=user
        )
    if request.form:
        try:
            name = request.form["username"]
            password = request.form["password"]
            user = Usr.get_by_username(username=name)
            if not user:
                return response(success=False, mes="用户不存在")
            if hash_password(password, user.salt) != user.password_hash:
                return response(success=False, mes="用户名或密码错误")
            login_user(user, remember=True)
            return response(success=True, mes="登录成功")
        except Exception:
            return response(success=False, mes="内部错误")
    return response(success=False, mes="请求错误")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("blog_bp.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template(
            "login.html",
            is_register=True,
            random_background=random_image(),
        )
    if request.form:
        try:
            email = session.get("valid_email")
            if not email:
                return response(success=False, mes="请验证邮箱", code=1)

            name = request.form["username"].strip()
            if not name:
                return response(success=False, mes="请输入用户名", code=2)
            if Usr.exists_username(name):
                return response(success=False, mes="用户名已存在", code=3)

            password = request.form["password"]
            if not password:
                return response(success=False, mes="请输入密码", code=4)

            salt = secrets.token_bytes(64)
            password_hash = hash_password(password, salt)
            Usr(
                id=0, password_hash=password_hash, salt=salt, username=name, email=email
            ).insert_into_db()
            return redirect(url_for("auth_bp.login"))
        except Exception:
            return response(success=False, mes="请求错误", code=100)
    return response(success=False, mes="请求错误", code=100)


@auth_bp.route("/register/validate", methods=["POST"])
def validate_mail():
    if request.json:
        if "email" in request.json.keys():
            timestamp = session.get("request_timestamp")
            if (
                timestamp
                and timestamp + current_app.config["MAIL_SEND_INTERVAL"] > time()
            ):
                return response(success=False, mes="请求过于频繁", code=1)
            session["request_timestamp"] = time()

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
                sender=current_app.config["MAIL_USER"],
                recipients=[email],
                body=f"[ayaBlogs] 你好，欢迎注册ayaBlogs，你的验证码是 {validateCode}",
            )
            try:
                current_app.extensions["mail"].send(message)
            except Exception:
                session.pop("email")
                return response(success=False, mes="请求错误", code=100)
            session["validate_code"] = str(validateCode)
            return response(success=False, mes="验证码发送成功")

        elif "validate_code" in request.json.keys():
            validate_code = session.get("validate_code")
            if not validate_code:
                return response(success=False, mes="验证码已过期或尚未获取", code=11)

            input_code = request.json["validate_code"].strip()
            if validate_code != input_code:
                if "retry_times" in session:
                    session["retry_times"] += 1
                else:
                    session["retry_times"] = 1
                if session["retry_times"] > current_app.config["MAX_RETRY"]:
                    session.pop("retry_times")
                    session.pop("validate_code")
                    session.pop("email")
                    return response(success=False, mes="验证码错误次数过多", code=12)
                return response(success=False, mes="验证码错误", code=13)
            session.pop("retry_times")
            session.pop("validate_code")
            session["valid_email"] = session.pop("email")
            return response(success=True, mes="验证码正确")
    return response(success=False, mes="请求错误", code=100)
