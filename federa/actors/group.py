from flask import Flask

from flask_cors import CORS

from framework.api.webfinger import make_webfinger_blueprint

from federa.config import Configuration
from federa.group import group
from federa.db import db


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Configuration)

    db.init_app(app.config.get("LOCAL_DYNAMODB"), prefix=app.config["TABLE_PREFIX"])

    CORS(app, supports_credentials=True)

    webfingerAPI = make_webfinger_blueprint()
    app.register_blueprint(group.blueprint, url_prefix="/")
    webfingerAPI.register_actor(group)

    app.register_blueprint(webfingerAPI, url_prefix="/.well-known")

    return app
