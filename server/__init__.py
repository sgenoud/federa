import datetime

from flask import Flask

from flask_cors import CORS

from framework.api.oauth import make_mastodon_blueprint
from framework.helpers import populate_actor_info

from server.config import Configuration
from server.group import groupAPI, groupViews
from server.site import site
from server.db import db
from server.backends import OAuthDynamoDbMemoryBackend


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(Configuration)
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=4000)

    db.init_app(app.config.get("LOCAL_DYNAMODB"), prefix=app.config["TABLE_PREFIX"])

    CORS(app, supports_credentials=True)

    mastodon_bp = make_mastodon_blueprint(
        app.config["SERVICE_NAME"],
        scope="read write follow",
        instance_credentials_backend=OAuthDynamoDbMemoryBackend(),
    )
    app.register_blueprint(mastodon_bp, url_prefix="/login")

    app.before_request(populate_actor_info)

    app.register_blueprint(site, url_prefix="/")
    app.register_blueprint(groupAPI, url_prefix="/api")
    app.register_blueprint(groupViews, url_prefix="/group")

    return app
