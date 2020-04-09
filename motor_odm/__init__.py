"""The :mod:`motor_odm` module contains classes and functions related to Motor-ODM."""

from typing import Union

from bson import ObjectId
from funcy import monkey


@monkey(ObjectId)
def __get_validators__():
    """
    Returns a generator yielding the validators for the `ObjectId` type.
    """

    def validate(value: Union[str, bytes]):
        """
        Creates an `ObjectId` from a value. If the
        :param value: An `ObjectId` or a string.
        :return: An `ObjectId`.
        :raises TypeError: If `value` os not a string type.
        :raises InvalidId: If `value` does not represent a valid `ObjectId`.
        """

        return ObjectId(value)

    yield validate


from .document import *
from .fixtures import *
