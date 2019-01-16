from flask import Flask

from flask_cors import CORS

from framework.api.webfinger import make_webfinger_blueprint

from federa.config import Configuration
from federa.db import db

from .api import observerAPI
from .actor import observer


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Configuration)

    db.init_app(app.config.get("LOCAL_DYNAMODB"), prefix=app.config["TABLE_PREFIX"])

    CORS(app, supports_credentials=True)

    webfingerAPI = make_webfinger_blueprint()
    app.register_blueprint(observer.blueprint, url_prefix="/")
    webfingerAPI.register_actor(observer)

    app.register_blueprint(webfingerAPI, url_prefix="/.well-known")
    app.register_blueprint(observerAPI, url_prefix="/api")

    return app
