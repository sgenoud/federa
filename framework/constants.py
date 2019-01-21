import re

# from https://github.com/dsblank/activitypub/blob/master/activitypub/manager/ap_routes.py
WEBFINGER = re.compile(r"@?(?:acct:)?(?P<username>[\w.!#$%&\'*+-/=?^_`{|}~]+)@(?P<host>[\w.:-]+)")

AP_CONTEXT = "https://www.w3.org/ns/activitystreams"
PUBLIC_AUDIENCE = ""
