from dns import resolver as dns_resolver
from flask import jsonify
import hashlib


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


def response(success, mes, data=None):
    return jsonify({"success": success, "message": mes, "data": data})


def hash_password(password, salt):
    salted_password = salt + password.encode()
    hashed_password = hashlib.sha512(salted_password).digest()
    return hashed_password
