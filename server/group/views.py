from flask import Blueprint, request, render_template, redirect, url_for, abort

from server.api.utils import check_logged_in

from .common import find_group, group_members, save_group, actor_is_admin

groupViews = Blueprint("group-views", __name__, template_folder="templates")


@groupViews.route("/")
@check_logged_in
def index():
    return render_template("edit_group.html", group=None)


@groupViews.route("/<group_id>")
def group_info(group_id):
    is_admin = actor_is_admin(group_id)
    return render_template(
        "group.html", is_admin=is_admin, group=find_group(group_id), members=group_members(group_id)
    )


@groupViews.route("/<group_id>/edit")
@check_logged_in
def group_edit(group_id):
    is_admin = actor_is_admin(group_id)
    if not is_admin:
        abort(403)

    return render_template(
        "edit_group.html",
        group=find_group(group_id),
        next=url_for(".group_edit", group_id=group_id),
    )


@groupViews.route("/", methods=["POST"])
@check_logged_in
def save():
    group_name = request.form.get("id", "")
    save_group(group_name, request.form.get("name", ""), request.form.get("summary", ""))
    if "next" in request.args:
        return redirect(request.args["next"])
    return render_template("edit_group.html", group=None)
