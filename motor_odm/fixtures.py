from typing import Any

from funcy import monkey

from .document import Document

__all__ = []

try:
    import fastapi


    @monkey(fastapi.routing)
    def _prepare_response_content(res: Any, *, by_alias: bool = True, exclude_unset: bool):
        if isinstance(res, Document):
            return res
        return _prepare_response_content.original(res, by_alias=by_alias, exclude_unset=exclude_unset)
except ImportError:
    pass
