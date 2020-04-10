from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny

    Query = Optional[Union[DictStrAny, Any]]


def create_query(db_filter: "Query" = None, **kwargs: Any) -> "DictStrAny":
    if db_filter is None:
        query = {}
    elif not isinstance(db_filter, dict):
        query = {"_id": db_filter}
    else:
        query = dict(db_filter)
    query.update(kwargs)
    return query
