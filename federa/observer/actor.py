import json

from flask import request

from framework.actor_manager import ActorManager
from framework.actor_actions import accept_object
from framework.helpers import activity_actor_from_source

from federa.db import db
from federa.key_store import key_store

from .model import ObservedActivity
from .common import find_observer


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
