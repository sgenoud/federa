from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.requests import OAuth2Session
from flask_dance.consumer.storage.session import SessionStorage
from lazy import lazy
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
from flask import request, url_for
import requests

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

REGISTERED_INSTANCES_CACHE = {}


class InMemoryBackend:
    def __init__(self):
        self.cache = dict(REGISTERED_INSTANCES_CACHE)

    def get(self, bp):
        return self.cache.get(bp.instance_host, {})

    def set(self, bp, value):
        host = bp.instance_host
        if not host:
            return
        self.cache[host] = value

    def delete(self, bp):
        del self.cache[bp.instance_host]


class MastodonSession(OAuth2Session):
    @property
    def instance_host(self):
        return self.blueprint.instance_host


class MastodonConsumerBlueprint(OAuth2ConsumerBlueprint):
    def __init__(
        self,
        *args,
        client_name,
        instance_host_backend=None,
        instance_credentials_backend=None,
        session_class=None,
        **kwargs
    ):
        if session_class is None:
            session_class = MastodonSession

        OAuth2ConsumerBlueprint.__init__(self, *args, session_class=session_class, **kwargs)
        self.client_name = client_name

        if instance_host_backend is None:
            self.instance_host_backend = SessionStorage(key="{bp.name}_instance_host")
        elif callable(instance_host_backend):
            self.instance_host_backend = instance_host_backend()
        else:
            self.instance_host_backend = instance_host_backend

        if instance_credentials_backend is None:
            self.instance_credentials_backend = InMemoryBackend()
        elif callable(instance_credentials_backend):
            self.instance_credentials_backend = instance_credentials_backend()
        else:
            self.instance_credentials_backend = instance_credentials_backend

    def _get_instance_credentials(self, host):
        url = "https://{instance}/api/v1/apps".format(instance=host)
        try:
            response = requests.post(
                url,
                data=dict(
                    client_name=self.client_name,
                    redirect_uris=url_for(".authorized", _external=True),
                    scopes=self.scope,
                ),
            ).json()

            if "error" in response:
                return None

            return dict(client_id=response["client_id"], client_secret=response["client_secret"])

        except Exception:
            return None

    @property
    def credentials(self):
        if not self.instance_host:
            return {}
        cached = self.instance_credentials_backend.get(self)
        if cached:
            return cached

        retrieved = self._get_instance_credentials(self.instance_host)
        if not retrieved:
            return {}

        self.instance_credentials_backend.set(self, retrieved)
        return retrieved

    @property
    def instance_host(self):
        return self.instance_host_backend.get(self)

    @instance_host.setter
    def instance_host(self, value):
        self.instance_host_backend.set(self, value)

        instance_config = self.credentials
        self.client_id = instance_config.get("client_id")

        lazy.invalidate(self.session, "token")

    @instance_host.deleter
    def instance_host(self):
        self.instance_host_backend.delete(self)
        lazy.invalidate(self.session, "token")

    @property
    def client_secret(self):
        return self.credentials.get("client_secret")

    @client_secret.setter
    def client_secret(self, value):
        pass

    @property
    def authorization_url(self):
        instance = self.instance_host
        return "https://{instance}/oauth/authorize".format(instance=instance)

    @authorization_url.setter
    def authorization_url(self, value):
        pass

    @property
    def token_url(self):
        instance = self.instance_host
        return "https://{instance}/oauth/token".format(instance=instance)

    @token_url.setter
    def token_url(self, value):
        pass

    @lazy
    def session(self):
        """
        This is a session between the consumer (your website) and the provider
        (e.g. Twitter). It is *not* a session between a user of your website
        and your website.
        :return:
        """

        instance = self.instance_host

        ret = self.session_class(
            client_id=self.credentials.get("client_id"),
            client=self.client,
            auto_refresh_url=self.auto_refresh_url,
            auto_refresh_kwargs=self.auto_refresh_kwargs,
            scope=self.scope,
            state=self.state,
            blueprint=self,
            base_url="https://{instance}".format(instance=instance),
            **self.kwargs
        )

        def token_updater(token):
            self.token = token

        ret.token_updater = token_updater
        return self.session_created(ret)

    def login(self):
        if "instance_host" in request.args:
            self.instance_host = request.args["instance_host"]

        return super().login()


def make_mastodon_blueprint(
    client_name,
    backend=None,
    instance_host_backend=None,
    instance_credentials_backend=None,
    scope="read",
):
    if backend is None:
        backend = SessionStorage(key="{bp.name}_{bp.instance_host}_oauth_token")

    mastodon_bp = MastodonConsumerBlueprint(
        "mastodon",
        __name__,
        client_name=client_name,
        scope=scope,
        backend=backend,
        instance_credentials_backend=instance_credentials_backend,
    )

    @mastodon_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.mastodon_oauth = mastodon_bp.session

    return mastodon_bp


mastodon = LocalProxy(partial(_lookup_app_object, "mastodon_oauth"))
