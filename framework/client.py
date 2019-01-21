import requests

from framework.constants import WEBFINGER


def retrieve_actor(actor_string):
    print(f"str {actor_string}")
    parsed_finger = WEBFINGER.match(actor_string)

    if not parsed_finger["username"] or not parsed_finger["host"]:
        return None

    print(f"parsed {parsed_finger}")

    try:
        finger = requests.get(
            f"https://{parsed_finger['host']}/.well-known/webfinger",
            params={"resource": f"acct:{parsed_finger['username']}@{parsed_finger['host']}"},
        ).json()
    except ValueError:
        return None
    print(f"finger {finger}")

    if "links" not in finger:
        return None
    print(f"links")

    possible_ids = [
        info["href"]
        for info in finger["links"]
        if "type" in info and info["type"] == "application/activity+json"
    ]
    print(f"ids {possible_ids}")

    if not possible_ids:
        return None

    actor = requests.get(possible_ids[0], headers={"accept": "application/activity+json"})
    try:
        return actor.json()
    except ValueError:
        return None
