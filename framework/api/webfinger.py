import json

from flask import url_for, request, Blueprint, abort, current_app, Response
from framework.constants import WEBFINGER


class WebfingerBlueprint(Blueprint):
    def __init__(
        self,
        import_name,
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
            name="webfinger",
            import_name=import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
        )

        self._managers = []
        self.add_url_rule(rule="/webfinger", endpoint="webfinger", view_func=self.handler)

    def handler(self):
        resource = request.args.get("resource")
        if not resource:
            abort(404)

        matches = WEBFINGER.match(resource)
        if (
            not current_app.config["DEBUG"]
            and current_app.config["WEBFINGER_CHECK_HOST"]
            and matches["host"] != current_app.config["SERVER_NAME"]
        ):
            abort(404)

        actor = None
        for manager in self._managers:
            actor = manager.find(matches["username"])
            if actor is not None:
                break

        if not actor:
            abort(404)

        out = {
            "subject": resource,
            "links": [
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": url_for(f"{manager.name}.actor", actor_id=actor.id, _external=True),
                }
            ],
        }

        return Response(
            response=json.dumps(out),
            headers={"Content-Type": "application/jrd+json; charset=utf-8"},
        )

    def register_actor(self, manager):
        self._managers.append(manager)


def make_webfinger_blueprint():
    return WebfingerBlueprint(__name__)
