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
from models import UserCredential
from .util import response, random_image, get_config, get_extension
from enum import Enum
import math

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
    class LoginStatusCode(Enum):
        UsernameNull = 1
        UsernamePasswordNotMatch = 2
        BadRequest = 100
        InternalError = 101

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
                return response(success=False, code=LoginStatusCode.UsernameNull.value)
            user = UserCredential.get_by_username(username=name)
            if not user:
                return response(
                    success=False, code=LoginStatusCode.UsernamePasswordNotMatch.value
                )
            if hash_password(password, user.salt) != user.password_hash:
                return response(
                    success=False, code=LoginStatusCode.UsernamePasswordNotMatch.value
                )
            if login_user(user, remember=True):
                return response(
                    success=True,
                    data={
                        "space": url_for("page.space", uid=current_user.id),
                    },
                )
            else:
                current_app.logger.error(
                    "In login function, an user login failure occurred, USERNAME: %s, EMAIL: %s",
                    user.username,
                    user.email,
                )
                return response(success=False, code=LoginStatusCode.InternalError.value)
        except Exception as e:
            current_app.logger.error("In login function, an error occurred: %s", e)
            return response(success=False, code=LoginStatusCode.InternalError.value)
    return response(success=False, code=LoginStatusCode.BadRequest.value)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    class RegisterStatusCode(Enum):
        EmailNotVerified = 1
        UsernameNull = 2
        UsernameOccupied = 3
        EmailOccupied = 4
        PasswordNull = 5
        BadRequest = 100
        InternalError = 101

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
                return response(
                    success=False, code=RegisterStatusCode.EmailNotVerified.value
                )

            name = request.json["username"].strip()
            if not name:
                return response(
                    success=False, code=RegisterStatusCode.UsernameNull.value
                )

            if UserCredential.exists_username(name):
                return response(
                    success=False, code=RegisterStatusCode.UsernameOccupied.value
                )
            if UserCredential.exists_email(email):
                return response(
                    success=False, code=RegisterStatusCode.EmailOccupied.value
                )
            password = request.json["password"]
            if not password:
                return response(
                    success=False, code=RegisterStatusCode.PasswordNull.value
                )

            salt = secrets.token_bytes(64)
            password_hash = hash_password(password, salt)
            UserCredential.insert_new(password_hash, salt, name, email)
            return response(success=True)

        except Exception as e:
            current_app.logger.error(e)
            return response(success=False, code=RegisterStatusCode.InternalError.value)
    return response(success=False, code=RegisterStatusCode.BadRequest.value)


@auth_bp.route("/register/validate", methods=["POST"])
def validate():
    class ValidateStatusCode(Enum):
        TooFrequent = 1
        Unavailable = 2
        Occupied = 3
        CodeExpiredOrNotRequest = 4
        RetryTooFrequent = 5
        WrongCode = 6
        BadRequest = 100
        InternalError = 101

    if request.json:
        if "email" in request.json.keys():
            timestamp = session.get("request_timestamp")
            if timestamp and timestamp + get_config("MAIL_SEND_INTERVAL") > time():
                return response(
                    success=False,
                    code=ValidateStatusCode.TooFrequent.value,
                    data={"timestamp": timestamp},
                )

            email = request.json["email"]
            email_former = session.get("email")
            if not email_former or email_former != email:
                if not check_email_service(email):
                    return response(
                        success=False, code=ValidateStatusCode.Unavailable.value
                    )
                session["email"] = email

            if UserCredential.exists_email(email):
                return response(success=False, code=ValidateStatusCode.Occupied.value)

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
                current_app.logger.error(
                    "In validate function, while sending mail to address: %s, an error occurred",
                    email,
                    e,
                )
                session.pop("email")
                return response(
                    success=False, code=ValidateStatusCode.InternalError.value
                )
            session["validate_code"] = str(validateCode)
            session["retry_times"] = 0
            session["request_timestamp"] = time()
            return response(success=True)

        elif "validate_code" in request.json.keys():
            validate_code = session.get("validate_code")
            if not validate_code:
                return response(
                    success=False, code=ValidateStatusCode.CodeExpiredOrNotRequest.value
                )

            input_code = request.json["validate_code"].strip()
            if validate_code != input_code:
                session["retry_times"] += 1
                if session["retry_times"] > get_config("CODE_MAX_RETRY"):
                    session.pop("retry_times")
                    session.pop("validate_code")
                    session.pop("email")
                    return response(
                        success=False, code=ValidateStatusCode.RetryTooFrequent.value
                    )
                return response(
                    success=False,
                    code=ValidateStatusCode.WrongCode.value,
                    data={
                        "opportunity": get_config("CODE_MAX_RETRY")
                        - session["retry_times"]
                    },
                )
            session.pop("retry_times")
            session.pop("validate_code")
            session["valid_email"] = session["email"]
            return response(success=True)
    return response(success=False, code=ValidateStatusCode.BadRequest.value)


