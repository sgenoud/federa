from flask import Blueprint, request, abort, jsonify

from server.api.utils import check_logged_in

from .common import find_group, group_members, group_activity, save_group

groupAPI = Blueprint("group-api", __name__)


@groupAPI.route("/group", methods=("POST",))
@check_logged_in
def make_group():
    if not request.json or "group_name" not in request.json:
        abort(400, "Needs group_name")

    group_name = request.json["group_name"]
    name = request.json.get("name", group_name)
    summary = request.json.get("summary", "")

    save_group(group_name, name, summary)

    return jsonify({"ok": True})


@groupAPI.route("/group/<group_name>", methods=("GET",))
def group_info(group_name):
    group = find_group(group_name)

    if group is None:
        abort(404)

    members = group_members(group.id)

    return jsonify(
        {"group_name": group.id, "name": group.name, "summary": group.summary, "members": members}
    )


@groupAPI.route("/group/<group_name>/activity", methods=("GET",))
@check_logged_in
def group_info_activity(group_name):
    group = find_group(group_name)

    if group is None:
        abort(404)

    activity = group_activity(group.id)

    return jsonify(
        {"group_name": group.id, "name": group.name, "summary": group.summary, "activity": activity}
    )
