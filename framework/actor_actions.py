from uuid import uuid4
from multiprocessing.pool import ThreadPool

from flask import url_for, current_app

from framework.signatures import signed_request
from requests.exceptions import ConnectionError


def random_id():
    return f"https://{current_app.config.get('SERVER_NAME')}/{uuid4()}"


def detailed_post_to_inbox(actor_key, key_id, actor_recieving, data):
    try:
        return signed_request(
            actor_key,
            key_id,
            "post",
            f"{actor_recieving}/inbox",
            json=data,
            headers={"content-type": "application/activity+json"},
        )
    except ConnectionError:
        pass


def post_to_inbox(actor_sending, actor_recieving, data, bp_name=""):
    try:
        return detailed_post_to_inbox(
            actor_sending.private_key,
            url_for(
                f"{bp_name}.actor", actor_id=actor_sending.id, _external=True, _anchor="main-key"
            ),
            actor_recieving,
            data,
        )
    except ConnectionError:
        pass


def accept_object(source_actor, target_actor, obj, bp_name=""):
    post_to_inbox(
        source_actor,
        target_actor,
        {
            "@context": "https://www.w3.org/ns/activitystreams",
            "id": random_id(),
            "type": "Accept",
            "actor": url_for("{bp_name}.actor", actor_id=source_actor.id, _external=True),
            "object": obj,
        },
    )


def announce_object(source_actor, target_actors, obj, announce_id=None, bp_name=""):
    if announce_id is None:
        announce_id = random_id()

    actor_id = url_for(f"{bp_name}.actor", actor_id=source_actor.id, _external=True)
    key_id = url_for(
        f"{bp_name}.actor", actor_id=source_actor.id, _external=True, _anchor="main-key"
    )

    def _post_announce(target_actor):
        detailed_post_to_inbox(
            source_actor.private_key,
            key_id,
            target_actor,
            {
                "@context": "https://www.w3.org/ns/activitystreams",
                "id": announce_id,
                "type": "Announce",
                "actor": actor_id,
                "object": obj,
            },
        )

    with ThreadPool(20) as pool:
        pool.map(_post_announce, target_actors)


def request_follow(source_actor, target_actor, bp_name=""):
    post_to_inbox(
        source_actor,
        target_actor,
        {
            "@context": "https://www.w3.org/ns/activitystreams",
            "id": random_id(),
            "type": "Follow",
            "actor": url_for(f"{bp_name}.actor", actor_id=source_actor.id, _external=True),
            "object": target_actor,
        },
        bp_name=bp_name,
    )


def request_unfollow(source_actor, target_actor, bp_name=""):
    post_to_inbox(
        source_actor,
        target_actor,
        {
            "@context": "https://www.w3.org/ns/activitystreams",
            "id": random_id(),
            "type": "Undo",
            "actor": url_for(f"{bp_name}.actor", actor_id=source_actor.id, _external=True),
            "object": {"type": "Follow", "object": target_actor},
        },
        bp_name=bp_name,
    )
