from bloop import Boolean, Column, GlobalSecondaryIndex, String, UUID

from framework.crypto_utils import new_key, extract_public_key
from federa.db import db
from federa.model import RSAKey


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
