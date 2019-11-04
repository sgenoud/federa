from uuid import uuid4
import json

from flask import abort, url_for
from bloop.exceptions import ConstraintViolation

from framework.actor_manager import ActorManager
from framework.actor_actions import accept_object, announce_object
from framework.helpers import activity_actor_from_source, activityjsonify

from server.key_store import key_store
from server.db import db

from .common import find_group, group_members, serialize_announce
from .model import GroupMember, GroupActivity

group = ActorManager("group", find_group, external_key_store=key_store)


@group.register_default_activity
def follow_default(group, activity):
    print(f'unknown activity "{activity.get("type")}"')


@group.register_activity("Follow")
@activity_actor_from_source
def follow(group, follow_activity):
    follower = follow_activity.get("actor")

    target = follow_activity.get("object")
    if target != url_for(".actor", actor_id=group.id, _external=True):
        abort(400, "Wrong target")

    accept_object(group, follower, follow_activity)

    q = db.engine.query(
        GroupMember.by_follower,
        key=GroupMember.follower_id == follower,
        filter=GroupMember.group_id == group.id,
        projection="count",
    )
    if q.count > 0:
        return "done"

    db.engine.save(GroupMember(id=uuid4(), follower_id=follower, group_id=group.id))
    return "done"


@group.register_activity("Undo")
@activity_actor_from_source
def undo(group, undo_activity):
    follower = undo_activity.get("actor")

    action = undo_activity.get("object", {})
    if action.get("type").lower() != "follow":
        return "done"

    if action.get("actor") != follower:
        abort(400, "Inconsistant follow activity")

    target = action.get("object")
    if target != url_for(".actor", actor_id=group.id, _external=True):
        abort(400, "Wrong target")

    q = db.engine.query(
        GroupMember.by_follower,
        key=GroupMember.follower_id == follower,
        filter=GroupMember.group_id == group.id,
    )
    try:
        membership = q.first()
    except ConstraintViolation:
        return "done"

    db.engine.delete(membership)

    return "done"


@group.register_activity("Create")
@activity_actor_from_source
def create(group, create_activity):
    # We go with the simple and stupid approach so far. We check that the actor
    # creating belongs to the group. If it is the case we just announce the id
    # of the activity created to all the members of the group.
    # There is a lot of work to be done with the different levels of sharing
    # and privacy. For now we assume that you will need to have everything
    # public in some way

    activity_details = create_activity.get("object")
    if activity_details is None:
        abort(400, "activity not detailed")

    activity_id = (
        activity_details if isinstance(activity_details, str) else activity_details.get("id")
    )
    if activity_id is None:
        abort(400, "not external activity id")

    actor = create_activity.get("actor")
    members = set(group_members(group.id))

    if actor not in members:
        abort(401, "actor needs to be member of the group")

    members.discard(actor)
    announce_id = str(uuid4())
    announce_uri = url_for(".announce_activity", announce_id=announce_id, _external=True)
    announce_object(group, members, activity_id, announce_uri)

    announce = GroupActivity(
        id=announce_id, type="Announce", group_id=group.id, object=json.dumps(activity_id)
    )
    db.engine.save(announce)

    return serialize_announce(announce)


@group.register_activity("Delete")
def delete(group, follow_activity):
    print(f"created {group.id}")


@group.register_list("followers")
def followers(group):
    # TODO: introduce pagination
    q = db.engine.query(
        GroupMember.by_group, key=GroupMember.group_id == group.id, projection="count"
    )
    total_items = q.count

    if q.count > 0:
        ordered_items = group_members(group.id)
    else:
        ordered_items = []

    return dict(type="OrderedCollection", totalItems=total_items, orderedItems=ordered_items)


@group.blueprint.route("/activity/announce/<announce_id>")
def announce_activity(announce_id):
    q = db.engine.query(GroupActivity, key=GroupActivity.id == announce_id)
    try:
        announce = q.one()
    except ConstraintViolation:
        abort(404)

    if announce.type != "Announce":
        abort(404)

    return activityjsonify(serialize_announce(announce), add_context=True)
