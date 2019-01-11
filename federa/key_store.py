import json

from bloop.exceptions import ConstraintViolation
import requests

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend

from federa.model import PublicKey
from federa.db import db


class KeyStore:
    def query_key(self, key_id):
        raw_key_info = requests.get(key_id, headers={"accept": "application/activity+json"})
        try:
            serialized_key = raw_key_info.json().get("publicKey", {}).get("publicKeyPem")
        except json.decoder.JSONDecodeError:
            print("could not decode")
            print(raw_key_info.text)
            return None

        if serialized_key is None:
            print("no key")
            return None

        public_key = load_pem_public_key(serialized_key.encode("ascii"), backend=default_backend())
        key = PublicKey(key_id=key_id, public_key=public_key)
        db.engine.save(key)
        return key

    def get(self, key_id):
        q = db.engine.query(PublicKey, key=PublicKey.key_id == key_id)
        try:
            return q.one().public_key
        except ConstraintViolation:
            key = self.query_key(key_id)
            if key is None:
                return None
            return key.public_key


key_store = KeyStore()
