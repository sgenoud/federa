from datetime import datetime, timezone

from bloop import Binary, Boolean, Column, DateTime, GlobalSecondaryIndex, String, UUID

from framework.crypto_utils import new_key, extract_public_key, serialize, deserialize
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


class Group(db.Model):
    type = "Group"
    id = Column(String, hash_key=True)
    name = Column(String)
    summary = Column(String)
    private_key = Column(RSAKey(False), default=new_key)

    @property
    def public_key(self):
        return extract_public_key(self.private_key)


class GroupMember(db.Model):
    id = Column(UUID, hash_key=True)
    group_id = Column(String)
    follower_id = Column(String)
    is_admin = Column(Boolean, default=False)

    by_group = GlobalSecondaryIndex(projection=["follower_id"], hash_key="group_id")
    by_follower = GlobalSecondaryIndex(projection=["group_id", "is_admin"], hash_key="follower_id")


class GroupActivity(db.Model):
    id = Column(String, hash_key=True)
    group_id = Column(String)
    type = Column(String)
    object = Column(String)

    by_group = GlobalSecondaryIndex(projection="all", hash_key="group_id")
