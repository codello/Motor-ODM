from bson import ObjectId
from funcy import monkey


@monkey(ObjectId)
def __get_validators__():
    def validate(value):
        return ObjectId(value)

    yield validate


from .document import *
from .fixtures import *
