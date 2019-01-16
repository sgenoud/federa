import json

from server.db import db
from .model import Group, GroupMember, GroupActivity

from flask import url_for
from bloop.exceptions import ConstraintViolation


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
