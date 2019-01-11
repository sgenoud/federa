import base64
from datetime import datetime, timezone
from urllib.parse import urlparse
from email.utils import format_datetime

import requests

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

TARGET = "(request-target)"


def sign(key, message):
    signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature)


def verify(key, message, signature):
    try:
        key.verify(
            base64.b64decode(signature),
            message.encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def signed_request(key, key_id, method, url, *args, signing_headers=(), headers=None, **kwargs):
    if headers is None:
        headers = {}
    urlinfo = urlparse(url)
    headers["Date"] = format_datetime(datetime.now(timezone.utc), True)
    headers["Host"] = urlinfo.hostname

    used_headers = [
        (TARGET, f"{method.lower()} {urlinfo.path}"),
        ("Host", headers["Host"]),
        ("Date", headers["Date"]),
    ] + [(header, headers[header]) for header in signing_headers if header in headers]

    to_sign = "\n".join(
        [f"{header.lower()}: {header_value}" for header, header_value in used_headers]
    )
    signature = sign(key, to_sign.encode("ascii"))

    signature_parts = (
        ("keyId", key_id),
        ("algorithm", "rsa-sha256"),
        ("headers", " ".join(h for h, _ in used_headers)),
        ("signature", signature.decode("ascii")),
    )
    headers["Signature"] = ",".join(['{}="{}"'.format(k, v) for k, v in signature_parts])
    print(headers)
    return requests.request(method, url, *args, headers=headers, **kwargs)


def _parse_sig_val(chars):
    key, _, val = chars.partition("=")
    return key, val[1:-1]


def parse_signature_header(header):
    return dict(_parse_sig_val(elem.strip()) for elem in header.split(",") if elem)


def signature_is_valid(get_key, headers, path, method="GET"):
    target = f"{method.lower()} {path}"
    signature = parse_signature_header(headers.get("Signature", ""))
    if "headers" not in signature or "signature" not in signature or "keyId" not in signature:
        return False

    to_verify = "\n".join(
        f"{header.lower()}: {target if header == TARGET else headers.get(header)}"
        for header in signature["headers"].split(" ")
    )
    key = get_key(signature["keyId"])
    if not key:
        return False
    print(to_verify)

    return verify(key, to_verify, signature.get("signature"))
