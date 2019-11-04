import base64
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse
from email.utils import format_datetime

import requests


from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from pyld import jsonld

# cache the downloaded "schemas", otherwise the library is super slow
# (https://github.com/digitalbazaar/pyld/issues/70)
_CACHE = {}
LOADER = jsonld.requests_document_loader()


def _caching_document_loader(url):
    if url in _CACHE:
        return _CACHE[url]
    resp = LOADER(url)
    _CACHE[url] = resp
    return resp


jsonld.set_document_loader(_caching_document_loader)


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

    return verify(key, to_verify, signature.get("signature"))


# Copied from https://github.com/tsileo/little-boxes/blob/master/little_boxes/linked_data_sig.py


def _options_hash(doc):
    doc = dict(doc["signature"])
    for k in ["type", "id", "signatureValue"]:
        if k in doc:
            del doc[k]
    doc["@context"] = "https://w3id.org/identity/v1"
    normalized = jsonld.normalize(doc, {"algorithm": "URDNA2015", "format": "application/nquads"})
    h = hashlib.new("sha256")
    h.update(normalized.encode("utf-8"))
    return h.hexdigest()


def _doc_hash(doc):
    doc = dict(doc)
    if "signature" in doc:
        del doc["signature"]
    normalized = jsonld.normalize(doc, {"algorithm": "URDNA2015", "format": "application/nquads"})
    h = hashlib.new("sha256")
    h.update(normalized.encode("utf-8"))
    return h.hexdigest()


def document_is_valid(get_key, content):
    to_be_signed = _options_hash(content) + _doc_hash(content)

    if (
        "signature" not in content
        or "signatureValue" not in content["signature"]
        or "creator" not in content["signature"]
    ):
        return False

    signature = content["signature"]["signatureValue"]
    key = get_key(content["signature"]["creator"])
    return verify(key, to_be_signed.encode("utf-8"), signature)


def signed_content(key, key_id, content):
    doc = dict(content)
    options = {
        "type": "RsaSignature2017",
        "creator": key_id,
        "created": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }
    doc["signature"] = options

    to_be_signed = _options_hash(doc) + _doc_hash(doc)
    options["signatureValue"] = sign(key, to_be_signed.encode("utf-8")).decode("ascii")
    return doc
