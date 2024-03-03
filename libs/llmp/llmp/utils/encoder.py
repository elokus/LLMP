import json
from datetime import datetime, date
from enum import Enum
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, datetime):
            return str(obj)
        if isinstance(obj, date):
            return str(obj)

        return json.JSONEncoder.default(self, obj)


def dumps_encoder(obj):
    return json.dumps(obj, cls=JSONEncoder)
