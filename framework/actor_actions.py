from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import url_for, current_app

from framework.signatures import signed_request, signed_content
from framework.constants import AP_CONTEXT, PUBLIC_AUDIENCE
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
            "@context": AP_CONTEXT,
            "id": random_id(),
            "type": "Accept",
            "actor": url_for(f"{bp_name}.actor", actor_id=source_actor.id, _external=True),
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
        content = signed_content(
            source_actor.private_key,
            key_id,
            {
                "@context": AP_CONTEXT,
                "id": announce_id,
                "to": "https://www.w3.org/ns/activitystreams#Public",
                "type": "Announce",
                "actor": actor_id,
                "object": obj,
            },
        )

        detailed_post_to_inbox(source_actor.private_key, key_id, target_actor, content)

    with ThreadPoolExecutor(max_workers=20) as pool:
        pool.map(_post_announce, [a for a in target_actors if a != actor_id])


def request_follow(source_actor, target_actor, bp_name=""):
    post_to_inbox(
        source_actor,
        target_actor,
        {
            "@context": AP_CONTEXT,
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
            "@context": AP_CONTEXT,
            "id": random_id(),
            "type": "Undo",
            "actor": url_for(f"{bp_name}.actor", actor_id=source_actor.id, _external=True),
            "object": {"type": "Follow", "object": target_actor},
        },
        bp_name=bp_name,
    )


def update_object(source_actor, target_actors, obj, announce_id=None, bp_name=""):
    if announce_id is None:
        announce_id = random_id()

    actor_id = url_for(f"{bp_name}.actor", actor_id=source_actor.id, _external=True)
    key_id = url_for(
        f"{bp_name}.actor", actor_id=source_actor.id, _external=True, _anchor="main-key"
    )

    def _post_update(target_actor):
        detailed_post_to_inbox(
            source_actor.private_key,
            key_id,
            target_actor,
            {
                "@context": AP_CONTEXT,
                "id": announce_id,
                "type": "Update",
                "to": [PUBLIC_AUDIENCE],
                "actor": actor_id,
                "object": obj,
            },
        )

    with ThreadPoolExecutor(max_workers=20) as pool:
        pool.map(_post_update, [a for a in target_actors if a != actor_id])
