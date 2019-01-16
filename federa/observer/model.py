from datetime import datetime, timezone

from bloop import Column, DateTime, String

from federa.db import db


class ObservedActivity(db.Model):
    observer = Column(String, hash_key=True)
    date = Column(DateTime, range_key=True, default=lambda: datetime.now(timezone.utc))
    type = Column(String, default="")

    source_host = Column(String, default="")

    object = Column(String, default="")
