from functools import wraps
from urllib.parse import urlparse
import json
import re

from flask import request, abort, Response

from framework.signatures import parse_signature_header


# from https://github.com/dsblank/activitypub/blob/master/activitypub/manager/ap_routes.py
WEBFINGER = re.compile(r"@?(?:acct:)?(?P<username>[\w.!#$%&\'*+-/=?^_`{|}~]+)@(?P<host>[\w.:-]+)")


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
        data["@context"] = "https://www.w3.org/ns/activitystreams"
    return Response(
        response=json.dumps(data),
        headers={"Content-Type": "application/activity+json; charset=utf-8"},
    )
