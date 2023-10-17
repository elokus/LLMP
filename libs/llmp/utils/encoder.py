import json
from enum import Enum
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        if isinstance(obj, Enum):
            return obj.value

        return json.JSONEncoder.default(self, obj)


def dumps_encoder(obj):
    return json.dumps(obj, cls=JSONEncoder)
