from bloop.exceptions import MissingObjects

from server.db import db
from server.model import OAuthKeys


class OAuthDynamoDbMemoryBackend:
    def __init__(self):
        self.cache = dict()

    def _fill_cache(self, host):
        keys = OAuthKeys(host=host)
        try:
            db.engine.load(keys)
        except MissingObjects:
            return {}

        value = {"client_id": keys.client_id, "client_secret": keys.client_secret}
        self.cache[host] = value
        return value

    def get(self, bp):
        cached = self.cache.get(bp.instance_host)
        if cached is None:
            return cached
        return self._fill_cache(bp.instance_host)

    def set(self, bp, value):
        host = bp.instance_host
        if not host:
            return
        self.cache[host] = value
        print("saving key")
        print(host)
        db.save(
            OAuthKeys(host=host, client_id=value["client_id"], client_secret=value["client_secret"])
        )

    def delete(self, bp):
        del self.cache[bp.instance_host]