@auth_bp.route("/register/recaptcha", methods=["POST"])
def recaptcha():
    class RecaptchaStatusCode(Enum):
        NotPassed = 1
        NotFinish = 2
        TooFrequent = 3
        BadRequest = 100
        InternalError = 101

    if not request.json or "recaptcha" not in request.json:
        return response(success=False, code=RecaptchaStatusCode.BadRequest.value)

    recaptcha_token = request.json["recaptcha"]
    if not recaptcha_token:
        return response(success=False, code=RecaptchaStatusCode.NotFinish.value)

    retry = session.get("recaptcha_retry_times", 0) + 1
    max_retry = get_config("RECAPTCHA_MAX_RETRY")
    interval = get_config("RECAPTCHA_INTERVAL")

    if retry >= max_retry:
        recaptcha_timestamp = session.get("recaptcha_timestamp")
        current_time = time()
        if recaptcha_timestamp:
            wait_time = recaptcha_timestamp + interval - current_time
            if wait_time > 0:
                return response(
                    success=False,
                    code=RecaptchaStatusCode.TooFrequent.value,
                    data={"time": math.ceil(wait_time)},
                )
            else:
                session.pop("recaptcha_timestamp")
                session.pop("recaptcha_retry_times")
        else:
            session["recaptcha_timestamp"] = current_time
            return response(
                success=False,
                code=RecaptchaStatusCode.TooFrequent.value,
                data={"time": interval},
            )
    else:
        session["recaptcha_retry_times"] = retry
    try:
        resp = req(
            method="POST",
            url="https://www.google.com/recaptcha/api/siteverify",
            params={"secret": get_config("SECRET_KEY"), "response": recaptcha_token},
        )
        resp_json = resp.json()
    except Exception as e:
        current_app.logger.error("In recaptcha function, an error occurred: %s", e)
        return response(success=False, code=RecaptchaStatusCode.InternalError.value)

    if resp_json.get("success"):
        return response(success=True)
    else:
        return response(success=False, code=RecaptchaStatusCode.NotPassed.value)


@auth_bp.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("page.index"))


# @auth_bp.route("/admin")
# @login_required
# def admin():
#     if not current_user.is_administrator:
#         return redirect(url_for("page.index"))

#     passages = query_database(
#         "select * from passage where author=%d", params=(user.uid,)
#     )
#     announcements = query_database(
#         "select * from announcement where author=%d", params=(user.uid,)
#     )
#     polls = query_database("select * from vote where creator=%d", params=(user.uid,))
#     images = query_database("select * from image where ownedBy=%d", params=(user.uid,))
#     user = query_database("select * from usr where uid=%d", params=(user.uid,))
#     return render_template(
#         "manage.html",
#         passages=[
#             {"title": item[2], "author": item[4], "timestamp": item[3], "pid": item[0]}
#             for item in passages
#         ],
#         announcements=[
#             {"title": item[1], "timestamp": item[3], "aid": item[0]}
#             for item in announcements
#         ],
#         polls=[
#             {"title": item[2], "timestamp": item[6], "vid": item[0]} for item in polls
#         ],
#         images=[
#             {"imgname": item[1], "describe": item[4], "imgid": item[0]}
#             for item in images
#         ],
#         user={
#             "uname": user[0][3],
#             "uemail": user[0][4],
#             "ubirthday": user[0][5],
#             "usex": user[0][6],
#             "uintro": user[0][7],
#         },
#     )
