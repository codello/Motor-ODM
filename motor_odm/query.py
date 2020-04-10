from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny

    Query = Optional[Union[DictStrAny, Any]]


def create_query(query: 'Query' = None, **kwargs) -> 'DictStrAny':
    if query is None:
        query = {}
    elif not isinstance(query, dict):
        return {"_id": query}
    else:
        query = dict(query)
    query.update(kwargs)
    return query
