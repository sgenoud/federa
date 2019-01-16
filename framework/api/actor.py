import json
from datetime import datetime, timezone

from flask import Response, url_for, request, Blueprint, abort, current_app

from email.utils import parsedate_to_datetime


from framework.signatures import signature_is_valid
from framework.helpers import activityjsonify


class ActorBlueprint(Blueprint):
    def __init__(
        self,
        name,
        import_name,
        actor_manager,
        base_url=None,
        static_folder=None,
        static_url_path=None,
        template_folder=None,
        url_prefix=None,
        subdomain=None,
        url_defaults=None,
        root_path=None,
        login_url=None,
        authorized_url=None,
        backend=None,
    ):

        Blueprint.__init__(
            self,
            name=name,
            import_name=import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
        )

        base_url = base_url or f"/"
        actor_url = f"{base_url}/<actor_id>"
        inbox_url = f"{actor_url}/inbox"
        outbox_url = f"/{actor_url}/outbox"
        followers_url = f"/{actor_url}/followers"
        following_url = f"/{actor_url}/following"

        self.add_url_rule(rule=actor_url, endpoint="actor", view_func=self.actor)
        self.add_url_rule(rule=inbox_url, endpoint="inbox", view_func=self.inbox, methods=("POST",))
        self.add_url_rule(rule=outbox_url, endpoint="outbox", view_func=self.outbox)
        self.add_url_rule(rule=followers_url, endpoint="followers", view_func=self.followers)
        self.add_url_rule(rule=following_url, endpoint="following", view_func=self.following)

        self.manager = actor_manager

    def actor(self, actor_id):
        actor = self.manager.find(actor_id)
        out = {
            "@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1"],
            "id": url_for(".actor", actor_id=actor_id, _external=True),
            "inbox": url_for(".inbox", actor_id=actor_id, _external=True),
            "type": actor.type,
            "preferredUsername": actor.id,
            "name": actor.name,
            "publicKey": {
                "id": url_for(".actor", actor_id=actor_id, _external=True, _anchor="main-key"),
                "owner": url_for(".actor", actor_id=actor_id, _external=True),
                "publicKeyPem": actor.public_key,
            },
        }
        if hasattr(actor, "summary"):
            out["summary"] = actor.summary

        if self.manager.supports_list("followers"):
            out["followers"] = url_for(".followers", actor_id=actor_id, _external=True)

        if self.manager.supports_list("following"):
            out["following"] = url_for(".following", actor_id=actor_id, _external=True)

        if self.manager.supports_list("outbox"):
            out["outbox"] = url_for(".outbox", actor_id=actor_id, _external=True)

        print(out)

        return Response(
            response=json.dumps(out),
            headers={"Content-Type": "application/jrd+json; charset=utf-8"},
        )

    def inbox(self, actor_id):
        if request.json is None:
            abort(400, "json body is necessary")

        if request.headers.get("Host") != current_app.config["SERVER_NAME"]:
            abort(401, "Incorrect host")

        raw_date = request.headers.get("Date")
        if not raw_date:
            abort(401, "Date not provided")
        time_difference = datetime.now(timezone.utc) - parsedate_to_datetime(raw_date)
        if abs(time_difference.total_seconds()) > 30:
            abort(401, "Invalid date")

        # TODO: implement digest check

        signature_check = signature_is_valid(
            self.manager.external_key_store.get,
            request.headers,
            url_for(".inbox", actor_id=actor_id),
            "POST",
        )
        if not signature_check and not current_app.config.get("DEBUG_INBOX_IGNORE_SIGNATURE"):
            abort(401, "Request signature could not be verified")

        actor = self.manager.find(actor_id)

        if not actor:
            abort(404)

        response = self.manager.handle_activity(actor, request.json)
        return activityjsonify(response)

    def _conditional_list(self, list_id, actor_id):
        if not self.manager.supports_list(list_id):
            abort(404)
        actor = self.manager.find(actor_id)

        if not actor:
            abort(404)

        return_list = self.manager.build_list(actor, list_id)
        return activityjsonify(return_list, add_context=True)

    def outbox(self, actor_id):
        return self._conditional_list("outbox", actor_id)

    def followers(self, actor_id):
        return self._conditional_list("followers", actor_id)

    def following(self, actor_id):
        return self._conditional_list("following", actor_id)


def make_actor_blueprint(name, actor_manager):
    return ActorBlueprint(name, __name__, actor_manager=actor_manager)
