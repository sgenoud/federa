from collections import namedtuple
import json

from flask import Blueprint, request, jsonify, abort

from framework.actor_manager import ActorManager
from framework.actor_actions import accept_object, request_follow, request_unfollow
from framework.helpers import activity_actor_from_source
from framework.crypto_utils import deserialize, extract_public_key
from framework.client import retrieve_actor

from federa.key_store import key_store
from federa.model import ObservedActivity
from federa.db import db


key = deserialize(
    """
-----BEGIN RSA PRIVATE KEY-----
MIIEpgIBAAKCAQEAtl7gqJw+Mua/lGSeIjaCTUZCOMa83D//zj+I3MZoNAvRyyQX
kG8mNueG2pZTrqM+K40stuTNVKhfsU8/0rQYS/mWHmYBFKW+ZUKzmwLSB0b65NwC
SsGPwyUF1p5fUB20PFGEh1cDZuVxdeWSC/l7no/hZJZGCZ0tzpJk5yoQ/rYYb4mw
347ZeW0BzI3IvwCf1M8wEFF/92OuNXsJ8cbwI60E51pAiHwNy61oMDitIQsNpeaG
xD1VKvIbToM3rW7jhtRw3Lsr69UdeWqtf7LC40s4zNoscJgIkh47PNDcc7bs8x/e
Ug3L/DorWAbvDil3lhuEUDw579Fatixqat8ZiQIDAQABAoIBAQCYKg3VYZhcLEAJ
dvKipUyPYWH7sYb/Vr7/ve9aFon3cy03DARFVRhTk1bnp6pm+nnzKLX4XGweiOZf
MTqVegMT0Uo6Tu3z5l84ajEl03Ke89B/iDq5WUu0jX2Tl0z7se0irvmfWzDRd/v1
XPlA2IcWxAJSRThm6SjBRVC/uE+51Zieeif7lf9GyGwLE+aH5s12vYiuJswI2Bbq
69ajDIpsRU1HmDzxJNwTaql+7hPkAlwJdYESTt+2NEAHUZ1Sg/ES2dodDJcTlvZ9
CXNGlvKTSvHXbDWC/PwYNQ7xvizwMHy9EdAQWCL8zxoVecalG4VM6hgKAVI+nJKH
M8X2TqjpAoGBAOdnpTkr5p46W/a5gs+zFxUI5/i4Lfj0tgi5bt7J17ZaU+7GhORw
1R0tC+fxwUKvG2iBovi6wkhABT+0tu4A0yesuC3ubjy9Uot6s8IC3gwBCWKR1oh7
R6KrFzrLZtZ1f68Io6tJ8Bu1M2C3abbhzSkThGGFtaPkk7TEyEBWyrNrAoGBAMnB
C/DYLIBv3BmGMS04KBnSalKjuwYGOfSbxEBvOHelQ25wIgOTSPvMTR2CvFp4ks73
0Zx5276SDLXeddC8+ow6FqhgkOkmoqhfgwlpjQ1aIwbJWCrUdyzr8AmnFpptM2hv
uwykSMgCQNIT7EXIhQtO5hnUfb79V4qkDLJvSxfbAoGBAOEHLmoJYgvOrq2gOzAl
dTXUYljBKpulxPt47/MhD29aKbLSRFstymDD9IcK1qg1Ro77OfNtEg9WioQoBZgv
Hye+06B+856HcSUIHpR1W18LBwhez+QLFl9+x2k6cXft7UvWN+sTTLZ1IFBWLCxX
Kr5eJ2b6sud9GZI5po7Cl/2fAoGBAJwLfPHWMW1Rl1oCiYyhD5sRPP0X+DJrpG3G
AJ+ZpoIbx7Dmd9huFZfzZ324vXf4JAyCbpRpSAX4rm4IVvWRBPRqhVXMAqjiIhK6
dP5VriwymD7Kgi/2TwrmnazJmFjut0FCkdjwQ/62h240zJ0Yv5aEesJlsLCFAC2S
PuPP4rPbAoGBAMz4bXR7nf8mtMAgxTGj+8XWNl5xFUF67xuWrHpzTfOQPiOn3GmA
N3y9AAvnAgRqMNm2MK2A02RdawWSIPl6ByW6mTpYch5R0Ea160VnhmzwHUiB9LEy
Pqp32KJwyEuVaZcTc94K9uoe9p1ISs80oEfj40lU+Y8sIJ+wA9unk4pX
-----END RSA PRIVATE KEY-----
""".encode(
        "ascii"
    ),
    False,
)
pub_key = extract_public_key(key)

Observer = namedtuple("Observer", ["id", "type", "name", "summary", "private_key", "public_key"])


def find_observer(observer_id):
    return Observer(observer_id, "Service", f"Observer {observer_id}", "", key, pub_key)


def content(activity):
    content = json.loads(activity.object)
    del content["@context"]
    return content


def activities(observer_id):
    q = db.engine.query(ObservedActivity, ObservedActivity.observer == observer_id, forward=False)
    return [
        {
            "observer": activity.observer,
            "date": activity.date,
            "type": activity.type,
            "source_host": activity.source_host,
            "content": content(activity),
        }
        for activity in q.all()
    ]


observer = ActorManager("observer", find_observer, external_key_store=key_store)


def save_activity(observer, activity):
    db.engine.save(
        ObservedActivity(
            observer=observer.id,
            type=activity.get("type"),
            source_host=request.headers.get("host"),
            object=json.dumps(activity),
        )
    )
    return "done"


@observer.register_default_activity
def follow_default(observer, activity):
    save_activity(observer, activity)


@observer.register_activity("Follow")
@activity_actor_from_source
def follow(observer, follow_activity):
    save_activity(observer, follow_activity)
    follower = follow_activity.get("actor")
    accept_object(observer, follower, follow_activity)
    return "done"


observerAPI = Blueprint("observer-api", __name__)


@observerAPI.route("/observer/<observer_name>", methods=("GET",))
def group_info(observer_name):
    return jsonify({"observer": observer_name, "activity": activities(observer_name)})


@observerAPI.route("/observer/<observer_name>/follow", methods=("POST",))
def follow_actor(observer_name):
    target_actor = retrieve_actor(request.form.get("target"))

    if target_actor is None or "inbox" not in target_actor:
        abort(404)

    request_follow(find_observer(observer_name), target_actor["id"], bp_name="observer")
    return ("done", 202)


@observerAPI.route("/observer/<observer_name>/unfollow", methods=("POST",))
def unfollow_actor(observer_name):
    target_actor = retrieve_actor(request.form.get("target"))

    if target_actor is None or "inbox" not in target_actor:
        abort(404)

    request_unfollow(find_observer(observer_name), target_actor["id"], bp_name="observer")
    return ("done", 202)
