from .common import notify_update
from .app import create_app


def group_updated(change_info, context):
    updates = (
        change.get("dynamodb").get("Keys", {}).get("id", {}).get("S")
        for change in change_info.get("Records", [])
        if change.get("eventName") == "MODIFY"
    )

    if not updates:
        return

    with create_app().app_context():
        for group_name in updates:
            notify_update(group_name)
