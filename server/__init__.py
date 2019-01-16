import datetime
from uuid import uuid4

from flask import Flask, redirect, url_for, jsonify, current_app

from flask_cors import CORS

from framework.api.oauth import make_mastodon_blueprint, mastodon

from server.config import Configuration
from server.group import groupAPI
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
    app.register_blueprint(groupAPI, url_prefix="/api")

    @app.route("/")
    def index():
        if not mastodon.authorized:
            return redirect(url_for("mastodon.login"))
        resp = mastodon.get("/api/v1/accounts/verify_credentials")

        return jsonify(resp.json())

    @app.route("/random")
    def text():
        return f"https://{current_app.config.get('SERVER_NAME')}/{uuid4()}"

    return app
