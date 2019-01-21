from functools import wraps
from urllib.parse import urlparse
import json

from flask import request, abort, Response, session

from framework.signatures import parse_signature_header
from framework.client import retrieve_actor
from framework.constants import AP_CONTEXT
from framework.api.oauth import mastodon


def activity_actor_from_source(f):
    @wraps(f)
    def decorated_function(actor, activity):

        activity_actor = activity.get("actor")
        if activity_actor is None:
            abort(400, "Missing actor")

        signature = parse_signature_header(request.headers.get("Signature", ""))
        if urlparse(activity_actor).netloc != urlparse(signature.get("keyId", "")).netloc:
            abort(401)

        return f(actor, activity)

    return decorated_function


def activityjsonify(data, add_context=False):
    if add_context:
        data["@context"] = AP_CONTEXT
    return Response(
        response=json.dumps(data),
        headers={"Content-Type": "application/activity+json; charset=utf-8"},
    )


def populate_actor_info():
    if "actor_id" in session and "actor_handle" in session:
        return

    if not mastodon.authorized:
        if "actor_id" in session:
            del session["actor_id"]
        if "actor_handle" in session:
            del session["actor_handle"]
        return

    try:
        account_info = mastodon.get("/api/v1/accounts/verify_credentials").json()
    except ValueError:
        return

    handle = f"{account_info.get('acct')}@{mastodon.instance_host}"
    actor = retrieve_actor(handle)
    if actor is None:
        return

    session["actor_id"] = actor.get("id")
    session["actor_handle"] = handle
