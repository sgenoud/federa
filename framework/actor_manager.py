from framework.api.actor import make_actor_blueprint


class ActorManager:
    def __init__(self, name, find_actor, external_key_store=None):
        self._activities = {}
        self._default_activity = None

        self.external_key_store = external_key_store

        self._lists = {}

        self._find_actor = find_actor

        self.name = name
        self.blueprint = make_actor_blueprint(name, actor_manager=self)

    def find(self, actor_id):
        return self._find_actor(actor_id)

    def handle_activity(self, actor, activity):
        if "type" not in activity:
            return None

        type_ = activity["type"].lower()
        if type_ in self._activities:
            return self._activities[type_](actor, activity)

        if self._default_activity is not None:
            return self._default_activity(actor, activity)

        return None

    def register_activity(self, activity_type):
        def function_wrapper(fcn):
            self._activities[activity_type.lower()] = fcn
            return fcn

        return function_wrapper

    def register_default_activity(self, fcn):
        self._default_activity = fcn
        return fcn

    def register_list(self, list_type):
        def function_wrapper(fcn):
            self._lists[list_type.lower()] = fcn
            return fcn

        return function_wrapper

    def supports_list(self, list_type):
        return list_type.lower() in self._lists

    def build_list(self, actor, list_type):
        return self._lists[list_type.lower()](actor)
