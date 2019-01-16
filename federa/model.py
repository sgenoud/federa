from datetime import datetime, timezone

from bloop import Binary, Column, DateTime, String

from framework.crypto_utils import serialize, deserialize
from federa.db import db


class RSAKey(Binary):
    def __init__(self, public_only=True):
        self.public_only = public_only
        super().__init__()

    def dynamo_dump(self, key, *, context, **kwargs):
        if key is None:
            return None

        serialized_key = serialize(key, self.public_only)

        return super().dynamo_dump(serialized_key, context=context, **kwargs)

    def dynamo_load(self, value, *, context, **kwargs):
        serialized_key = super().dynamo_load(value, context=context, **kwargs)
        if serialized_key is None:
            return None

        return deserialize(serialized_key, self.public_only)


class Account(db.Model):
    account_name = Column(String, hash_key=True)
    name = Column(String)
    token = Column(String)


class PublicKey(db.Model):
    key_id = Column(String, hash_key=True)
    public_key = Column(RSAKey)
    last_change = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OAuthKeys(db.Model):
    host = Column(String, hash_key=True)
    client_id = Column(String)
    client_secret = Column(String)
