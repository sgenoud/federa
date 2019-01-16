from bloop.session import key_schema, index_projection, attribute_definitions

from server.config import Configuration
from server.db import db
from server.model import GroupActivity


def run():
    config = Configuration()

    db.init_app(config.LOCAL_DYNAMODB, prefix=config.TABLE_PREFIX, skip=True)

    table_name = db.engine._compute_table_name(GroupActivity)
    index = [g for g in GroupActivity.Meta.gsis if g.dynamo_name == "by_group"][0]

    table_changes = {
        "TableName": table_name,
        "AttributeDefinitions": attribute_definitions(GroupActivity),
        "GlobalSecondaryIndexUpdates": [
            {
                "Create": {
                    "IndexName": index.dynamo_name,
                    "KeySchema": key_schema(index=index),
                    "Projection": index_projection(index),
                    "ProvisionedThroughput": {
                        # On create when not specified, use minimum values instead of None
                        "WriteCapacityUnits": index.write_units or 1,
                        "ReadCapacityUnits": index.read_units or 1,
                    },
                }
            }
        ],
    }

    return db.engine.session.dynamodb_client.update_table(**table_changes)
