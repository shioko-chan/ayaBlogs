from flask import Flask
from .auth import auth_bp
from .page import page_bp


def register_bp(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(page_bp)
