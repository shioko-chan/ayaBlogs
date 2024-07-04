from flask import Flask
from auth import auth_bp
from blog import blog_bp


def register_bp(app):

    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)

    return app
