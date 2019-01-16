from flask import Blueprint, request, jsonify, abort

from framework.actor_actions import request_follow, request_unfollow
from framework.client import retrieve_actor

from .common import activities, find_observer

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
