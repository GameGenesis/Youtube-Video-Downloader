from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1234"

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")
    return app