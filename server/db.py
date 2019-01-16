import boto3

from bloop import BaseModel, Engine


class PatchedDynamoDBClient:
    def __init__(self, real_client):
        self.__client = real_client
        self.mock_ttl = {}
        self.mock_backups = {}

    def describe_time_to_live(self, TableName, **_):
        r = "ENABLED" if self.mock_ttl.get(TableName) else "DISABLED"
        return {"TimeToLiveDescription": {"TimeToLiveStatus": r}}

    def describe_continuous_backups(self, TableName, **_):
        r = "ENABLED" if self.mock_backups.get(TableName) else "DISABLED"
        return {"ContinuousBackupsDescription": {"ContinuousBackupsStatus": r}}

    # TODO override any other methods that DynamoDBLocal doesn't provide

    def __getattr__(self, name):
        # use the original client for everything else
        return getattr(self.__client, name)


def patch_engine(engine):
    client = PatchedDynamoDBClient(engine.session.dynamodb_client)
    engine.session.dynamodb_client = client
    return client


class DynamoDb:
    def __init__(self):
        self._local_dynamodb = None
        self.Model = BaseModel
        self.engine = None

    def _init_local(self, local_dynamodb="http://127.0.0.1:4444", name_template="{table_name}"):
        dynamodb = boto3.client("dynamodb", endpoint_url=local_dynamodb)
        dynamodbstreams = boto3.client("dynamodbstreams", endpoint_url=local_dynamodb)

        self.engine = Engine(
            dynamodb=dynamodb, dynamodbstreams=dynamodbstreams, table_name_template=name_template
        )

        client = patch_engine(self.engine)

        client.mock_ttl["MyTableName"] = True
        client.mock_backups["MyTableName"] = False

    def init_app(self, local_dynamodb=None, prefix="", skip=False):
        name_template = prefix + "{table_name}"
        if local_dynamodb is not None:
            self._init_local(local_dynamodb, name_template)
        else:
            self.engine = Engine(table_name_template=name_template)
        self.engine.bind(self.Model, skip_table_setup=skip)


db = DynamoDb()
