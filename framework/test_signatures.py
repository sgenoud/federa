from .signatures import signature_is_valid
from .crypto_utils import deserialize


pubkey = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvU5+dzpcdibYAKqwJj+7
PFdhSE15N5hbc6RPVmCaWr1qNurN43JzxzYOhhehqYdVvB19nK42gfvBt7km3pbl
/arRxuAN9dNugGZ3Ac//MvYstXVXfpRuEOyCkrAjoYD26BDHK41Bx8YtYiL6Ca2t
dX5FI5gJEkuoRRrcK+I+6BO0euOAyQYDfjsG0OkgnYJ5luwnzA7FNfQlTV/To9v/
7eUqmaHtI6bSth4xX9sesIhQYJDdbf3BjUqipsLW57ag1+gN0koxxbV9xl6LLVmn
/P2hf35Hurl5hOvny7M+Y2snGmxtmudDnHKTP2Cz94SrhUG28ovQ2jzhaeeS8prR
EwIDAQAB
-----END PUBLIC KEY-----
"""

pubkey_test = """
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDCFENGw33yGihy92pDjZQhl0C3
6rPJj+CvfSC8+q28hxA161QFNUd13wuCTUcq0Qd2qsBe/2hFyc2DCJJg0h1L78+6
Z4UMR7EOcpfdUE9Hf3m/hs+FUR45uBJeDK1HSFHD8bHKD6kv8FPGfJTotc+2xjJw
oYi+1hqp1fIekaxsyQIDAQAB
-----END PUBLIC KEY-----
"""

privkey_test = """
-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDCFENGw33yGihy92pDjZQhl0C36rPJj+CvfSC8+q28hxA161QF
NUd13wuCTUcq0Qd2qsBe/2hFyc2DCJJg0h1L78+6Z4UMR7EOcpfdUE9Hf3m/hs+F
UR45uBJeDK1HSFHD8bHKD6kv8FPGfJTotc+2xjJwoYi+1hqp1fIekaxsyQIDAQAB
AoGBAJR8ZkCUvx5kzv+utdl7T5MnordT1TvoXXJGXK7ZZ+UuvMNUCdN2QPc4sBiA
QWvLw1cSKt5DsKZ8UETpYPy8pPYnnDEz2dDYiaew9+xEpubyeW2oH4Zx71wqBtOK
kqwrXa/pzdpiucRRjk6vE6YY7EBBs/g7uanVpGibOVAEsqH1AkEA7DkjVH28WDUg
f1nqvfn2Kj6CT7nIcE3jGJsZZ7zlZmBmHFDONMLUrXR/Zm3pR5m0tCmBqa5RK95u
412jt1dPIwJBANJT3v8pnkth48bQo/fKel6uEYyboRtA5/uHuHkZ6FQF7OUkGogc
mSJluOdc5t6hI1VsLn0QZEjQZMEOWr+wKSMCQQCC4kXJEsHAve77oP6HtG/IiEn7
kpyUXRNvFsDE0czpJJBvL/aRFUJxuRK91jhjC68sA7NsKMGg5OXb5I5Jj36xAkEA
gIT7aFOYBFwGgQAQkWNKLvySgKbAZRTeLBacpHMuQdl1DfdntvAyqpAZ0lY0RKmW
G6aFKaqQfOXKCyWoUiVknQJAXrlgySFci/2ueKlIE1QqIiLSZ8V8OlpFLRnb1pzI
7U1yQXnTAEFYM560yJlzUpOb1V4cScGd365tiSMvxLOvTA==
-----END RSA PRIVATE KEY-----
"""

headers = {
    "content-type": "application/activity+json",
    "date": "Fri, 11 Jan 2019 09:29:02 GMT",
    "digest": "SHA-256=TJA8B6dJhHCVedxUbAsBrNlVKVehfUL09IGljgNvgYs=",
    "host": "dev-group.federa.site",
    "Signature": 'keyId="https://malfunctioning.technology/users/mytestaccount#main-key",'
    'algorithm="rsa-sha256",headers="(request-target) host date digest content-type",'
    'signature="RwHFZKXCRNKXLDHhci06GU6Oji0Q9bY2nuIrQn3oa52XmrlaABGGfHEq2av2y0Uppwaah'
    "nRksAbagO5yt8BFb4wa2AsXpWDMyn7jaiPX0gfseKyZw0LW/wJcvSTZhWFuee9Awv3JfnkAqpP9QbKGi"
    "FFTG4ryjwgQ+D4U+peoiFgerwfXNMrGeP4eRpcQuBtIkgImb91tAVKzKQiGf3Hu3LmBE+4Ue3VIrTMwM"
    "GZViYpYEAs6Ad0Wy3TtGPZ7mnwHfvVV165R1xZnIPkfrJltshvkq6nxn1+"
    'P8ugVroNVIFLQrMetUltItVtUBCgxhKXHXCJMlkqLYWLpYeCykzPBUg=="',
}

headers_test = {
    "host": "example.com",
    "date": "Thu, 05 Jan 2014 21:31:40 GMT",
    "content-type": "application/json",
    "digest": "SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=",
    "content-length": 18,
    "Signature": 'keyId="Test",algorithm="rsa-sha256",headers="date",signature="jKyvPcxB4JbmYY4mByyBY7cZfNl4OW9HpFQlG7N4YcJPteKTu4MWCLyk+gIr0wDgqtLWf9NLpMAMimdfsH7FSWGfbMFSrsVTHNTk0rK3usrfFnti1dxsM4jl0kYJCKTGI/UWkqiaxwNiKqGcdlEDrTcUhhsFsOIo8VhddmZTZ8w="',
}


def get_key_prod(k):
    return deserialize(pubkey.encode("ascii"), True)


def get_key_test(k):
    return deserialize(pubkey_test.encode("ascii"), True)


def test_signature_prod():
    assert signature_is_valid(get_key_prod, headers, "/testaccount/inbox", "POST")


def test_signature_test():
    """
    Test with values from
    https://github.com/joyent/node-http-signature/blob/master/http_signing.md
    """
    assert signature_is_valid(get_key_test, headers_test, "/foo?param=value&pet=dog", "POST")
