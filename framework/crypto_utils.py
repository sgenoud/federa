from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ENCODING = serialization.Encoding.PEM


def new_key(*args):
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())


def extract_public_key(private_key):
    return (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )


def serialize(key, public_only):
    if public_only:
        return key.public_bytes(
            encoding=ENCODING, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    return key.private_bytes(
        encoding=ENCODING,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


def deserialize(serialized_key, public_only):
    if public_only:
        return serialization.load_pem_public_key(serialized_key, backend=default_backend())
    return serialization.load_pem_private_key(
        serialized_key, password=None, backend=default_backend()
    )
