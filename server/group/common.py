import json
from uuid import uuid4
import re

from server.db import db
from .model import Group, GroupMember, GroupActivity
from framework.actor_actions import update_object

from flask import url_for, session, abort
from zappa.async import task
from bloop.exceptions import ConstraintViolation

ALPHANUMERIC = re.compile("^[A-Za-z0-9]+$")


def find_group(group_id):
    q = db.engine.query(Group, key=Group.id == group_id)
    try:
        return q.one()
    except ConstraintViolation:
        return None


def group_members(group_id):
    q = db.engine.query(GroupMember.by_group, key=GroupMember.group_id == group_id)
    return [member.follower_id for member in q.all()]


def group_activity(group_id):
    q = db.engine.query(GroupActivity.by_group, key=GroupActivity.group_id == group_id)
    return [json.loads(activity.object) for activity in q.all()]


def serialize_announce(announce):
    return {
        "id": url_for(".announce_activity", announce_id=announce.id, _external=True),
        "type": announce.type,
        "actor": url_for(".actor", actor_id=announce.group_id, _external=True),
        "object": json.loads(announce.object),
    }


def user_groups():
    q = db.engine.query(
        GroupMember.by_follower, key=GroupMember.follower_id == session.get("actor_id", "")
    )
    try:
        return [(find_group(member.group_id), member) for member in q.all()]
    except ConstraintViolation:
        return []


def actor_is_admin(group_id):
    if not group_id:
        return False
    actor_id = session.get("actor_id", "")
    if not actor_id:
        return False

    q = db.engine.query(
        GroupMember.by_follower,
        key=GroupMember.follower_id == actor_id,
        filter=GroupMember.group_id == group_id,
    )
    try:
        info = q.one()
    except ConstraintViolation:
        return False

    return info.is_admin


def notify_update(group_id):
    from .actor import group as group_manager

    group = find_group(group_id)

    update_object(
        group,
        group_members(group.id),
        group_manager.blueprint.format_actor_info(group),
        bp_name=group_manager.name,
    )


def save_group(group_name, name, summary):
    if len(group_name) > 128:
        abort(400, "group_name too long")

    if not ALPHANUMERIC.match(group_name):
        abort(400, "non alphanumeric group_name")

    if len(name) > 256:
        abort(400, "group_name too long")
    if len(summary) > 2560:
        abort(400, "summary too long")

    existing_group = find_group(group_name)
    if existing_group is not None:
        if not actor_is_admin(group_name):
            abort(403)

        existing_group.name = name
        existing_group.summary = summary
        db.engine.save(existing_group)

        return

    db.engine.save(
        Group(id=group_name, name=name, summary=summary),
        GroupMember(
            id=uuid4(), group_id=group_name, follower_id=session["actor_id"], is_admin=True
        ),
    )
