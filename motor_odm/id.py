from typing import Any, Callable, Iterator, Union

from bson import ObjectId

from motor_odm.helpers import monkey_patch


@monkey_patch(ObjectId)
def __get_validators__() -> Iterator[Callable[[Any], ObjectId]]:
    """
    Returns a generator yielding the validators for the `ObjectId` type.
    """

    def validate(value: Union[str, bytes]) -> ObjectId:
        """
        Creates an `ObjectId` from a value. If the
        :param value: An `ObjectId` or a string.
        :return: An `ObjectId`.
        :raises TypeError: If `value` os not a string type.
        :raises InvalidId: If `value` does not represent a valid `ObjectId`.
        """

        return ObjectId(value)

    yield validate
