from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny

    Query = Optional[Union[DictStrAny, Any]]


def create_query(db_filter: "Query" = None, **kwargs: Any) -> "DictStrAny":
    """
    Creates a MongoDB query from the specified arguments. This helper can be invoked in three ways (which can also be
    combined):

    Create a filter from keyword arguments. The arguments are transformed into a :class:`dict` and returned verbatim.

    >>> create_query(username="john")
    {'username': 'john'}

    :param db_filter: Either a dict that is included as a filter or any other type that is used as an ``_id`` query.
    :param kwargs: Filter arguments. Keyword arguments are preceeded by the ``db_filter`` parameter.
    :return: A :class:`dict` that can be used to filter a MongoDB collection.
    """
    query = kwargs
    if db_filter is None:
        pass
    elif not isinstance(db_filter, dict):
        query.update({"_id": db_filter})
    else:
        query.update(db_filter)
    return query
