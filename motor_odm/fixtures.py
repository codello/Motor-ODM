from typing import Any, Union

from bson import ObjectId
from funcy import monkey

from .document import Document


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


def patch_fastapi():
    import fastapi

    @monkey(fastapi.routing)
    def _prepare_response_content(res: Any, *args, **kwargs):
        if isinstance(res, Document):
            return res
        return _prepare_response_content.original(res, **kwargs)


try:
    patch_fastapi()
except ImportError:
    pass
