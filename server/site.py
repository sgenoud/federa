from flask import Blueprint, redirect, url_for, jsonify, render_template

from framework.api.oauth import mastodon

from .group.common import user_groups

site = Blueprint("site", __name__)


@site.route("/")
def index():
    if not mastodon.authorized:
        return render_template("login.html")

    print(mastodon.authorized)

    return render_template("main.html", groups=user_groups())
