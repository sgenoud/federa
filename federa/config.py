from flask_env import MetaFlaskEnv


class Configuration(metaclass=MetaFlaskEnv):
    DEBUG = False
    DEBUG_INBOX_IGNORE_SIGNATURE = False
    LOCAL_DYNAMODB = None
    SERVER_NAME = "localhost:3003"
    SECRET_KEY = "this is super secret"
    SERVICE_NAME = "Federa"
    TABLE_PREFIX = ""
    WEBFINGER_CHECK_HOST = True
