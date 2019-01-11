from functools import wraps

from flask import session, abort
from framework.api.oauth import mastodon

UID = "mastodon_user_id"


def get_user_id():
    user_info = mastodon.get("/api/v1/accounts/verify_credentials")
    username = user_info.json().get("acct")
    return f"https://{mastodon.instance_host}/users/{username}"


def check_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not mastodon.authorized:
            abort(403)

        if UID not in session:
            session[UID] = get_user_id()

        return f(*args, **kwargs)

    return decorated_function
